from pathlib import Path
import hashlib,io,json,subprocess,tarfile
r=Path(json.loads(Path('.agents/webui-p2-current.json').read_text())['run'])
repo=r/'upstream';module=repo/'src/mtc_cpp_mock_bringup/mtc_webui';rows=[]
assert subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()=='8f11750e0bd2e485826acb904fd31382945ba0b9'
for p in sorted(Path('webui').rglob('*')):
    if not p.is_file() or '__pycache__' in p.parts or p.name=='run.sh':continue
    out=module/p.relative_to('webui');out.parent.mkdir(parents=True,exist_ok=True);data=p.read_bytes()
    if p.suffix=='.py':
        data=data.replace(b'from webui.',b'from mtc_webui.').replace(b'import webui.',b'import mtc_webui.').replace(b'python3 -m webui.',b'python3 -m mtc_webui.')
    out.write_bytes(data)
    rows.append(dict(personal=str(p),package=str(out.relative_to(repo)),personal_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),package_sha256=hashlib.sha256(data).hexdigest(),transform='Python import/module namespace webui -> mtc_webui only'))
(r/'source-sync.json').write_text(json.dumps(rows,indent=2)+'\n')
buffer=io.BytesIO()
with tarfile.open(fileobj=buffer,mode='w') as archive:
    archive.add(repo/'src/mtc_cpp_mock_bringup',arcname='mtc_cpp_mock_bringup')
subprocess.run(['/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe','exec','-i','mtc-webui-p2-20261013','tar','--no-same-owner','-xf','-','-C','/p2-package/src'],input=buffer.getvalue(),check=True)
print('Synchronized',len(rows),'Web files')
