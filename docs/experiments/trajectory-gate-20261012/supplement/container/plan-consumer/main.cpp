// OpenAI Codex assisted installed API/ABI and plan data diagnostic. No ROS init or Node.
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <mtc_moveit_planner/trajectory_conversion.hpp>
#include <mtc_trajectory_execution_cpp/trajectory_validator.hpp>
int main(int argc,char **argv) {
 if(argc!=2)return 2;
 std::ifstream in(argv[1]);size_t n=0;std::string frame;double stamp;
 in>>n>>frame>>stamp;if(!in || n<2 || n>10000)return 2;
 mtc::moveit_planner::RawTrajectory raw;
 for(int j=0;j<6;++j){std::string name;in>>name;raw.joint_names.push_back(name);}
 for(size_t k=0;k<n;++k){mtc::moveit_planner::RawTrajectoryPoint p;in>>p.time_from_start_s;
  for(auto *v:{&p.positions,&p.velocities,&p.accelerations})for(int j=0;j<6;++j){double x;in>>x;v->push_back(x);}
  raw.points.push_back(p);
 }
 if(!in)return 2;
 mtc::trajectory::Config cfg;for(const auto &name:cfg.joints)cfg.limits[name]={-0.5,0.5,0.2,0.5};
 auto plan=mtc::moveit_planner::to_timed_trajectory(raw,cfg.joints,frame,stamp);
 std::cout<<std::setprecision(17)<<"Planner conversion="<<plan.ok<<" points="<<plan.trajectory.points.size()<<" first_t="<<raw.points.front().time_from_start_s<<" duration="<<raw.points.back().time_from_start_s<<" stamp="<<stamp<<"\n";
 if(!plan.ok){std::cout<<plan.error<<"\n";return 1;}
 mtc::core::MotionCommand c;c.simulation_only=true;c.trajectory=plan.trajectory;
 c.timeout_ms=static_cast<uint32_t>(std::ceil(raw.points.back().time_from_start_s*1500+1000));
 const auto unidentified=mtc::trajectory::convert(c,cfg);
 std::cout<<"Before diagnostic IDs: accepted="<<bool(unidentified.trajectory)<<" error="<<unidentified.error<<"\n";
 c.command_id="acceptance-static-plan";c.trajectory->trajectory_id="acceptance-static-trajectory";
 const auto identified=mtc::trajectory::convert(c,cfg);
 std::cout<<"After diagnostic IDs: accepted="<<bool(identified.trajectory)<<" error="<<identified.error<<" timeout_ms="<<c.timeout_ms<<"\n";
 std::cout<<"No Node, Action Client, Goal, stamp substitution or capability widening.\n";
 bool ok=!unidentified.trajectory && unidentified.error.find("identified")!=std::string::npos;
 std::cout<<(ok?"PASS":"FAIL")<<": installed cross-package consumer and actual plan conversion diagnostic\n";
 return ok?0:1;
}
