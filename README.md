# ChampQuadbot

A ROS 2 Humble simulation of a custom 12-DOF quadruped (**"quadbot"**) driven by the
[CHAMP](https://github.com/chvmp/champ) locomotion controller, with SLAM and Nav2 for
autonomous point-to-point navigation in Gazebo Classic.

Click a goal in RViz → the robot plans a path and walks there, building a map as it goes.

---

## Visualization

<img width="672" height="360" alt="quadbotmovement-ezgif com-video-to-gif-converter" src="https://github.com/user-attachments/assets/8583b27f-c73b-4dae-baf0-3273d485b66e" />


## What's in it

- **Custom quadruped** — 12 DOF (4 legs × hip/upper/lower), hand-modeled URDF, effort-controlled.
- **CHAMP controller** — header-only IK/gait core + `champ_base` rclcpp nodes generate the gait.
- **Gazebo Classic** simulation with `gazebo_ros2_control` (effort joint trajectory controller).
- **slam_toolbox** — live 2D mapping from a simulated lidar (`/scan`).
- **Nav2** — global/local planning + control; navigate by clicking a goal in RViz.

## Stack / dependencies

| Piece | Used for |
|---|---|
| ROS 2 **Humble** | base |
| **Gazebo Classic** (`gazebo_ros`, `gazebo_ros2_control`) | physics sim + spawn + controllers |
| **ros2_control** (`joint_trajectory_controller`, effort interface) | joint control |
| **slam_toolbox** | online async SLAM → `map`, `map→odom`, `/map` |
| **Nav2** (`nav2_bringup`, DWB, NavFn, costmap_2d, bt_navigator) | navigation |
| **robot_localization** (EKF ×2) | `odom→base_footprint→base_link` |
| **RViz2** | visualization + Nav2 Goal tool |

External vendored sources (in `src/`): `chvmp/champ` (ros2 branch) and `champ_teleop`.

## Packages

```
src/
├── champ/            # vendored CHAMP (controller core, champ_base, champ_gazebo, ...)
├── champ_teleop/     # keyboard teleop (publishes /cmd_vel)
├── champbot_nodes/   # robot description: urdf/, worlds/, rviz/, launch/
└── quadbot_config/   # the per-robot config + launch (this is where most work lives)
    ├── config/
    │   ├── gait/joints/links/ros_control/   # CHAMP + ros2_control params
    │   └── autonomy/                         # slam.yaml, navigation.yaml
    └── launch/
        ├── bringup.launch.py     # CHAMP controller only (real robot / controller half)
        ├── gazebo.launch.py      # Gazebo (world.sdf) + robot + CHAMP
        ├── gazebo_rviz.launch.py # ^ + RViz + SLAM (slam:=true) + Nav2 (nav2:=true)
        ├── gazebo_open.launch.py # empty world, lidar rays hidden
        └── nav2.launch.py        # Nav2 servers only
```

> **Why config is hand-written:** CHAMP's setup assistant is ROS 1 only, so the
> per-robot config (links/joints/gait/ros_control) was written by hand, modeled on
> [`anujjain-dev/unitree-go2-ros2`](https://github.com/anujjain-dev/unitree-go2-ros2).
> The quadbot's link/joint names match CHAMP convention 1:1 (`lf/rf/lh/rh` +
> `hip/upper_leg/lower_leg/foot`), so `links.yaml`/`joints.yaml` are name maps only.

---

## Quick start

```bash
# build
cd ~/ChampQuadbot
colcon build
source install/setup.bash

# full sim: Gazebo + CHAMP + RViz + SLAM + Nav2
ros2 launch quadbot_config gazebo_rviz.launch.py
```

**On WSL2, prefer headless Gazebo** (the Gazebo GUI is unreliable here — see below):

```bash
ros2 launch quadbot_config gazebo_rviz.launch.py gui:=false
```

### Tutorial — drive it

1. **Teleop (manual):** in another terminal,
   ```bash
   ros2 run champ_teleop champ_teleop.py
   ```
   Click that terminal and use `i/j/l/k/u/o/m`. (Teleop only reads keys from its own
   focused terminal.)

2. **Autonomous (Nav2):** in RViz, click **"Nav2 Goal"** in the toolbar, then click a
   destination on the map. The robot plans a path (green) and walks to it. Costmaps and
   the path show up in RViz; the gray `/map` grows as you explore.

### Useful launch args (`gazebo_rviz.launch.py`)

| arg | default | effect |
|---|---|---|
| `gui` | `true` | `gui:=false` runs Gazebo headless (no gzclient window) — **recommended on WSL2** |
| `rviz` | `true` | RViz on/off |
| `slam` | `true` | slam_toolbox on/off |
| `nav2` | `true` | Nav2 stack on/off |

### Other launches

```bash
ros2 launch quadbot_config gazebo_open.launch.py   # empty world, lidar rays hidden
ros2 launch quadbot_config gazebo.launch.py         # Gazebo + CHAMP only (no RViz/SLAM/Nav2)
```

---

## Problems faced & solved

Lessons from building this (kept here so they aren't re-derived). More detail lives in the
project memory under `.claude/projects/.../memory/`.

### Locomotion / stability (Gazebo)
- **Joint velocity limit is the smoothness governor.** Lowering joint `velocity` to ~1.5
  (with effort ~25) stopped the legs from whipping/"getting excited" — the single biggest
  smoothness win. High limits = jerky gait, worst during forward motion.
- **A wide body gives passive stability.** Body is `0.50 × 0.26 × 0.08`, 3 kg. Widening
  0.18→0.26 nearly doubled roll inertia and stopped tipping at speed + idle drift. *Do not*
  revert to a narrow body.
- **Going lighter destabilizes** (PID/inertia limited). To lighten, widen for inertia
  instead of dropping mass.
- **`nominal_height ≈ 0.22` is the sweet spot** — higher (0.25) is crisp but slides when
  idle; lower (0.18) is planted but laggy.
- **Joint damping 0.2** holds idle best (0.0 shakes, 0.4 drifts).
- Foot contact must stay soft (`mu 1.2 / kp 1e5 / kd 2.0`); the reference's stiff values
  destabilize this robot.

### WSL2 Gazebo GUI (gzclient)
- **gzclient is unreliable on this WSL2** — the world renders but live model/sensor updates
  don't sync (robot looks missing, lidar rays don't show, the Models tree is empty). Log
  spams `Dropped Escape call with ulEscapeCode` (WSL2 d3d12 GL passthrough dropping calls).
- The **simulation (gzserver) is fine** — RViz, SLAM, and `/odom/ground_truth` all confirm
  the robot is really there and moving.
- **Fix:** run with `gui:=false` and work in RViz. If you really need the Gazebo window,
  `LIBGL_ALWAYS_SOFTWARE=1 ros2 launch …` uses a more stable (slower) GL path.

### Leftover/zombie processes
- Failing to fully kill a previous launch leaves **duplicate controllers / a second Gazebo**,
  which fight over topics → robot freezes or behaves erratically.
- **TF_OLD_DATA flood at a *frozen* timestamp** = gzserver died, the sim clock stopped, and
  the surviving nodes keep re-stamping TF at that old time. Kill the launch and restart.
- Clean-slate kill:
  ```bash
  pkill -9 -f 'gzserver|gzclient|quadruped_controller_node|state_estimation_node|ekf_node|async_slam_toolbox|rviz2'
  ```
  Verify with `pgrep gzserver` (empty = clean) before relaunching.

### Nav2
- **cmd_vel wiring:** `controller_server → /cmd_vel_nav → velocity_smoother → /cmd_vel`, and
  CHAMP's controller subscribes to `/cmd_vel`, so a Nav2 goal drives the robot directly.
- **Planner found no path / "GridBased failed":** set `track_unknown_space: false` so Nav2
  plans into not-yet-mapped space, and align DWB velocity limits to the gait (0.3 / 0.5).
- **"No valid trajectories out of 419 / BaseObstacle hits obstacle"** = the robot's footprint
  is treated as in-collision in the tight apartment. Shrink `robot_radius` and
  `inflation_radius` (currently 0.16) so it fits doorways/clutter.
- SLAM + Nav2 run together — slam_toolbox provides the map and `map→odom`; Nav2 uses the
  navigation servers only (no map_server/AMCL).

---

## Key tuning knobs

| File | Knob | Note |
|---|---|---|
| `champbot_nodes/urdf/robot.urdf.xacro` | body size, leg/joint limits, foot contact, `lidar_visualize` | stability + rays toggle |
| `quadbot_config/config/gait/gait.yaml` | `nominal_height`, velocities, `knee_orientation` | gait |
| `quadbot_config/config/ros_control/ros_control.yaml` | effort PID (`p 80`) | tracking |
| `quadbot_config/config/autonomy/slam.yaml` | slam_toolbox params | mapping |
| `quadbot_config/config/autonomy/navigation.yaml` | DWB limits, `robot_radius`, `inflation_radius`, `track_unknown_space` | navigation |

## Known limitations

- Gazebo GUI (gzclient) unreliable on WSL2 → use `gui:=false` + RViz.
- The apartment world is tight; Nav2 needs the small footprint/inflation above to plan.
- Locomotion traction can be marginal (occasional walk-in-place); check
  `/odom/ground_truth` actually moves when driving.
