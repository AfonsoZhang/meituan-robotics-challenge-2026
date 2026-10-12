"""Real temporary Git histories: discovery, deduplication, force-push and expiry.

OpenAI Codex assisted, 2026-10-11. These tests never contact GitHub or Docker.
"""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import tempfile
import time
import unittest

import watch_upstream as watcher


class WatcherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.git('init', '-b', 'main')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.name', 'Test Fixture')
        self.base = self.commit('README.md', 'Initial fixture\n')
        self.out = self.root / 'watch'
        self.config = {'repository': str(self.repo), 'baseline': self.base,
                       'output': str(self.out), 'ready_file': str(self.root / 'ready'),
                       'until': (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(),
                       'interval_seconds': 1}
        watcher.initialize(self.config)
        self.cache = self.out / 'upstream.git'
        self.state = json.loads((self.out / 'state.json').read_text())

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args],
                                       text=True, stderr=subprocess.DEVNULL).strip()

    def commit(self, path, text):
        file = self.repo / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text)
        self.git('add', path)
        self.git('commit', '-m', 'fixture ' + path)
        return self.git('rev-parse', 'HEAD')

    def poll(self):
        watcher.git(self.cache, 'fetch', '--prune', 'origin', '+refs/heads/*:refs/heads/*')
        watcher.discover(self.cache, self.state, watcher.heads(self.cache), self.out)

    def test_feature_branch_triggers_without_main_change(self):
        self.git('switch', '-c', 'feature/moveit')
        sha = self.commit('docs/setup.md', 'MoveIt Plan -> Execute\n')
        self.poll()
        self.assertEqual(self.state['refs']['refs/heads/main'], self.base)
        self.assertEqual(len(self.state['pending']), 1)
        event = json.loads(next((self.out / 'events').glob('*.json')).read_text())
        self.assertEqual(event['commit'], sha)

    def test_duplicate_refs_and_repeated_polls_only_queue_once(self):
        sha = self.commit('src/node.cpp', 'int fixture;\n')
        self.git('branch', 'same-commit', sha)
        self.poll()
        self.poll()
        self.assertEqual(len(self.state['pending']), 1)

    def test_new_branch_at_known_commit_does_not_trigger(self):
        self.git('branch', 'old-history', self.base)
        self.poll()
        self.assertEqual(self.state['events'], [])

    def test_irrelevant_document_change_is_recorded_not_executed(self):
        self.commit('docs/team.md', 'Meeting room\n')
        self.poll()
        self.assertEqual(len(self.state['events']), 1)
        self.assertEqual(self.state['pending'], [])

    def test_force_push_new_code_is_captured_and_old_evidence_kept(self):
        old_sha = self.commit('src/node.cpp', 'first\n')
        self.poll()
        first = (self.out / 'events' / (self.state['events'][0] + '.json')).read_bytes()
        self.git('reset', '--hard', self.base)
        self.commit('src/node.cpp', 'replacement\n')
        self.poll()
        self.assertEqual(len(self.state['pending']), 2)
        self.assertEqual(watcher.git(self.cache, 'rev-parse', 'refs/mtc/observed/' + old_sha).strip(), old_sha)
        self.assertEqual((self.out / 'events' / (self.state['events'][0] + '.json')).read_bytes(), first)

    def test_deleted_branch_is_not_a_new_commit(self):
        self.git('branch', 'delete-me')
        self.poll()
        self.git('branch', '-D', 'delete-me')
        self.poll()
        self.assertNotIn('refs/heads/delete-me', self.state['refs'])
        self.assertEqual(self.state['pending'], [])

    def test_refuses_to_reinitialize_existing_monitor(self):
        with self.assertRaises(FileExistsError):
            watcher.initialize(self.config)

    def test_expired_monitor_keeps_unexecuted_queue_and_stops(self):
        self.state['pending'] = ['unavailable-environment']
        watcher.save(self.out / 'state.json', self.state)
        config = self.root / 'config.json'
        watcher.save(config, self.config)
        self.assertEqual(watcher.watch(config), 0)
        state = json.loads((self.out / 'state.json').read_text())
        self.assertEqual(state['status'], 'EXPIRED_PENDING_ENVIRONMENT')
        self.assertEqual(state['pending'], ['unavailable-environment'])

    def test_live_poll_dispatches_new_commit_to_runner(self):
        runner = self.root / 'fixture_runner.py'
        runner.write_text('import json, pathlib, sys\n'
                          'config=json.loads(pathlib.Path(sys.argv[1]).read_text())\n'
                          'event=json.loads(pathlib.Path(sys.argv[2]).read_text())\n'
                          '(pathlib.Path(config["output"])/"dispatched-sha").write_text(event["commit"])\n')
        self.config.update(runner=str(runner), until=(datetime.now(timezone.utc) + timedelta(seconds=30)).isoformat())
        Path(self.config['ready_file']).touch()
        config = self.root / 'config.json'
        watcher.save(config, self.config)
        self.git('switch', '-c', 'feature/late-moveit')
        sha = self.commit('src/planner.cpp', 'fixture\n')
        proc = subprocess.Popen(['python3', watcher.__file__, 'watch', str(config)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            until = time.monotonic() + 12
            state = {}
            while time.monotonic() < until:
                state = json.loads((self.out / 'state.json').read_text())
                if state['completed']:
                    break
                time.sleep(0.1)
            self.assertEqual((self.out / 'dispatched-sha').read_text(), sha)
            self.assertEqual(len(state['completed']), 1)
            self.assertEqual(state['completed'][0]['exit_code'], 0)
            self.assertEqual(state['pending'], [])
        finally:
            proc.terminate()
            proc.communicate(timeout=5)


if __name__ == '__main__':
    unittest.main()
