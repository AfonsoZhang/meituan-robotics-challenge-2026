"""Validate freeze, original failures, prior receipts and unchanged deferred task. Codex assisted."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re,subprocess
raw=Path(__file__).resolve().parent;root=raw.parents[1];w=root/'outputs/moveit-watch-20261011';event='sha-681bb64bfb8cd482d1e78950cef4cfe395b21bff'
base=root/'docs/experiments/trajectory-ownership-20261012';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=read(root/'materials/manifest.json');entries={e['id']:e for g in ['sources','project_decisions','external_references','local_observations'] for e in m[g]}
assert len(entries)==sum(len(m[g]) for g in ['sources','project_decisions','external_references','local_observations'])
checks={'at':datetime.now(timezone.utc).isoformat()};verified={}
for ident,e in entries.items():
 if not e.get('index') or not e.get('index_sha256'):continue
 p=root/e['index'];assert p.is_file() and sha(p)==e['index_sha256'],ident
 files=read(p)['files']
 for f in files:
  q=root/f['path'] if f['path'].startswith('docs/experiments/') else p.parent/f['path']
  assert q.is_file() and sha(q)==f['sha256'],q
 verified[ident]=len(files)
checks['frozen_indices_verified']=verified
assert 'ENV-TRAJECTORY-OWNERSHIP-20261012' in verified
receipts=[]
for p in sorted((w/'wake').glob('*/receipt.json')):
 r=read(p)
 if r.get('completed_at'):
  assert sha(Path(r['report']))==r['report_sha256'],p
  receipts.append({'event':r['event'],'report_sha256':r['report_sha256']})
assert len(receipts)>=13;checks['prior_signed_reports_verified']=receipts
auto=w/'runs'/event;idx=read(auto/'index.json')
assert len(idx['files'])==317 and all(sha(auto/f['path'])==f['sha256'] for f in idx['files'])
checks['original_raw_files_verified']=317
i=read(base/'inputs.json')
assert sha(root/'robot/fsm-baseline.repos')==i['formal_baseline_sha256'] and i['formal_baseline_commit'] in (root/'robot/fsm-baseline.repos').read_text()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==i['project_head_before']
assert sha(w/'config.json')==sha(base/'monitor/config.json')
checks['project_head_formal_pin_monitor_config_unchanged']=True
rx=re.compile(r'USER-[A-Z]+-[0-9]{8}(?:-[0-9]+)?|(?:VAC|AUBO|RS|CV)-[A-Z0-9]+|(?:VISION|ROBUST|DEMO|ENV|SPRINT)-[A-Z-]+-[0-9]{8}|CTRL-[A-Z]+-[0-9]{4}|TEAMMATE-[A-Z]+-[0-9]{8}|POLYU-[A-Z0-9]+(?:-[A-Z0-9]+)*')
files=[root/'README.md',root/'materials/README.md']
for n in ['docs','demo','robot']:files.extend((root/n).glob('*.md'))
refs={v for p in files for v in rx.findall(p.read_text())};assert not refs-entries.keys(),refs-entries.keys()
changed=[root/p for p in ['README.md','docs/trajectory-ownership-acceptance.md','docs/hardware-vision-plan.md','docs/open-questions.md','docs/upstream-monitor.md','robot/README.md']]
for p in changed:
 text=p.read_text()
 for ident in set(rx.findall(text)):assert str(p.relative_to(root)) in entries[ident]['derived_files'],(p,ident)
 for target in re.findall(r'\]\(([^)]+)\)',text):
  if '://' not in target and not target.startswith('#'):assert (p.parent/target.split('#')[0]).exists(),(p,target)
pattern=re.compile(r'(?<![A-Z0-9-])(?:'+'|'.join(re.escape(k) for k in sorted(entries,key=len,reverse=True))+r')(?![A-Z0-9-])')
for p in base.rglob('*'):
 if not p.is_file():continue
 try:text=p.read_text()
 except UnicodeDecodeError:continue
 for ident in set(pattern.findall(text)):assert str(p.relative_to(root)) in entries[ident]['derived_files'],(p,ident)
checks['citations_reverse_indices_links']='PASS'
qs=re.findall(r'^\| (Q\d+)',(root/'docs/open-questions.md').read_text(),re.M);assert sorted(qs,key=lambda x:int(x[1:]))==[f'Q{i:02d}' for i in range(1,20)]
assert not Path('/proc/59420').exists()
for name in ['mtc-repro-5c8f61d8af9f-681bb64bfb8c','mtc-trajectory-ownership-review-681bb64']:
 v=json.loads(subprocess.check_output(['docker','inspect',name]))[0];h=v['HostConfig']
 assert not v['State']['Running'] and not v['State']['OOMKilled']
 assert h['NetworkMode']=='none' and h['NanoCpus']==2000000000 and h['Memory']==4294967296
 assert not v['Mounts'] and not h['Devices'] and not h['PortBindings']
assert not subprocess.check_output(['docker','ps','--filter','name=mtc-','--format','{{.Names}}'],text=True).strip()
checks['all_task_containers_stopped']=True
s=read(w/'state.json');assert s['active'] is None and s['main_review']['event']==event and s['main_review']['status']=='ACKNOWLEDGED'
assert Path('/proc',str(s['pid'])).exists();checks['monitor_before_complete']={k:s.get(k) for k in ['pid','status','last_successful_poll','pending']}
timer=root/'outputs/cpp-mock-after-watch-20261012';t=read(timer/'state.json');r=read(timer/'scheduler-registration.json')
assert t['status']=='SCHEDULED' and not t['attempts']
assert Path('/proc',str(t['timer_pid']),'stat').read_text().split()[21]==r['process_start_ticks']
assert all(sha(timer/name)==v for name,v in r['files_sha256'].items());checks['deferred_task_not_started_and_unchanged']=True
s=read(base/'summary.json');a=s['analysis'];sup=a['supplement']
assert s['cpp_original_xml_passed']==417 and s['fjt_original_timeout_seconds']==120 and s['ordinary_fjt_retry_cases']==61 and s['ubsan_cases']==478
assert sup['native_goal_count']==0 and sup['native_gate']['status_messages']==0 and sup['native_gate']['driver_files_unchanged']
assert sup['native_gate']['status']=='PASS_COEXISTENCE_BLOCKED' and sup['native_gate']['native_domain155']['status']=='FAIL'
assert a['automatic']['moveit']['clean_shutdown']=='FAIL' and 'TIMEOUT_UNRESOLVED' in a['verdict']
report=root/'docs/trajectory-ownership-acceptance.md';assert entries['ENV-TRAJECTORY-OWNERSHIP-20261012']['index_sha256'] in report.read_text()
checks['reported_counts_scope_and_failures_checked']=True
p=subprocess.run(['git','diff','--check'],cwd=root,capture_output=True,text=True);assert p.returncode==0,p.stdout+p.stderr
checks['git_diff_check']='PASS';checks['report_sha256']=sha(report)
(raw/'verification.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n');print(json.dumps(checks,ensure_ascii=False,indent=2))
