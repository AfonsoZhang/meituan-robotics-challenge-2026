timeout --signal=TERM --kill-after=10 120 python3 -m pytest -q vision_core/tests/test_ros2_p0.py --junitxml=/review-evidence/adapter-original.xml
