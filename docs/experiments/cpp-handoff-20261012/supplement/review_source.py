"""Read-only source/results provenance review; OpenAI Codex assisted."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess,xml.etree.ElementTree as ET
r=Path(__file__).resolve().parent;src=r/'source';w=r.parent/'moveit-watch-20261011';sha='a04ac6831dd3963e6b1ec4b9e27214eb564f9f24';prev='c10f6ed59966401684851f917f9137b0a6cf12ae';p=w/'runs'/('sha-'+sha)
def git(*a):return subprocess.check_output(['git','-C',str(src),*a],text=True).strip()
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):(r/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
paths=git('diff','--name-only',prev,sha).splitlines();assert paths==['README.md','README_FSM.md'];assert git('rev-parse','HEAD')==sha
unchanged=['src','tests','config','scripts','docs']
for q in unchanged:assert not git('diff','--name-only',prev,sha,'--',q)
assert not (src/'src/mtc_moveit_planner').exists()
review={'commit':sha,'previous':prev,'parents':git('show','-s','--format=%P',sha).split(),'commit_metadata':git('show','-s','--format=fuller',sha),'commit_date':git('show','-s','--format=%cI',sha),'changed_files':paths,'source_files':[{'path':q,'size_bytes':(src/q).stat().st_size,'sha256':digest(src/q)} for q in paths],'all_runtime_source_tests_config_scripts_docs_same_as_previous':True,'verified_unchanged_paths':unchanged,'planner_package_present':False,'cpp_action_package_present':True,'new_cpp_bringup_launch_present':False,'source_git_status':git('status','--short'),'handoff_data_summary':'README clarifies Phase 2A Mock vs full chain, 358-case verifier and graph/QoS CLI, Python bringup not C++. Requests future C++ bringup as upstream handoff; not an instruction to this event to implement it. Upstream main@c0f7017 handoff reference is distinct from this observed a04ac68 commit and local formal 1d940f7 pin.','supplement_scope':'Verify documented current audit and graph/QoS CLI on exact built binaries. No goal/cancel standalone, UBSan, consumer or new planning rerun: unchanged code, current automatic registered tests plus separately cited history.','formal_baseline_advanced':False,'local_merge_performed':False,'at':datetime.now(timezone.utc).isoformat()}
write('source-review.json',review)
idx=json.loads((p/'index.json').read_text())
for f in idx['files']:assert digest(p/f['path'])==f['sha256'],f['path']
counts={};cpp=[];python=[]
for f in sorted((p/'container/test-results').rglob('*.xml')):
 z=ET.parse(f).getroot();cases=list(z.iter('testcase'))
 if f.name.endswith('.gtest.xml'):
  pkg=f.relative_to(p/'container/test-results').parts[0];assert all(c.get('status')=='run' and c.get('result')=='completed' and not list(c) for c in cases)
  assert len(cases)==int(z.attrib['tests']);counts[pkg]=counts.get(pkg,0)+len(cases);cpp.append({'path':str(f.relative_to(p)),'cases':[c.get('classname')+'.'+c.get('name') for c in cases]})
 elif 'pytest' in f.name:
  assert all(not list(c) for c in cases);python.extend(cases)
assert counts=={'mtc_core_cpp':23,'mtc_manipulation_cpp':120,'mtc_motion_execution_cpp':88,'mtc_ros2_action_cpp':40,'mtc_task_cpp':87}
assert len(cpp)==20 and len(python)==269
ros=list(ET.parse(p/'container/ros-wiring.xml').getroot().iter('testcase'));assert len(ros)==6 and all(not list(c) for c in ros)
s=json.loads((p/'summary.json').read_text());assert len(s['steps'])==25 and s['ended_at'] and s['status']=='COMPLETED_WITH_FAILURES'
for name in ['stop','collect']:assert next(t for t in s['steps'] if t['name']==name)['exit_code']==0
assert 'E2E RESULT: PASS 15 / FAIL 0 / SKIP 0' in (p/'logs/python-mock-e2e.log').read_text()
write('automatic-counts.json',{'original_index_sha256':digest(p/'index.json'),'original_files_verified':len(idx['files']),'summary_steps':25,'summary_complete':True,'cpp_total':sum(counts.values()),'cpp_by_package':counts,'cpp_executables':20,'cpp_xml':cpp,'python_cases':269,'python_mock_e2e':15,'ros_wiring_cases':6,'ros_wiring_identities':[{k:c.get(k) for k in ['classname','name']} for c in ros],'source_bundle_sha256':digest(p/'source.bundle')})
print(json.dumps({'changed_files':paths,'verified_original_files':len(idx['files']),'cpp':counts,'python':269,'e2e':15,'ros':6}))
