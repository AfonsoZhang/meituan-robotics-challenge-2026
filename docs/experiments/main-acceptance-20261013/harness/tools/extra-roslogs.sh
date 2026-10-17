python3 - <<'INNER'
from pathlib import Path
import shutil,datetime,json
out=Path('/review/extra-roslogs');out.mkdir(exist_ok=False)
cutoff=datetime.datetime.fromisoformat('2026-10-13T05:07:30+00:00').timestamp();items=[]
for base in [Path('/tmp/mtc_phase2a_test_logs'),Path('/tmp/mtc_phase2b_tests')]:
 for p in base.rglob('*'):
  if p.is_file() and p.stat().st_mtime >= cutoff:
   q=out/base.name/p.relative_to(base);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);items.append(str(p))
(out/'collection.json').write_text(json.dumps({'cutoff':cutoff,'files':items},indent=2)+'\n')
print('Additional current-container ROS logs',len(items))
INNER
