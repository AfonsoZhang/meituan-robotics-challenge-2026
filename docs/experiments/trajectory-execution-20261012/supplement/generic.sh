source /driver_work/install/setup.bash
source /candidate-install/setup.bash
timeout --signal=TERM --kill-after=15 170 python3 /review-tools/probe_generic.py /review-evidence/generic
