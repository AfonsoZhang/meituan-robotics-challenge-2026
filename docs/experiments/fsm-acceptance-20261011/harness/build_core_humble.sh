#!/usr/bin/env bash
# Supplementary host-only check; never substitutes for the Jazzy gate.
set -eo pipefail
source /opt/ros/humble/setup.bash
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
export CMAKE_BUILD_PARALLEL_LEVEL=2 MAKEFLAGS=-j2
MTC_ACCEPT_RUN=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$MTC_ACCEPT_RUN/source"
colcon --log-base "$MTC_ACCEPT_RUN/humble/log-build" build --build-base "$MTC_ACCEPT_RUN/humble/build" --install-base "$MTC_ACCEPT_RUN/humble/install" --executor sequential --packages-select mtc_core_cpp mtc_task_cpp mtc_motion_execution_cpp mtc_manipulation_cpp --cmake-args -DBUILD_TESTING=ON -DCMAKE_CXX_STANDARD=17 -DPYTHON_EXECUTABLE=/usr/bin/python3 -DPython3_EXECUTABLE=/usr/bin/python3
source "$MTC_ACCEPT_RUN/humble/install/setup.bash"
colcon --log-base "$MTC_ACCEPT_RUN/humble/log-test" test --build-base "$MTC_ACCEPT_RUN/humble/build" --install-base "$MTC_ACCEPT_RUN/humble/install" --executor sequential --packages-select mtc_core_cpp mtc_task_cpp mtc_motion_execution_cpp mtc_manipulation_cpp --return-code-on-test-failure
colcon test-result --test-result-base "$MTC_ACCEPT_RUN/humble/build" --all
python3 tests/verify_cpp_audit_results.py --build-base "$MTC_ACCEPT_RUN/humble/build"
