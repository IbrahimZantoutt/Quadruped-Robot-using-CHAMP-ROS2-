<div align="center">

# ChampQuadbot — Autonomous 12-DOF Quadruped

**Point-to-point navigation for a custom quadruped in ROS 2 & Gazebo, driven by the CHAMP locomotion controller with SLAM and Nav2.**

A hand-modeled 12-DOF quadruped walks itself to any goal you click in RViz — CHAMP generates the gait, slam_toolbox builds the map as it explores, and Nav2 plans a **collision-free** path through a cluttered apartment.

![ROS 2](https://img.shields.io/badge/ROS_2-Humble-22314E?logo=ros&logoColor=white)
![Gazebo](https://img.shields.io/badge/Gazebo-Classic-FF6C2C?logo=gazebo&logoColor=white)
![Nav2](https://img.shields.io/badge/Nav2-Navigation-2E7D32)
![slam_toolbox](https://img.shields.io/badge/slam__toolbox-Mapping-1565C0)
![CHAMP](https://img.shields.io/badge/CHAMP-Locomotion-6A1B9A)
![C++17](https://img.shields.io/badge/C%2B%2B-17-00599C?logo=cplusplus&logoColor=white)

</div>

---

## Demo

<div align="center">

### Autonomous navigation — click a goal, the quadbot walks there

<img width="80%" alt="Quadbot navigating to a Nav2 goal in Gazebo" src="https://github.com/user-attachments/assets/8583b27f-c73b-4dae-baf0-3273d485b66e" />

</div>

<table>
<tr>
<td width="50%" align="center">

### Live SLAM mapping while walking

<img width="100%" alt="slam_toolbox building the map as the quadbot explores" src="https://github.com/user-attachments/assets/db5e9237-4f84-4e6b-b46e-d48d2f32fff6" />

</td>
<td width="50%" align="center">

### Quadbot URDF model

<!-- Paste a screenshot of the Quadbot URDF (RViz RobotModel) here — drag-drop the file into GitHub's editor to get the <img ... /> tag. -->
<img width="100%" alt="12-DOF quadbot URDF in RViz" src="https://github.com/user-attachments/assets/7dd05895-9856-43b3-9235-5f13c7bf3c1e" />

</td>
</tr>
</table>

---

## Highlights

- **No pre-built map** — slam_toolbox maps the apartment live from a simulated lidar while the robot drives; the `/map` grows as it explores.
- **Click-to-walk autonomy** — a Nav2 goal in RViz becomes a `/cmd_vel` stream that CHAMP turns into a quadruped gait, so the robot plans a path and physically walks it.
- **Real collision avoidance** — Nav2's global/local costmaps keep every trajectory clear of walls and clutter in a tight apartment world.
- **Hand-written robot config** — CHAMP's setup assistant is ROS 1 only, so the full per-robot config (links, joints, gait, `ros2_control`) was authored by hand.
- **Tuned for stability** — a wide body, a joint-velocity governor, and soft foot contact were dialed in to stop the legs whipping and the body tipping at speed.

---

## How It Works

```
  RViz "Nav2 Goal"            Keyboard teleop
        │                          │
        ▼                          │
  Nav2 (planner · controller       │
       · costmaps · BT)            │
        │  /cmd_vel_nav            │
        ▼                          ▼
  velocity_smoother ─────────►  /cmd_vel
                                   │
                                   ▼
              CHAMP controller (quadruped_controller_node)
               • gait generator + body IK  →  12 joint targets
                                   │
                                   ▼
              ros2_control (effort joint_trajectory_controller)
                                   │
                                   ▼
        Gazebo Classic  (gazebo_ros2_control · physics · lidar)
                    │  /scan · /joint_states · /odom/ground_truth
                    ▼
   state_estimation + EKF ×2  ──►  odom→base_footprint→base_link
                    │
                    ▼
        slam_toolbox  ──►  /map  +  map→odom   (consumed by Nav2)
```

**1. Command —** motion comes from one of two sources: a **Nav2 Goal** clicked in RViz (planned through the costmaps) or **keyboard teleop**. Both resolve to a single `/cmd_vel` twist.

**2. Gait —** the CHAMP controller (`quadruped_controller_node`) runs a header-only gait generator + body IK to convert that twist into targets for all 12 joints (4 legs × hip / upper / lower).

**3. Control + sim —** an effort `joint_trajectory_controller` (via `ros2_control` / `gazebo_ros2_control`) drives the joints inside **Gazebo Classic**, which publishes lidar `/scan`, `/joint_states`, and ground-truth odometry.

**4. Estimation —** two `robot_localization` EKFs fuse odometry into the `odom→base_footprint→base_link` transform tree.

**5. Mapping + planning —** `slam_toolbox` builds `/map` and provides `map→odom` online (no map_server / AMCL); Nav2 uses only the navigation servers, planning fresh into not-yet-mapped space as the map fills in.

---

## Tech Stack

| Layer | Tools / Libraries |
|---|---|
| **Middleware** | ROS 2 **Humble** (`rclcpp`, launch) |
| **Locomotion** | **CHAMP** (`champ`, `champ_base` — header-only IK + gait core) |
| **Simulation** | **Gazebo Classic** (`gazebo_ros`, `gazebo_ros2_control`) |
| **Joint control** | **ros2_control** (`joint_trajectory_controller`, effort interface) |
| **Mapping** | **slam_toolbox** (online async SLAM) |
| **Navigation** | **Nav2** (`nav2_bringup`, NavFn, DWB, `costmap_2d`, `bt_navigator`) |
| **State estimation** | **robot_localization** (EKF ×2) |
| **Robot model** | URDF / Xacro (12-DOF quadruped + lidar) |
| **Visualization** | **RViz2** + Nav2 Goal tool |
| **Language / build** | C++17, `colcon`, `ament_cmake` |

Vendored sources (in `src/`): [`chvmp/champ`](https://github.com/chvmp/champ) (ros2 branch) and `champ_teleop`.

---

## Repository Layout

```
src/
├── champ/            # vendored CHAMP (controller core, champ_base, champ_gazebo, ...)
├── champ_teleop/     # keyboard teleop (publishes /cmd_vel)
├── champbot_nodes/   # robot description: urdf/, worlds/, rviz/, launch/
└── quadbot_config/   # per-robot config + launch (where most of the work lives)
    ├── config/
    │   ├── gait / joints / links / ros_control /   # CHAMP + ros2_control params
    │   └── autonomy/                               # slam.yaml, navigation.yaml
    └── launch/
        ├── bringup.launch.py     # CHAMP controller only (real-robot / controller half)
        ├── gazebo.launch.py      # Gazebo (world.sdf) + robot + CHAMP
        ├── gazebo_rviz.launch.py # ^ + RViz + SLAM (slam:=true) + Nav2 (nav2:=true)
        ├── gazebo_open.launch.py # empty world, lidar rays hidden
        └── nav2.launch.py        # Nav2 servers only
```

> **Why the config is hand-written:** CHAMP's setup assistant is ROS 1 only, so the
> per-robot config was written by hand, modeled on
> [`anujjain-dev/unitree-go2-ros2`](https://github.com/anujjain-dev/unitree-go2-ros2).
> The quadbot's link/joint names match CHAMP convention 1:1 (`lf/rf/lh/rh` +
> `hip/upper_leg/lower_leg/foot`), so `links.yaml` / `joints.yaml` are name maps only.

---

## Getting Started

### Prerequisites
- Ubuntu 22.04 + **ROS 2 Humble**
- **Gazebo Classic**, Nav2, slam_toolbox, and `ros2_control` / `gazebo_ros2_control`

```bash
sudo apt install ros-humble-gazebo-ros-pkgs ros-humble-gazebo-ros2-control \
  ros-humble-ros2-control ros-humble-ros2-controllers \
  ros-humble-nav2-bringup ros-humble-slam-toolbox ros-humble-robot-localization
```

### Build

```bash
git clone https://github.com/IbrahimZantoutt/ChampQuadbot.git
cd ChampQuadbot
colcon build
source install/setup.bash
```

### Run

```bash
# full sim: Gazebo + CHAMP + RViz + SLAM + Nav2
ros2 launch quadbot_config gazebo_rviz.launch.py
```

Then in RViz, click **"Nav2 Goal"** in the toolbar and click a destination on the map — the
robot plans a path (green) and walks to it, mapping as it goes. To drive it manually instead:

```bash
ros2 run champ_teleop champ_teleop.py    # focus this terminal, then use i/j/l/k/u/o/m
```

> **On WSL2, run headless.** The Gazebo GUI (gzclient) is unreliable here — work in RViz with
> `gui:=false` (see [Challenges](#challenges--lessons-learned)):
> ```bash
> ros2 launch quadbot_config gazebo_rviz.launch.py gui:=false
> ```

**Launch args (`gazebo_rviz.launch.py`):** `gui` (`false` = headless, recommended on WSL2),
`rviz`, `slam`, `nav2` — each `true` by default. Other entry points:

```bash
ros2 launch quadbot_config gazebo_open.launch.py   # empty world, lidar rays hidden
ros2 launch quadbot_config gazebo.launch.py        # Gazebo + CHAMP only (no RViz/SLAM/Nav2)
```

---

## Challenges & Lessons Learned

The hard-won lessons from building this — kept here so they aren't re-derived.

### Locomotion & stability (Gazebo)
- **Joint velocity limit is the smoothness governor.** Lowering joint `velocity` to ~1.5 (with
  effort ~25) stopped the legs whipping/"getting excited" — the single biggest smoothness win.
  High limits = jerky gait, worst during forward motion.
- **A wide body gives passive stability.** Body is `0.50 × 0.26 × 0.08`, 3 kg. Widening
  0.18→0.26 nearly doubled roll inertia and stopped tipping at speed + idle drift. Don't revert
  to a narrow body; to lighten, widen for inertia rather than dropping mass.
- **`nominal_height ≈ 0.22` is the sweet spot** — higher (0.25) is crisp but slides when idle;
  lower (0.18) is planted but laggy. **Joint damping 0.2** holds idle best (0.0 shakes, 0.4 drifts).
- **Foot contact must stay soft** (`mu 1.2 / kp 1e5 / kd 2.0`); the reference's stiff values
  destabilize this robot.

### WSL2 Gazebo GUI (gzclient)
- **gzclient is unreliable on this WSL2** — the world renders but live model/sensor updates don't
  sync (robot looks missing, lidar rays don't show, Models tree empty), spamming
  `Dropped Escape call with ulEscapeCode` (WSL2 d3d12 GL passthrough dropping calls).
- The **simulation (gzserver) is fine** — RViz, SLAM, and `/odom/ground_truth` confirm the robot
  is really there and moving. **Fix:** run `gui:=false` and work in RViz. If you truly need the
  window, `LIBGL_ALWAYS_SOFTWARE=1 ros2 launch …` uses a more stable (slower) GL path.

### Leftover / zombie processes
- A partially-killed launch leaves **duplicate controllers / a second Gazebo** fighting over
  topics → the robot freezes or acts erratically. A **`TF_OLD_DATA` flood at a frozen timestamp**
  means gzserver died and surviving nodes keep re-stamping TF at the old sim time — restart.
- Clean-slate kill, then verify `pgrep gzserver` is empty before relaunching:
  ```bash
  pkill -9 -f 'gzserver|gzclient|quadruped_controller_node|state_estimation_node|ekf_node|async_slam_toolbox|rviz2'
  ```

### Nav2
- **cmd_vel wiring:** `controller_server → /cmd_vel_nav → velocity_smoother → /cmd_vel`, and CHAMP
  subscribes to `/cmd_vel`, so a Nav2 goal drives the robot directly.
- **"GridBased failed" / no path:** set `track_unknown_space: false` so Nav2 plans into
  not-yet-mapped space, and align DWB velocity limits to the gait (0.3 / 0.5).
- **"No valid trajectories / BaseObstacle hits obstacle":** the footprint reads as in-collision in
  the tight apartment — shrink `robot_radius` and `inflation_radius` (currently 0.16) to fit
  doorways and clutter.

---

## Key Tuning Knobs

| File | Knob | Note |
|---|---|---|
| `champbot_nodes/urdf/robot.urdf.xacro` | body size, leg/joint limits, foot contact, `lidar_visualize` | stability + rays toggle |
| `quadbot_config/config/gait/gait.yaml` | `nominal_height`, velocities, `knee_orientation` | gait |
| `quadbot_config/config/ros_control/ros_control.yaml` | effort PID (`p 80`) | tracking |
| `quadbot_config/config/autonomy/slam.yaml` | slam_toolbox params | mapping |
| `quadbot_config/config/autonomy/navigation.yaml` | DWB limits, `robot_radius`, `inflation_radius`, `track_unknown_space` | navigation |

## Known Limitations

- Gazebo GUI (gzclient) unreliable on WSL2 → use `gui:=false` + RViz.
- The apartment world is tight; Nav2 needs the small footprint / inflation above to plan.
- Locomotion traction can be marginal (occasional walk-in-place) — check `/odom/ground_truth`
  actually moves when driving.

---

<div align="center">

*Built by [Ibrahim Zantout](https://github.com/IbrahimZantoutt) — quadruped locomotion, SLAM & navigation in ROS 2.*

</div>
