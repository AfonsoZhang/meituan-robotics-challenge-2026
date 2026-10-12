python3 - <<'INNER'
import json,importlib,sys
from pathlib import Path
v={'python':sys.version,'imports':{}}
for name in ['numpy','scipy','cv2','yaml','matplotlib','pytest','pip','venv','setuptools','rclpy','mtc_interfaces.msg','mtc_vision_adapter']:
 try:
  m=importlib.import_module(name);v['imports'][name]={'file':getattr(m,'__file__',None),'version':getattr(m,'__version__',None)}
 except Exception as e:v['imports'][name]={'error':repr(e)}
Path('/review-evidence/base-environment.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
INNER
python3 src/mtc_ros2_action_cpp/test/verify_results.py /candidate-build
