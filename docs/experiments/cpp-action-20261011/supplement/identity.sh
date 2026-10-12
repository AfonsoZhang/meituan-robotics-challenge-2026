git rev-parse HEAD
git diff --exit-code 1d940f7c5f12561fed6641457c0b4b630a282b05 HEAD -- src/mtc_core_cpp src/mtc_task_cpp src/mtc_manipulation_cpp src/mtc_motion_execution_cpp src/mtc_interfaces src/mtc_task src/mtc_manipulation
git status --short
python3 src/mtc_ros2_action_cpp/test/verify_results.py --build-base /candidate-build
ament_xmllint src/mtc_ros2_action_cpp/package.xml
rosdep check --from-paths src/mtc_ros2_action_cpp --ignore-src
