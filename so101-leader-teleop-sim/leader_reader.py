import json
import math
import socket
import time

from lerobot.teleoperators.so_leader import SO101Leader, SO101LeaderConfig

JOINTS = ["shoulder_pan", "shoulder_lift", "elbow_flex",
          "wrist_flex", "wrist_roll", "gripper"]
GRIPPER_RANGE = (-0.174533, 1.74533)  # from your URDF limits
PORT = "/dev/ttyACM0"
UDP_ADDR = ("127.0.0.1", 5005)


def main():
    leader = SO101Leader(SO101LeaderConfig(port=PORT, id="my_leader"))
    leader.connect()
    print("Leader connected on", PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    last_print = 0.0
    try:
        while True:
            a = leader.get_action()
            if time.time() - last_print > 0.5:
                last_print = time.time()
                print("RAW:", {k: round(v, 1) for k, v in a.items()})
            pos = []
            for j in JOINTS:
                v = a[j + ".pos"]
                if j == "gripper":
                    lo, hi = GRIPPER_RANGE
                    v = lo + (hi - lo) * v / 100.0
                else:
                    v = math.radians(v)
                pos.append(float(v))
            sock.sendto(json.dumps(pos).encode(), UDP_ADDR)
            time.sleep(1 / 30)
    except KeyboardInterrupt:
        pass
    finally:
        leader.disconnect()


if __name__ == "__main__":
    main()
