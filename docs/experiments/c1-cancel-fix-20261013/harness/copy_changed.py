"""Copy only changed tracked source paths; verify the complete tree separately."""
import io,subprocess,tarfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'source'
files=subprocess.check_output(['git','-C',str(root),'diff','--name-only','-z','7da4322']).decode().split('\0')
buffer=io.BytesIO()
with tarfile.open(fileobj=buffer,mode='w') as archive:
    for name in filter(None,files):archive.add(root/name,arcname=name,recursive=False)
subprocess.run(['docker','exec','-i','mtc-c1-fix-20261013','tar','--no-same-owner','-xf','-','-C','/c1-source'],input=buffer.getvalue(),check=True)
print('copied',len([name for name in files if name]))
