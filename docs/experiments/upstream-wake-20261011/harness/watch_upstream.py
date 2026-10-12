#!/usr/bin/env python3
"""Bounded, read-only Git monitoring and isolated reproduction dispatch.

OpenAI Codex assisted implementation, 2026-10-11. No GitHub writes, hardware
access, source merges or automatic promotion of the project's locked baseline.
"""
import argparse
from datetime import datetime
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

import wake_main
from wake_main import now, read, save


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
        # Stable across a crash between recording the event and saving state.
        key = 'sha-' + sha
        event_path = root / 'events' / (key + '.json')
        if event_path.exists():
            event = read(event_path)
        else:
            (root / 'events' / (key + '.patch')).write_text(diff)
            save(event_path, event)
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


def stop_container(config, active):
    """Stop only this monitor's labelled container; preserve it and all logs."""
    if not config.get('docker'):
        return {'status': 'NO_CONTAINER_RUNNER'}
    docker = config['docker']
    name = active.get('container')
    if not name:
        return {'status': 'LEGACY_RUN_REQUIRES_INSPECTION'}
    record = {'container': name, 'at': now()}
    try:
        proc = subprocess.run([docker, 'container', 'ls', '-aq', '--filter',
                               'name=^/' + name + '$'], capture_output=True, text=True,
                              check=True, timeout=20)
        if not proc.stdout.strip():
            record['status'] = 'NOT_CREATED'
            return record
        info = json.loads(subprocess.check_output([docker, 'inspect', name], timeout=20))[0]
        labels = info['Config'].get('Labels') or {}
        if (labels.get('mtc.event') != active['event'] or
                labels.get('mtc.watch-root') != wake_main.root_hash(config['output'])):
            raise RuntimeError('Container ownership labels do not match; inspection required')
        if info['State']['Running']:
            subprocess.run([docker, 'stop', '-t', '12', name], check=True,
                           capture_output=True, timeout=30)
            info = json.loads(subprocess.check_output([docker, 'inspect', name], timeout=20))[0]
        record['status'] = 'STOPPED' if not info['State']['Running'] else 'STILL_RUNNING'
    except Exception as exc:
        record.update(status='CLEANUP_REQUIRES_INSPECTION', error=repr(exc))
    return record


def terminate_group(pid, signum):
    try:
        if os.getpgid(pid) == pid:
            os.killpg(pid, signum)
    except ProcessLookupError:
        pass


def recover_interrupted(config, state):
    active = state['active']
    pids = wake_main.runner_pids(config, active['event'])
    for pid in pids:
        terminate_group(pid, signal.SIGTERM)
    # Covers a crash after spawn but before saving its PID. Inspect exact argv,
    # never signal an unrelated process merely because its PID was reused.
    limit = time.monotonic() + 5
    while wake_main.runner_pids(config, active['event']) and time.monotonic() < limit:
        time.sleep(0.1)
    for pid in wake_main.runner_pids(config, active['event']):
        terminate_group(pid, signal.SIGKILL)
    return stop_container(config, active)


def wake_gate(config, config_path, state):
    if not config.get('wake', {}).get('enabled'):
        return None
    for completed in state['completed']:
        job = wake_main.prepare(config, config_path, completed)
        if job['status'] == 'COMPLETE':
            continue
        status = wake_main.pump(config, job)
        if status != 'COMPLETE':
            return {'event': job['event'], 'status': status,
                    'job': str(wake_main.directory(config, job['event']) / 'job.json')}
    return None


