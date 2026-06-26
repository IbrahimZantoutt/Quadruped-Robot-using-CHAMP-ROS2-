# Nav2 navigation stack for quadbot, running on top of the live SLAM map.
#
# This brings up ONLY the Nav2 navigation servers (controller, planner, smoother,
# behaviors, bt_navigator, waypoint_follower, velocity_smoother) -- NOT a
# map_server or AMCL. slam_toolbox (started by gazebo_rviz.launch.py) already
# provides the `map` frame, the map->odom transform, and the /map grid, so Nav2
# plans on the map being built live.
#
# cmd_vel path: controller_server -> /cmd_vel_nav -> velocity_smoother -> /cmd_vel,
# and CHAMP's quadruped_controller subscribes to /cmd_vel, so a Nav2 goal drives
# the robot directly. Params (DWB limits, costmaps, footprint) live in
# config/autonomy/navigation.yaml, tuned to the quadbot gait.
#
# Usually started via gazebo_rviz.launch.py with nav2:=true. To run standalone
# (e.g. SLAM already up in another terminal):
#   ros2 launch quadbot_config nav2.launch.py
# Then in RViz use the "Nav2 Goal" tool to click a destination.

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    default_params_file = os.path.join(
        get_package_share_directory("quadbot_config"),
        "config", "autonomy", "navigation.yaml",
    )

    declare_use_sim_time = DeclareLaunchArgument(
        "use_sim_time", default_value="true",
        description="Use simulation (Gazebo) clock",
    )
    declare_params_file = DeclareLaunchArgument(
        "params_file", default_value=default_params_file,
        description="Nav2 params file",
    )

    nav2_ld = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("nav2_bringup"), "launch", "navigation_launch.py"]
            )
        ),
        launch_arguments={
            "use_sim_time": LaunchConfiguration("use_sim_time"),
            "params_file": LaunchConfiguration("params_file"),
        }.items(),
    )

    return LaunchDescription([
        declare_use_sim_time,
        declare_params_file,
        nav2_ld,
    ])
