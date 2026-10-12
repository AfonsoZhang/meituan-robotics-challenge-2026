git rev-parse HEAD
git status --short
git diff --exit-code c10f6ed59966401684851f917f9137b0a6cf12ae HEAD -- src tests config scripts docs
python3 src/mtc_ros2_action_cpp/test/verify_results.py --build-base /candidate-build
