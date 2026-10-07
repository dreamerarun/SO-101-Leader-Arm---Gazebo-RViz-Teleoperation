#!/usr/bin/env bash
# Starts the ROS side and the leader reader. Gazebo must already be running.
# Usage: ./run_all.sh   (run from a terminal WITHOUT conda active)
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
source /opt/ros/humble/setup.bash
source "${SO101_WS:-$HOME/so101}/install/setup.bash"

/usr/bin/python3 "$DIR/leader_ros.py" --ros-args -r /joint_states:=/leader/joint_states &
ROS_PID=$!
trap 'kill $ROS_PID 2>/dev/null' EXIT
sleep 2

CONDA_BASE="$(conda info --base)"
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate lerobot
python "$DIR/leader_reader.py"
