"""Local read-only evidence audit; OpenAI Codex assisted, 2026-10-12."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,re,subprocess,xml.etree.ElementTree as ET
root=Path('/home/afonso/meituan-robotics-challenge-2026')
raw=root/'outputs/planner-acceptance-20261011-fcdd8ea';src=raw/'source'
w=root/'outputs/moveit-watch-20261011';sha='fcdd8eae897cbc37c539d4bad57b712f08124938';old='1d940f7c5f12561fed6641457c0b4b630a282b05';auto=w/'runs'/('sha-'+sha)
def git(*a):return subprocess.check_output(['git','-C',str(src),*a],text=True).strip()
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,d):(raw/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
assert git('rev-parse','HEAD')==sha
paths=git('diff','--name-only',old,sha).splitlines();assert len(paths)==53
index=json.loads((auto/'index.json').read_text())
for f in index['files']:assert digest(auto/f['path'])==f['sha256'],f['path']
assert len(index['files'])==290
unchanged=['src/mtc_core_cpp','src/mtc_task_cpp','src/mtc_manipulation_cpp','src/mtc_motion_execution_cpp','src/mtc_interfaces','src/mtc_task','src/mtc_manipulation','docs/setup']
for p in unchanged:assert not git('diff','--name-only',old,sha,'--',p),p
review={'commit':sha,'previous':old,'metadata':git('show','-s','--format=fuller',sha),'parents':git('show','-s','--format=%P',sha).split(),'branch':'refs/heads/feature/moveit-planner','changed_files':paths,'changed_file_inventory':[{'path':p,'sha256':digest(src/p),'size_bytes':(src/p).stat().st_size} for p in paths],'unchanged_compared_to_sdk_baseline':unchanged,'cpp_action_package_present':(src/'src/mtc_ros2_action_cpp').exists(),'ros_wiring_test_present':(src/'tests/test_ros_wiring.py').exists(),'git_status':git('status','--short'),'original_files_verified':len(index['files']),'original_index_sha256':digest(auto/'index.json'),'source_bundle_sha256':digest(auto/'source.bundle'),'recorded_at':datetime.now(timezone.utc).isoformat(),'review_scope':'New planner core, MoveGroup backend, config, launch, SOP, both tool entry points, four tests, upstream handoff. Upstream archived evidence is supplied data, not local execution. Core/Action/Cancel implementations unchanged; no baseline merge.'}
assert not review['cpp_action_package_present'] and not review['ros_wiring_test_present']
write('source-review.json',review)
cpp=[];counts={}
for p in sorted((auto/'container/test-results').rglob('*.gtest.xml')):
 z=ET.parse(p).getroot();pkg=p.relative_to(auto/'container/test-results').parts[0];cases=list(z.iter('testcase'))
 assert len(cases)==int(z.attrib['tests']);assert int(z.get('failures','0'))==int(z.get('errors','0'))==int(z.get('disabled','0'))==0
 for c in cases:assert c.get('status')=='run' and c.get('result')=='completed' and not list(c)
 counts[pkg]=counts.get(pkg,0)+len(cases)
 cpp.append({'path':str(p.relative_to(auto)),'package':pkg,'cases':[c.get('classname')+'.'+c.get('name') for c in cases]})
assert counts=={'mtc_core_cpp':23,'mtc_manipulation_cpp':120,'mtc_motion_execution_cpp':88,'mtc_moveit_planner':29,'mtc_task_cpp':87},counts
expected={}
for p in sorted((src/'src/mtc_moveit_planner/test').glob('test_*.cpp')):
 expected[p.stem]=['mtc_moveit_planner.'+a+'.'+b for a,b in re.findall(r'\bTEST\(\s*(\w+)\s*,\s*(\w+)\s*\)',p.read_text())]
actual={Path(v['path']).name.removesuffix('.gtest.xml'):v['cases'] for v in cpp if v['package']=='mtc_moveit_planner'}
assert expected==actual,(expected,actual)
py=[]
for p in sorted((auto/'container/test-results').rglob('*.xml')):
 if 'pytest' not in p.name:continue
 z=ET.parse(p).getroot();cases=list(z.iter('testcase'));py.extend(cases)
 assert all(not list(c) for c in cases),(p,[c.attrib for c in cases if list(c)])
assert len(py)==269,len(py)
s=json.loads((auto/'summary.json').read_text());assert len(s['steps'])==25 and s['ended_at'] and s['status']=='COMPLETED_WITH_FAILURES'
for n in ['stop','collect']:assert next(v for v in s['steps'] if v['name']==n)['exit_code']==0
write('automatic-counts.json',{'verified_at':datetime.now(timezone.utc).isoformat(),'original_files_verified':290,'summary_complete':True,'automatic_steps':len(s['steps']),'cpp_total':sum(counts.values()),'cpp_by_package':counts,'cpp_executables':len(cpp),'new_planner_cases_match_all_source_TEST_identities':True,'cpp_xml':cpp,'python_cases':len(py),'python_mock_e2e':15,'ros_wiring':'NOT RUN: test file absent on planning branch','cpp_action':'NOT PRESENT on planning branch','fixed_cpp_audit_scope':'318 cases / 16 executables, excludes new planner package; 29 verified independently here.'})
print(json.dumps({'changed_files':len(paths),'original_files_verified':290,'cpp':counts,'cpp_executables':len(cpp),'python':len(py)},ensure_ascii=False))
