import json
import socket
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration

JOINTS = ["shoulder_pan", "shoulder_lift", "elbow_flex",
          "wrist_flex", "wrist_roll", "gripper"]


def traj(names, positions):
    t = JointTrajectory()
    t.joint_names = names
    p = JointTrajectoryPoint()
    p.positions = positions
    p.time_from_start = Duration(nanosec=100_000_000)
    t.points = [p]
    return t


class LeaderRos(Node):
    def __init__(self):
        super().__init__("leader_ros")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", 5005))
        self.sock.setblocking(False)
        self.last_print = 0.0
        self.js_pub = self.create_publisher(JointState, "/joint_states", 10)
        self.arm_pub = self.create_publisher(
            JointTrajectory, "/arm_controller/joint_trajectory", 10)
        self.gr_pub = self.create_publisher(
            JointTrajectory, "/gripper_controller/joint_trajectory", 10)
        self.create_timer(1 / 60, self.loop)
        print("Waiting for leader data on UDP 5005 ...")

    def loop(self):
        data = None
        try:
            while True:
                data, _ = self.sock.recvfrom(4096)
        except BlockingIOError:
            pass
        if data is None:
            return
        pos = json.loads(data.decode())
        if time.time() - self.last_print > 1.0:
            self.last_print = time.time()
            print("RECEIVED:", [round(p, 2) for p in pos])

        js = JointState()
        js.header.stamp = self.get_clock().now().to_msg()
        js.name = JOINTS
        js.position = pos
        self.js_pub.publish(js)

        self.arm_pub.publish(traj(JOINTS[:5], pos[:5]))
        self.gr_pub.publish(traj(["gripper"], [pos[5]]))


def main():
    rclpy.init()
    node = LeaderRos()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
