# Observation Ablation

## Stage 1 — Stock Reward

## Research question

Compare Base / HeightScan / DepthCam terrain representation under identical Team1 training/evaluation environments, stock rewards, PPO, seeds and training budget.

## Canonical controlled protocol

| Variable | Base | HeightScan | DepthCam |
|---|---|---|---|
| Num envs | 4096 required; pending | 4096 | 4096 required; pending |
| Steps/env/iteration | 32 | 32 | 32 |
| Iterations | 1000 | 1000 | 1000 |
| Total transitions | 131,072,000 | 131,072,000 | 131,072,000 |
| Training seed / terrain seed | 42 / 42 | 42 / 42 | 42 / 42 |
| Reward | stock 7-term | stock 7-term | stock 7-term |
| Environment / action / reset / termination | same required | Team1 | same required |
| PPO / actor / critic | same required | [400,200,100] ELU | same required; sensor encoder permitted |
| Evaluation seed / num envs | 24 / 100 | 24 / 100 | 24 / 100 |
| Terrain observation | None | 63-D HeightScan | depth image → CNN embedding |

Base/DepthCam measurements remain TBD until their manifests confirm every shared field and checkpoint-selection rule. Historical Team1 custom-reward/depth results are not controlled-comparison results.

## Stock reward

| Term | Weight |
|---|---:|
| progress | 1.0 |
| alive | 0.5 |
| upright | 0.1 |
| move_to_target | 0.5 |
| action_l2 | -0.005 |
| energy | -0.05 |
| joint_pos_limits | -0.1 |

Canonical IsaacLab_RS Ant reward functions are reused directly. Team1 TotalReward and foot_contact / joint_velocity / foot_slip rewards are inactive.

## Environment and observation

Team1 five equal-proportion rough terrains, 20×10 patches of 10×10 m, terrain seed42. Physics dt=1/120 s, decimation2, control dt=1/60 s. Eight joint-effort actions, scale7.5. Native root reset, joint position ±0.2 / velocity ±0.1. Timeout16 s (960 steps) or body_z_down(pi/2); no boundary/torso-height termination.

HeightScan integration is adapted from the IsaacLab_RS Assignment 1 HeightScan implementation. Native proprio59 + scan63 = actor/critic122. Torso attached, yaw aligned, offset(0.8,0,20), 9×7 downward rays spaced0.2 m; sensor-Z − hit-Z −0.5, scale1, clip[-1,1]. No explicit Contact feature, CNN, dummy feature or empirical observation normalization. Existing incoming foot wrench is retained.

## Training protocol

Fresh seed42 initialization; resume=false, load_run=null, load_checkpoint=null. New driver: `scripts/observation_ablation_budget.py`; derived runner: `source/ant/agents/ablation_budget_ppo_cfg.py`. Historical task/config and driver remain intact. Only num_envs/max_iterations budget changes; rollout32 remains unchanged. The canonical protocol is [protocol.json](protocol.json).

PPO unchanged: lr0.0005 adaptive, gamma0.99, lambda0.95, clip0.2, entropy0, value loss1, clipped value loss, 5 epochs / 4 minibatches, desired KL0.01, grad norm1. Actor/critic [400,200,100] ELU; init Gaussian noise std1; actor/critic observation normalization false. Save interval50. Checkpoint selection, fixed before training: highest logged completed-episode training mean return. Final checkpoint is also retained.

## Evaluation protocol

Team1 environment, seed24, 100 envs, deterministic mean action, first episode only, stock7 terms; include terminal rewards and exclude subsequent reset episodes. Population standard deviation. Forward displacement is terminal minus initial world-X. Reward components accumulate actual RewardManager contributions (raw×weight×control_dt); residuals checked against official return. Terrain mesh and assignment must match the previous run.

## Artifact policy and caveats

Canonical HeightScan artifacts: [heightscan_4096x32x1000/manifest.json](heightscan_4096x32x1000/manifest.json). Previous exploratory run: [heightscan/manifest.json](heightscan/manifest.json), 2048×32×10000; preserved byte-for-byte. Large raw logs/intermediate checkpoints remain in ignored logs; compact JSON/CSV and selected/final checkpoints (<100 MiB each) are committed.

HeightScan feature count differs from depth embedding dimensions and sensor extractors have different parameter counts. Single-seed results do not establish general statistical significance; PPO remains stochastic. All shared settings must match for direct comparison.

## Results

| Metric | Base | HeightScan | DepthCam |
|---|---:|---:|---:|
| Return | TBD | 61.3354 ± 31.2305 | TBD |
| Displacement (m) | TBD | 60.5140 ± 29.1880 | TBD |
| Duration (s) | TBD | 12.1947 ± 5.5930 | TBD |
| Mean vx (m/s) | TBD | 4.4506 ± 1.5331 | TBD |
| Fall | TBD | 41/100 | TBD |
| Timeout | TBD | 59/100 | TBD |
| Other | TBD | 0/100 | TBD |
| >=5m | TBD | 87/100 | TBD |
| Out-of-terrain-X | TBD | 28/100 | TBD |

## Stock reward decomposition

