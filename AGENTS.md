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
├── scripts/
│   └── rsl_rl/
│       ├── cli_args.py
│       ├── play.py
│       └── train.py
└── source/
    └── ant/
        ├── __init__.py
        ├── ant_env_cfg.py
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
- `source/ant/agents/rsl_rl_ppo_cfg.py`
  - Defines the RSL-RL PPO runner, actor-critic, and PPO hyperparameters.
- `scripts/rsl_rl/train.py`
  - Starts PPO training, logging, checkpoint resume, and optional video capture.
- `scripts/rsl_rl/play.py`
  - Loads a checkpoint, runs inference, records optional video, and exports JIT/ONNX policies.
- `scripts/rsl_rl/cli_args.py`
  - Applies supported command-line overrides to the RSL-RL configuration.

## Current implementation state

The code is syntactically valid, but the requested experiment is not implemented yet.

Current environment behavior:

- Terrain is still `terrain_type="plane"`.
- Terrain static and dynamic friction are fixed at `1.0`.
- There is no friction randomization event.
- There is no terrain height scanner.
- The policy uses the original classic Ant observations and rewards.
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

1. The registered task ID is still `Isaac-Ant-v0`, which conflicts with Isaac Lab's built-in task. Rename it to a unique ID such as `Isaac-Ant-Rough-Friction-v0`.
2. `train.py` and `play.py` import `isaaclab_tasks` but do not import this project's `ant` package. Add `import ant` after Isaac Sim has launched and before Hydra resolves the task configuration.
3. The `source` directory must be importable. Either install the project as a package or launch with `PYTHONPATH=$PWD/source` from the project root.
4. Full runtime validation has not been performed in the current shell because Isaac Lab is not importable here. Only Python syntax compilation has been verified.

## Required implementation work

Complete tasks in this order.

### 1. Make the custom task runnable

- Rename the Gym task ID to `Isaac-Ant-Rough-Friction-v0`.
- Import `ant` in both RSL-RL scripts so that Gym registration runs.
- Confirm that the task appears in the Gym registry.
- Start with a small smoke test such as 4 to 16 environments before using 4096 environments.

### 2. Replace the plane with fixed square-tile rough terrain

Implement the terrain directly in `ant_env_cfg.py`; a separate terrain file is not required.

- Import `TerrainGeneratorCfg` and `isaaclab.terrains as terrain_gen`.
- Set `terrain_type="generator"`.
- Use only `terrain_gen.MeshRandomGridTerrainCfg` with `proportion=1.0`.
- Configure tile width and tile height range explicitly.
- Keep a flat spawn platform wide enough for the Ant initial pose.
- Set a deterministic terrain seed.
- Keep terrain curriculum disabled unless the experiment definition is changed later.
- Use terrain material friction `1.0` with `friction_combine_mode="multiply"` so the robot material controls the effective coefficient.

### 3. Add friction randomization

Add a material event to `EventCfg` in `ant_env_cfg.py`.

Initial implementation may use `mdp.randomize_rigid_body_material` in `startup` mode with a finite number of material buckets. Keep restitution fixed at zero.

Important experimental detail:

- Isaac Lab's built-in material randomizer samples static and dynamic friction separately and may assign different material buckets to different collision shapes.
- If the experiment requires exactly one scalar `mu` per environment with `static_friction == dynamic_friction == mu` on every Ant collision shape, implement a small custom event instead of relying on the built-in randomizer.
- Do not add any other domain-randomization event.

The friction range is not decided yet. Treat it as an experiment parameter that must be chosen deliberately before long training runs.

### 4. Decide whether terrain perception is allowed

This is an explicit design choice, not an automatic addition.

- Blind locomotion: keep only proprioceptive observations.
- Terrain-aware locomotion: add a `RayCasterCfg` height scanner and a height-scan observation.

Do not add the height scanner until this choice is made. If tile height differences are large, blind locomotion will be significantly harder.

### 5. Validate reward and termination behavior on rough terrain

- Check whether the fixed minimum torso height of `0.31` causes false termination on low tiles or gaps.
- Confirm that progress reward measures forward XY displacement as intended.
- Check for policies that exploit the alive reward without moving.
- Check whether energy and action penalties overwhelm progress on rough terrain.
- Tune rewards only after observing rollout metrics and videos; do not redesign them speculatively.

### 6. Evaluate friction robustness

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
