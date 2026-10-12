"""Stop only this event's supplemental container and collect evidence; Codex assisted."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess
r=Path('/home/afonso/meituan-robotics-challenge-2026/outputs/handoff-acceptance-20261012-a04ac68');name='mtc-handoff-review-a04ac68'
def inspect(n):return json.loads(subprocess.check_output(['docker','inspect',n]))[0]
assert not Path('/proc/7075').exists()
for n in ['mtc-repro-5c8f61d8af9f-a04ac6831dd3','mtc-repro-5c8f61d8af9f-c10f6ed59966','mtc-wiring-review-c10f6ed']:
 assert not inspect(n)['State']['Running'],n
v=inspect(name);assert v['State']['Running'];top=subprocess.check_output(['docker','top',name,'-eo','pid,ppid,args'],text=True)
(r/'container-processes-before-stop.txt').write_text(top)
assert len(top.strip().splitlines())==2 and top.strip().endswith('sleep infinity'),top
s=subprocess.run(['docker','stop','-t','12',name],capture_output=True,text=True,timeout=30)
assert s.returncode==0,s.stderr
(r/'container').mkdir()
subprocess.run(['docker','cp',name+':/review-evidence/.',str(r/'container')],check=True,timeout=60)
records=[]
for n in ['mtc-repro-5c8f61d8af9f-a04ac6831dd3',name]:
 v=inspect(n);assert not v['State']['Running'] and not v['State']['OOMKilled']
 (r/(n+'-final-inspect.json')).write_text(json.dumps(v,indent=2)+'\n')
 records.append({'container':n,'state':v['State'],'network':v['HostConfig']['NetworkMode'],'cpus':v['HostConfig']['NanoCpus'],'memory':v['HostConfig']['Memory'],'mounts':v['Mounts'],'devices':v['HostConfig']['Devices'],'ports':v['HostConfig']['PortBindings']})
(r/'cleanup.json').write_text(json.dumps({'recorded_at':datetime.now(timezone.utc).isoformat(),'original_runner_pid':7075,'original_runner_absent':True,'supplement_before_stop':'only sleep infinity; no ROS processes or daemons','stop':{'exit_code':s.returncode,'stdout':s.stdout,'stderr':s.stderr},'containers':records,'keeper_exit137_note':'docker stop terminates sleep keeper; not ROS child shutdown verdict.'},indent=2)+'\n')
print('CLEANED_AND_COLLECTED',name)
