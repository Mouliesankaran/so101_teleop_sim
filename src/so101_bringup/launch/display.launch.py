import os
from launch import LaunchDescription
from launch.substitutions import Command, FindExecutable
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    desc_dir = get_package_share_directory('so101_description')
    xacro_file = os.path.join(desc_dir, 'urdf', 'robots', 'so101.urdf.xacro')
    rviz_file = os.path.join(desc_dir, 'rviz', 'robot_arm_description.rviz')

    robot_description = ParameterValue(
        Command([FindExecutable(name='xacro'), ' ', xacro_file, ' use_gazebo:=false']),
        value_type=str)

    return LaunchDescription([
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': robot_description}]),
        Node(package='joint_state_publisher_gui', executable='joint_state_publisher_gui'),
        Node(package='rviz2', executable='rviz2', arguments=['-d', rviz_file]),
    ])
