"""Codex-assisted bounded commands; retain separate logs for failures and fixes."""
import argparse,datetime,json,os,signal,subprocess
from pathlib import Path
p=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('name');a.add_argument('script');a.add_argument('--host',action='store_true');a.add_argument('--timeout',type=int,default=600)
args=a.parse_args(); container='mtc-c1-fix-20261013'
env='set -e; source /opt/ros/jazzy/setup.bash; if test -f /c1-install/setup.bash; then source /c1-install/setup.bash; fi; unset ROS_STATIC_PEERS ROS_LOCALHOST_ONLY FASTRTPS_DEFAULT_PROFILES_FILE FASTDDS_DEFAULT_PROFILES_FILE CYCLONEDDS_URI; export ROS_DOMAIN_ID=182 RMW_IMPLEMENTATION=rmw_fastrtps_cpp ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST PYTHONDONTWRITEBYTECODE=1 ROS_LOG_DIR=/c1-evidence/roslogs; cd /c1-source; '
argv=['bash','-c',args.script] if args.host else ['docker','exec',container,'bash','-c',env+args.script]
record={'argv':argv,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'timeout_seconds':args.timeout}
meta=p/'meta'/f'{args.name}.json'
assert not meta.exists(),meta
with (p/'logs'/f'{args.name}.log').open('xb') as log:
    proc=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    try:rc=proc.wait(args.timeout)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid,signal.SIGTERM);proc.wait(10);rc=124
        if not args.host:subprocess.run(['docker','stop','--time','5',container],stdout=log,stderr=log,timeout=20)
record.update(exit_code=rc,ended_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
meta.write_text(json.dumps(record,indent=2)+'\n')
print(args.name,rc,flush=True)
print((p/'logs'/f'{args.name}.log').read_text()[-4000:])
raise SystemExit(rc)
