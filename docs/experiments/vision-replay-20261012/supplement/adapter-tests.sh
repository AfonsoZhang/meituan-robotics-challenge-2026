test ! -e /candidate/install
ln -s /candidate-install /candidate/install
export ROS_DOMAIN_ID=151 MTC_VALIDATION_OUT=/review-evidence/installed-processes
python3 -m pytest -q src/mtc_vision_adapter/test --junitxml=/review-evidence/adapter-tests.xml
