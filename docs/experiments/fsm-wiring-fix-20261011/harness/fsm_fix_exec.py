#!/usr/bin/env python3
"""Run acceptance commands with provenance, preserving failure logs."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[1]
run = Path(json.loads((root/'.agents/fsm-fix-current.json').read_text())['run'])
name, *argv = sys.argv[1:]
if argv and argv[0] == '--':
    argv.pop(0)
log = run/'logs'/f'{name}.log'
assert not log.exists(), f'Existing log: {log}'
started = datetime.datetime.now().astimezone().isoformat()
t = time.monotonic()
with log.open('w') as stream:
    child = subprocess.run(argv, stdout=stream, stderr=subprocess.STDOUT)
row = dict(name=name, argv=argv, cwd=os.getcwd(), started_at=started,
           ended_at=datetime.datetime.now().astimezone().isoformat(),
           duration_sec=round(time.monotonic()-t,3), exit_code=child.returncode,
           log=str(log.relative_to(run)),
           log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
(run/'artifacts'/f'{name}-command.json').write_text(json.dumps(row,indent=2)+'\n')
print(json.dumps(row,indent=2))
print(log.read_text(errors='replace')[-5000:])
sys.exit(child.returncode)
