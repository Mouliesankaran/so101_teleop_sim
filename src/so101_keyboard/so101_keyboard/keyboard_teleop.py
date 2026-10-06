import os
import select
import sys
import termios
import tty

import rclpy
from rclpy.node import Node
from builtin_interfaces.msg import Duration
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

ARM = ['shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex', 'wrist_roll']
GRIPPER = ['gripper']
ALL = ARM + GRIPPER

LIMITS = {
    'shoulder_pan': (-1.91986, 1.91986),
    'shoulder_lift': (-1.74533, 1.74533),
    'elbow_flex': (-1.69, 1.69),
    'wrist_flex': (-1.65806, 1.65806),
    'wrist_roll': (-2.74385, 2.84121),
    'gripper': (-0.174533, 1.74533),
}

# key: (joint, direction)
KEYS = {
    'q': ('shoulder_pan', 1), 'a': ('shoulder_pan', -1),
    'w': ('shoulder_lift', 1), 's': ('shoulder_lift', -1),
    'e': ('elbow_flex', 1), 'd': ('elbow_flex', -1),
    'r': ('wrist_flex', 1), 'f': ('wrist_flex', -1),
    't': ('wrist_roll', 1), 'g': ('wrist_roll', -1),
    'y': ('gripper', 1), 'h': ('gripper', -1),
}

STEP = 0.1        # rad per letter-key press
SPEED = 0.05      # rad/s for continuous motion
DT = 0.05         # loop period in seconds

UP, DOWN, RIGHT, LEFT = '\x1b[A', '\x1b[B', '\x1b[C', '\x1b[D'

HELP = """
SO-101 keyboard teleop
  Arrows:  LEFT/RIGHT = select joint   UP/DOWN = move selected joint continuously
           SPACE = stop
  Letters: q/a shoulder_pan   w/s shoulder_lift   e/d elbow_flex
           r/f wrist_flex     t/g wrist_roll      y/h gripper   (0.1 rad per press)
  z = all joints to zero      c = quit
"""


class KeyboardTeleop(Node):
    def __init__(self):
        super().__init__('so101_keyboard_teleop')
        self.arm_pub = self.create_publisher(JointTrajectory, '/arm_controller/joint_trajectory', 10)
        self.grip_pub = self.create_publisher(JointTrajectory, '/gripper_controller/joint_trajectory', 10)
        self.target = {j: 0.0 for j in ALL}
        self.selected = 0
        self.direction = 0

    def send(self):
        for names, pub in ((ARM, self.arm_pub), (GRIPPER, self.grip_pub)):
            msg = JointTrajectory()
            msg.joint_names = names
            point = JointTrajectoryPoint()
            point.positions = [self.target[j] for j in names]
            point.time_from_start = Duration(sec=0, nanosec=150000000)
            msg.points = [point]
            pub.publish(msg)

    def move(self, joint, delta):
        """Move a joint by delta. Returns True if it hit a limit."""
        low, high = LIMITS[joint]
        new = self.target[joint] + delta
        self.target[joint] = min(high, max(low, new))
        return new < low or new > high

    def zero(self):
        for j in self.target:
            self.target[j] = 0.0


def get_key(fd, settings, timeout):
    tty.setraw(fd)
    key = ''
    if select.select([fd], [], [], timeout)[0]:
        data = os.read(fd, 3).decode(errors='ignore')
        key = data[:3] if data.startswith('\x1b[') else data[:1]
    termios.tcsetattr(fd, termios.TCSADRAIN, settings)
    return key


def main():
    rclpy.init()
    node = KeyboardTeleop()
    fd = sys.stdin.fileno()
    settings = termios.tcgetattr(fd)
    print(HELP)
    print(f'Selected joint: {ALL[node.selected]}')
    try:
        while rclpy.ok():
            key = get_key(fd, settings, DT)
            if key == 'c':
                break
            elif key == UP:
                node.direction = 1
                print(f'Moving {ALL[node.selected]} (+)')
            elif key == DOWN:
                node.direction = -1
                print(f'Moving {ALL[node.selected]} (-)')
            elif key in (LEFT, RIGHT):
                node.direction = 0
                node.selected = (node.selected + (1 if key == RIGHT else -1)) % len(ALL)
                print(f'Selected joint: {ALL[node.selected]}')
            elif key == ' ':
                node.direction = 0
                print('Stopped')
            elif key == 'z':
                node.direction = 0
                node.zero()
                node.send()
            elif key in KEYS:
                joint, direction = KEYS[key]
                node.move(joint, direction * STEP)
                node.send()
                print(f'{joint}: {node.target[joint]:.2f} rad')

            if node.direction != 0:
                joint = ALL[node.selected]
                if node.move(joint, node.direction * SPEED * DT):
                    node.direction = 0
                    print(f'{joint} reached its limit ({node.target[joint]:.2f} rad)')
                node.send()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
