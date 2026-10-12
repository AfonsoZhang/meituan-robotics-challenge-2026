source /driver_work/install/setup.bash
source /candidate-install/setup.bash
timeout --signal=TERM --kill-after=15 185 python3 /review-tools/probe_topology_plan.py /review-evidence/topology-plan
