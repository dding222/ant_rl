# Ant Rough-Terrain PPO Project

## Project goal

Train the Isaac Lab Ant robot with the built-in RSL-RL PPO implementation.

The final policy must move forward stably under different friction conditions while traversing a fixed family of rough terrain made from square tiles with different heights.

## Fixed experiment requirements

- Robot: Isaac Lab's built-in Ant asset.
- Environment workflow: `ManagerBasedRLEnv`.
- RL library and algorithm: RSL-RL PPO only.
- Terrain type: square grid tiles with varying heights.
- Terrain family must remain fixed; do not mix stairs, slopes, waves, or other terrain families.
- Use a fixed terrain seed when exact geometry must be reproducible between runs.
- The only randomized physical parameter is friction coefficient `mu`.
- Do not randomize mass, center of mass, motor strength, joint properties, gravity, external forces, or pushes.
- The objective is forward locomotion, not velocity-command tracking in arbitrary directions.
- Keep the current compact package structure unless a structural change is required for execution.

## Current package structure

```text
ant/
├── AGENTS.md
├── pyproject.toml
├── scripts/
│   └── rsl_rl/
│       ├── cli_args.py
│       ├── play.py
│       └── train.py
└── source/
    └── ant/
        ├── __init__.py
        ├── ant_env_cfg.py
        ├── rewards.py
        └── agents/
            ├── __init__.py
            └── rsl_rl_ppo_cfg.py
```

Generated `.vscode` database files under `source/ant/.vscode/` are not part of the environment implementation.

## File responsibilities

- `source/ant/__init__.py`
  - Registers the Gymnasium task.
  - Registers only the RSL-RL agent configuration.
- `source/ant/ant_env_cfg.py`
  - Defines the scene, Ant asset, actions, observations, events, rewards, terminations, and simulation settings.
  - This is the main file for terrain and friction changes.
- `source/ant/rewards.py`
  - Contains all seven reward calculations used by `RewardsCfg`.
  - Reward equations can be modified here without editing Isaac Lab source files.
- `source/ant/agents/rsl_rl_ppo_cfg.py`
  - Defines the RSL-RL PPO runner, actor-critic, and PPO hyperparameters.
- `scripts/rsl_rl/train.py`
  - Starts PPO training, logging, checkpoint resume, and optional video capture.
- `scripts/rsl_rl/play.py`
  - Loads a checkpoint, runs inference, records optional video, and exports JIT/ONNX policies.
- `scripts/rsl_rl/cli_args.py`
  - Applies supported command-line overrides to the RSL-RL configuration.

## Current implementation state

The code is syntactically valid, and the initial rough-terrain and friction-randomization implementation is present.

Current environment behavior:

- Terrain uses deterministic `MeshRandomGridTerrainCfg` square tiles with seed `42`.
- Terrain friction is fixed at `1.0` with multiply combination mode.
- Robot friction is randomized once at startup for each environment.
- There is no terrain height scanner.
- The policy uses the original classic Ant observations.
- All active reward calculations are local in `source/ant/rewards.py` while retaining the original formulas and weights.
- The environment imports the shared classic humanoid MDP functions from Isaac Lab.
- The robot uses `isaaclab_assets.robots.ant.ANT_CFG`.
- The PPO configuration is still based on the built-in Ant example.

The following copied generic features were intentionally removed because this project only uses RSL-RL PPO with a single manager-based environment:

- RL-Games, SKRL, and SB3 registrations.
- DirectRL and multi-agent conversion paths.
- Distillation runner support.
- Published pretrained-checkpoint lookup.
- Ray-only and IO-descriptor options.
- Old RSL-RL compatibility branches.

## Known execution issues

Resolve these before attempting full training:

1. `play.py` does not import this project's `ant` package, so the custom task may not be registered during playback.
2. Install the project into the Isaac Lab environment with `python -m pip install -e .` or launch with `PYTHONPATH=$PWD/source`.
3. Full simulator smoke testing is still required. Python syntax compilation and Gym registration with `PYTHONPATH` have been verified.

## Remaining implementation work

Complete tasks in this order.

### 1. Finish task execution setup

- Import `ant` in `play.py` so Gym registration runs during playback.
- Install the project with `python -m pip install -e .` in the Isaac Lab environment.
- Start with a smoke test using 4 to 16 environments before using 4096 environments.

### 2. Review local reward behavior

- Modify reward equations only in `source/ant/rewards.py`.
- Confirm that progress reward measures forward XY displacement as intended.
- Compare each `Episode_Reward/*` term before changing weights.
- Check for policies that exploit the alive reward without moving.
- Check whether energy and action penalties overwhelm progress on rough terrain.

### 3. Decide whether terrain perception is allowed

This is an explicit design choice, not an automatic addition.

- Blind locomotion: keep only proprioceptive observations.
- Terrain-aware locomotion: add a `RayCasterCfg` height scanner and a height-scan observation.

Do not add the height scanner until this choice is made. If tile height differences are large, blind locomotion will be significantly harder.

### 4. Validate termination behavior on rough terrain

- Check whether the fixed minimum torso height of `0.31` causes false termination on low tiles or gaps.
- Tune termination settings only after observing rollout metrics and videos.

### 5. Evaluate friction robustness

Use separate training and evaluation checks:

- Report performance across several fixed friction values spanning the training range.
- Include at least one friction value near each end of the range.
- Keep the terrain seed and geometry fixed while sweeping friction, so friction is the only changing physical parameter.
- Track forward distance or average forward velocity, fall rate, and episode length.
- Also test one or more friction values just outside the training range if extrapolation robustness matters.

## Verification checklist

Before a long PPO run, verify all of the following:

- The custom task ID resolves without overwriting the built-in Ant task.
- `gym.make()` succeeds with 4 environments.
- Generated terrain contains only square height-varying tiles.
- Repeating a run with the same terrain seed produces the same geometry.
- Ant robots spawn on stable platforms and do not intersect tiles.
- Different environments receive different friction values.
- No physical property other than friction changes.
- Observations and actions contain finite values after reset and several steps.
- Episodes terminate correctly when the Ant falls.
- One short PPO iteration completes and writes a checkpoint.
- `play.py` can load the checkpoint and run inference.

## Working rules for future changes

- Preserve the current compact structure.
- Add only functionality required by the experiment.
- Do not reintroduce other RL libraries, multi-agent support, distillation, or unrelated domain randomization.
- Do not modify PPO hyperparameters until the environment can run and produce valid rollouts.
- Keep training and evaluation configuration changes reproducible and recorded.
- Run syntax checks after edits and simulator smoke tests when Isaac Lab is available.
