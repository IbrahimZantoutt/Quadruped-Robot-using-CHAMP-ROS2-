# Modeled on chvmp go2_config/launch/bringup.launch.py.
# Brings up the CHAMP controller (champ_base) for quadbot using this package's
# links/joints/gait config. Used for the real robot or as the controller half of
# the gazebo launch.

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    this_package = FindPackageShare('quadbot_config')

    # quadbot's robot description lives in the champbot_nodes package
    description_path = PathJoinSubstitution(
        [FindPackageShare('champbot_nodes'), 'urdf', 'robot.urdf.xacro']
    )
    joints_config = PathJoinSubstitution(
        [this_package, 'config', 'joints', 'joints.yaml']
    )
    gait_config = PathJoinSubstitution(
        [this_package, 'config', 'gait', 'gait.yaml']
    )
    links_config = PathJoinSubstitution(
        [this_package, 'config', 'links', 'links.yaml']
    )
    bringup_launch_path = PathJoinSubstitution(
        [FindPackageShare('champ_bringup'), 'launch', 'bringup.launch.py']
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            name='robot_name',
            default_value='quadbot',
            description='Robot name (used for multi-robot / namespacing)'
        ),
        DeclareLaunchArgument(
            name='sim',
            default_value='false',
            description='Set use_sim_time true'
        ),
        DeclareLaunchArgument(
            name='rviz',
            default_value='false',
            description='Run rviz'
        ),
        DeclareLaunchArgument(
            name='hardware_connected',
            default_value='false',
            description='Set true when connected to a physical robot'
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(bringup_launch_path),
            launch_arguments={
                # passing description_path explicitly so champ uses quadbot's
                # URDF (go2_config omitted this in bringup.launch.py)
                "description_path": description_path,
                "use_sim_time": LaunchConfiguration("sim"),
                "robot_name": LaunchConfiguration("robot_name"),
                "gazebo": LaunchConfiguration("sim"),
                "rviz": LaunchConfiguration("rviz"),
                "hardware_connected": LaunchConfiguration("hardware_connected"),
                "publish_foot_contacts": "true",
                "close_loop_odom": "true",
                "joint_controller_topic": "joint_group_effort_controller/joint_trajectory",
                "joints_map_path": joints_config,
                "links_map_path": links_config,
                "gait_config_path": gait_config,
            }.items(),
        )
    ])
