export MPLBACKEND=Agg MPLCONFIGDIR=/review-evidence/matplotlib
cd /candidate
timeout --signal=TERM --kill-after=10 300 /review-venv/bin/python -m pytest -q vision_core/tests --junitxml=/review-evidence/vision-suite-compatible.xml
