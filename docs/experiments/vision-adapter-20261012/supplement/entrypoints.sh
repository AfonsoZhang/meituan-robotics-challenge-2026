export MPLBACKEND=Agg MPLCONFIGDIR=/review-evidence/matplotlib
mkdir -p /review-evidence/entrypoints
cd /candidate/vision_core
timeout 30 /review-venv/bin/python scripts/live_rgbd_preview.py --help > /review-evidence/entrypoints/rgbd-help.txt
timeout 30 /review-venv/bin/python scripts/live_realsense_handheld.py --help > /review-evidence/entrypoints/handheld-help.txt
timeout --signal=TERM --kill-after=10 120 /review-venv/bin/python scripts/replay_ros2_p0.py --output /review-evidence/synthetic --session /review-evidence/no-private-session