| Component | HeightScan mean ± population std |
|---|---:|
| progress | 60.4711 ± 29.1633 |
| alive | 6.0939 ± 2.7998 |
| upright | 1.0924 ± 0.5508 |
| move_to_target | 5.3633 ± 2.6815 |
| action_l2 | -1.2979 ± 8.7617 |
| energy | -7.2101 ± 3.5063 |
| joint_pos_limits | -3.1773 ± 1.6496 |
| total | 61.3354 ± 31.2305 |

## Training-budget sensitivity (diagnostic only)

| Metric | Previous: 2048×32×10000 | Canonical: 4096×32×1000 |
|---|---:|---:|
| Transitions | 655,360,000 | 131,072,000 |
| Selected saved iteration | 4911 | 804 |
| Return | 63.3921 ± 29.9427 | 61.3354 ± 31.2305 |
| Displacement | 62.8269 ± 29.5298 | 60.5140 ± 29.1880 |
| Fall | 35% | 41% |
| Timeout | 65% | 59% |
| >=5m | 86% | 87% |
| Out-of-terrain-X | 27% | 28% |

The new run has five times fewer transitions. This is training-budget sensitivity, not an isolated environment-count effect or the observation-ablation result.

Terrain boundary diagnostic: 28/100 terminal world-X positions outside [-102, 102] m. No boundary or torso-height termination exists; displacement/return can include unsupported movement beyond the map. Raw ray misses retain the canonical clipping to -1.

## Stage 2 — Contact + Modified Reward

This is the HeightScan terrain-representation arm under the Contact + Modified Reward condition. DepthCam is TBD until the teammate arm is merged; this work trains only HeightScan.

Both arms must use the same Team1 environment, explicit 4-D contact definition, Team1 v3_depth modified reward for both training and evaluation, PPO, post-feature [400,200,100] ELU actor/critic, 4096×32×1000 budget (131,072,000 transitions), training/terrain seed42, checkpoint-selection rule, and seed24/100-env deterministic first-episode evaluation. The intended comparison variable is HeightScan vs DepthCam terrain representation. Sensor-specific depth encoders and resulting input dimensions may differ.

Shared machine-readable protocol: [shared/stage2_contact_modified_protocol.json](shared/stage2_contact_modified_protocol.json). Contact spec: [shared/contact_observation.json](shared/contact_observation.json). Result manifest: [heightscan_contact_modified_4096x32x1000/manifest.json](heightscan_contact_modified_4096x32x1000/manifest.json).

HeightScan and contact observation are adapted from the existing IsaacLab_RS Assignment 1 HeightScan+Contact implementation. Observation order is Team1 proprio59, unchanged scan63, then contact4 (126-D). No CNN, dummy feature or empirical normalization. Observation contact uses current net-force norm >1N, ordered front_left_foot/front_right_foot/left_back_foot/right_back_foot, float32 binary states, history0, no clipping or scaling change.

Modified reward directly reuses Team1 v3_depth `ant.rewards.TotalReward`, manager term `total_reward` weight1. Internal weights: progress2.5, alive0.5, upright0.05, move_to_target1.5, foot_contact1, action_l2−0.005, energy−0.15, joint_velocity−0.001, joint_pos_limits−0.5, foot_slip−0.07. Reward-side contact separately uses the 3-frame maximum vertical force >5N; contact bonus requires at least two feet; slip penalizes contacted-feet XY speed. These semantics differ from observation-side contact.

Fresh initialization: resume=false, load_run/load_checkpoint=null. PPO and action/reset/termination/terrain are unchanged from Stage 1. Selection rule fixed before training: highest logged completed-episode mean training return under the modified reward. The best checkpoint and last-iteration checkpoint are retained. Single-seed results do not establish general statistical significance.

Decomposition observes the actual TotalReward function's weighted components without copying its calculations or changing its implementation. Each contribution is weighted_component × manager_weight(1) × control_dt. TotalReward episode_sums already apply dt once; dt is not applied twice. Terminal contributions are included, reset episodes excluded. Direct Stage 2 total-return comparison requires the DepthCam arm to use the identical modified reward.

| Metric | HeightScan + Contact + Modified | DepthCam + Contact + Modified |
|---|---:|---:|
| Return | 134.8413 ± 68.0187 | TBD |
| Displacement (m) | 56.5627 ± 28.3639 | TBD |
| Duration (s) | 12.1187 ± 5.6815 | TBD |
| Mean vx (m/s) | 4.0718 ± 1.5654 | TBD |
| Fall | 43/100 | TBD |
| Timeout | 57/100 | TBD |
| Other | 0/100 | TBD |
| >=5m | 86/100 | TBD |
| Out-of-terrain-X | 26/100 | TBD |

### Stage 2 reward decomposition

| Component | HeightScan+Contact mean ± population std | DepthCam+Contact |
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

Residuals: step max=9e-08, episode max=4.57e-06, episode mean=9.97e-07.

Boundary diagnostic: 26/100 terminal world-X positions outside [-102,102] m. Native Team1 has no boundary or torso-height termination, so displacement/return can include unsupported movement beyond the terrain mesh.

Stage 1 and Stage 2 have different reward definitions. Do not subtract total returns to claim improvement. Physical metrics (displacement, duration, fall, timeout and reach ratios) may be inspected as descriptive diagnostics.
