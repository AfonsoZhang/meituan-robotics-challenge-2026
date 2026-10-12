source /driver_work/install/setup.bash
timeout --signal=TERM --kill-after=10 180 python3 /acceptance-tools/probe_moveit.py /review-evidence/moveit-repeat
