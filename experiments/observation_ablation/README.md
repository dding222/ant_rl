# Observation Ablation

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

Canonical retraining in progress. Base and DepthCam: TBD.
