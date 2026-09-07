"""Execute a frozen experiment protocol sequentially; retain every attempt.

Gazebo uses a fixed port/domain, so trials must not run concurrently.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parent.parent

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('protocol',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    protocol=json.loads(args.protocol.read_text())
    for name,digest in protocol['files'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:
            raise RuntimeError('Frozen input changed: '+name)
    args.output.mkdir(parents=True,exist_ok=True)
    frozen=args.output/'protocol.json'
    if frozen.exists() and frozen.read_bytes()!=args.protocol.read_bytes():
        raise RuntimeError('Existing output uses a different protocol')
    frozen.write_bytes(args.protocol.read_bytes())
    for trial in protocol['trials']:
        out=args.output/trial['id']
        audit=args.output/(trial['id']+'-process.json')
        if audit.exists():
            print('Retained completed attempt: '+trial['id'],flush=True);continue
        if out.exists():
            raise RuntimeError('Interrupted attempt retained; audit it before resuming: '+str(out))
        print('START '+trial['id'],flush=True)
        started=time.time()
        with (args.output/(trial['id']+'.log')).open('w') as log:
            p=subprocess.run(['bash','demo/run.sh','--vision',trial['mode'],
                 '--yellow-offset-mm',str(trial['offset_mm']),'--timeout','180',
                 '--output',str(out.resolve())],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        audit.write_text(json.dumps(dict(trial=trial,exit_code=p.returncode,wall_seconds=time.time()-started),indent=2)+'\n')
        summary=json.loads((out/'summary.json').read_text()) if (out/'summary.json').exists() else {}
        print(json.dumps(dict(id=trial['id'],exit=p.returncode,passed=summary.get('passed',False),
                             center_error_mm=summary.get('center_error_mm'),error=summary.get('error'))),flush=True)

if __name__=='__main__':main()
