#!/usr/bin/env python3
"""Bounded, read-only Git monitoring and isolated reproduction dispatch.

OpenAI Codex assisted implementation, 2026-10-11. No GitHub writes, hardware
access, source merges or automatic promotion of the project's locked baseline.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, data):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(path)


def git(cache, *args):
    return subprocess.check_output(
        ['git', '--git-dir=' + str(cache), *args], text=True, timeout=90,
        stderr=subprocess.PIPE,
        env={**os.environ, 'GIT_TERMINAL_PROMPT': '0'})


def heads(cache):
    rows = git(cache, 'for-each-ref', '--format=%(refname) %(objectname)',
               'refs/heads/', 'refs/pull/').splitlines()
    return {ref: sha for ref, sha in (row.split() for row in rows)
            if ref.startswith('refs/heads/') or ref.endswith('/head')}


def relevant(paths, diff):
    return any(p.startswith(('src/', 'tests/', 'config/', 'launch/', 'scripts/'))
               or p.endswith(('CMakeLists.txt', 'package.xml', '.repos'))
               for p in paths) or bool(re.search(
                   r'moveit|motion.?adapter|phase.?2|B0[1-6]|Plan\s*→\s*Execute',
                   diff, re.I))


def discover(cache, state, current, root):
    """Persist one event per previously unseen commit, including feature branches."""
    previous = state['refs']
    seen = set(state['seen_commits'])
    for sha in sorted(set(current.values()) - seen):
        if sha in seen:
            continue
        refs = sorted(ref for ref, value in current.items() if value == sha)
        old = next((previous[r] for r in refs if r in previous), state['base'])
        paths = git(cache, 'diff', '--name-only', old, sha).splitlines()
        diff = git(cache, 'diff', '--no-ext-diff', '--no-textconv', old, sha)
        event = {'observed_at': now(), 'commit': sha, 'previous': old,
                 'refs': refs, 'paths': paths, 'relevant': relevant(paths, diff),
                 'commit_info': git(cache, 'show', '-s', '--format=fuller', sha)}
        key = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + sha[:12]
        save(root / 'events' / (key + '.json'), event)
        (root / 'events' / (key + '.patch')).write_text(diff)
        if event['relevant']:
            # Keep queued SHAs reachable even if a branch is force-pushed again
            # before the worker creates its source bundle.
            git(cache, 'update-ref', 'refs/mtc/observed/' + sha, sha)
            state['pending'].append(key)
        state['events'].append(key)
        # A newly introduced branch at an old ancestor must not trigger a replay.
        seen.update(git(cache, 'rev-list', sha).splitlines())
    state['refs'] = current
    state['seen_commits'] = sorted(seen)


def initialize(config):
    root = Path(config['output'])
    root.mkdir(parents=True, exist_ok=True)
    (root / 'events').mkdir(exist_ok=True)
    (root / 'runs').mkdir(exist_ok=True)
    cache = root / 'upstream.git'
    if not cache.exists():
        subprocess.run(['git', 'clone', '--mirror', config['repository'], str(cache)],
                       check=True, timeout=180)
    state_path = root / 'state.json'
    if state_path.exists():
        raise FileExistsError('Refusing to overwrite existing monitoring state')
    state = {'started_at': now(), 'base': config['baseline'], 'refs': heads(cache),
             'seen_commits': git(cache, 'rev-list', '--all').splitlines(),
             'pending': [], 'events': [], 'completed': [], 'active': None,
             'status': 'INITIALIZED', 'last_successful_poll': None}
    save(state_path, state)
    save(root / 'initial-state.json', state)


def watch(config_path):
    config = json.loads(config_path.read_text())
    root = Path(config['output'])
    cache = root / 'upstream.git'
    with (root / 'monitor.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = json.loads((root / 'state.json').read_text())
        # A killed parent leaves a detectable interrupted run; do not silently
        # call it successful or start a second runner against the same commit.
        if state['active']:
            state['status'] = 'INTERRUPTED_RUN_REQUIRES_INSPECTION'
            save(root / 'state.json', state)
            return 2
        state['pid'] = os.getpid()
        state.pop('ended_at', None)
        child = None
        log = None
        stopping = False

        def stop(_signum, _frame):
            nonlocal stopping
            stopping = True

        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        deadline = datetime.fromisoformat(config['until']).timestamp()
        while not stopping:
            expired = time.time() >= deadline
            if child and child.poll() is not None:
                state['completed'].append({**state['active'], 'exit_code': child.returncode,
                                           'ended_at': now()})
                state['active'] = None
                log.close()
                child = log = None
            if expired and not child and (not state['pending'] or not Path(config['ready_file']).exists()):
                state['status'] = 'EXPIRED_PENDING_ENVIRONMENT' if state['pending'] else 'EXPIRED'
                break
            if not expired:
                try:
                    git(cache, 'fetch', '--prune', 'origin',
                        '+refs/heads/*:refs/heads/*', '+refs/pull/*/head:refs/pull/*/head')
                    discover(cache, state, heads(cache), root)
                    state['last_successful_poll'] = now()
                    state.pop('poll_error', None)
                except Exception as exc:
                    state['poll_error'] = {'at': now(), 'error': str(exc)}
            if not child and state['pending'] and Path(config['ready_file']).exists():
                key = state['pending'].pop(0)
                log = (root / 'runs' / (key + '.log')).open('a')
                child = subprocess.Popen([sys.executable, config['runner'],
                                          str(config_path), str(root / 'events' / (key + '.json'))],
                                         stdout=log, stderr=subprocess.STDOUT)
                state['active'] = {'event': key, 'pid': child.pid, 'started_at': now()}
            state['status'] = ('RUNNING_REPRODUCTION' if child else
                               'WAITING_ENVIRONMENT' if state['pending'] else 'WATCHING')
            state['heartbeat'] = now()
            save(root / 'state.json', state)
            for _ in range(config['interval_seconds']):
                if stopping:
                    break
                time.sleep(1)
        if stopping and child:
            # The bounded runner finishes and cleans up only its own container.
            state['status'] = 'STOPPING_AFTER_ACTIVE_RUN'
            save(root / 'state.json', state)
            child.wait()
            log.close()
            state['completed'].append({**state['active'], 'exit_code': child.returncode,
                                       'ended_at': now()})
            state['active'] = None
        if stopping:
            state['status'] = 'STOPPED'
        state['ended_at'] = now()
        save(root / 'state.json', state)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['init', 'watch', 'status'])
    parser.add_argument('config', type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if args.command == 'init':
        initialize(config)
    elif args.command == 'watch':
        return watch(args.config.resolve())
    else:
        state = json.loads((Path(config['output']) / 'state.json').read_text())
        state.pop('seen_commits', None)
        print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
