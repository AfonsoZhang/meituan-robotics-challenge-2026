"""Failure-path integration tests; real Git/processes, fake queue transport only.

OpenAI Codex assisted, 2026-10-11. No GitHub, model, Docker or device access.
"""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch

from test_watch_upstream import GitFixture
import wake_main as wake
import watch_upstream as watcher


FIXTURE_RUNNER = '''import json, pathlib, sys, time
config=json.loads(pathlib.Path(sys.argv[1]).read_text())
event_path=pathlib.Path(sys.argv[2])
event=json.loads(event_path.read_text())
root=pathlib.Path(config['output'])
with (root/'executions.jsonl').open('a') as f:
 f.write(json.dumps({'sha':event['commit'], 'at':time.time()})+'\\n')
dest=root/'runs'/event_path.stem
dest.mkdir()
(dest/'fixture.log').write_text('Controlled fixture failure; no ROS, Docker or hardware.\\n')
time.sleep(config.get('fixture_sleep',0))
code=config.get('fixture_exit',1)
(dest/'summary.json').write_text(json.dumps({'status':'FIXTURE_FAILURE' if code else 'FIXTURE_PASS',
 'steps':[{'name':'controlled-fixture','exit_code':code}], 'scope':'transport fixture only'}))
sys.exit(code)
'''


