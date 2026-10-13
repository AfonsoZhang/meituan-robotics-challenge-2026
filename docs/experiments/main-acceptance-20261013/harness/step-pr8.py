"""Bounded single-container acceptance runner; no monitor/queue or kernel edits."""
import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess

p=Path(__file__).resolve().parent
a=argparse.ArgumentParser();a.add_argument('name');a.add_argument('--host',action='store_true');a.add_argument('--timeout',type=int,default=300)
args=a.parse_args();name='mtc-pr8-c1-review-20261013'
def stamp():return datetime.now(timezone.utc).isoformat()
script=(p/'tools'/f'{args.name}.sh').read_text()
if args.host:
    argv=['bash','-c',script]
else:
    ros=('set -e; source /opt/ros/jazzy/setup.bash; source /driver_work/install/setup.bash; '
         'if test -f /pr8-install/setup.bash; then source /pr8-install/setup.bash; fi; '
         'unset ROS_STATIC_PEERS ROS_LOCALHOST_ONLY FASTRTPS_DEFAULT_PROFILES_FILE FASTDDS_DEFAULT_PROFILES_FILE CYCLONEDDS_URI; '
         'export ROS_DOMAIN_ID=181 RMW_IMPLEMENTATION=rmw_fastrtps_cpp ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST '
         'PYTHONDONTWRITEBYTECODE=1 ROS_LOG_DIR=/pr8-review/roslogs XML_CATALOG_FILES=/acceptance-tools/offline-schema/catalog.xml '
         'GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=safe.directory GIT_CONFIG_VALUE_0=/pr8-source; '
         'cd /pr8-source; ')
    argv=['docker','exec',name,'bash','-c',ros+script]
record={'name':args.name,'started_at':stamp(),'argv':argv,'timeout_seconds':args.timeout}
meta=p/'meta'/f'{args.name}.json'
def save():meta.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
with (p/'execution.lock').open('a') as lock, (p/'logs'/f'{args.name}.log').open('xb') as log:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    save()
    proc=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    record['pid']=proc.pid;save()
    try:
        rc=proc.wait(timeout=args.timeout)
    except (subprocess.TimeoutExpired,KeyboardInterrupt) as exc:
        record['interruption']=type(exc).__name__
        os.killpg(proc.pid,signal.SIGTERM)
        try:proc.wait(timeout=10)
        except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=5)
        if not args.host:subprocess.run(['docker','stop','--time','5',name],stdout=log,stderr=log,timeout=20)
        rc=124
    record.update(exit_code=rc,ended_at=stamp());save()
print(args.name,rc,flush=True)
raise SystemExit(rc)
