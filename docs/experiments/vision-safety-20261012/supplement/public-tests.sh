export MPLBACKEND=Agg MPLCONFIGDIR=/review-evidence/matplotlib
/review-venv/bin/python -m pytest -q vision_core/tests --junitxml=/review-evidence/public-vision-tests.xml
