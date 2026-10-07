# SO-101 Leader Arm → Gazebo / RViz Teleoperation

Move a real **LeRobot SO-101 leader arm** and a **simulated SO-101 follower** in Gazebo (and RViz) follows it. No follower hardware is needed.

```
Leader arm (USB) ──► leader_reader.py ──UDP 127.0.0.1:5005──► leader_ros.py ──► ROS 2 controllers ──► Gazebo / RViz
                     (Python 3.12 + LeRobot)                   (system Python 3.10 + ROS 2 Humble)
```

## Why two scripts?

LeRobot (0.6.x) needs **Python ≥ 3.12**, while ROS 2 Humble uses **Python 3.10**. They cannot be imported in one process, so the leader is read in a conda env and sent to the ROS node over local UDP.

## Requirements

| Item | Tested with |
|------|-------------|
| OS | Ubuntu 22.04 |
| ROS 2 | Humble + Gazebo Classic (`gazebo_ros2_control`) |
| LeRobot | 0.6.2, Python 3.12 (conda env) |
| Leader arm | SO-101 leader, calibrated, on `/dev/ttyACM0` |
| Simulation | An SO-101 ROS 2 package with `arm_controller` and `gripper_controller` (`JointTrajectoryController`) |

Joint names used: `shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper`.

## Setup

### 1. LeRobot environment
```bash
conda create -y -n lerobot python=3.12
conda activate lerobot
conda install -y ffmpeg -c conda-forge
git clone https://github.com/huggingface/lerobot.git ~/lerobot
cd ~/lerobot && pip install -e ".[feetech]"
```

### 2. Find the port and calibrate the leader
```bash
lerobot-find-port
sudo chmod 666 /dev/ttyACM0          # or: sudo usermod -aG dialout $USER (then re-login)
lerobot-calibrate --teleop.type=so101_leader --teleop.port=/dev/ttyACM0 --teleop.id=my_leader
```
Press `c` to calibrate: move the arm to the middle of its range, press Enter, then move every joint through its full range.

### 3. Check the settings in the scripts
- `leader_reader.py`: `PORT`, and `GRIPPER_RANGE` (must match your URDF gripper limits).
- `leader_ros.py`: topic names `/arm_controller/joint_trajectory` and `/gripper_controller/joint_trajectory`.

## Run

Use separate terminals. **Do not run ROS commands with conda active** (`conda deactivate` until the prompt has no `(base)`).

**Terminal 1: Gazebo**
```bash
source /opt/ros/humble/setup.bash && source ~/so101/install/setup.bash
ros2 launch so101_gazebo so101_gazebo.launch.py
ros2 control list_controllers      # arm_controller and gripper_controller must be active
```

**Terminal 2: ROS bridge (system Python)**
```bash
source /opt/ros/humble/setup.bash && source ~/so101/install/setup.bash
/usr/bin/python3 leader_ros.py --ros-args -r /joint_states:=/leader/joint_states
```

**Terminal 3: leader reader (conda)**
```bash
conda activate lerobot
python leader_reader.py
```

Or start terminals 2 and 3 together (from a terminal without conda): `./run_all.sh`

Keep your hand on the leader at start: the simulated arm jumps to its pose. Terminal 3 prints `RAW:` values and terminal 2 prints `RECEIVED:` values, so you can see data at each stage.

### RViz
Gazebo publishes the real state on `/joint_states`, so RViz follows the Gazebo arm:
```bash
ros2 launch so101_gazebo so101_rviz.launch.py
```
The `--ros-args -r /joint_states:=/leader/joint_states` remap stops the bridge from fighting Gazebo's own `/joint_states`. For RViz only (no Gazebo), remove the remap.

## Conversions
- Arm joints: leader degrees → radians.
- Gripper: leader 0–100 % → URDF range (`GRIPPER_RANGE`).

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `No module named 'rclpy._rclpy_pybind11'` | ROS was run with conda Python. `conda deactivate`, use `/usr/bin/python3`. |
| `No module named 'lxml'` in `spawn_entity.py` | Gazebo was launched with conda active. Launch it from a plain terminal. |
| `requires a different Python: 3.10 not in '>=3.12'` | Create the conda env with Python 3.12. |
| `No module named 'lerobot.teleoperators.so101_leader'` | In 0.6.x the module is `lerobot.teleoperators.so_leader` (already used here). |
| `Address already in use` (UDP 5005) | `leader_ros.py` is already running. `pkill -f leader_ros.py`. |
| No `RAW:` values change | Check port, permissions (`ls -l /dev/ttyACM0`), and re-run calibration. |
| `RAW:` changes, no `RECEIVED:` | The ROS node is not running or uses a different port. |
| Gazebo arm does not move | `ros2 topic info /arm_controller/joint_trajectory` should show 1 subscriber. |
| A joint moves the wrong way | Negate that joint's value in `leader_reader.py`. |
| Constant offset between leader and sim | Add a per-joint offset in `leader_reader.py`. |

## Files
| File | Purpose |
|------|---------|
| `leader_reader.py` | Reads the leader with LeRobot, converts units, sends UDP |
| `leader_ros.py` | Receives UDP, publishes `JointState` and trajectory commands |
| `run_all.sh` | Starts the bridge and reader together |

## Safety
This only commands the simulation. Do not connect a physical follower to this pipeline without adding speed and range limits.

## Credits
Built on [LeRobot](https://github.com/huggingface/lerobot) by Hugging Face.
