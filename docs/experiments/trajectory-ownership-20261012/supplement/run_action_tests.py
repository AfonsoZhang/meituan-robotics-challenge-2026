"""Bounded unchanged GTest runs; preserve timeout and /proc wait evidence. Codex assisted."""
from pathlib import Path
from datetime import datetime,timezone
import json,os,signal,subprocess,time,sys
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
binary=sys.argv[2];mode=sys.argv[3]
def write(n,v):(out/n).write_text(json.dumps(v,indent=2)+'\n')
def one(label,args,seconds):
 start=datetime.now(timezone.utc).isoformat();started=time.monotonic()
 argv=[binary,*args,'--gtest_output=xml:'+str(out/(label+'.xml'))]
 with (out/(label+'.log')).open('w') as log:
  p=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  timed=False
  try:p.wait(timeout=seconds)
  except subprocess.TimeoutExpired:
   timed=True;threads=[]
   for t in sorted(Path('/proc',str(p.pid),'task').glob('*')):
    item={'tid':t.name}
    for name in ['status','wchan','stack','syscall']:
     try:item[name]=(t/name).read_text()
     except OSError as e:item[name]=repr(e)
    threads.append(item)
   write(label+'-timeout-threads.json',threads)
   os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(timeout=3)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=5)
 rec={'label':label,'argv':argv,'pid':p.pid,'started_at':start,'ended_at':datetime.now(timezone.utc).isoformat(),
      'elapsed_seconds':time.monotonic()-started,'deadline_seconds':seconds,'timed_out':timed,'process_exit_code':p.returncode,
      'exit_code':124 if timed else p.returncode,'process_reaped':not Path('/proc',str(p.pid)).exists(),'xml_exists':(out/(label+'.xml')).exists()}
 write(label+'.json',rec);print(json.dumps(rec),flush=True);return rec
listing=subprocess.check_output([binary,'--gtest_list_tests'],text=True,timeout=15);(out/'registration.txt').write_text(listing)
if mode=='full': rows=[one('full',[],120)]
elif mode=='individual':
 names=[line.strip() for line in listing.splitlines() if line.startswith('  ')];assert len(names)==61
 rows=[one(name,['--gtest_filter=FjtAction.'+name],15) for name in names]
else:raise ValueError(mode)
write('summary.json',rows)
sys.exit(0 if all(x['exit_code']==0 for x in rows) else 1)
