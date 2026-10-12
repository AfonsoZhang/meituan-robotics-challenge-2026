from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
p=Path(__file__).resolve().parent;root=p.parents[1]
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
m=json.loads((root/'materials/manifest.json').read_text());checks={'at':datetime.now(timezone.utc).isoformat(),'indices':{},'receipts':[]}
for group in ['sources','project_decisions','external_references','local_observations']:
 for e in m[group]:
  if e.get('index') and e.get('index_sha256'):
   idx=root/e['index'];assert sha(idx)==e['index_sha256'],e['id']
   index=json.loads(idx.read_text())
   for f in index.get('files',[]):
    q=root/f['path'] if f['path'].startswith('docs/experiments/') else idx.parent/f['path']
    assert sha(q)==f['sha256'],str(q)
   checks['indices'][e['id']]={'sha256':sha(idx),'flat_files_verified':len(index.get('files',[])),'legacy_run_format':'runs' in index}
for f in (root/'outputs/moveit-watch-20261011/wake').glob('*/receipt.json'):
 r=json.loads(f.read_text())
 if r.get('completed_at'):
  assert sha(Path(r['report']))==r['report_sha256'],str(f)
  checks['receipts'].append({'event':r['event'],'report':r['report'],'report_sha256':r['report_sha256']})
state=json.loads((root/'outputs/moveit-watch-20261011/state.json').read_text())
assert state['status']=='EXPIRED' and not state['active'] and not state['main_review'] and not state['pending']
checks['expired_state_sha256']=sha(root/'outputs/moveit-watch-20261011/state.json')
checks['baseline_file_sha256']=sha(root/'robot/fsm-baseline.repos')
(p/'evidence/prior-integrity.json').write_text(json.dumps(checks,indent=2)+'\n')
print('prior indices',len(checks['indices']),'completed receipts',len(checks['receipts']))
