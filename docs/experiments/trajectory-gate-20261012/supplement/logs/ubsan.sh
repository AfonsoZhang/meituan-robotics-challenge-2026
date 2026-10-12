set -e
source /opt/ros/jazzy/setup.bash
source /candidate-install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export ROS_DOMAIN_ID=106 PYTHONDONTWRITEBYTECODE=1 ROS_LOG_DIR=/review-evidence/ros-logs
export XML_CATALOG_FILES=/acceptance-tools/offline-schema/catalog.xml
unset ROS_STATIC_PEERS ROS_LOCALHOST_ONLY FASTRTPS_DEFAULT_PROFILES_FILE FASTDDS_DEFAULT_PROFILES_FILE CYCLONEDDS_URI
mkdir -p /review-evidence
cd /candidate
export ROS_DOMAIN_ID=139
export CMAKE_BUILD_PARALLEL_LEVEL=2 MAKEFLAGS=-j2
colcon --log-base /review-evidence/ubsan-build-log build --build-base /review-ubsan-build --install-base /review-ubsan-install --packages-up-to mtc_moveit_planner mtc_ros2_action_cpp mtc_moveit_planner mtc_trajectory_execution_cpp --executor sequential --cmake-args -DBUILD_TESTING=ON -DCMAKE_CXX_STANDARD=17 -DCMAKE_EXPORT_COMPILE_COMMANDS=ON '-DCMAKE_CXX_FLAGS=-fsanitize=undefined -fno-sanitize-recover=all -fno-omit-frame-pointer' '-DCMAKE_SHARED_LINKER_FLAGS=-fsanitize=undefined' '-DCMAKE_EXE_LINKER_FLAGS=-fsanitize=undefined'
source /review-ubsan-install/setup.bash
export UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1
colcon --log-base /review-evidence/ubsan-test-log test --build-base /review-ubsan-build --install-base /review-ubsan-install --packages-select mtc_core_cpp mtc_task_cpp mtc_manipulation_cpp mtc_motion_execution_cpp mtc_ros2_action_cpp mtc_moveit_planner mtc_trajectory_execution_cpp --executor sequential --return-code-on-test-failure
colcon test-result --test-result-base /review-ubsan-build --all
python3 src/mtc_trajectory_execution_cpp/test/verify_results.py --build-base /review-ubsan-build
python3 - <<'PY'
from pathlib import Path
import json, shutil
base=Path('/review-ubsan-build'); evidence=Path('/review-evidence/ubsan')
for p in base.rglob('*'):
 if p.is_file() and (p.suffix=='.xml' and ('test_results' in p.parts or 'Testing' in p.parts) or p.name in ('compile_commands.json','CMakeCache.txt','link.txt')):
  q=evidence/p.relative_to(base); q.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(p,q)
for package in ('mtc_core_cpp','mtc_task_cpp','mtc_manipulation_cpp','mtc_motion_execution_cpp','mtc_ros2_action_cpp','mtc_moveit_planner','mtc_trajectory_execution_cpp'):
 commands=json.loads((base/package/'compile_commands.json').read_text())
 assert commands and all('-fsanitize=undefined' in x['command'] and '-fno-sanitize-recover=all' in x['command'] for x in commands), package
print('PASS: compile command instrumentation verified for all seven C++ packages')
PY