def watch(config_path):
    config_path = Path(config_path).resolve()
    config = read(config_path)
    if config.get('wake', {}).get('enabled'):
        for field, expected in (('thread', wake_main.THREAD), ('remote', wake_main.REMOTE)):
            if config['wake'].get(field, expected) != expected:
                raise ValueError('Wake target is fixed: ' + field)
        if config.get('wake_e2e_fixture') and not Path(config['repository']).is_dir():
            raise ValueError('E2E fixture mode requires an explicit local repository')
    root = Path(config['output'])
    cache = root / 'upstream.git'
    with (root / 'monitor.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = read(root / 'state.json')
        state['version'] = 2
        if state['active']:
            cleanup = recover_interrupted(config, state)
            state['completed'].append({**state['active'], 'exit_code': None,
                                       'result': 'INTERRUPTED_REQUIRES_ANALYSIS',
                                       'cleanup': cleanup, 'ended_at': now()})
            state['active'] = None
        state['pid'] = os.getpid()
        state.pop('ended_at', None)
        save(root / 'state.json', state)
        child = None
        log = None
        stopping = False
        next_poll = 0

        def finish(code, result):
            nonlocal child, log
            active = state['active']
            cleanup = stop_container(config, active)
            record = {**active, 'exit_code': code, 'result': result,
                      'ended_at': now(), 'cleanup': cleanup}
            # This terminal record precedes outbox delivery. A restart resumes
            # delivery/review, never the already executed runner.
            save(root / 'runs' / (active['event'] + '.completion.json'), record)
            state['completed'].append(record)
            state['active'] = None
            if log:
                log.close()
            child = log = None
            save(root / 'state.json', state)

        def stop(_signum, _frame):
            nonlocal stopping
            stopping = True

        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        deadline = datetime.fromisoformat(config['until']).timestamp()
        while True:
            expired = time.time() >= deadline
            if child and child.poll() is not None:
                timed_out = state['active'].get('timed_out_at')
                finish(124 if timed_out else child.returncode,
                       'TIMEOUT' if timed_out else 'EXITED')
            if child and time.time() >= state['active']['deadline']:
                active = state['active']
                if not active.get('timed_out_at'):
                    active['timed_out_at'] = now()
                    active['kill_at'] = time.time() + config.get('termination_grace_seconds', 180)
                    save(root / 'state.json', state)
                    terminate_group(child.pid, signal.SIGTERM)
                elif time.time() >= active['kill_at']:
                    terminate_group(child.pid, signal.SIGKILL)
            gate = wake_gate(config, config_path, state) if not child else None
            state['main_review'] = gate
            if stopping and not child:
                state['status'] = 'STOPPED_WITH_PENDING_REVIEW' if gate else 'STOPPED'
                break
            if expired and not child and not gate and (not state['pending'] or not Path(config['ready_file']).exists()):
                state['status'] = 'EXPIRED_PENDING_ENVIRONMENT' if state['pending'] else 'EXPIRED'
                break
            if expired and gate and gate['status'] == 'DELIVERY_EXHAUSTED':
                state['status'] = 'EXPIRED_DELIVERY_EXHAUSTED'
                break
            if not expired and not stopping and time.monotonic() >= next_poll:
                try:
                    git(cache, 'fetch', '--prune', 'origin',
                        '+refs/heads/*:refs/heads/*', '+refs/pull/*/head:refs/pull/*/head')
                    discover(cache, state, heads(cache), root)
                    state['last_successful_poll'] = now()
                    state.pop('poll_error', None)
                except Exception as exc:
                    state['poll_error'] = {'at': now(), 'error': str(exc)}
                next_poll = time.monotonic() + config['interval_seconds']
            if not child and not gate and not stopping and state['pending'] and Path(config['ready_file']).exists():
                key = state['pending'].pop(0)
                event = read(root / 'events' / (key + '.json'))
                state['active'] = {'event': key, 'pid': None, 'started_at': now(),
                                   'container': wake_main.container_name(root, event['commit']),
                                   'deadline': time.time() + config.get('run_timeout_seconds', 5400)}
                # A crash after this point is analyzed, not silently rerun.
                save(root / 'state.json', state)
                log = (root / 'runs' / (key + '.log')).open('a')
                try:
                    child = subprocess.Popen([sys.executable, config['runner'],
                                              str(config_path), str(root / 'events' / (key + '.json'))],
                                             stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                    state['active']['pid'] = child.pid
                except OSError as exc:
                    state['active']['launch_error'] = repr(exc)
                    finish(127, 'LAUNCH_FAILED')
            state['status'] = ('STOPPING_AFTER_ACTIVE_RUN' if stopping and child else
                               'RUNNING_REPRODUCTION' if child else
                               'WAITING_MAIN_REVIEW' if gate else
                               'WAITING_ENVIRONMENT' if state['pending'] else 'WATCHING')
            state['heartbeat'] = now()
            save(root / 'state.json', state)
            time.sleep(config.get('tick_seconds', 1))
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
