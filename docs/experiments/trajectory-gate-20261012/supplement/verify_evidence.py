"""Final provenance, isolation and preserved-evidence verification; Codex assisted."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,re,subprocess
raw=Path('outputs/trajectory-gate-acceptance-20261012-45f497c');w=Path('outputs/moveit-watch-20261011');base=Path('docs/experiments/trajectory-gate-20261012');event='sha-45f497ce3444e255463faf41f7b736aa9ad07d7b'
m=json.loads(Path('materials/manifest.json').read_text());entries={e['id']:e for k in ['sources','project_decisions','external_references','local_observations'] for e in m[k]};assert len(entries)==sum(len(m[k]) for k in ['sources','project_decisions','external_references','local_observations'])
checks={'verified_at':datetime.now(timezone.utc).isoformat()};sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for ident in ['ENV-TRAJECTORY-GATE-20261012','ENV-CALIBRATION-20261012','ENV-TRAJECTORY-20261012','ENV-PLANNER-MAIN-20261012','ENV-VISION-ADAPTER-20261012','ENV-PLANNER-SCENE-20261012','ENV-PLANNER-MERGE-20261012','ENV-HANDOFF-20261012','ENV-PLANNER-20261012','ENV-WIRING-MERGE-20261011','ENV-CPP-ACTION-20261011','ENV-FSM-FIX-20261011','ENV-UPSTREAM-WAKE-20261011','ENV-UPSTREAM-WATCH-20261011']:
 e=entries[ident];p=Path(e['index']);assert sha(p)==e['index_sha256'],ident
 fs=json.loads(p.read_text())['files']
 for f in fs:
  q=Path(f['path']) if f['path'].startswith('docs/experiments/') else p.parent/f['path']
  assert q.is_file() and sha(q)==f['sha256'],str(q)
 checks[ident]=len(fs)
auto=w/'runs'/event;original=json.loads((auto/'index.json').read_text());assert all(sha(auto/f['path'])==f['sha256'] for f in original['files']);assert len(original['files'])==317;checks['original_raw_files_verified']=len(original['files'])
i=json.loads((base/'inputs.json').read_text());assert sha(Path('robot/fsm-baseline.repos'))==i['formal_baseline_sha256'];assert i['formal_baseline_commit'] in Path('robot/fsm-baseline.repos').read_text();checks['formal_baseline_unchanged']=True
for previous in ['sha-06ab689f25e87dcebf9fd04fdd581ec4755206f6','sha-688d80d63ba2196e3c1753b69d18c1bfa30919b3','sha-f7eaa2c0d2887aeada4fd635112c63c237962ff7','sha-0e329f10e6f607c9c417a54ae60d290b8e2395b5','sha-30e3c6e64516c47afe9ada25d02df7ed4669825c','sha-4a1a81652fca39efe2916a19ad49187d29789697','sha-c0f70172e4b0271046d5f52813e0730d40ae772a','sha-c10f6ed59966401684851f917f9137b0a6cf12ae','sha-fcdd8eae897cbc37c539d4bad57b712f08124938','sha-a04ac6831dd3963e6b1ec4b9e27214eb564f9f24']:
 r=json.loads((w/'wake'/previous/'receipt.json').read_text());assert sha(Path(r['report']))==r['report_sha256'];checks[previous+'_signed_report_unchanged']=True
assert sha(w/'config.json')==sha(base/'monitor/config.json');checks['monitor_config_unchanged']=True
rx=re.compile(r'USER-[A-Z]+-[0-9]{8}(?:-[0-9]+)?|(?:VAC|AUBO|RS|CV)-[A-Z0-9]+|(?:VISION|ROBUST|DEMO|ENV|SPRINT)-[A-Z-]+-[0-9]{8}|CTRL-[A-Z]+-[0-9]{4}|TEAMMATE-[A-Z]+-[0-9]{8}|POLYU-[A-Z0-9]+(?:-[A-Z0-9]+)*')
files=[Path('README.md'),*Path('docs').glob('*.md'),*Path('demo').glob('*.md'),*Path('robot').glob('*.md'),Path('materials/README.md')]
refs={r for p in files for r in rx.findall(p.read_text())};assert not refs-entries.keys(),refs-entries.keys()
changed=[Path(x) for x in ['README.md','docs/trajectory-gate-acceptance.md','docs/hardware-vision-plan.md','docs/open-questions.md','docs/upstream-monitor.md','robot/README.md']]
for p in changed:
 for ref in rx.findall(p.read_text()):assert str(p) in entries[ref]['derived_files'],(p,ref)
 for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' not in target and not target.startswith('#'):assert (p.parent/target.split('#')[0]).exists(),(p,target)
for ident in ['TEAMMATE-TRAJECTORYGATE-20261012','ENV-TRAJECTORY-GATE-20261012']:
 for x in entries[ident]['derived_files']:assert Path(x).is_file(),x
checks['references_links_and_reverse_links']='PASS'
qs=re.findall(r'^\| (Q\d+)',Path('docs/open-questions.md').read_text(),re.M);assert sorted(qs,key=lambda x:int(x[1:]))==[f'Q{i:02d}' for i in range(1,20)];checks['Q01_to_Q19_preserved']=True
for c in ['mtc-repro-5c8f61d8af9f-45f497ce3444','mtc-trajectory-gate-review-45f497c','mtc-repro-5c8f61d8af9f-06ab689f25e8','mtc-calibration-review-06ab689','mtc-repro-5c8f61d8af9f-688d80d63ba2','mtc-trajectory-review-688d80d','mtc-repro-5c8f61d8af9f-f7eaa2c0d288','mtc-planner-main-review-f7eaa2c','mtc-repro-5c8f61d8af9f-0e329f10e6f6','mtc-vision-adapter-review-0e329f1','mtc-repro-5c8f61d8af9f-30e3c6e64516','mtc-planner-scene-review-30e3c6e']:
 v=json.loads(subprocess.check_output(['docker','inspect',c]))[0];h=v['HostConfig'];assert not v['State']['Running'] and not v['State']['OOMKilled'] and h['NetworkMode']=='none' and not v['Mounts'] and not h['Devices'] and not h['PortBindings'] and h['NanoCpus']==2000000000 and h['Memory']==4294967296
checks['current_and_previous_containers_stopped_and_isolated']=True;assert not Path('/proc/35809').exists()
s=json.loads((w/'state.json').read_text());assert s['active'] is None and s['main_review']['event']==event and s['main_review']['status']=='ACKNOWLEDGED' and Path('/proc/'+str(s['pid'])).exists();checks['monitor']={k:s[k] for k in ['pid','status','last_successful_poll','pending']}
v=subprocess.run(['git','diff','--check'],capture_output=True,text=True);assert v.returncode==0,v.stdout+v.stderr;checks['git_diff_whitespace']='PASS'
checks['project_git_head']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();assert checks['project_git_head']=='96b76245da4c9ffe856d26d156bbd72f7f956a84'
assert sha(Path('robot/fsm-baseline.repos'))==json.loads((raw/'project-before.json').read_text())['formal_pin_sha256']
# Validate the newly reported outcomes against raw data and ensure no current task containers remain.
a= json.loads((base/'summary.json').read_text())
assert a['analysis']['automatic']['moveit']['execute']['result']['error_code']['val']==1
assert a['analysis']['automatic']['moveit']['clean_shutdown']=='FAIL'
assert a['cpp_cases']==463 and a['cpp_executables']==26 and a['build_packages']==15
sup=a['analysis']['supplement'];assert sup['ubsan']['cases']==463 and len(sup['ubsan']['compile_commands_instrumented'])==7
assert len(sup['generic_cases'])==4 and [x['exit_code'] for x in sup['generic_cases']]==[0,0,0,0]
assert sup['generic_cases'][3]['cached_read_and_three_changed_content_refusals']
assert sup['topology_and_plan']['topology']['exit_code']==2 and not sup['topology_and_plan']['fjt_goal_uuids']
assert not sup['plan_consumer']['after_id_accepted']
freeze=json.loads((raw/'freeze-result.json').read_text())
assert len(json.loads((base/'index.json').read_text())['files'])==freeze['files'] and sha(base/'index.json')==freeze['index_sha256']
checks['reported_identity_ubsan_generic_and_blocked_topology']='PASS'
assert not subprocess.check_output(['docker','ps','--filter','name=mtc-','--format','{{.Names}}'],text=True).strip()
checks['no_task_containers_running']=True
# Every registered reference in the new frozen text also has a reverse index.
pat=re.compile(r'(?<![A-Z0-9-])(?:'+'|'.join(re.escape(k) for k in sorted(entries,key=len,reverse=True))+r')(?![A-Z0-9-])')
for p in base.rglob('*'):
 if not p.is_file():continue
 try:txt=p.read_text()
 except UnicodeDecodeError:continue
 for ref in set(pat.findall(txt)):assert str(p) in entries[ref]['derived_files'],(str(p),ref)
checks['frozen_reverse_links']='PASS'
checks['report_sha256']=sha(Path('docs/trajectory-gate-acceptance.md'));(raw/'verification.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n');print(json.dumps(checks,ensure_ascii=False,indent=2))
