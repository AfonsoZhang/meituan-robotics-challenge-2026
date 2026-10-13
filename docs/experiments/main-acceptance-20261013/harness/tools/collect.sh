python3 /review-tools/collect.py
for domain in 98 99 110 111 112 113 171 176; do ROS_DOMAIN_ID=$domain ros2 daemon stop; done
ros2 node list --no-daemon --spin-time 2
