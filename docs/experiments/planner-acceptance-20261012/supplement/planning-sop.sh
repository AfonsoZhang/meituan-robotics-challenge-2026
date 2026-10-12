export ROS_DOMAIN_ID=116
export AUBO_WS=/driver_ws MTC_WS=/candidate MTC_RMW=rmw_fastrtps_cpp
export ROS_LOG_DIR=/review-evidence/planning-sop/ros-logs
[ ! -e /driver_ws/install_no_symlink ]
ln -s /driver_work/install /driver_ws/install_no_symlink
mkdir -p /candidate/install
[ ! -e /candidate/install/planner ]
ln -s /candidate-install /candidate/install/planner
printf '%s\n' 'Workspace-only aliases; upstream source, parameters and algorithms unchanged.'
timeout --signal=TERM --kill-after=15 360 bash /candidate/src/mtc_moveit_planner/scripts/run_planning_evidence.sh /review-evidence/planning-sop
