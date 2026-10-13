"""Bounded regression: 40 fresh processes, ten fixed tests, no retries on failure.

OpenAI Codex assisted acceptance only. Never modifies upstream code or XML.
"""
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import signal
import subprocess
import time
import xml.etree.ElementTree as ET

out = Path('/review/repeat-fjt')
out.mkdir(exist_ok=False)
names = ['ConcurrentGoalsSingleOwner', 'DuplicateCancelOnlyOneBackendCall',
         'ConcurrentPollingAndCancel', 'RepeatedScopedCancelUnderContention',
         'ConcurrentSnapshotPolling', 'ConcurrentResponseAndCancelPreservesUuid',
         'DestroyDuringPendingAction', 'LateGoalResponseAfterFaultRetainsOriginalSession',
         'RepeatedSessionPollingAndScopedCancel', 'ConcurrentCompletedIdentityRejection']
expected = {'FjtAction.' + name for name in names}
rows = []
for iteration in range(1, 41):
    stem = out / f'{iteration:02d}'
    argv = ['/main-build/mtc_trajectory_execution_cpp/test_fjt_action',
            '--gtest_filter=' + ':'.join(sorted(expected)),
            '--gtest_output=xml:' + str(stem.with_suffix('.xml'))]
    row = {'iteration': iteration, 'argv': argv, 'timeout_seconds': 40,
           'started_at': datetime.now(timezone.utc).isoformat()}
    start = time.monotonic()
    with stem.with_suffix('.log').open('xb') as log:
        proc = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT,
                                start_new_session=True,
                                env=dict(os.environ, ROS_DOMAIN_ID='178'))
        try:
            row['exit_code'] = proc.wait(timeout=40)
        except subprocess.TimeoutExpired:
            row['timeout'] = True
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait(timeout=3)
            row['exit_code'] = 124
    row['elapsed_seconds'] = time.monotonic() - start
    try:
        cases = list(ET.parse(stem.with_suffix('.xml')).getroot().iter('testcase'))
        actual = [c.attrib['classname'] + '.' + c.attrib['name'] for c in cases]
        assert len(actual) == len(expected) and set(actual) == expected, actual
        assert all(c.find('failure') is None and c.find('error') is None and
                   c.find('skipped') is None and c.get('status') == 'run' and
                   c.get('result') == 'completed' for c in cases)
        assert row['exit_code'] == 0
        row['status'] = 'PASS'
    except Exception as exc:
        row.update(status='FAIL', exception=repr(exc))
    rows.append(row)
    stem.with_suffix('.json').write_text(json.dumps(row, indent=2) + '\n')
    print(iteration, row['status'], round(row['elapsed_seconds'], 3), flush=True)
    if row['status'] != 'PASS':
        break
summary = {'planned_processes': 40, 'tests_per_process': sorted(expected),
           'processes': rows, 'status': 'PASS' if len(rows) == 40 and
           all(r['status'] == 'PASS' for r in rows) else 'FAIL',
           'scope': '400 repeated executions of 10 identities, not 400 new tests'}
(out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
raise SystemExit(0 if summary['status'] == 'PASS' else 1)
