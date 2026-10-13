"""Collect C1 test identities and byte-verified source/binaries, without old snapshots."""
import hashlib,json,subprocess
from pathlib import Path
run=Path(__file__).resolve().parents[1]
container='mtc-c1-fix-20261013'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
out=run/'container';out.mkdir(exist_ok=False)
subprocess.run(['docker','cp',container+':/c1-evidence/.',str(out)],check=True)
packages=['mtc_core_cpp','mtc_motion_execution_cpp','mtc_manipulation_cpp','mtc_task_cpp','mtc_ros2_action_cpp']
for package in packages:
    dest=out/'test-results'/package;dest.mkdir(parents=True)
    subprocess.run(['docker','cp',container+':/c1-build/'+package+'/test_results/.',str(dest)],check=True)
import xml.etree.ElementTree as ET
cases=[]
for path in (out/'test-results').rglob('*.gtest.xml'):
    tree=ET.parse(path)
    for case in tree.iter('testcase'):
        cases.append(dict(file=str(path.relative_to(out)),suite=case.get('classname'),name=case.get('name'),failed=case.find('failure') is not None,error=case.find('error') is not None,skipped=case.find('skipped') is not None))
summary=dict(cases=len(cases),failed=sum(x['failed'] for x in cases),errors=sum(x['error'] for x in cases),skipped=sum(x['skipped'] for x in cases),identities=cases)
(run/'meta/tests.json').write_text(json.dumps(summary,indent=2)+'\n')
assert cases and summary['failed']==summary['errors']==summary['skipped']==0,summary
source=run/'source'
tracked=subprocess.check_output(['git','-C',str(source),'ls-files','-z']).decode().split('\0')
# All build-relevant source and config must match; documentation is recorded by Git.
expected={name:sha(source/name) for name in filter(None,tracked) if name.startswith('src/') and not name.endswith('.md')}
code='''import hashlib,json,sys\nfrom pathlib import Path\nexpected=json.load(sys.stdin)\nactual={name:hashlib.sha256((Path('/c1-source')/name).read_bytes()).hexdigest() for name in expected}\nprint(json.dumps(actual,sort_keys=True))\n'''
raw=subprocess.check_output(['docker','exec','-i',container,'python3','-c',code],input=json.dumps(expected).encode())
actual=json.loads(raw);assert expected==actual,'compiled source differs'
(run/'meta/source-integrity.json').write_text(json.dumps({'files':expected,'matches_container':True},indent=2)+'\n')
for name,argv in {
 'fixed-binaries.sha256':['sha256sum','/c1-install/mtc_motion_execution_cpp/lib/libmtc_motion_execution_cpp.so','/c1-install/mtc_ros2_action_cpp/lib/libmtc_ros2_action_cpp.so'],
 'environment.txt':['bash','-c','cat /etc/os-release; uname -m; g++ --version; python3 --version; dpkg-query -W ros-jazzy-rclcpp ros-jazzy-rclcpp-action ros-jazzy-rclpy ros-jazzy-rmw-fastrtps-cpp'],
 'processes-before-stop.txt':['ps','-eo','pid,ppid,state,args'],
}.items():
 (run/'meta'/name).write_bytes(subprocess.check_output(['docker','exec',container,*argv]))
print(json.dumps({k:v for k,v in summary.items() if k!='identities'}))
print('Source files verified:',len(expected))
