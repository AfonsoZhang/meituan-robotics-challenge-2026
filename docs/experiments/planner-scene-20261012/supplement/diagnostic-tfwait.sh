export ROS_DOMAIN_ID=128
export AUBO_WS=/driver_ws MTC_WS=/candidate MTC_INSTALL=/candidate-install MTC_RMW=rmw_fastrtps_cpp
export ROS_LOG_DIR=/review-evidence/diagnostic-tfwait/ros-logs
mkdir -p /review-evidence/diagnostic-tfwait
python3 - <<'PY'
from pathlib import Path
import yaml
p=Path('/candidate/src/mtc_moveit_planner/config/planner.yaml')
y=yaml.safe_load(p.read_text());y['/**']['ros__parameters']['backend']['tf_timeout_s']=5.0
Path('/review-evidence/diagnostic-tfwait/planner-tfwait.yaml').write_text(yaml.safe_dump(y,sort_keys=False))
PY
timeout --signal=TERM --kill-after=15 360 bash /review-tools/diagnostic-tfwait-sop.sh /review-evidence/diagnostic-tfwait
