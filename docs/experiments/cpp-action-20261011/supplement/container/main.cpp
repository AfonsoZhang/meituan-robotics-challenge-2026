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
