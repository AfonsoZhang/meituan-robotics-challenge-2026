set -e
source /opt/ros/jazzy/setup.bash
source /candidate-install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export ROS_DOMAIN_ID=106 PYTHONDONTWRITEBYTECODE=1 ROS_LOG_DIR=/review-evidence/ros-logs
export XML_CATALOG_FILES=/acceptance-tools/offline-schema/catalog.xml
unset ROS_STATIC_PEERS ROS_LOCALHOST_ONLY FASTRTPS_DEFAULT_PROFILES_FILE FASTDDS_DEFAULT_PROFILES_FILE CYCLONEDDS_URI
mkdir -p /review-evidence
cd /candidate
python3 - <<'INNER'
from pathlib import Path
import json
base=Path('/candidate/vision_core')
paths=['outputs/cad_analysis/geometry.json','assets/cad/电池道具.stp','assets/cad/舌规V1.STEP','outputs/live_rgbd_integration/v33_diagnostic/audit_frames.json','outputs/live_rgbd_integration/v33_diagnostic/ring_axis_refined_frames.jsonl','outputs/live_rgbd_integration/v33_diagnostic/paired_frames.jsonl','outputs/live_rgbd_integration/v41/before.json','outputs/live_rgbd_integration/dual_90dd28e6']
result={'required_private_inputs':[{'path':p,'exists':(base/p).exists()} for p in paths],'scope':'Read-only inventory; no private fixture or calibration fabricated.'}
Path('/review-evidence/private-entrypoint-inputs.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
INNER
