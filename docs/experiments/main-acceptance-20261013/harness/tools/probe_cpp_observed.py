"""Extend the existing external acceptance client with read-only DDS witnesses.

No upstream changes; no observer sends a PickPlace Goal or Cancel. Terminal
GetResult queries occur only after the Task has terminated. Times are local
receipt times, not internal callback/dispatch timestamps. Codex assisted.
"""
from datetime import datetime, timezone
import hashlib
import time
import probe_cpp_actions as probe


class ObservedSession(probe.Session):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from action_msgs.msg import GoalStatusArray
        from mtc_interfaces.action import PickPlace, ExecuteTask
        from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
        from rosidl_runtime_py.convert import message_to_ordereddict as convert
        self.witness = []
        self.subscriptions = []
        self.result['dds_witness'] = self.witness
        self.result['started_at'] = datetime.now(timezone.utc).isoformat()
        self.result['binary_identity'] = []
        for exe, process, _ in self.children:
            from pathlib import Path
            binary = Path(f'/proc/{process.pid}/exe').resolve()
            self.result['binary_identity'].append({'pid': process.pid,
                'executable': str(binary), 'sha256': hashlib.sha256(binary.read_bytes()).hexdigest()})
        for base, action in [('/mtc/task/execute', ExecuteTask),
                             ('/mtc/manipulation/pick_place', PickPlace)]:
            for suffix, cls, durability in [('/_action/status', GoalStatusArray, DurabilityPolicy.TRANSIENT_LOCAL),
                    ('/_action/feedback', action.Impl.FeedbackMessage, DurabilityPolicy.VOLATILE)]:
                topic = base + suffix
                def callback(message, topic=topic):
                    self.witness.append({'topic': topic, 'received_monotonic': time.monotonic(),
                                         'message': convert(message)})
                self.subscriptions.append(self.node.create_subscription(cls, topic, callback,
                    QoSProfile(depth=100, reliability=ReliabilityPolicy.RELIABLE, durability=durability)))

    def client(self, action, name, expected_node):
        from mtc_interfaces.action import PickPlace
        from rclpy.action import get_action_server_names_and_types_by_node, get_action_client_names_and_types_by_node
        if action is not PickPlace:
            return super().client(action, name, expected_node)
        deadline = time.monotonic() + 8
        servers, clients = [], []
        while time.monotonic() < deadline:
            self.spin(.05)
            servers, clients = [], []
            for node, ns in self.node.get_node_names_and_namespaces():
                for dest, fn in [(servers, get_action_server_names_and_types_by_node),
                                 (clients, get_action_client_names_and_types_by_node)]:
                    for topic, types in fn(self.node, node, ns):
                        if topic == name:
                            dest.append({'node': node, 'namespace': ns, 'types': types})
            if len(servers) == 1 and len(clients) == 1:
                break
        self.result.setdefault('servers', {})[name] = servers
        self.result.setdefault('clients', {})[name] = clients
        self.check('PickPlace unique C++ server', len(servers) == 1 and servers[0]['node'] == expected_node)
        self.check('Only C++ Task is downstream ActionClient', len(clients) == 1 and clients[0]['node'] == 'mtc_mock_task')
        self.result['topic_qos'] = {}
        for topic in [name + '/_action/status', name + '/_action/feedback']:
            self.result['topic_qos'][topic] = [{'node': e.node_name, 'namespace': e.node_namespace,
                'type': e.topic_type, 'reliability': str(e.qos_profile.reliability),
                'durability': str(e.qos_profile.durability), 'history': str(e.qos_profile.history),
                'depth': e.qos_profile.depth} for e in self.node.get_publishers_info_by_topic(topic)]
        return None

    def send(self, client, goal):
        start = time.monotonic()
        handle, record = super().send(client, goal)
        record.update(request_monotonic=start, response_monotonic=time.monotonic())
        return handle, record

    def cancel(self, handle, record):
        record['cancel_request_monotonic'] = time.monotonic()
        super().cancel(handle, record)
        record['cancel_response_monotonic'] = time.monotonic()

    def terminal(self, handle, record, timeout=30):
        result = super().terminal(handle, record, timeout)
        record['terminal_received_monotonic'] = time.monotonic()
        self.spin(.1)
        from mtc_interfaces.action import PickPlace
        from rosidl_runtime_py.convert import message_to_ordereddict as convert
        uuids = {}
        first_seen = {}
        for row in self.witness:
            if row['topic'] != '/mtc/manipulation/pick_place/_action/status':
                continue
            for state in row['message']['status_list']:
                key = tuple(state['goal_info']['goal_id']['uuid'])
                first_seen.setdefault(key, row['received_monotonic'])
                if first_seen[key] < record['request_monotonic']:
                    continue
                uuids.setdefault(key, []).append({'status': state['status'], 'received_monotonic': row['received_monotonic']})
        record['child_statuses_in_window'] = [{'uuid': list(k), 'states': v} for k, v in uuids.items()]
        # Exclude cached UUIDs first seen before this parent's send window.
        terminal = [key for key, states in uuids.items() if states[-1]['status'] in (4, 5, 6)]
        if terminal:
            service = self.node.create_client(PickPlace.Impl.GetResultService,
                                             '/mtc/manipulation/pick_place/_action/get_result')
            try:
                self.check('child terminal result service', service.wait_for_service(timeout_sec=3))
                record['child_terminal_results'] = []
                for uuid in terminal:
                    request = PickPlace.Impl.GetResultService.Request()
                    request.goal_id.uuid = list(uuid)
                    answer = self.wait(service.call_async(request), 5)
                    record['child_terminal_results'].append({'uuid': list(uuid), 'response': convert(answer),
                                                             'received_monotonic': time.monotonic()})
            finally:
                self.node.destroy_client(service)
        if self.result['case'] in ('task-basic-sequence-after-idle', 'task-associated-cancel'):
            expected_count = len(record['goal']['ordered_colors']) if result.status == 4 else 1
            self.check('child UUID count in this parent send window', len(uuids) == expected_count)
            answers = record.get('child_terminal_results', [])
            self.check('independent child terminal results match parent', len(answers) == expected_count and
                       all(a['response']['status'] == result.status and
                           a['response']['result']['error_code'] == result.result.error_code for a in answers))
        return result


probe.Session = ObservedSession
raise SystemExit(probe.main())
