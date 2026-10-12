#!/usr/bin/env python3
"""Reproduce one observed upstream SHA in a disposable, networkless container.

OpenAI Codex assisted, 2026-10-11. Host operations only copy source, orchestrate
Docker, and save evidence. Upstream build/test code runs inside the container.
"""
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import signal
import subprocess
import sys
import tarfile
import time

from wake_main import container_name, root_hash


def stamp():
    return datetime.now(timezone.utc).isoformat()


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def main():
    config = json.loads(Path(sys.argv[1]).read_text())
    event = json.loads(Path(sys.argv[2]).read_text())
    sha = event['commit']
    assert re.fullmatch('[0-9a-f]{40}', sha), sha
    root = Path(config['output'])
    evidence = root / 'runs' / Path(sys.argv[2]).stem
    evidence.mkdir()  # never overwrite a previous run
    logs = evidence / 'logs'
    logs.mkdir()
    ready = json.loads(Path(config['ready_file']).read_text())
    docker = config['docker']
    name = container_name(root, sha)
    steps = []
    summary = {'started_at': stamp(), 'upstream': event, 'environment': ready,
               'container': name, 'steps': steps,
               'scope': 'Isolated Jazzy / GenericSystem only; no physical devices',
               'not_verified': ['NUC and physical robot', 'SDK licence/vendor checksum',
                                'New C++ FSM end-to-end launch unless provided as an upstream test',
                                'Perception/tool physical evidence', 'TSan race analysis']}
    created = False

    def interrupted(signum, _frame):
        raise RuntimeError('Runner interrupted by signal ' + str(signum))

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    write(evidence / 'summary.json', summary)

    def run(label, argv, timeout=180, data=None):
        start = stamp()
        with (logs / (label + '.log')).open('wb') as stream:
            try:
                proc = subprocess.run(argv, input=data, stdout=stream,
                                      stderr=subprocess.STDOUT, timeout=timeout)
                code = proc.returncode
            except subprocess.TimeoutExpired:
                code = 124
        steps.append({'name': label, 'argv': argv, 'started_at': start,
                      'ended_at': stamp(), 'exit_code': code})
        write(evidence / 'summary.json', summary)
        print(label, code, flush=True)
        return code

    def shell(label, script, timeout=180):
        return run(label, [docker, 'exec', name, 'bash', '-c', script], timeout)

    ros = ('source /opt/ros/jazzy/setup.bash; '
           'source /driver_work/install/setup.bash; '
           'export ROS_DOMAIN_ID=98 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST '
           'RMW_IMPLEMENTATION=rmw_fastrtps_cpp PYTHONDONTWRITEBYTECODE=1 '
           'XML_CATALOG_FILES=/acceptance-tools/offline-schema/catalog.xml; '
           'unset ROS_STATIC_PEERS ROS_LOCALHOST_ONLY FASTRTPS_DEFAULT_PROFILES_FILE '
           'FASTDDS_DEFAULT_PROFILES_FILE CYCLONEDDS_URI; ')
    try:
        if run('create', [docker, 'run', '-d', '--name', name, '--network', 'none',
                          '--cpus', '2', '--memory', '4g', '--pids-limit', '512',
                          '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                          '--label', 'mtc.purpose=upstream-reproduction',
                          '--label', 'mtc.event=' + Path(sys.argv[2]).stem,
                          '--label', 'mtc.watch-root=' + root_hash(root), ready['image'],
                          'sleep', 'infinity']):
            raise RuntimeError('Container creation failed')
        created = True
        run('isolation', [docker, 'inspect', name])
        shell('directories', 'mkdir -p /candidate /candidate-evidence /acceptance-tools')
        # The upstream audit compares historical tests using git show, so a
        # working-tree archive alone is insufficient. Bundle the observed Git
        # history, then detach the candidate at the exact event SHA.
        bundle = evidence / 'source.bundle'
        if run('source-bundle', ['git', '--git-dir=' + str(root / 'upstream.git'),
                                'bundle', 'create', str(bundle), '--all'], 120):
            raise RuntimeError('Source bundle failed')
        payload = bundle.read_bytes()
        summary['source_bundle_sha256'] = hashlib.sha256(payload).hexdigest()
        if run('source-copy', [docker, 'exec', '-i', name, 'sh', '-c',
                               'cat > /candidate-source.bundle'], data=payload):
            raise RuntimeError('Source copy failed')
        if shell('source-checkout', 'git -C /candidate init && git -C /candidate fetch '
                 '/candidate-source.bundle "+refs/*:refs/remotes/upstream/*" && '
                 'git -C /candidate checkout --detach ' + sha + ' && git -C /candidate rev-parse HEAD'):
            raise RuntimeError('Source checkout failed')
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode='w') as tar:
            for filename in ('probe_moveit.py', 'probe_task_mock.py'):
                tar.add(Path(config['harness_directory']) / filename, arcname=filename)
            if ready.get('offline_schema_directory'):
                tar.add(ready['offline_schema_directory'], arcname='offline-schema')
        if run('probes', [docker, 'exec', '-i', name, 'tar', '--no-same-owner', '-xf', '-', '-C', '/acceptance-tools'], data=buf.getvalue()):
            raise RuntimeError('Probe import failed')
        shell('environment', ros + 'env | sort | grep -E "^(ROS|RMW|AMENT|COLCON|CMAKE_PREFIX_PATH|PYTHONPATH)="; '
              'dpkg-query -W; git -C /driver_ws/src/aubo_ros2_driver rev-parse HEAD; '
              'git -C /driver_ws/src/aubo_ros2_driver/aubo_description rev-parse HEAD')
        shell('dependencies', ros + 'cd /candidate; rosdep check --from-paths src --ignore-src', 180)
        shell('source-inventory', "find /candidate -type f '(' -name '*.launch.py' -o -name 'package.xml' -o -iname '*moveit*' ')' -print")
        build = shell('build', ros + 'set -e; cd /candidate; '
                      'export CMAKE_BUILD_PARALLEL_LEVEL=2 MAKEFLAGS=-j2; '
                      'colcon --log-base /candidate-evidence/build-log build '
                      '--build-base /candidate-build --install-base /candidate-install '
                      '--executor sequential --cmake-args -DBUILD_TESTING=ON -DCMAKE_CXX_STANDARD=17', 1800)
        if build == 124:
            # docker exec timeout does not kill its container process. Never
            # launch another step while a timed-out build might still run.
            raise RuntimeError('Build timed out; container will be stopped')
        if build == 0:
            candidate = ros + 'source /candidate-install/setup.bash; cd /candidate; '
            test = shell('colcon-test', candidate + 'colcon --log-base /candidate-evidence/test-log test '
                         '--build-base /candidate-build --install-base /candidate-install '
                         '--executor sequential --return-code-on-test-failure', 1200)
            if test == 124:
                raise RuntimeError('Tests timed out; container will be stopped')
            shell('test-results', candidate + 'colcon test-result --test-result-base /candidate-build --all')
            shell('test-xml', 'python3 - <<\'PY\'\nfrom pathlib import Path\nimport shutil\n'
                  'for p in Path("/candidate-build").rglob("*.xml"):\n'
                  ' if "test_results" in p.parts or p.name == "pytest.xml":\n'
                  '  q=Path("/candidate-evidence/test-results")/p.relative_to("/candidate-build")\n'
                  '  q.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(p,q)\nPY')
            for label, file, arguments in (
                ('cpp-audit', 'tests/verify_cpp_audit_results.py', '--build-base /candidate-build'),
                ('python-mock-e2e', 'tests/test_mock_end_to_end.py', '')):
                shell(label, candidate + f'if test -f {file}; then timeout 120 python3 {file} {arguments}; else echo "NOT RUN: entrypoint absent"; exit 3; fi', 150)
            shell('ros-wiring-regression', candidate + 'if test -f tests/test_ros_wiring.py; then '
                  'timeout 90 python3 -m pytest -q tests/test_ros_wiring.py '
                  '--junitxml=/candidate-evidence/ros-wiring.xml; else '
                  'echo "NOT RUN: optional PR regression file absent"; fi', 110)
            shell('actual-task-mock', candidate + 'timeout --signal=TERM --kill-after=10 210 '
                  'python3 /acceptance-tools/probe_task_mock.py /candidate-evidence/task-mock', 230)
        # MoveIt is independent of candidate FSM build success. Keep the scope
        # explicit: the known driver/config pins come from the prepared image.
        shell('driver-rosdep', ros + 'rosdep check --from-paths /driver_ws/src/aubo_ros2_driver/aubo_description '
              '/driver_ws/src/aubo_ros2_driver/aubo_ros2_driver '
              '/driver_ws/src/aubo_ros2_driver/aubo_msgs /driver_ws/src/aubo_ros2_driver/aubo_dashboard_msgs '
              '/driver_ws/src/aubo_ros2_driver/aubo_moveit_config --ignore-src', 180)
        shell('driver-tests', ros + 'cd /driver_ws; timeout --signal=TERM --kill-after=10 160 colcon --log-base /candidate-evidence/driver-test-log test '
              '--build-base /driver_work/build --install-base /driver_work/install '
              '--executor sequential --packages-select aubo_description aubo_dashboard_msgs aubo_msgs '
              'aubo_ros2_driver aubo_moveit_config --return-code-on-test-failure', 180)
        shell('driver-test-results', ros + 'colcon test-result --test-result-base /driver_work/build --all')
        shell('driver-test-xml', 'python3 - <<\'PY\'\nfrom pathlib import Path\nimport shutil\n'
              'for p in Path("/driver_work/build").rglob("*.xml"):\n'
              ' if "test_results" in p.parts:\n'
              '  q=Path("/candidate-evidence/driver-test-results")/p.relative_to("/driver_work/build")\n'
              '  q.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(p,q)\nPY')
        driver_result = (logs / 'driver-test-results.log').read_text()
        match = re.search(r'Summary: (\d+) tests', driver_result)
        summary['driver_test_coverage'] = ('NO_TEST_CASES' if match and int(match[1]) == 0
                                           else 'SEE_DRIVER_TEST_RESULTS_LOG')
        shell('moveit-plan-execute', ros + 'timeout --signal=TERM --kill-after=10 180 '
              'python3 /acceptance-tools/probe_moveit.py /candidate-evidence/moveit', 200)
        summary['status'] = 'COMPLETED_WITH_FAILURES' if any(x['exit_code'] for x in steps) else 'CHECKS_PASSED_WITH_SCOPE_LIMITS'
    except Exception as exc:
        summary['status'] = 'INFRASTRUCTURE_OR_HARNESS_ERROR'
        summary['error'] = repr(exc)
    finally:
        # One cancellation enters cleanup; repeated TERM cannot skip evidence.
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        if created:
            run('stop', [docker, 'stop', '-t', '12', name], 30)
            # Keep the stopped container and copy its evidence even on failure.
            run('collect', [docker, 'cp', name + ':/candidate-evidence', str(evidence / 'container')], 120)
        if summary.get('status') == 'CHECKS_PASSED_WITH_SCOPE_LIMITS' and any(x['exit_code'] for x in steps):
            summary['status'] = 'COMPLETED_WITH_FAILURES'
        summary['ended_at'] = stamp()
        write(evidence / 'summary.json', summary)
        files = [{'path': str(p.relative_to(evidence)), 'bytes': p.stat().st_size,
                  'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                 for p in sorted(evidence.rglob('*')) if p.is_file()]
        write(evidence / 'index.json', {'created_at': stamp(), 'files': files})
    return 0 if summary['status'] == 'CHECKS_PASSED_WITH_SCOPE_LIMITS' else 1


if __name__ == '__main__':
    sys.exit(main())
