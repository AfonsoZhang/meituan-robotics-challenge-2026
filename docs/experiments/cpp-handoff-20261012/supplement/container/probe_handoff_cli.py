"""Check documented C++ Mock ROS graph commands only. Codex assisted, 2026-10-12.
No Goal, Cancel, driver, MoveIt or physical device is invoked by this probe.
"""
import json,os,signal,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
out=Path('/review-evidence/documented-cli');out.mkdir(parents=True)
records=[];shutdown=[];checks=[]

def cli(domain,label,args,timeout=20):
 env=dict(os.environ,ROS_DOMAIN_ID=str(domain),ROS_LOG_DIR=str(out/'ros-logs'))
 started=datetime.now(timezone.utc).isoformat()
 try:
  p=subprocess.run(['ros2',*args],env=env,capture_output=True,text=True,timeout=timeout);rc=p.returncode;log=p.stdout+p.stderr
 except subprocess.TimeoutExpired as e:
  rc=124;log=str(e.stdout or '')+'\n'+str(e.stderr or '')
 (out/(label+'.log')).write_text(log)
 row={'label':label,'domain':domain,'argv':['ros2',*args],'exit_code':rc,'started_at':started,'ended_at':datetime.now(timezone.utc).isoformat()};records.append(row)
 print(json.dumps(row),flush=True)
 return rc,log

def inspect_action(domain,name,label,server):
 rc,log=cli(domain,label,['action','info',name,'-t'])
 if rc==2 and 'unrecognized arguments: -t' in log:
  rc,log=cli(domain,label+'-without-t',['action','info',name]);records[-1]['scope']='Compatibility diagnosis only; original documented flag failure retained'
 checks.append({'check':label+'-unique-server','pass':rc==0 and 'Action servers: 1' in log and server in log})

for domain,programs,expected in [(121,['mock_pick_place_server','mock_task_server'],['/mtc_mock_pick_place','/mtc_mock_task']),(122,['mock_motion_server'],['/mtc_mock_joint_move'])]:
 procs=[]
 try:
  rc,log=cli(domain,f'domain-{domain}-before',['node','list','--no-daemon','--spin-time','2'])
  assert rc==0 and not log.strip(),(rc,log)
  for program in programs:
   env=dict(os.environ,ROS_DOMAIN_ID=str(domain),ROS_LOG_DIR=str(out/'ros-logs'))
   f=(out/(program+'.log')).open('w');p=subprocess.Popen(['ros2','run','mtc_ros2_action_cpp',program],env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);procs.append((program,p,f));time.sleep(.5)
  time.sleep(2)
  rc,log=cli(domain,f'domain-{domain}-nodes',['node','list','--no-daemon','--spin-time','2'])
  checks.append({'check':f'domain-{domain}-exact-nodes','pass':rc==0 and sorted(log.splitlines())==sorted(expected),'observed':log.splitlines()})
  for node in expected:cli(domain,node.removeprefix('/')+'-info',['node','info',node])
  cli(domain,f'domain-{domain}-actions',['action','list','-t'])
  if domain==121:
   inspect_action(domain,'/mtc/task/execute','task-action-info','/mtc_mock_task')
   inspect_action(domain,'/mtc/manipulation/pick_place','pickplace-action-info','/mtc_mock_pick_place')
   cli(domain,'hidden-topics',['topic','list','-t','--include-hidden-topics'])
   for name,path in [('task','/mtc/task/execute/_action/feedback'),('pickplace','/mtc/manipulation/pick_place/_action/feedback')]:
    rc,log=cli(domain,name+'-feedback-qos',['topic','info',path,'--verbose'])
    checks.append({'check':name+'-feedback-qos','pass':rc==0 and 'Publisher count: 1' in log and 'RELIABLE' in log and 'VOLATILE' in log})
  else:inspect_action(domain,'/mtc/motion/execute_joint_move','motion-action-info','/mtc_mock_joint_move')
 finally:
  for program,p,f in reversed(procs):
   escalated=False
   if p.poll() is None:
    os.killpg(p.pid,signal.SIGINT)
    try:p.wait(timeout=12)
    except subprocess.TimeoutExpired:
     escalated=True;os.killpg(p.pid,signal.SIGTERM)
     try:p.wait(timeout=5)
     except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=5)
   f.close();shutdown.append({'program':program,'domain':domain,'ros2_run_exit':p.returncode,'escalated':escalated})
  rc,log=cli(domain,f'domain-{domain}-after',['node','list','--no-daemon','--spin-time','2'])
  checks.append({'check':f'domain-{domain}-empty-after','pass':rc==0 and not log.strip()})
  cli(domain,f'domain-{domain}-daemon-stop',['daemon','stop'])
summary={'scope':'New README graph/QoS command validation using unmodified Mock executables; no goal or motion issued','commands':records,'checks':checks,'shutdown':shutdown,'documented_command_errors':[x for x in records if x['exit_code']!=0],'all_checks_pass':all(x['pass'] for x in checks),'all_servers_clean_exit':all(x['ros2_run_exit']==0 and not x['escalated'] for x in shutdown),'goal_cancel_scenarios_this_supplement':'NOT RERUN: code unchanged from c10f6ed; current registered C++ tests and historical standalone verification retained separately'}
(out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':checks,'shutdown':shutdown,'command_errors':summary['documented_command_errors']},indent=2),flush=True)
raise SystemExit(0 if summary['all_checks_pass'] and summary['all_servers_clean_exit'] and not summary['documented_command_errors'] else 1)
