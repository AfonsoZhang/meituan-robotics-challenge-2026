export CMAKE_BUILD_PARALLEL_LEVEL=2 MAKEFLAGS='-j2 -l2'
colcon --log-base /review/build-log build --build-base /main-build --install-base /main-install --executor sequential --cmake-args -DBUILD_TESTING=ON -DCMAKE_CXX_STANDARD=17 -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
