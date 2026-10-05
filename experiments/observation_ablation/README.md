# Terrain Observation Ablation: HeightScan vs DepthCam

Compare HeightScan and DepthCam terrain representations for Ant locomotion using the Team1 terrain/environment and shared PPO, seeds, and training budget. The comparison is repeated under two reward settings: Stock Reward and Contact + Modified Reward.

## Research Question

Under the same terrain, PPO, training budget, and seeds, which terrain representation—HeightScan or DepthCam—is more effective for Ant locomotion?

This question is evaluated separately in:

1. **Stock reward condition** — HeightScan vs DepthCam.
2. **Contact + Modified reward condition** — HeightScan + Contact vs DepthCam + Contact.

## Experiment Overview

| Stage | HeightScan arm | DepthCam arm | Reward |
|---|---|---|---|
| Stage 1 | HeightScan | DepthCam | Stock Isaac-Ant reward |
| Stage 2 | HeightScan + Contact | DepthCam + Contact | Modified reward |

Stage 1 provides the baseline condition for comparing terrain representation. Stage 2 repeats that comparison with the same explicit Contact observation and the same modified reward applied to both arms. Within each stage, the intended comparison variable is terrain representation; sensor-specific encoders may differ.

> **Comparison rule:** Because Stage 1 and Stage 2 use different reward definitions and scales, their total returns should not be interpreted as a direct performance delta. Compare HeightScan vs DepthCam **within the same stage**, after verifying the shared protocol. Cross-stage physical metrics may be inspected descriptively, but these runs do not isolate the individual effects of Contact or reward changes.

## Common Training Protocol

The following protocol applies to both stages and is required for the pending DepthCam arms.

| Item | Value |
|---|---|
| Training environment | Team1 rough terrain |
| Terrain types | 5 types, equal proportion 0.2 |
| Terrain layout | 20 × 10 patches |
| Patch size | 10 × 10 m |
| Training seed | 42 |
| Terrain seed | 42 |
| Num environments | 4096 |
| Rollout steps/env/iteration | 32 |
| Iterations | 1000 |
| Total transitions | 131,072,000 |
| Physics dt | 1/120 s |
| Control dt | 1/60 s |
| Episode length | 16 s / 960 steps |
| Action | 8-D joint effort |
| Action scale | 7.5 |
| Actor/Critic post-feature MLP | [400, 200, 100], ELU |
| Resume | No |

Native Team1 root reset is preserved, with joint position ±0.2 and joint velocity ±0.1. Termination is timeout or `body_z_down(pi/2)`; no map-boundary or torso-height termination is added.

PPO is identical across the completed HeightScan arms: learning rate 0.0005 (adaptive), gamma 0.99, lambda 0.95, clip 0.2, entropy coefficient 0, value-loss coefficient 1, clipped value loss, 5 epochs, 4 minibatches, desired KL 0.01, and max gradient norm 1. Initial Gaussian noise std is 1; actor/critic observation normalization is disabled.

Checkpoint selection is fixed before training: **highest logged completed-episode training mean return**, using that stage's training reward. The selected checkpoint and last-iteration checkpoint are both retained.

## Common Evaluation Protocol

| Item | Value |
|---|---|
| Evaluation environment | Same Team1 terrain setup |
| Evaluation seed | 24 |
| Num envs | 100 |
| Policy action | Deterministic mean action |
| Episode policy | First episode only |
| Evaluation reward | Same as the corresponding stage's training reward |

Both completed HeightScan evaluations finished 100/100 first episodes and used the same terrain mesh and assignment. Terminal rewards are included; post-reset rewards are excluded. Displacement is terminal minus initial world-X. All reported standard deviations are **population std** (`ddof=0`). Reward decomposition accumulates actual weighted episode contributions, including control dt, and is checked against official episode return.

## Observation Design

### HeightScan

| Item | Specification |
|---|---|
| Proprio | 59-D native Team1 interface |
| HeightScan | 63-D |
| Stage 1 actor/critic input | 122-D |
| Attachment / alignment | Torso-attached / yaw-aligned |
| Ray pattern | 9 × 7 downward rays |
| Spacing | 0.2 m |
| Offset | `(0.8, 0, 20)` |
| Height calculation | `sensor_z - hit_z - 0.5` |
| Scale / clipping | 1 / `[-1, 1]` |
| CNN | None |
| Empirical observation normalization | None |

