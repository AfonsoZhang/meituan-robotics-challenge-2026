"""Isolated recording world; wiring adapted from the local meituan_sim launch.

Original simulation wiring: Claude Code-assisted project work, 2026-09-06.
Recording isolation: OpenAI Codex-assisted project work, 2026-09-07.
Robot/tool models remain in the external ROS workspace.
"""
import os
from pathlib import Path
import xml.etree.ElementTree as ET

import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.actions import ExecuteProcess
from launch_ros.actions import Node


def generate_launch_description():
    sim = Path(get_package_share_directory('meituan_sim'))
    desc = Path(get_package_share_directory('aubo_description'))
    robot = xacro.process_file(str(sim / 'urdf/aubo_S3_gazebo.urdf.xacro'),
                              mappings={'controllers_file': str(sim / 'config/aubo_S3_controllers.yaml')}).toxml()
    # Avoid uncontrolled fall while the six-axis controller is being spawned.
    # The recorder MUST restore and read back gravity on all six links before recording.
    xml = ET.fromstring(robot)
    for link in ('shoulder_Link','upperArm_Link','foreArm_Link','wrist1_Link','wrist2_Link','wrist3_Link'):
        tag = ET.SubElement(xml,'gazebo',reference=link)
        ET.SubElement(tag,'gravity').text = 'false'
    robot = ET.tostring(xml,encoding='unicode')
    server = ExecuteProcess(cmd=['gzserver', '--verbose',
                                 '-s', 'libgazebo_ros_init.so',
                                 '-s', 'libgazebo_ros_factory.so', os.environ['DEMO_WORLD']],
                            output='screen')
    state = Node(package='robot_state_publisher', executable='robot_state_publisher',
                 parameters=[{'robot_description': robot, 'use_sim_time': True}], output='screen')
    spawn = Node(package='gazebo_ros', executable='spawn_entity.py',
                 arguments=['-topic', 'robot_description', '-entity', 'aubo_S3'], output='screen')
    jsb = Node(package='controller_manager', executable='spawner',
               arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'])
    jtc = Node(package='controller_manager', executable='spawner',
               arguments=['joint_trajectory_controller', '--controller-manager', '/controller_manager'])
    return LaunchDescription([server, state, spawn,
                              RegisterEventHandler(OnProcessExit(target_action=spawn, on_exit=[jsb])),
                              RegisterEventHandler(OnProcessExit(target_action=jsb, on_exit=[jtc]))])
