set -e
source /opt/ros/jazzy/setup.bash
source /candidate-install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export ROS_DOMAIN_ID=106 PYTHONDONTWRITEBYTECODE=1 ROS_LOG_DIR=/review-evidence/ros-logs
export XML_CATALOG_FILES=/acceptance-tools/offline-schema/catalog.xml
unset ROS_STATIC_PEERS ROS_LOCALHOST_ONLY FASTRTPS_DEFAULT_PROFILES_FILE FASTDDS_DEFAULT_PROFILES_FILE CYCLONEDDS_URI
mkdir -p /review-evidence
cd /candidate
python3 -m venv --without-pip --system-site-packages /review-venv
PYTHONPATH=/review-deps/pip-25.0.1-py3-none-any.whl /review-venv/bin/python -m pip install --no-index --no-deps /review-deps/pip-25.0.1-py3-none-any.whl
/review-venv/bin/python -m pip install --no-index --find-links /review-deps --no-compile -r /review-tools/requirements-review.txt
/review-venv/bin/python -m pip install --no-index --no-deps --no-build-isolation --no-compile -e /candidate/vision_core -e /candidate/src/mtc_vision_adapter
/review-venv/bin/python -m pip check
/review-venv/bin/python -m pip freeze --all > /review-evidence/vision-python-freeze.txt
/review-venv/bin/python - <<'INNER'
import cv2,numpy,scipy,yaml,matplotlib,pytest,sys,json
from pathlib import Path
v={'python':sys.version,'opencv':cv2.__version__,'numpy':numpy.__version__,'scipy':scipy.__version__,'yaml':yaml.__version__,'matplotlib':matplotlib.__version__,'pytest':pytest.__version__}
Path('/review-evidence/vision-python-versions.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
INNER