### HeightScan + Contact

Stage 2 concatenates **59-D proprio + 63-D HeightScan + 4-D Contact = 126-D actor/critic input**. HeightScan preprocessing is unchanged.

Contact order:

1. `front_left_foot`
2. `front_right_foot`
3. `left_back_foot`
4. `right_back_foot`

The explicit Contact observation uses current **world-frame net-force norm > 1 N**, history length **0**, and **float32 binary** encoding. No additional clipping or normalization is applied. See the [shared Contact definition](shared/contact_observation.json).

HeightScan and explicit Contact integration are adapted from the existing IsaacLab_RS HeightScan+Contact implementation. Observation-side Contact and reward-side foot contact use different definitions; the reward-side definition is documented in Stage 2 below.

### DepthCam

- Terrain representation: depth camera + CNN.
- Proprio interface: common 59-D Team1 interface.
- Stage 2 Contact: the same shared 4-D definition.
- Detailed runtime dimensions and results: **TBD**.

No dummy features are added to match input dimensions. Sensor encoder parameters and resulting feature dimensions may differ between representations.

## Stage 1 — Stock Reward Observation Comparison

This condition fixes the reward to the stock Isaac-Ant objective, avoiding additional task-specific reward shaping and weight tuning so the comparison focuses on terrain representation.

### Stock Reward

| Component | Weight |
|---|---:|
| progress | 1.0 |
| alive | 0.5 |
| upright | 0.1 |
| move_to_target | 0.5 |
| action_l2 | -0.005 |
| energy | -0.05 |
| joint_pos_limits | -0.1 |

The canonical Isaac-Ant stock reward functions and weights are used unchanged for both training and evaluation. Team1 custom reward terms are inactive.

### Stage 1 Results

| Metric | HeightScan + Stock | DepthCam + Stock |
|---|---:|---:|
| Return mean ± std | 61.3354 ± 31.2305 | TBD |
| Displacement mean ± std | 60.5140 ± 29.1880 m | TBD |
| Episode duration mean ± std | 12.1947 ± 5.5930 s | TBD |
| Mean forward velocity | 4.4506 m/s | TBD |
| Fall | 41/100 | TBD |
| Timeout | 59/100 | TBD |
| ≥2 m | 87/100 | TBD |
| ≥5 m | 87/100 | TBD |
| ≥10 m | 86/100 | TBD |
| Out-of-terrain-X | 28/100 | TBD |

Return min/max: **-18.0859 / 98.2898**.

### Stage 1 Reward Decomposition

Values are mean ± population std.

| Component | HeightScan + Stock | DepthCam + Stock |
|---|---:|---:|
| progress | 60.4711 ± 29.1633 | TBD |
| alive | 6.0939 ± 2.7998 | TBD |
| upright | 1.0924 ± 0.5508 | TBD |
| move_to_target | 5.3633 ± 2.6815 | TBD |
| action_l2 | -1.2979 ± 8.7617 | TBD |
| energy | -7.2101 ± 3.5063 | TBD |
| joint_pos_limits | -3.1773 ± 1.6496 | TBD |
| total | 61.3354 ± 31.2305 | TBD |

## Stage 2 — Contact + Modified Reward Comparison

To discourage locomotion dominated by repeated jumping/hopping and to encourage more controlled ground interaction, the modified reward extends the objective to include ground contact, foot slip, joint motion, and control effort.

This describes the shaping objective, not a demonstrated effect of any individual term. Both arms are required to use the same Contact observation and the same Team1 v3_depth modified reward for **training and evaluation**; terrain representation remains the intended within-stage comparison variable.

### Modified Reward

| Component | Weight |
|---|---:|
| progress | 2.5 |
| alive | 0.5 |
| upright | 0.05 |
| move_to_target | 1.5 |
| foot_contact | 1.0 |
| action_l2 | -0.005 |
| energy | -0.15 |
| joint_velocity | -0.001 |
| joint_pos_limits | -0.5 |
| foot_slip | -0.07 |

