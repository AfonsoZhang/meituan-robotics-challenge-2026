set -e
source /opt/ros/jazzy/setup.bash
source /candidate-install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export ROS_DOMAIN_ID=106 PYTHONDONTWRITEBYTECODE=1 ROS_LOG_DIR=/review-evidence/ros-logs
export XML_CATALOG_FILES=/acceptance-tools/offline-schema/catalog.xml
unset ROS_STATIC_PEERS ROS_LOCALHOST_ONLY FASTRTPS_DEFAULT_PROFILES_FILE FASTDDS_DEFAULT_PROFILES_FILE CYCLONEDDS_URI
mkdir -p /review-evidence
cd /candidate
python3 - <<'PY'
from pathlib import Path
import json, subprocess
out=Path('/review-evidence/launch-guard');out.mkdir()
base=['ros2','launch','mtc_moveit_planner','plan_tool.launch.py','program:=plan_fixed_pose']
records=[]
for name,parameter in [('missing-main','params_file'),('missing-override','extra_params_file')]:
    missing='/review-evidence/no-such-'+name+'.yaml'
    assert not Path(missing).exists()
    argv=base+[parameter+':='+missing]
    p=subprocess.run(argv,capture_output=True,text=True,timeout=25)
    text=p.stdout+p.stderr;(out/(name+'.log')).write_text(text)
    record={'case':name,'argv':argv,'exit_code':p.returncode,
        'explicit_missing_file_rejected':p.returncode!=0 and 'parameter file not found: '+missing in text,
        'no_node_process_started':'process started with pid' not in text}
    records.append(record)
(out/'summary.json').write_text(json.dumps(records,indent=2)+'\n')
assert all(r['explicit_missing_file_rejected'] and r['no_node_process_started'] for r in records),records
print(json.dumps(records,indent=2))
PY
