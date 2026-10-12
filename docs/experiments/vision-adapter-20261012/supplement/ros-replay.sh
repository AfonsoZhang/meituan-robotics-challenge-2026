export ROS_DOMAIN_ID=129
python3 /review-tools/probe_vision_ros.py
ros2 daemon stop
ps -eo pid,ppid,stat,args
