set -e
source /opt/ros/jazzy/setup.bash
source /candidate-install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export ROS_DOMAIN_ID=106 PYTHONDONTWRITEBYTECODE=1 ROS_LOG_DIR=/review-evidence/ros-logs
export XML_CATALOG_FILES=/acceptance-tools/offline-schema/catalog.xml
unset ROS_STATIC_PEERS ROS_LOCALHOST_ONLY FASTRTPS_DEFAULT_PROFILES_FILE FASTDDS_DEFAULT_PROFILES_FILE CYCLONEDDS_URI
mkdir -p /review-evidence
cd /candidate
mkdir -p /review-consumer
cat > /review-consumer/CMakeLists.txt <<'EOF'
cmake_minimum_required(VERSION 3.16)
project(mtc_phase2a_acceptance_consumer LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
find_package(mtc_ros2_action_cpp REQUIRED)
add_executable(consumer main.cpp)
target_link_libraries(consumer PRIVATE mtc_ros2_action_cpp::mtc_ros2_action_cpp)
EOF
cat > /review-consumer/main.cpp <<'EOF'
// OpenAI Codex assisted standalone export validation, 2026-10-11.
#include <memory>
#include <mtc_ros2_action_cpp/task_server.hpp>
#include <mtc_ros2_action_cpp/pick_place_server.hpp>
#include <mtc_ros2_action_cpp/motion_server.hpp>
int main(int argc, char **argv) {
  rclcpp::init(argc, argv);
  {
    auto task=std::make_shared<mtc::ros2_action::TaskServer>();
    auto pick=std::make_shared<mtc::ros2_action::PickPlaceServer>();
    auto motion=std::make_shared<mtc::ros2_action::MotionServer>();
  }
  rclcpp::shutdown();
  return 0;
}
EOF
cmake -S /review-consumer -B /review-consumer/build
cmake --build /review-consumer/build -j2
timeout 20 /review-consumer/build/consumer
cp /review-consumer/CMakeLists.txt /review-consumer/main.cpp /review-evidence/
echo 'PASS: exported CMake target, public headers, constructors and clean destruction'
