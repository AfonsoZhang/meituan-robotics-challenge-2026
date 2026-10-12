source /driver_work/install/setup.bash
timeout --signal=TERM --kill-after=10 180 python3 /review-tools/probe_moveit_wait5.py /review-evidence/moveit-wait5
