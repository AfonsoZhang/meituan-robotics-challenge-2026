export ROS_DOMAIN_ID=130
python3 /review-tools/probe_vision_ros_wait5.py
ros2 daemon stop
ps -eo pid,ppid,stat,args
