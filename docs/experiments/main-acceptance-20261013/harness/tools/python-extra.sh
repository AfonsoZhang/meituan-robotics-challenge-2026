python3 tests/test_mock_end_to_end.py
python3 -m pytest -q -p no:cacheprovider tests/test_ros_wiring.py --junitxml=/review/ros-wiring.xml
python3 -m unittest discover -s tests/calibration -p "test_*.py" -v
