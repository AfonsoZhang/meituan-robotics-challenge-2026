"""Replay the saved RGB-D measurement without ROS or Gazebo."""
import argparse
import json
import numpy as np
from detector import detect
from vision import COLORS, correction

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('snapshot',help='Path to vision-snapshot.npz')
    args = p.parse_args()
    with np.load(args.snapshot) as s:
        detections = detect(s['bgr'],s['depth'],s['K_color'],s['K_depth'],s['T_base_camera'],COLORS)
    print(json.dumps({'delta_xy_mm':(correction(detections)*1000).tolist()},indent=2))
