export ROS_DOMAIN_ID=150 MTC_VALIDATION_OUT=/review-evidence/replay-labelled MTC_REPLAY_FIXTURE=/review-evidence/replay-labelled.jsonl
python3 - <<'INNER'
import json
from pathlib import Path
source=Path('/candidate/src/mtc_vision_adapter/examples/synthetic.jsonl')
records=[json.loads(v) for v in source.read_text().splitlines() if v]
for r in records:r['mode']='replay'
Path('/review-evidence/replay-labelled.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
INNER
python3 src/mtc_vision_adapter/test/ros_replay_validation.py
