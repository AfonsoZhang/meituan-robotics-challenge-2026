"""遨博 S3 在 Gazebo Classic 中的最小可跑 launch。

gui:=false 时只起 gzserver（WSL2 无显卡时先用这个验证控制链路），
gui:=true 时额外起 gzclient。
"""
from launch import LaunchDescription
from launch.actions import (AppendEnvironmentVariable, DeclareLaunchArgument,
                            IncludeLaunchDescription, RegisterEventHandler,
                            SetEnvironmentVariable)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (Command, FindExecutable,
                                  LaunchConfiguration, PathJoinSubstitution, TextSubstitution)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    gui = LaunchConfiguration("gui")
    launch_rviz = LaunchConfiguration("rviz")
    aubo_type = LaunchConfiguration("aubo_type")
    task = LaunchConfiguration("task")

    pkg_share = FindPackageShare("meituan_sim")
    models_dir = PathJoinSubstitution([pkg_share, "models"])
    world_file = PathJoinSubstitution(
        [pkg_share, "worlds", [TextSubstitution(text="task_"), task, TextSubstitution(text=".world")]]
    )

    controllers = PathJoinSubstitution(
        [FindPackageShare("meituan_sim"), "config", "aubo_S3_controllers.yaml"]
    )
    robot_description = {
        "robot_description": Command([
            PathJoinSubstitution([FindExecutable(name="xacro")]), " ",
            PathJoinSubstitution([FindPackageShare("meituan_sim"), "urdf", "aubo_S3_gazebo.urdf.xacro"]),
            " aubo_type:=", aubo_type, " controllers_file:=", controllers,
        ])
    }

    gz_share = FindPackageShare("gazebo_ros")
    gzserver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([gz_share, "/launch/gzserver.launch.py"]),
        launch_arguments={"verbose": "true", "pause": "false", "world": world_file}.items(),
    )
    gzclient = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([gz_share, "/launch/gzclient.launch.py"]),
        condition=IfCondition(gui),
    )

    rsp = Node(package="robot_state_publisher", executable="robot_state_publisher",
               output="screen", parameters=[robot_description])
    spawn = Node(package="gazebo_ros", executable="spawn_entity.py", output="screen",
                 arguments=["-topic", "robot_description", "-entity", "aubo_S3", "-z", "0.0"])
    jsb = Node(package="controller_manager", executable="spawner", output="screen",
               arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"])
    jtc = Node(package="controller_manager", executable="spawner", output="screen",
               arguments=["joint_trajectory_controller", "--controller-manager", "/controller_manager"])
    rviz = Node(package="rviz2", executable="rviz2", output="screen",
                condition=IfCondition(launch_rviz))

    return LaunchDescription([
        # WSL2 两个必设项：
        # 1) 不清空模型库 URI 时，gzserver 会卡在拉取已下线的 models.gazebosim.org，
        #    表现为 spawn 报成功但模型永不插入、gazebo_ros2_control 插件不加载、controller_manager 不出现。
        SetEnvironmentVariable("GAZEBO_MODEL_DATABASE_URI", ""),
        # 2) 不固定 IP 时 gazebo 会把 master 公布到 WSL 的 10.255.255.254，gz 命令行工具连不上。
        SetEnvironmentVariable("GAZEBO_IP", "127.0.0.1"),
        SetEnvironmentVariable("GAZEBO_MASTER_URI", "http://127.0.0.1:11345"),
        # 本机从未 source /usr/share/gazebo/setup.sh，GAZEBO_* 全空，必须在这里补齐，
        # 否则 model:// 一律解析失败：sun/ground_plane 找不到（电池无限自由落体）、
        # aubo_description 的 STL 碰撞网格加载失败（机器人没有碰撞体，且 gzserver 只报 [Err] 不中止）。
        AppendEnvironmentVariable("GAZEBO_RESOURCE_PATH", "/usr/share/gazebo-11"),
        AppendEnvironmentVariable("GAZEBO_MODEL_PATH", "/usr/share/gazebo-11/models"),
        AppendEnvironmentVariable(  # 含 aubo_description/ 的 share 目录，供其网格 model:// 解析
            "GAZEBO_MODEL_PATH", PathJoinSubstitution([FindPackageShare("aubo_description"), ".."])),
        AppendEnvironmentVariable("GAZEBO_MODEL_PATH", models_dir),
        DeclareLaunchArgument("task", default_value="p2",
                              description="底图任务页：p1=基础任务(T0)，p2=序列任务(P1-P3)"),
        DeclareLaunchArgument("gui", default_value="false", description="是否起 gzclient 图形界面"),
        DeclareLaunchArgument("rviz", default_value="false"),
        DeclareLaunchArgument("aubo_type", default_value="aubo_S3"),
        gzserver, gzclient, rsp, spawn,
        # 实体 spawn 完成后再拉控制器，否则 controller_manager 还没起来
        RegisterEventHandler(OnProcessExit(target_action=spawn, on_exit=[jsb])),
        RegisterEventHandler(OnProcessExit(target_action=jsb, on_exit=[jtc])),
        rviz,
    ])
