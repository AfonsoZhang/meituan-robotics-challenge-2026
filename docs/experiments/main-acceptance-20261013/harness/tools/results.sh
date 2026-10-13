colcon test-result --test-result-base /main-build --all
python3 src/mtc_trajectory_execution_cpp/test/verify_results.py --build-base /main-build
