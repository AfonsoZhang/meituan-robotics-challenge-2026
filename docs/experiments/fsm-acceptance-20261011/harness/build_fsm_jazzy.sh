#!/usr/bin/env bash
# Acceptance orchestration only; upstream source is unmodified.
set -eo pipefail
source /opt/ros/jazzy/setup.bash
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
export CMAKE_BUILD_PARALLEL_LEVEL=2 MAKEFLAGS=-j2
cd /ws
test "$(git rev-parse HEAD)" = 1d940f7c5f12561fed6641457c0b4b630a282b05
colcon list
colcon --log-base /evidence/colcon-build build --build-base /work/build --install-base /work/install --executor sequential --cmake-args -DBUILD_TESTING=ON -DCMAKE_CXX_STANDARD=17
source /work/install/setup.bash
colcon --log-base /evidence/colcon-test test --build-base /work/build --install-base /work/install --executor sequential --return-code-on-test-failure
colcon test-result --test-result-base /work/build --all
python3 tests/verify_cpp_audit_results.py --build-base /work/build
python3 tests/test_mock_end_to_end.py
git status --porcelain
