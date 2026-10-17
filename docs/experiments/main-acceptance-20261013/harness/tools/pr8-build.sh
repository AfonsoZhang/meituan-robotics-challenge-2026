git rev-parse HEAD
git status --porcelain
export CMAKE_BUILD_PARALLEL_LEVEL=2 MAKEFLAGS='-j2 -l2'
colcon --log-base /pr8-review/build-log build --build-base /pr8-build --install-base /pr8-install --packages-up-to mtc_cpp_mock_bringup --executor sequential --cmake-args -DBUILD_TESTING=ON -DCMAKE_CXX_STANDARD=17 -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
