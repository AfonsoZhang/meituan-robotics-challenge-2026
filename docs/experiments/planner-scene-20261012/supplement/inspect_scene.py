"""Read the isolated MoveIt scene after diagnostic tools, without modifying it."""
from pathlib import Path
import json, sys
import rclpy
from moveit_msgs.msg import PlanningSceneComponents
from moveit_msgs.srv import GetPlanningScene, GetStateValidity
from rosidl_runtime_py.convert import message_to_ordereddict

out = Path(sys.argv[1]); out.mkdir(parents=True)
rclpy.init(); node = rclpy.create_node('acceptance_scene_reader')
result = {'scope': 'Read-only scene and current-state validity; no scene mutation, Goal or execution', 'status': 'FAIL'}
def call(service, name, request):
    client = node.create_client(service, name)
    try:
        assert client.wait_for_service(timeout_sec=8), name
        future = client.call_async(request)
        rclpy.spin_until_future_complete(node, future, timeout_sec=8)
        assert future.done(), name + ' timed out'
        return future.result()
    finally:
        node.destroy_client(client)
try:
    request = GetPlanningScene.Request()
    request.components.components = (PlanningSceneComponents.WORLD_OBJECT_GEOMETRY |
        PlanningSceneComponents.ROBOT_STATE | PlanningSceneComponents.ROBOT_STATE_ATTACHED_OBJECTS)
    response = call(GetPlanningScene, '/get_planning_scene', request)
    (out/'scene.json').write_text(json.dumps(message_to_ordereddict(response), indent=2) + '\n')
    objects = response.scene.world.collision_objects
    table = next(o for o in objects if o.id == 'table')
    assert len(table.primitives) == 1 and list(table.primitives[0].dimensions) == [0.9, 1.2, 0.05]
    state = response.scene.robot_state
    check = GetStateValidity.Request(); check.robot_state = state; check.group_name = 'manipulator'
    validity = call(GetStateValidity, '/check_state_validity', check)
    (out/'current-state-validity.json').write_text(json.dumps(message_to_ordereddict(validity), indent=2) + '\n')
    result.update({'object_ids': [o.id for o in objects], 'table_frame': table.header.frame_id,
        'table': message_to_ordereddict(table), 'global_attached_objects': [o.object.id for o in state.attached_collision_objects],
        'current_joints': message_to_ordereddict(state.joint_state), 'current_state_valid': validity.valid,
        'status': 'PASS'})
    assert validity.valid, 'Current Fake state invalid'
    assert not state.attached_collision_objects, 'Unexpected persistent global payload'
except Exception as exc:
    result['status'] = 'FAIL'; result['exception'] = repr(exc)
finally:
    node.destroy_node(); rclpy.shutdown()
    (out/'summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False))
raise SystemExit(0 if result['status'] == 'PASS' else 1)
