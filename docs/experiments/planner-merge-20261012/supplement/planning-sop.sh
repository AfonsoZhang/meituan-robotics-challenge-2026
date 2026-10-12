export ROS_DOMAIN_ID=126
export AUBO_WS=/driver_ws MTC_WS=/candidate MTC_RMW=rmw_fastrtps_cpp
export ROS_LOG_DIR=/review-evidence/planning-sop/ros-logs
[ ! -e /driver_ws/install_no_symlink ]
ln -s /driver_work/install /driver_ws/install_no_symlink
mkdir -p /candidate/install
[ ! -e /candidate/install/planner ]
ln -s /candidate-install /candidate/install/planner
printf '%s\n' 'Workspace path aliases only; no source, parameters, budgets or algorithms modified.'
timeout --signal=TERM --kill-after=15 360 bash /candidate/src/mtc_moveit_planner/scripts/run_planning_evidence.sh /review-evidence/planning-sop
