"""C1 fixed-head regression with actual installed C++ parent/child Actions.

Codex-assisted external harness: no synthetic ROS result or robot feedback.
"""
import argparse,json,os,re,signal,subprocess,time
from datetime import datetime,timezone
from pathlib import Path

a=argparse.ArgumentParser();a.add_argument('phase',choices=['baseline','fixed']);args=a.parse_args()
root=Path('/c1-evidence')/args.phase;root.mkdir(exist_ok=False)

def stamp():return datetime.now(timezone.utc).isoformat()
def check(value,message):
    if not value:raise AssertionError(message)
def run_client(out,ns,label,cancel_delay=None,mode=1):
    goal=dict(task_id=label,mode=mode,ordered_colors=[1] if mode==1 else [3,1,2],timeout_ms=30000,placement_stability_sec=3.0)
    argv=['ros2','run','mtc_cpp_mock_bringup','mock_task','--namespace',ns,'--output-dir',str(out),'--goal',json.dumps(goal)]
    if cancel_delay is not None:argv+=['--cancel-at','MOVE_PRE_ALIGN','--cancel-delay-ms',str(cancel_delay)]
    with out.with_suffix('.log').open('xb') as log:
        p=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,timeout=55)
    final=json.loads((out/'result.json').read_text())
    events=[json.loads(line) for line in (out/'events.jsonl').read_text().splitlines()]
    return dict(argv=argv,exit_code=p.returncode,final=final,cancel_replies=[e for e in events if e['kind']=='cancel_reply'],events=events)

def scenario(label,delay=400,result_delay=700,profile='success',expected=(5,0),followup=None):
    out=root/label;out.mkdir();ns='/c1_'+label
    argv=['ros2','run','mtc_cpp_mock_bringup','mock_stack','--namespace',ns,'--output-dir',str(out/'stack'),'--result-delay-ms',str(result_delay),'--profile',profile,'--no-web']
    summary=dict(started_at=stamp(),argv=argv,profile=profile,delay_ms=delay,result_delay_ms=result_delay,status='ERROR')
    with (out/'stack.log').open('xb') as log:
        stack=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            deadline=time.monotonic()+35
            while time.monotonic()<deadline:
                check(stack.poll() is None,'stack exited during readiness')
                f=out/'stack'/'ready.json'
                if f.exists() and json.loads(f.read_text()).get('ok'):break
                time.sleep(.05)
            else:raise TimeoutError('stack readiness')
            task=run_client(out/'client',ns,label,delay)
            summary['task']={k:v for k,v in task.items() if k!='events'}
            final=task['final'];check((final['status'],final['result']['error_code'])==expected,f'unexpected terminal {final}')
            check(final['result']['completed_count']==0,'cancel/fault counted completion')
            check(not final['result']['success'],'cancel/fault claimed success')
            if delay is not None:
                check(len(task['cancel_replies'])==1 and task['cancel_replies'][0]['response']['goals_canceling'],'cancel ACK missing')
            task_log=(out/'stack'/'task.log').read_text()
            matches=re.findall(r'event=child_result parent='+final['goal_id']+r' child=([0-9a-f]+) status=(\d+) error=(\d+)',task_log)
            check(len(matches)==1,f'missing unique correlated child result: {matches}')
            child,status,error=matches[0]
            check((int(status),int(error))==expected,'child terminal mismatch')
            summary['child']=dict(goal_id=child,status=int(status),error_code=int(error))
            if followup:
                nxt=run_client(out/'followup',ns,label+'_next')
                summary['followup']={k:v for k,v in nxt.items() if k!='events'}
                if followup=='success':
                    f=nxt['final'];check(f['status']==4 and f['result']['error_code']==0 and f['result']['completed_count']==1,'next task failed')
                else:check(nxt['final']['status']=='REJECTED','fault admission unlocked')
            summary['status']='PASS'
        except Exception as exc:
            summary['error']=repr(exc)
        finally:
            if stack.poll() is None:
                stack.send_signal(signal.SIGINT)
                try:stack.wait(timeout=25)
                except subprocess.TimeoutExpired:
                    summary['forced_cleanup']=True;os.killpg(stack.pid,signal.SIGTERM)
                    try:stack.wait(timeout=5)
                    except subprocess.TimeoutExpired:os.killpg(stack.pid,signal.SIGKILL);stack.wait(3)
            summary['stack_exit_code']=stack.returncode
            cleanup=out/'stack'/'cleanup.json'
            summary['cleanup']=json.loads(cleanup.read_text()) if cleanup.exists() else None
            if stack.returncode!=0 or not summary['cleanup'] or not summary['cleanup'].get('cleanup_ok'):
                summary['status']='CLEANUP_FAIL'
            summary['ended_at']=stamp()
            (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(label,summary['status'],summary.get('error',''),flush=True)
    return summary

if args.phase=='baseline':
    rows=[scenario('baseline_delayed',expected=(6,520),followup='reject')]
else:
    rows=[]
    for delay in [0,200,400,600,1000]:
        rows.append(scenario('delay_'+str(delay),delay=delay,result_delay=1500 if delay==1000 else 700,followup='success' if delay==400 else None))
    rows.append(scenario('missing_evidence',profile='cancel_unconfirmed',expected=(6,520),followup='reject'))
    rows.append(scenario('unknown_state',delay=None,profile='status_unknown',expected=(6,230),followup='reject'))
(root/'summary.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
raise SystemExit(0 if all(r['status']=='PASS' for r in rows) else 1)
