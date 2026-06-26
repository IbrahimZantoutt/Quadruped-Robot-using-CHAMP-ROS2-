# One-shot simulation bringup: Gazebo (world + robot + CHAMP controller) plus
# RViz preloaded with the quadbot.rviz config so you can see the robot model,
# TF, laser scan, the SLAM map, and (once Nav2 is added) costmaps and paths.
#
#   ros2 launch quadbot_config gazebo_rviz.launch.py
#
# By default it also starts slam_toolbox (slam:=true) so a map is built live and
# the `map` frame exists for RViz's fixed frame. Turn it off with slam:=false.
# With nav2:=true (default) it also brings up the Nav2 stack a few seconds later,
# so you can use RViz's "Nav2 Goal" tool to click a destination and the robot
# drives there. The costmap/path displays in the RViz config populate once Nav2
# is up. Turn Nav2 off with nav2:=false.

import os

import launch_ros
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription,
                            TimerAction)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    config_pkg_share = launch_ros.substitutions.FindPackageShare(
        package="quadbot_config"
    ).find("quadbot_config")

    default_rviz_path = os.path.join(config_pkg_share, "rviz", "quadbot.rviz")
    default_slam_params = os.path.join(
        config_pkg_share, "config", "autonomy", "slam.yaml"
    )

    use_sim_time = LaunchConfiguration("use_sim_time")

    declare_use_sim_time = DeclareLaunchArgument(
        "use_sim_time", default_value="true",
        description="Use simulation (Gazebo) clock",
    )
    declare_gui = DeclareLaunchArgument(
        "gui", default_value="true", description="Launch the Gazebo client (GUI)"
    )
    declare_rviz = DeclareLaunchArgument(
        "rviz", default_value="true", description="Launch RViz"
    )
    declare_rviz_config = DeclareLaunchArgument(
        "rviz_config", default_value=default_rviz_path,
        description="Absolute path to the RViz config file",
    )
    declare_slam = DeclareLaunchArgument(
        "slam", default_value="true",
        description="Also start slam_toolbox to build a map live",
    )
    declare_slam_params = DeclareLaunchArgument(
        "slam_params_file", default_value=default_slam_params,
        description="slam_toolbox params file",
    )
    declare_nav2 = DeclareLaunchArgument(
        "nav2", default_value="true",
        description="Bring up the Nav2 stack (click a goal in RViz to navigate)",
    )

    # Gazebo + robot + CHAMP controller (this is the launch the world is wired into)
    gazebo_ld = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("quadbot_config"),
                "launch",
                "gazebo.launch.py",
            )
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "gui": LaunchConfiguration("gui"),
        }.items(),
    )

    # slam_toolbox (online async) -- gives the `map` frame + occupancy grid
    slam_ld = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("slam_toolbox"), "launch", "online_async_launch.py"]
            )
        ),
        condition=IfCondition(LaunchConfiguration("slam")),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "slam_params_file": LaunchConfiguration("slam_params_file"),
        }.items(),
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", LaunchConfiguration("rviz_config")],
        parameters=[{"use_sim_time": use_sim_time}],
        condition=IfCondition(LaunchConfiguration("rviz")),
    )

    # Nav2 navigation servers, fed by the live SLAM map. Delayed ~10s so gzserver,
    # CHAMP TF (map->odom->base_footprint->base_link), /scan and /map are all
    # flowing before the costmaps initialize -- otherwise they come up dirty.
    nav2_ld = TimerAction(
        period=10.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(
                        get_package_share_directory("quadbot_config"),
                        "launch",
                        "nav2.launch.py",
                    )
                ),
                condition=IfCondition(LaunchConfiguration("nav2")),
                launch_arguments={"use_sim_time": use_sim_time}.items(),
            )
        ],
    )

    return LaunchDescription([
        declare_use_sim_time,
        declare_gui,
        declare_rviz,
        declare_rviz_config,
        declare_slam,
        declare_slam_params,
        declare_nav2,
        gazebo_ld,
        slam_ld,
        rviz_node,
        nav2_ld,
    ])
