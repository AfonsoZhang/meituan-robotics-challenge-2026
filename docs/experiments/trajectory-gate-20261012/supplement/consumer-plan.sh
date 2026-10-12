export ROS_DOMAIN_ID=146
mkdir -p /review-plan-consumer /review-evidence/plan-consumer
python3 - <<'PY'
from pathlib import Path
import hashlib,json,math,yaml
paths=list(Path('/review-evidence/topology-plan/planning').glob('fixed_pose_plan_*.yaml'));assert len(paths)==1
plan=yaml.safe_load(paths[0].read_text());assert plan['result']['ok'];t=plan['trajectory'];points=t['points']
names=['shoulder_joint','upperArm_joint','foreArm_joint','wrist1_joint','wrist2_joint','wrist3_joint']
assert t['joint_names']==names and t['header_frame_id']=='world' and t['trajectory_id']=='' and len(points)==t['point_count']
values=[str(len(points)),t['header_frame_id'],format(t['stamp_s'],'.17g'),*names]
for p in points:
 assert all(len(p[k])==6 for k in ['positions_rad','velocities_rad_s','accelerations_rad_s2'])
 for v in [p['time_from_start_s'],*p['positions_rad'],*p['velocities_rad_s'],*p['accelerations_rad_s2']]:
  assert math.isfinite(v);values.append(format(v,'.17g'))
Path('/review-plan-consumer/trajectory.txt').write_text('\n'.join(values)+'\n')
record={'source':str(paths[0]),'source_sha256':hashlib.sha256(paths[0].read_bytes()).hexdigest(),'points':len(points),'first_t':points[0]['time_from_start_s'],'duration_s':t['duration_s'],'stamp_s':t['stamp_s'],'trajectory_id':t['trajectory_id'],'names':names,'frame':t['header_frame_id'],'max_abs_position':max(abs(v) for p in points for v in p['positions_rad']),'max_abs_velocity':max(abs(v) for p in points for v in p['velocities_rad_s']),'max_abs_acceleration':max(abs(v) for p in points for v in p['accelerations_rad_s2']),'scope':'Actual serialized plan; no trajectory modification, retiming, stamp substitution or movement. Diagnostic IDs and timeout are set only in the pure conversion consumer.'}
Path('/review-evidence/plan-consumer/input.json').write_text(json.dumps(record,indent=2)+'\n')
PY
cat > /review-plan-consumer/CMakeLists.txt <<'CMAKE'
cmake_minimum_required(VERSION 3.16)
project(mtc_plan_fjt_export_consumer LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
find_package(mtc_moveit_planner REQUIRED)
find_package(mtc_trajectory_execution_cpp REQUIRED)
add_executable(consumer main.cpp)
target_link_libraries(consumer PRIVATE mtc_moveit_planner::mtc_moveit_planner_core mtc_trajectory_execution_cpp::mtc_trajectory_execution_cpp)
CMAKE
cat > /review-plan-consumer/main.cpp <<'CPP'
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
CPP
cmake -S /review-plan-consumer -B /review-plan-consumer/build
cmake --build /review-plan-consumer/build -j2
timeout --signal=TERM --kill-after=5 20 /review-plan-consumer/build/consumer /review-plan-consumer/trajectory.txt
cp /review-plan-consumer/CMakeLists.txt /review-plan-consumer/main.cpp /review-plan-consumer/trajectory.txt /review-plan-consumer/build/CMakeCache.txt /review-evidence/plan-consumer/
