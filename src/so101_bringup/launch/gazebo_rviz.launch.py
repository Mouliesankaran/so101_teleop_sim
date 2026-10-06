import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    desc_dir = get_package_share_directory('so101_description')
    gz_dir = get_package_share_directory('ros_gz_sim')
    xacro_file = os.path.join(desc_dir, 'urdf', 'robots', 'so101.urdf.xacro')
    rviz_file = os.path.join(desc_dir, 'rviz', 'robot_arm_description.rviz')

    robot_description = ParameterValue(
        Command([FindExecutable(name='xacro'), ' ', xacro_file, ' use_gazebo:=true']),
        value_type=str)

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(gz_dir, 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': '-r empty.sdf'}.items())

    rsp = Node(package='robot_state_publisher', executable='robot_state_publisher',
               parameters=[{'robot_description': robot_description, 'use_sim_time': True}])

    spawn = Node(package='ros_gz_sim', executable='create',
                 arguments=['-topic', 'robot_description', '-name', 'so101', '-z', '0.0'],
                 output='screen')

    clock_bridge = Node(package='ros_gz_bridge', executable='parameter_bridge',
                        arguments=['/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock'],
                        output='screen')

    def spawner(name):
        return Node(package='controller_manager', executable='spawner',
                    arguments=[name, '--controller-manager', '/controller_manager'])

    jsb = spawner('joint_state_broadcaster')
    arm = spawner('arm_controller')
    gripper = spawner('gripper_controller')

    rviz = Node(package='rviz2', executable='rviz2', arguments=['-d', rviz_file],
                parameters=[{'use_sim_time': True}])

    return LaunchDescription([
        gazebo, rsp, clock_bridge, spawn,
        RegisterEventHandler(OnProcessExit(target_action=spawn, on_exit=[jsb])),
        RegisterEventHandler(OnProcessExit(target_action=jsb, on_exit=[arm, gripper])),
        rviz,
    ])
