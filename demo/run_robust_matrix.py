"""Run the frozen effort-control comparison; preserve all attempts without retries."""
import hashlib,json,subprocess,time
from pathlib import Path
import argparse

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('protocol',type=Path);p.add_argument('output',type=Path)
    args=p.parse_args();protocol=json.loads(args.protocol.read_text())
    for name,digest in protocol['files'].items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=digest:raise RuntimeError('Frozen input changed: '+name)
    args.output.mkdir(exist_ok=False,parents=True)
    (args.output/'protocol.json').write_bytes(args.protocol.read_bytes())
    for t in protocol['trials']:
        run=args.output/t['id'];start=time.time();print('START '+t['id'],flush=True)
        with (args.output/(t['id']+'.log')).open('w') as log:
            proc=subprocess.run(['bash','demo/run.sh','--control',t['control'],'--robust-probe',
                 '--disturbance-nm',str(t['disturbance_nm']),'--timeout','90','--output',str(run.resolve())],stdout=log,stderr=subprocess.STDOUT)
        audit=dict(trial=t,exit_code=proc.returncode,wall_seconds=time.time()-start)
        (args.output/(t['id']+'-process.json')).write_text(json.dumps(audit,indent=2)+'\n')
        s=json.loads((run/'summary.json').read_text()) if (run/'summary.json').exists() else {}
        print(json.dumps(dict(id=t['id'],passed=s.get('passed',False),error=s.get('error'),windows=s.get('windows'))),flush=True)