Relative to stock, the objective increases progress and target-direction weights, strengthens energy and joint-limit penalties, and adds foot-contact reward, joint-velocity penalty, and foot-slip penalty. The upright weight is reduced. Individual-term causal effects are not isolated by these runs.

The implementation reuses Team1 v3_depth `ant.rewards.TotalReward`; its component weights were verified against the saved training configuration. It does not use the play-time evaluation reward.

### Shared Contact Condition

Both Stage 2 arms use the same four feet, **world-frame net-force norm > 1 N**, **binary float32**, and **no history** for the explicit observation.

> **Separate reward-side definition:** Foot-contact reward and foot-slip penalty use the **3-frame maximum vertical force > 5 N**. The contact bonus requires at least two contacting feet; slip penalizes the XY speed of contacted feet. This differs from the observation-side norm threshold and history semantics.

### Stage 2 Results

| Metric | HeightScan + Contact + Modified | DepthCam + Contact + Modified |
|---|---:|---:|
| Return mean ± std | 134.8413 ± 68.0187 | TBD |
| Displacement mean ± std | 56.5627 ± 28.3639 m | TBD |
| Episode duration mean ± std | 12.1187 ± 5.6815 s | TBD |
| Mean forward velocity | 4.0718 m/s | TBD |
| Fall | 43/100 | TBD |
| Timeout | 57/100 | TBD |
| ≥2 m | 86/100 | TBD |
| ≥5 m | 86/100 | TBD |
| ≥10 m | 84/100 | TBD |
| Out-of-terrain-X | 26/100 | TBD |

Return min/max: **-0.2848 / 220.2166**.

### Stage 2 Reward Decomposition

Values are mean ± population std. Direct total-return comparison requires the DepthCam arm to use the identical modified reward.

| Component | HeightScan + Contact + Modified | DepthCam + Contact + Modified |
|---|---:|---:|
| progress | 141.3719 ± 70.9343 | TBD |
| alive | 6.0558 ± 2.8440 | TBD |
| upright | 0.5720 ± 0.2875 | TBD |
| move_to_target | 16.4496 ± 8.0588 | TBD |
| foot_contact | 2.5842 ± 1.3074 | TBD |
| action_l2 | -0.1891 ± 0.3820 | TBD |
| energy | -19.2751 ± 9.6769 | TBD |
| joint_velocity | -2.6589 ± 1.3529 | TBD |
| joint_pos_limits | -8.5355 ± 5.0240 | TBD |
| foot_slip | -1.5334 ± 0.7835 | TBD |
| total | 134.8413 ± 68.0187 | TBD |

## Terrain-Boundary Caveat

> Displacement and progress can include motion beyond the generated terrain bounds, because the Team1 environment does not terminate episodes at the map boundary. Reported displacement is therefore not entirely rough-terrain locomotion distance.

| HeightScan experiment | Terminal world-X outside terrain bounds |
|---|---:|
| Stage 1: Stock | 28/100 |
| Stage 2: Contact + Modified | 26/100 |

The generated terrain X bounds are `[-102, 102]` m. Single-seed measurements do not establish general statistical significance; PPO training remains stochastic.

## Protocols and Artifacts

| Stage | Shared protocol | HeightScan results |
|---|---|---|
| Stage 1 | [Stock protocol](protocol.json) | [Manifest and compact results](heightscan_4096x32x1000/manifest.json) |
| Stage 2 | [Contact + Modified protocol](shared/stage2_contact_modified_protocol.json) | [Manifest and compact results](heightscan_contact_modified_4096x32x1000/manifest.json) |

The [previous exploratory HeightScan run](heightscan/manifest.json) used 2048 × 32 × 10000 and is preserved as a reference. It is outside the canonical comparison budget above.

## Current Status

| Experiment | Status |
|---|---|
| HeightScan + Stock | Complete |
| DepthCam + Stock | Pending |
| HeightScan + Contact + Modified | Complete |
| DepthCam + Contact + Modified | Pending |

DepthCam results will be added once the corresponding runs are completed under the shared protocol.
