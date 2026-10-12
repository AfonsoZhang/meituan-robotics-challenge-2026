// OpenAI Codex assisted public export/disabled-default check; no driver or Goal.
#include <iostream>
#include <memory>
#include <mtc_trajectory_execution_cpp/fjt_motion_port.hpp>
int main(int argc,char **argv) {
 rclcpp::init(argc,argv);
 int code=1;
 {
  auto node=std::make_shared<rclcpp::Node>("phase2b_export_consumer");
  mtc::trajectory::Config cfg;
  for(const auto &name:cfg.joints) cfg.limits[name]={-0.5,0.5,0.2,0.5};
  mtc::trajectory::FjtMotionPort port(node,cfg);
  mtc::core::MotionCommand c;c.command_id="disabled-consumer";c.simulation_only=true;c.timeout_ms=6000;
  mtc::core::TimedTrajectory t;t.trajectory_id="consumer-three-points";t.joint_names=cfg.joints;
  for(int n=0;n<3;++n) {
   mtc::core::TrajectoryPoint p;p.time_from_start_s=n;p.positions_rad.assign(6,0.01*n);
   p.velocities_rad_s.assign(6,0);p.accelerations_rad_s2.assign(6,0);t.points.push_back(p);
  }
  c.trajectory=t;
  auto converted=mtc::trajectory::convert(c,cfg);auto result=port.execute_trajectory(c);auto snapshot=port.snapshot();
  bool pass=!cfg.enable_fake_execution && converted.trajectory && result &&
   result->exec_state==mtc::core::ExecState::REJECTED && !result->success &&
   !snapshot.ready && snapshot.goals_sent==0 && snapshot.cancel_requests==0;
  std::cout<<"valid_trajectory="<<bool(converted.trajectory)<<" default_enabled="<<cfg.enable_fake_execution
   <<" goals_sent="<<snapshot.goals_sent<<" cancels_sent="<<snapshot.cancel_requests
   <<" ready="<<snapshot.ready<<" rejected="<<bool(result)<<"\n";
  if(result)std::cout<<"message="<<result->message<<"\n";
  std::cout<<(pass ? "PASS" : "FAIL")<<": exported target and default-disabled execution\n";code=pass?0:1;
 }
 rclcpp::shutdown();return code;
}
