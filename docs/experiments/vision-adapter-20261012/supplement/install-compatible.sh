/review-venv/bin/python - <<'INNER'
import setuptools,sys
assert sys.prefix=='/review-venv'
assert setuptools.__file__.startswith('/review-venv/')
assert setuptools.__version__=='80.9.0'
INNER
/review-venv/bin/python -m pip uninstall -y setuptools
/review-venv/bin/python - <<'INNER'
import setuptools
assert setuptools.__version__=='68.1.2',setuptools.__version__
print('Reuse base Jazzy-compatible setuptools',setuptools.__version__,setuptools.__file__)
INNER
/review-venv/bin/python -m pip install --no-index --no-deps --no-build-isolation --no-compile -e /candidate/vision_core
/review-venv/bin/python -m pip install --no-index --no-deps --no-build-isolation --no-compile -e /candidate/src/mtc_vision_adapter
/review-venv/bin/python -m pip check
/review-venv/bin/python -m pip freeze --all > /review-evidence/vision-python-freeze.txt
/review-venv/bin/python - <<'INNER'
import cv2,numpy,scipy,yaml,matplotlib,pytest,sys,json
from pathlib import Path
v={'python':sys.version,'opencv':cv2.__version__,'numpy':numpy.__version__,'scipy':scipy.__version__,'yaml':yaml.__version__,'matplotlib':matplotlib.__version__,'pytest':pytest.__version__}
Path('/review-evidence/vision-python-versions.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
INNER