class WakeTests(GitFixture):
    def setUp(self):
        super().setUp()
        self.path = self.root / 'config.json'
        self.runner = self.root / 'fixture_runner.py'
        self.runner.write_text(FIXTURE_RUNNER)
        self.cli = self.root / 'queue-fixture'
        self.calls = self.root / 'queue-calls.jsonl'
        self.cli.write_text('#!' + sys.executable + '\n' +
                           'import json, os, pathlib, sys, time\n' +
                           f'config=json.loads(pathlib.Path({str(self.path)!r}).read_text())\n' +
                           f'path=pathlib.Path({str(self.calls)!r})\n' +
                           'n=len(path.read_text().splitlines()) if path.exists() else 0\n'
                           'with path.open("a") as f:\n'
                           ' f.write(json.dumps({"argv":sys.argv[1:], "thread_env":os.environ.get("CODEX_THREAD_ID"),'
                           ' "session_env":os.environ.get("CODEX_SESSION_ID")})+"\\n")\n'
                           'time.sleep(config.get("queue_sleep",0))\n'
                           'codes=config.get("queue_codes",[0])\n'
                           'print("queue fixture")\n'
                           'sys.exit(codes[min(n,len(codes)-1)])\n')
        self.cli.chmod(0o755)
        self.config.update(runner=str(self.runner), harness_directory=str(Path(wake.__file__).parent),
                           until=(datetime.now(timezone.utc) + timedelta(seconds=60)).isoformat(),
                           interval_seconds=0.2, tick_seconds=0.05,
                           wake={'enabled': True, 'cli': str(self.cli), 'retry_seconds': [0, 0],
                                 'timeout_seconds': 2, 'max_attempts': 3})
        Path(self.config['ready_file']).touch()
        wake.save(self.path, self.config)

    def start(self):
        proc = subprocess.Popen([sys.executable, watcher.__file__, 'watch', str(self.path)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        def cleanup():
            if proc.poll() is None:
                proc.terminate()
            proc.communicate(timeout=8)
        self.addCleanup(cleanup)
        return proc

    def wait_for(self, predicate, timeout=8):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            result = predicate()
            if result:
                return result
            time.sleep(0.05)
        self.fail('Timed out waiting for fixture; state=' + (self.out / 'state.json').read_text())

    def job(self):
        paths = list((self.out / 'wake').glob('*/job.json'))
        return wake.read(paths[0]) if paths else None

    def queue_count(self):
        return len(self.calls.read_text().splitlines()) if self.calls.exists() else 0

    def terminal_job(self, code=1):
        self.commit('src/moveit.cpp', 'fixture\n')
        self.poll()
        key = self.state['pending'].pop()
        record = {'event': key, 'exit_code': code, 'result': 'EXITED', 'ended_at': wake.now()}
        self.state['completed'].append(record)
        wake.save(self.out / 'state.json', self.state)
        return wake.prepare(self.config, self.path, record)

    def test_queue_uses_fixed_target_clean_environment_and_real_result(self):
        job = self.terminal_job()
        with patch.dict(os.environ, CODEX_THREAD_ID='wrong-thread', CODEX_SESSION_ID='wrong-session'):
            self.assertEqual(wake.pump(self.config, job), 'QUEUED')
        call = json.loads(self.calls.read_text())
        self.assertIsNone(call['thread_env'])
        self.assertIsNone(call['session_env'])
        self.assertEqual(call['argv'][0:5], ['queue', '--remote', wake.REMOTE, '--thread', wake.THREAD])
        prompt = call['argv'][-1]
        self.assertIn(job['commit'], prompt)
        self.assertIn('MISSING_SUMMARY', prompt)
        self.assertIn('src/moveit.cpp', prompt)
        self.assertIn('孙嘉明', prompt)

    def test_finite_retries_survive_reload_and_never_rerun_tests(self):
        self.config['queue_codes'] = [1, 1, 0]
        wake.save(self.path, self.config)
        job = self.terminal_job()
        job_path = wake.directory(self.config, job['event']) / 'job.json'
        for expected in ('RETRY_WAIT', 'RETRY_WAIT', 'QUEUED'):
            self.assertEqual(wake.pump(self.config, wake.read(job_path)), expected)
        for _ in range(4):
            self.assertEqual(wake.pump(self.config, wake.read(job_path)), 'QUEUED')
        self.assertEqual(self.queue_count(), 3)
        self.assertFalse((self.out / 'executions.jsonl').exists())

    def test_exhausted_delivery_remains_blocked_without_loop(self):
        self.config['queue_codes'] = [1]
        wake.save(self.path, self.config)
        job = self.terminal_job()
        for _ in range(6):
            wake.pump(self.config, job)
        self.assertEqual(job['status'], 'DELIVERY_EXHAUSTED')
        self.assertEqual(self.queue_count(), 3)
        self.assertEqual(watcher.wake_gate(self.config, self.path, self.state)['status'], 'DELIVERY_EXHAUSTED')

    def test_transport_timeout_and_ambiguous_restart_use_same_token(self):
        self.config['queue_sleep'] = 2
        self.config['wake']['timeout_seconds'] = 0.1
        wake.save(self.path, self.config)
        job = self.terminal_job()
        token = job['token']
        self.assertEqual(wake.pump(self.config, job), 'RETRY_WAIT')
        self.assertEqual(job['attempts'][0]['exit_code'], 124)
        job['status'] = 'SENDING'  # crash before persisting a transport result
        self.assertEqual(wake.pump(self.config, job), 'RETRY_WAIT')
        self.assertEqual(job['token'], token)
        self.assertEqual(self.queue_count(), 2)

    def test_ack_claim_is_once_and_complete_is_idempotent(self):
        job = self.terminal_job(0)
        with self.assertRaises(ValueError):
            wake.acknowledge(self.config, job['event'], 'incorrect')
        self.assertEqual(wake.acknowledge(self.config, job['event'], job['token']), 'CLAIMED')
        self.assertEqual(wake.acknowledge(self.config, job['event'], job['token']), 'ALREADY_ACKNOWLEDGED')
        self.assertEqual(wake.pump(self.config, job), 'ACKNOWLEDGED')
        self.assertEqual(self.queue_count(), 0)
        report = self.root / 'report.md'
        report.write_text('Actual fixture review\n')
        self.assertEqual(wake.acknowledge(self.config, job['event'], job['token'], report, 'fixture reviewed'), 'COMPLETED')
        self.assertEqual(wake.pump(self.config, job), 'COMPLETE')
        self.assertIsNone(watcher.wake_gate(self.config, self.path, self.state))

    def test_complete_requires_claim_real_report_and_idle_runner(self):
        job = self.terminal_job()
        report = self.root / 'report.md'
        report.write_text('fixture')
        with self.assertRaises(ValueError):
            wake.acknowledge(self.config, job['event'], job['token'], report, 'done')
        wake.acknowledge(self.config, job['event'], job['token'])
        with self.assertRaises(FileNotFoundError):
            wake.acknowledge(self.config, job['event'], job['token'], self.root / 'missing', 'done')
        self.state['active'] = {'event': job['event']}
        wake.save(self.out / 'state.json', self.state)
        with self.assertRaises(RuntimeError):
            wake.acknowledge(self.config, job['event'], job['token'], report, 'done')

    def test_live_failure_review_blocks_second_sha_until_completed(self):
        self.commit('src/first.cpp', 'fixture one\n')
        self.start()
        self.wait_for(lambda: self.job() and self.job()['status'] == 'QUEUED')
        first = self.job()
        self.assertEqual(first['completed_run']['exit_code'], 1)
        self.commit('src/second.cpp', 'fixture two\n')
        self.wait_for(lambda: len(wake.read(self.out / 'state.json')['pending']) == 1)
        self.assertEqual(len((self.out / 'executions.jsonl').read_text().splitlines()), 1)
        wake.acknowledge(self.config, first['event'], first['token'])
        time.sleep(0.25)
        self.assertEqual(len((self.out / 'executions.jsonl').read_text().splitlines()), 1)
        report = self.root / 'report.md'
        report.write_text('fixture failure reviewed')
        wake.acknowledge(self.config, first['event'], first['token'], report, 'reviewed with failure')
        self.wait_for(lambda: len(wake.read(self.out / 'state.json')['completed']) == 2)
        self.wait_for(lambda: self.queue_count() == 2)
        self.assertEqual(len((self.out / 'executions.jsonl').read_text().splitlines()), 2)

    def test_live_runner_timeout_wakes_and_preserves_partial_log(self):
        self.config.update(fixture_sleep=30, run_timeout_seconds=0.3, termination_grace_seconds=0.2)
        wake.save(self.path, self.config)
        self.commit('src/slow.cpp', 'fixture slow\n')
        self.start()
        self.wait_for(lambda: self.job() and self.job()['status'] == 'QUEUED')
        job = self.job()
        self.assertEqual(job['completed_run']['result'], 'TIMEOUT')
        self.assertEqual(job['completed_run']['exit_code'], 124)
        self.assertTrue((self.out / 'runs' / job['event'] / 'fixture.log').exists())
        self.assertEqual(wake.runner_pids(self.config, job['event']), [])

    def test_parent_crash_recovers_without_rerunning_and_wakes(self):
        self.config['fixture_sleep'] = 30
        wake.save(self.path, self.config)
        self.commit('src/interrupted.cpp', 'fixture interruption\n')
        proc = self.start()
        self.wait_for(lambda: (self.out / 'executions.jsonl').exists())
        proc.kill()
        proc.wait(timeout=3)
        self.start()
        self.wait_for(lambda: self.job() and self.job()['status'] == 'QUEUED')
        job = self.job()
        self.assertEqual(job['completed_run']['result'], 'INTERRUPTED_REQUIRES_ANALYSIS')
        self.assertEqual(len((self.out / 'executions.jsonl').read_text().splitlines()), 1)
        self.assertEqual(wake.runner_pids(self.config, job['event']), [])

    def test_restart_after_queue_acceptance_does_not_send_twice(self):
        self.commit('src/once.cpp', 'fixture once\n')
        proc = self.start()
        self.wait_for(lambda: self.job() and self.job()['status'] == 'QUEUED')
        proc.terminate()
        proc.wait(timeout=3)
        newer = self.start()
        self.wait_for(lambda: wake.read(self.out / 'state.json')['pid'] == newer.pid)
        time.sleep(0.3)
        self.assertEqual(self.queue_count(), 1)
        self.assertEqual(len((self.out / 'executions.jsonl').read_text().splitlines()), 1)

    def test_no_update_does_not_invoke_transport(self):
        self.start()
        self.wait_for(lambda: wake.read(self.out / 'state.json')['last_successful_poll'])
        time.sleep(0.3)
        self.assertEqual(self.queue_count(), 0)
        self.assertFalse((self.out / 'executions.jsonl').exists())

    def test_discovery_crash_keeps_same_event_and_original_patch(self):
        self.commit('src/crash.cpp', 'fixture crash\n')
        old_state = json.loads(json.dumps(self.state))
        self.poll()
        key = self.state['events'][0]
        snapshot = (self.out / 'events' / (key + '.json')).read_bytes()
        self.state = old_state
        self.poll()
        self.assertEqual(self.state['events'], [key])
        self.assertEqual(self.state['pending'], [key])
        self.assertEqual((self.out / 'events' / (key + '.json')).read_bytes(), snapshot)

    def test_second_monitor_cannot_acquire_same_slot(self):
        self.start()
        self.wait_for(lambda: wake.read(self.out / 'state.json')['last_successful_poll'])
        proc = subprocess.run([sys.executable, watcher.__file__, 'watch', str(self.path)],
                              capture_output=True, text=True, timeout=3)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('BlockingIOError', proc.stderr)

    def test_expiry_still_delivers_completed_failure(self):
        job = self.terminal_job()
        self.config['until'] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        wake.save(self.path, self.config)
        self.start()
        self.wait_for(lambda: self.job()['status'] == 'QUEUED')
        self.assertEqual(self.queue_count(), 1)
        self.assertEqual(self.job()['token'], job['token'])
