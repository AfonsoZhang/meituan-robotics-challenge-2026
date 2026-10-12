"""Read-only source/automatic evidence audit. OpenAI Codex assisted."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import hashlib,json,re,subprocess,xml.etree.ElementTree as ET
raw=Path(__file__).resolve().parent;root=raw.parents[1];source=raw/'source';watch=root/'outputs/moveit-watch-20261011'
commit='681bb64bfb8cd482d1e78950cef4cfe395b21bff';previous='45f497ce3444e255463faf41f7b736aa9ad07d7b';auto=watch/'runs'/('sha-'+commit)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git','-C',str(source),*a],text=True).strip()
def write(n,v):(raw/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
assert git('rev-parse','HEAD')==commit and not git('status','--short')
paths=git('diff','--name-only',previous,commit).splitlines();assert len(paths)==7
assert all(p.startswith('src/mtc_trajectory_execution_cpp/') or p=='docs/migration/PHASE2B_OWNERSHIP_FINAL_REVIEW.md' for p in paths)
(raw/'incremental.patch').write_text(git('diff','--binary',previous,commit)+'\n')
newtests=re.findall(r'TEST_F\(FjtAction, (\w+)\)',(source/'src/mtc_trajectory_execution_cpp/test/test_fjt_action.cpp').read_text())
oldtests=re.findall(r'TEST_F\(FjtAction, (\w+)\)',git('show',previous+':src/mtc_trajectory_execution_cpp/test/test_fjt_action.cpp'))
assert len(newtests)==61 and len(set(newtests)-set(oldtests))==15
review={'at':datetime.now(timezone.utc).isoformat(),'commit':commit,'previous':previous,'review_base':previous,
 'parents':git('show','-s','--format=%P',commit).split(),'commit_metadata':git('show','-s','--format=fuller',commit),
 'incremental_commits':git('log','--format=%H %P %s',previous+'..'+commit).splitlines(),'changed_files':paths,
 'changed_file_inventory':[{'path':p,'size_bytes':(source/p).stat().st_size,'sha256':sha(source/p)} for p in paths],
 'fjt_registered_source':newtests,'new_tests':sorted(set(newtests)-set(oldtests)),
 'unchanged':['Core FSM','ROSIDL','Action servers','Planner','driver configuration'],
 'changes':'Remove count==1 inferred ownership; require valid live Status with bounded local receive age (VOLATILE); retain pending UUIDs, exact handle comparison and fault lock; result-before-status successor gate; 15 controlled DDS status tests; probe diagnostics; verifier source/registration/XML comparison.',
 'scope':'Controlled test status heartbeat/remap is fixture only; native GenericSystem supplies no initial live status. No strict cross-process lock/absolute freshness proof. Snapshot ABI changed: consumers require rebuilding. Default PickPlace remains MockPlanner/AsyncMockMotion, Task integration not covered.',
 'source_modified':False,'formal_baseline_advanced':False,'local_merge_performed':False,
 'observed_refs':json.loads((auto/'summary.json').read_text())['upstream']['refs']}
write('source-review.json',review)
index=json.loads((auto/'index.json').read_text())
for f in index['files']:assert sha(auto/f['path'])==f['sha256'],f['path']
counts=Counter();xmls=[];errors=[]
for p in sorted((auto/'container/test-results').rglob('*.gtest.xml')):
 rt=ET.parse(p).getroot();cases=list(rt.iter('testcase'));pkg=p.relative_to(auto/'container/test-results').parts[0]
 ids=[]
 for c in cases:
  row={'classname':c.get('classname'),'name':c.get('name'),'status':c.get('status'),'result':c.get('result'),'children':[(v.tag,v.attrib,v.text) for v in c]}
  if list(c) or c.get('status')!='run' or c.get('result')!='completed':errors.append({'path':str(p.relative_to(auto)),'case':row})
  else:counts[pkg]+=1;ids.append(c.get('classname').split('.')[-1]+'.'+c.get('name'))
 xmls.append({'path':str(p.relative_to(auto)),'package':pkg,'passed_cases':ids,'root_attributes':rt.attrib})
assert sum(counts.values())==417 and len(errors)==1 and 'missing_result' in errors[0]['case']['name']
py=[c for p in (auto/'container/test-results').rglob('*pytest*.xml') for c in ET.parse(p).getroot().iter('testcase')]
assert len(py)==269 and all(not list(c) for c in py)
ros=list(ET.parse(auto/'container/ros-wiring.xml').getroot().iter('testcase'));assert len(ros)==6 and all(not list(c) for c in ros)
s=json.loads((auto/'summary.json').read_text());assert len(s['steps'])==25 and s['ended_at'] and s['status']=='COMPLETED_WITH_FAILURES'
assert all(v['started_at'] and v['ended_at'] and isinstance(v['exit_code'],int) for v in s['steps'])
assert 'E2E RESULT: PASS 15 / FAIL 0 / SKIP 0' in (auto/'logs/python-mock-e2e.log').read_text()
assert 'Summary: 15 packages finished' in (auto/'logs/build.log').read_text()
last=(raw/'original-trajectory-testing/Temporary/LastTest_20261011-1955.log').read_text()
assert '[ RUN      ] FjtAction.DuplicateCancelOnlyOneBackendCall\n<end of output>' in last and 'Test time = 120.00 sec' in last
write('automatic-counts.json',{'at':datetime.now(timezone.utc).isoformat(),'original_files_verified':len(index['files']),
 'original_index_sha256':sha(auto/'index.json'),'source_bundle_sha256':sha(auto/'source.bundle'),'summary_complete':True,'summary_steps':25,
 'failed_steps':[v['name'] for v in s['steps'] if v['exit_code']],'build_packages':15,'cpp_xml_passed':417,'cpp_by_package':dict(counts),'cpp_xml':xmls,
 'errors':errors,'fjt_original_log_only_passes':6,'fjt_original_timeout_case':'FjtAction.DuplicateCancelOnlyOneBackendCall','fjt_suite_timeout_seconds':120,
 'fjt_expected':61,'cpp_expected':478,'no_fjt_case_xml':True,'python_cases':269,'python_mock_e2e':15,'ros_wiring_cases':6,
 'colcon_aggregate':{'total':718,'errors':1,'failures':1,'note':'Includes wrappers/lint/missing-result; not independent test counts'},
 'old_fixed_audit':'Outdated16vs22 *_cpp programs excluding4 Planner, macro parsing error, AND real FJT missing-result failure. Not merely audit mismatch.'})
print('SOURCE_AND_ORIGINAL_VERIFIED',len(paths),len(index['files']),dict(counts),len(errors))
