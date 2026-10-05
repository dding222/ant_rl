# Observation Ablation

## Research question

동일한 Team1 training/evaluation environment와 stock Isaac-Ant reward에서
Base / HeightScan / DepthCam terrain observation representation의 성능을 비교한다.
이번 작업에서는 HeightScan만 학습한다. 기존 custom-reward depth 결과는 이 표의 비교 결과로 사용하지 않는다.

## Controlled variables

| Variable | Base | HeightScan | DepthCam |
|---|---|---|---|
| Training environment | same (pending) | Team1 AntEnvCfg | same (pending) |
| Evaluation environment | same (pending) | Team1 AntEnvCfg | same (pending) |
| Terrain | same (pending) | 20×10 patches, 10×10 m; stairs/inverse stairs/slope/inverse slope/boxes, each 0.2 | same (pending) |
| Reward | stock 7-term (pending) | stock 7-term | stock 7-term (pending) |
| Reward weights | same (pending) | canonical stock | same (pending) |
| PPO | same (pending) | Team1 PPO, see protocol.json | same (pending) |
| Training seed | 42 (pending) | 42 | 42 (pending) |
| Terrain seed | 42 (pending) | 42, independent of env seed | 42 (pending) |
| Termination | same (pending) | timeout; body_z_down(pi/2) | same (pending) |
| Action | same (pending) | 8 joint efforts, scale 7.5, no clipping | same (pending) |
| Terrain perception | None (pending) | 63-D HeightScan | DepthCam (pending) |

Physics dt=1/120 s; decimation=2; control dt=1/60 s; episode=16 s (960 steps).
Reset preserves native root pose/velocity and joint offsets (-0.2,0.2)/(-0.1,0.1).
Robot friction is drawn once at startup: static 0.3–1.0, dynamic=0.8×static.
Original Ant-rl-v0, its custom reward, checkpoints and evaluation artifacts are preserved.

## Stock reward

Canonical source: `IsaacLab_RS/source/isaaclab_tasks/isaaclab_tasks/manager_based/classic/ant/ant_env_cfg.py:RewardsCfg`.
The new config imports this actual stock class; it does not reproduce TotalReward.
Training and evaluation use the same class and weights.

| Term | Weight |
|---|---:|
| progress | 1.0 |
| alive | 0.5 |
| upright | 0.1 |
| move_to_target | 0.5 |
| action_l2 | -0.005 |
| energy | -0.05 |
| joint_pos_limits | -0.1 |

Target=(1000,0,0); upright threshold=0.93; heading threshold=0.8;
energy/limits gear_ratio=15 for all joints; limits threshold=0.99.
No foot_contact, joint_velocity or foot_slip reward.

## Observation variants

Base: native Team1 proprio only (59-D; future variant).

HeightScan: native Team1 proprio + 63-D ray-based height scan = 122-D actor and critic.
HeightScan integration is adapted from the IsaacLab_RS Assignment 1 HeightScan implementation.
Torso-attached yaw-aligned grid: X=0..1.6, Y=-0.6..0.6 m, spacing=0.2 m,
9×7 downward rays, xy ordering (X varies fastest), sensor offset=(0.8,0,20), max_distance=1e6 m.
Native height_scan computes torso/sensor pose Z minus hit Z minus 0.5, then clips to [-1,1].
Scale=1, no empirical normalization or corruption. Scan follows previous actions in the concatenation.
No added contact observation or CNN. Native 24-D incoming foot wrench is retained as part of the shared 59-D proprio.

DepthCam: native proprio + depth image → CNN embedding (future stock-reward training).
Historical depth embedding=64-D (123-D actor input); it must adopt this common protocol before comparison.

## Training protocol

Seed=42, terrain seed=42, 2048 envs, 10000 iterations, rollout=32 steps/env, checkpoint interval=50.
MLP actor/critic=[400,200,100], ELU, Gaussian actions, scalar per-action std initialized to 1.0,
actor/critic normalization disabled. Team1 PPO: 5 epochs, 4 minibatches, learning_rate=0.0005,
adaptive schedule, gamma=0.99, lambda=0.95, clip=0.2, entropy=0, desired KL=0.01,
value loss coefficient=1, clipped value loss, max gradient norm=1.
Fresh training; no checkpoint resume. Existing v3_depth saved env config uses 2048 envs;
its saved agent config describes 9750 resumed iterations after model_250, and model_9999 exists.
These provide the historical 10000-iteration budget reference.

Checkpoint selection is fixed before training: `best_model.pt`, highest logged training completed-episode
mean return, following the historical Team1 BestModelRunner. Base and DepthCam must use the same rule.
Evaluation results never influence selection. The selected checkpoint and hash will be recorded.

## Evaluation protocol

Same Team1 environment and stock reward; seed=24; terrain generator seed=42; num_envs=100;
deterministic mean actions; first episode only; maximum 960 control steps.
Capture terminal robot state before auto-reset. Include terminal reward; exclude subsequent reset episodes.
Fall=body_z_down (orientation > pi/2), timeout=time_out, other=neither. Fall/timeout flags can overlap;
overlap count is reported. No minimum torso height termination.
Report population std (ddof=0), displacement at terminal state, and step-average world +X velocity.
Distance thresholds use terminal net forward displacement, not maximum excursion.
Terrain mesh SHA256 and row/column/origin assignment are saved for future parity checks.

## Results

Pending runtime validation, training and evaluation. TBD is not a measured zero.

| Metric | Base | HeightScan | DepthCam |
|---|---:|---:|---:|
| Return mean ± population std | TBD | TBD | TBD |
| Displacement mean ± population std | TBD | TBD | TBD |
| Fall | TBD | TBD | TBD |
| Timeout | TBD | TBD | TBD |

## Reward decomposition

Actual RewardManager contributions are `_step_reward * step_dt` (raw × weight × dt).
Seven components and official total are accumulated in float64 through the terminal step;
episode residual tolerance=1e-3, per-step tolerance=1e-5. Component statistics are TBD.

## Reproduce and extend

`scripts/observation_ablation.py` has smoke/train/evaluate modes and refuses existing output directories.
Use the commands in `heightscan/commands.log` with the documented existing Python environment.
Run smoke before training. `shared/source_parity.json` freezes core config hashes;
future Base/DepthCam implementations must match them and the evaluation terrain mesh/assignment.
Use `AblationBaseCfg` as the common foundation, replacing sensor/observation and the sensor encoder only.
No Base or DepthCam training is part of this change.

Checkpoints and training TensorBoard logs remain under ignored `logs/rsl_rl/observation_ablation/`.
Compact config, CSV and JSON results are tracked; checkpoints, videos and step-level CSV are excluded.

## Caveats

HeightScan has 63 terrain features versus the historical 64-D depth embedding; no dummy feature is added.
MLP input size and sensor extractor parameter counts therefore differ. CNN sensor encoders are permitted
for DepthCam only. One training seed does not establish general statistical significance; PPO is stochastic
and GPU computation is not guaranteed bitwise deterministic. Canonical helper source hashes are recorded
because this repository relies on the external IsaacLab_RS checkout.

All variants use the same environment, stock 7-term reward, PPO configuration, seeds, and evaluation protocol;
only the terrain observation representation differs. This is the required protocol, not a claim that the
pending Base/DepthCam runs have already satisfied it.
