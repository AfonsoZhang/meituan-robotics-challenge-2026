export ROS_DOMAIN_ID=149 MTC_VALIDATION_OUT=/review-evidence/replay-synthetic
test ! -e /candidate/install
ln -s /candidate-install /candidate/install
python3 src/mtc_vision_adapter/test/ros_replay_validation.py
