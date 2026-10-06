from setuptools import setup

package_name = 'so101_keyboard'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='moulie',
    maintainer_email='moulie@example.com',
    description='Keyboard teleop for SO-101',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'keyboard_teleop = so101_keyboard.keyboard_teleop:main',
        ],
    },
)
