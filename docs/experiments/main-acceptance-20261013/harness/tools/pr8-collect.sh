git rev-parse HEAD
git diff --exit-code HEAD --
python3 - <<'INNER'
from pathlib import Path
import json,hashlib,subprocess,shutil
out=Path('/pr8-review');root=Path('/pr8-source')
tracked=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
rows=[{'path':name,'sha256':hashlib.sha256((root/name).read_bytes()).hexdigest()} for name in tracked if name]
(out/'source-identity.json').write_text(json.dumps({'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'files':rows},indent=2)+'\n')
base=Path('/pr8-install/mtc_cpp_mock_bringup/lib/python3.12/site-packages');pairs=[]
for module in ('mtc_cpp_mock_bringup','mtc_webui'):
 for source in (root/'src/mtc_cpp_mock_bringup'/module).rglob('*.py'):
  installed=base/module/source.relative_to(root/'src/mtc_cpp_mock_bringup'/module)
  assert installed.read_bytes()==source.read_bytes(),str(installed)
  pairs.append({'source':str(source),'installed':str(installed),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
(out/'installed-identity.json').write_text(json.dumps(pairs,indent=2)+'\n')
for p in Path('/pr8-build').rglob('*'):
 if p.is_file() and not p.is_symlink() and p.name in ['compile_commands.json','link.txt']:
  q=out/'build-artifacts'/p.relative_to('/pr8-build');q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
post={}
for scenario in ['c1','cleanup-only']:
 d=json.loads((out/scenario/'stack/cleanup.json').read_text());post[scenario]=d
 assert d['cleanup_ok'] and d['exit_code']==0 and all(v==0 for v in d['returncodes'].values())
for file in ['task.log','pick_place.log']:
 text=(out/'cleanup-only/stack'/file).read_text()
 assert 'MTC_TRACE' not in text, file
post['restart_no_goal_trace']=True
(out/'postcheck.json').write_text(json.dumps(post,ensure_ascii=False,indent=2)+'\n')
print('PR8 source/installed identity PASS',len(rows),len(pairs),'direct supervisor restart cleanup PASS, zero Goal traces')
INNER
ros2 daemon stop
ros2 node list --no-daemon --spin-time 2
