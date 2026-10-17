"""Preserve concurrent P1 decision; allocate C1 a distinct source ID before publication."""
import copy,hashlib,json,shutil
from pathlib import Path
run=Path(__file__).resolve().parents[1];project=run.parents[1];pub=run/'publication'
old='USER-HW-20261013-02';new='USER-HW-20261013-03';env='ENV-CANCEL-FIX-20261013'
evidence='docs/experiments/c1-cancel-fix-20261013';dest=pub/evidence
receipt=json.loads((run/'freeze-receipt.json').read_text())
# Only this task's own harness and new frozen files, never P1 references.
for name in ['freeze.py','register.py']:
 p=run/'harness'/name;s=p.read_text().replace(old,new);p.write_text(s);shutil.copyfile(p,dest/'harness'/name)
shutil.copyfile(Path(__file__),dest/'harness'/Path(__file__).name)
for name in ['protocol.md','inputs.json']:
 p=dest/name;p.write_text(p.read_text().replace(old,new))
(pub/'materials/manifest.json').exists()
pubdata=json.loads((pub/'materials/manifest.json').read_text())
for section in ['project_decisions','external_references','local_observations']:
 for x in pubdata[section]:
  if x['id']==old and x.get('original_text','').startswith('解决：PR #8'):
   x['id']=new
  if x['id']==env:x['triggered_by']=[new]
# Re-index this unpublished artifact before recording its final digest.
index=json.loads((dest/'index.json').read_text())
index['files']=[dict(path=str(p.relative_to(dest)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),size=p.stat().st_size) for p in sorted(dest.rglob('*')) if p.is_file() and p!=dest/'index.json']
(dest/'index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
receipt.update(index_sha256=hashlib.sha256((dest/'index.json').read_bytes()).hexdigest(),file_count=len(index['files']))
(run/'freeze-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
for x in pubdata['local_observations']:
 if x['id']==env:x['index_sha256']=receipt['index_sha256']
(pub/'materials/manifest.json').write_text(json.dumps(pubdata,ensure_ascii=False,indent=2)+'\n')
rootdata=json.loads((project/'materials/manifest.json').read_text())
assert any(x['id']==old and x['original_text'].startswith('P1：') for x in rootdata['project_decisions'])
for section,identity in [('project_decisions',new),('external_references','TEAMMATE-CANCELFIX-20261013'),('local_observations',env)]:
 assert not any(x['id']==identity for x in rootdata[section]),identity
 rootdata[section].append(copy.deepcopy(next(x for x in pubdata[section] if x['id']==identity)))
(project/'materials/manifest.json').write_text(json.dumps(rootdata,ensure_ascii=False,indent=2)+'\n')
for root in [pub,project]:
 for name in ['README.md','docs/current-status.md','docs/open-questions.md','docs/hardware-vision-plan.md','docs/cpp-mock-webui-acceptance.md']:
  p=root/name
  p.write_text(''.join(line.replace(old,new) if env in line else line for line in p.read_text().splitlines(keepends=True)))
 p=root/'docs/c1-cancel-fix.md';s=p.read_text().replace(old,new)
 import re
 s=re.sub(r'冻结目录含 \*\*\d+ 个索引成员\*\*',f"冻结目录含 **{receipt['file_count']} 个索引成员**",s)
 s=re.sub(r'(SHA-256：`)\w{64}(`)',r'\g<1>'+receipt['index_sha256']+r'\g<2>',s)
 p.write_text(s)
assert not (project/evidence).exists()
shutil.copytree(dest,project/evidence)
print(json.dumps(receipt,ensure_ascii=False))
