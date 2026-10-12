export ROS_DOMAIN_ID=137
python3 src/mtc_ros2_action_cpp/test/verify_results.py --build-base /candidate-build
python3 -B scripts/calibration/run_offline_validation.py --out /review-evidence/offline
python3 - <<'PY'
from pathlib import Path
import ast, hashlib, json, subprocess
r=Path('/candidate');p=Path('/review-evidence/offline/results.json');s=json.loads(p.read_text())
assert s['all_passed'] and s['unittest']['tests_ran']==54 and s['unittest']['skipped']==0
assert s['git']['head']=='06ab689f25e87dcebf9fd04fdd581ec4755206f6' and not s['git']['uncommitted_calibration_paths']
assert len(s['documented_cases'])==6 and len(s['generated_negative_cases'])==5
assert all(x['passed'] for x in s['documented_cases']+s['generated_negative_cases'])
identities=[]
for f in sorted((r/'tests/calibration').glob('test_*.py')):
 for cls in ast.parse(f.read_text()).body:
  if isinstance(cls,ast.ClassDef):
   identities += [f.stem+'.'+cls.name+'.'+x.name for x in cls.body if isinstance(x,ast.FunctionDef) and x.name.startswith('test_')]
assert len(identities)==len(set(identities))==54
text=Path('/review-evidence/offline/unittest.txt').read_text()
assert text.count(' ... ok')==54 and 'skipped' not in text
out={'source_test_identities':identities,'cases':54,'ordinary_cpp_verifier':'358/20; planner29 audited separately','source_clean':not subprocess.check_output(['git','diff','HEAD','--'],cwd=r,text=True)}
assert out['source_clean']
Path('/review-evidence/offline/source-identity.json').write_text(json.dumps(out,indent=2)+'\n')
print('PASS: 54 tests /6 documented cases /5 generated negatives; source unchanged')
PY
