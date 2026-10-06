# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Script to play one episode from a checkpoint if an RL agent from RSL-RL."""

"""Launch Isaac Sim Simulator first."""

import argparse
import sys
from pathlib import Path

from isaaclab.app import AppLauncher

# local imports
import cli_args  # isort: skip
import ant  # noqa: F401

# add argparse arguments
parser = argparse.ArgumentParser(description="Play one episode with an RL agent from RSL-RL.")
parser.add_argument("--video", action="store_true", default=False, help="Record videos during training.")
parser.add_argument("--video_length", type=int, default=200, help="Length of the recorded video (in steps).")
parser.add_argument(
    "--disable_fabric", action="store_true", default=False, help="Disable fabric and use USD I/O operations."
)
parser.add_argument(
    "--num_envs", "--num_env", dest="num_envs", type=int, default=None, help="Number of environments to simulate."
)
parser.add_argument("--task", type=str, default=None, help="Name of the task.")
parser.add_argument(
    "--agent", type=str, default="rsl_rl_cfg_entry_point", help="Name of the RL agent configuration entry point."
)
parser.add_argument("--seed", type=int, default=None, help="Seed used for the environment")
parser.add_argument(
    "--use_pretrained_checkpoint",
    action="store_true",
    help="Use the pre-trained checkpoint from Nucleus.",
)
parser.add_argument("--real-time", action="store_true", default=False, help="Run in real-time, if possible.")
# append RSL-RL cli arguments
cli_args.add_rsl_rl_args(parser)
# append AppLauncher cli args
AppLauncher.add_app_launcher_args(parser)
# parse the arguments
args_cli, hydra_args = parser.parse_known_args()
# depth observations always require camera rendering
args_cli.enable_cameras = True

# clear out sys.argv for Hydra
sys.argv = [sys.argv[0]] + hydra_args

# launch omniverse app
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest everything follows."""

import gymnasium as gym
import os
import time
import torch

from rsl_rl.runners import DistillationRunner, OnPolicyRunner

from isaaclab.envs import (
    DirectMARLEnv,
    DirectMARLEnvCfg,
    DirectRLEnvCfg,
    ManagerBasedRLEnvCfg,
    multi_agent_to_single_agent,
)
from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.managers import RewardTermCfg as RewTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.sensors import RayCasterCfg, patterns
from isaaclab.utils import configclass
from isaaclab.utils.assets import retrieve_file_path
from isaaclab.utils.dict import print_dict
from isaaclab.utils.pretrained_checkpoint import get_published_pretrained_checkpoint

from isaaclab_rl.rsl_rl import (
    RslRlBaseRunnerCfg,
    RslRlPpoActorCriticCfg,
    RslRlVecEnvWrapper,
    export_policy_as_jit,
    export_policy_as_onnx,
)

import isaaclab_tasks  # noqa: F401
import isaaclab_tasks.manager_based.classic.humanoid.mdp as mdp
from isaaclab_tasks.utils import get_checkpoint_path
from isaaclab_tasks.utils.hydra import hydra_task_config

from ant.depth_actor_critic import DepthActorCritic, register_depth_actor_critic

register_depth_actor_critic()


#########################
# Evaluation rewards
#########################


@configclass
class EvalRewardsCfg:
    """Original Isaac Lab Ant rewards used for every checkpoint."""

    progress = RewTerm(func=mdp.progress_reward, weight=1.0, params={"target_pos": (1000.0, 0.0, 0.0)})
    alive = RewTerm(func=mdp.is_alive, weight=0.5)
    upright = RewTerm(func=mdp.upright_posture_bonus, weight=0.1, params={"threshold": 0.93})
    move_to_target = RewTerm(
        func=mdp.move_to_target_bonus,
        weight=0.5,
        params={"threshold": 0.8, "target_pos": (1000.0, 0.0, 0.0)},
    )
    action_l2 = RewTerm(func=mdp.action_l2, weight=-0.005)
    energy = RewTerm(func=mdp.power_consumption, weight=-0.05, params={"gear_ratio": {".*": 15.0}})
    joint_pos_limits = RewTerm(
        func=mdp.joint_pos_limits_penalty_ratio,
        weight=-0.1,
        params={"threshold": 0.99, "gear_ratio": {".*": 15.0}},
    )


#########################
# Observation adapters
#########################


def foot_contact_state(env, sensor_cfg: SceneEntityCfg, threshold: float) -> torch.Tensor:
    """Return one binary contact value for each selected foot."""
    sensor = env.scene.sensors[sensor_cfg.name]
    forces = sensor.data.net_forces_w[:, sensor_cfg.body_ids]
    return (forces.norm(dim=-1) > threshold).float()


def infer_optional_observations(input_dim: int, perception_dim: int) -> tuple[bool, bool]:
    """Infer base-height and contact inputs from the policy input size."""
    optional_dim = input_dim - 59 - perception_dim
    include_contacts = optional_dim >= 4
    if include_contacts:
        optional_dim -= 4
    if optional_dim not in (0, 1):
        raise ValueError(
            f"Cannot match actor input size {input_dim} to 59-D proprioception, "
            f"{perception_dim}-D perception, optional base height, and optional 4-D contacts."
        )
    include_base_height = optional_dim == 1
    return include_base_height, include_contacts


@configclass
class HeightScanContactObservationsCfg:
    """127-D observations used by the height-scan/contact checkpoint."""

    @configclass
    class PolicyCfg(ObsGroup):
        base_height = ObsTerm(func=mdp.base_pos_z)
        base_lin_vel = ObsTerm(func=mdp.base_lin_vel)
        base_ang_vel = ObsTerm(func=mdp.base_ang_vel)
        base_yaw_roll = ObsTerm(func=mdp.base_yaw_roll)
        base_angle_to_target = ObsTerm(func=mdp.base_angle_to_target, params={"target_pos": (1000.0, 0.0, 0.0)})
        base_up_proj = ObsTerm(func=mdp.base_up_proj)
        base_heading_proj = ObsTerm(func=mdp.base_heading_proj, params={"target_pos": (1000.0, 0.0, 0.0)})
        joint_pos_norm = ObsTerm(func=mdp.joint_pos_limit_normalized)
        joint_vel_rel = ObsTerm(func=mdp.joint_vel_rel, scale=0.2)
        feet_body_forces = ObsTerm(
            func=mdp.body_incoming_wrench,
            scale=0.1,
            params={
                "asset_cfg": SceneEntityCfg(
                    "robot", body_names=["front_left_foot", "front_right_foot", "left_back_foot", "right_back_foot"]
                )
            },
        )
        actions = ObsTerm(func=mdp.last_action)
        height_scan = ObsTerm(
            func=mdp.height_scan,
            params={"sensor_cfg": SceneEntityCfg("height_scanner"), "offset": 0.5},
            clip=(-1.0, 1.0),
        )
        foot_contacts = ObsTerm(
            func=foot_contact_state,
            params={
                "sensor_cfg": SceneEntityCfg(
                    "feet_contacts",
                    body_names=["front_left_foot", "front_right_foot", "left_back_foot", "right_back_foot"],
                    preserve_order=True,
                ),
                "threshold": 1.0,
            },
        )

        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = True

    policy: PolicyCfg = PolicyCfg()


def configure_checkpoint_inputs(env_cfg, agent_cfg, checkpoint_path: str) -> str:
    """Match the observation and policy configuration to a known checkpoint shape."""
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    state_dict = checkpoint["model_state_dict"]

    input_dim = state_dict["actor.0.weight"].shape[1]
    checkpoint_uses_depth = any(name.startswith("depth_encoder.") for name in state_dict)

    if checkpoint_uses_depth:
        embedding_weights = [
            value
            for name, value in state_dict.items()
            if name.startswith("depth_encoder.") and name.endswith(".weight") and value.ndim == 2
        ]
        if len(embedding_weights) != 1:
            raise ValueError("Cannot determine the depth embedding size from the checkpoint.")
        depth_embedding_dim = embedding_weights[0].shape[0]
        include_base_height, include_contacts = infer_optional_observations(input_dim, depth_embedding_dim)
        if include_base_height:
            raise ValueError("Depth checkpoints with base_height are not supported by the current policy ordering.")
        if not include_contacts:
            env_cfg.observations.contact = None
            agent_cfg.obs_groups = {
                "policy": ["policy", "depth"],
                "critic": ["policy", "depth"],
            }
        return f"depth_cnn_{input_dim}d"

    agent_cfg.obs_groups = {
        "policy": ["policy"],
        "critic": ["policy"],
    }
    agent_cfg.policy = RslRlPpoActorCriticCfg(
        init_noise_std=1.0,
        actor_obs_normalization=False,
        critic_obs_normalization=False,
        actor_hidden_dims=[400, 200, 100],
        critic_hidden_dims=[400, 200, 100],
        activation="elu",
    )
    env_cfg.scene.depth_camera = None

    if input_dim == 59:
        env_cfg.scene.height_scanner = None
        env_cfg.observations = HeightScanContactObservationsCfg()
        env_cfg.observations.policy.base_height = None
        env_cfg.observations.policy.height_scan = None
        env_cfg.observations.policy.foot_contacts = None
        return "baseline_59d"

    if input_dim != 382:
        include_base_height, include_contacts = infer_optional_observations(input_dim, perception_dim=63)
        env_cfg.scene.height_scanner = RayCasterCfg(
            prim_path="{ENV_REGEX_NS}/Robot/torso",
            offset=RayCasterCfg.OffsetCfg(pos=(0.8, 0.0, 20.0)),
            ray_alignment="yaw",
            pattern_cfg=patterns.GridPatternCfg(resolution=0.2, size=(1.6, 1.2)),
            mesh_prim_paths=["/World/ground"],
            max_distance=1.0e6,
            debug_vis=False,
        )
        env_cfg.observations = HeightScanContactObservationsCfg()
        if not include_base_height:
            env_cfg.observations.policy.base_height = None
        if not include_contacts:
            env_cfg.observations.policy.foot_contacts = None
        return f"height_scan_{input_dim}d"

    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root / "IsaacLab_Ant"))
    from ant_rough.env_cfg import MySceneCfg as RoughSceneCfg
    from ant_rough.env_cfg import ObservationsCfg as RoughObservationsCfg

    env_cfg.scene.height_scanner = RoughSceneCfg().height_scanner
    env_cfg.scene.height_scanner.update_period = env_cfg.decimation * env_cfg.sim.dt
    env_cfg.observations = RoughObservationsCfg()
    return "height_scan_382d"


@hydra_task_config(args_cli.task, args_cli.agent)
def main(env_cfg: ManagerBasedRLEnvCfg | DirectRLEnvCfg | DirectMARLEnvCfg, agent_cfg: RslRlBaseRunnerCfg):
    """Play one episode with an RSL-RL agent."""
    # grab task name for checkpoint path
    task_name = args_cli.task.split(":")[-1]
    train_task_name = task_name.replace("-Play", "")

    # override configurations with non-hydra CLI arguments
    agent_cfg: RslRlBaseRunnerCfg = cli_args.update_rsl_rl_cfg(agent_cfg, args_cli)
    env_cfg.scene.num_envs = args_cli.num_envs if args_cli.num_envs is not None else env_cfg.scene.num_envs

    # set the environment seed
    # note: certain randomizations occur in the environment initialization so we set the seed here
    env_cfg.seed = agent_cfg.seed
    env_cfg.sim.device = args_cli.device if args_cli.device is not None else env_cfg.sim.device

    # specify directory for logging experiments
    log_root_path = os.path.join("logs", "rsl_rl", agent_cfg.experiment_name)
    log_root_path = os.path.abspath(log_root_path)
    print(f"[INFO] Loading experiment from directory: {log_root_path}")
    if args_cli.use_pretrained_checkpoint:
        resume_path = get_published_pretrained_checkpoint("rsl_rl", train_task_name)
        if not resume_path:
            print("[INFO] Unfortunately a pre-trained checkpoint is currently unavailable for this task.")
            return
    elif args_cli.checkpoint:
        resume_path = retrieve_file_path(args_cli.checkpoint)
    else:
        resume_path = get_checkpoint_path(log_root_path, agent_cfg.load_run, agent_cfg.load_checkpoint)

    log_dir = os.path.dirname(resume_path)

    # set the log directory for the environment (works for all environment types)
    env_cfg.log_dir = log_dir

    policy_input = configure_checkpoint_inputs(env_cfg, agent_cfg, resume_path)
    env_cfg.rewards = EvalRewardsCfg()
    print(f"[INFO] Checkpoint input adapter: {policy_input}")

    # configure the viewer to track the Ant root
    env_cfg.viewer.origin_type = "asset_root"
    env_cfg.viewer.asset_name = "robot"
    env_cfg.viewer.env_index = 0
    env_cfg.viewer.eye = (-4.0, 4.0, 2.5)
    env_cfg.viewer.lookat = (0.0, 0.0, 0.5)

    # create isaac environment
    env = gym.make(args_cli.task, cfg=env_cfg, render_mode="rgb_array" if args_cli.video else None)

    # convert to single-agent instance if required by the RL algorithm
    if isinstance(env.unwrapped, DirectMARLEnv):
        env = multi_agent_to_single_agent(env)

    # wrap for video recording
    if args_cli.video:
        video_kwargs = {
            "video_folder": os.path.join(log_dir, "videos", "play"),
            "step_trigger": lambda step: step == 0,
            "video_length": args_cli.video_length,
            "disable_logger": True,
        }
        print("[INFO] Recording videos during training.")
        print_dict(video_kwargs, nesting=4)
        env = gym.wrappers.RecordVideo(env, **video_kwargs)

    # wrap around environment for rsl-rl
    env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)

    print(f"[INFO]: Loading model checkpoint from: {resume_path}")
    # load previously trained model
    if agent_cfg.class_name == "OnPolicyRunner":
        runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=None, device=agent_cfg.device)
    elif agent_cfg.class_name == "DistillationRunner":
        runner = DistillationRunner(env, agent_cfg.to_dict(), log_dir=None, device=agent_cfg.device)
    else:
        raise ValueError(f"Unsupported runner class: {agent_cfg.class_name}")
    runner.load(resume_path)

    # obtain the trained policy for inference
    policy = runner.get_inference_policy(device=env.unwrapped.device)

    # extract the neural network module
    # we do this in a try-except to maintain backwards compatibility.
    try:
        # version 2.3 onwards
        policy_nn = runner.alg.policy
    except AttributeError:
        # version 2.2 and below
        policy_nn = runner.alg.actor_critic

    # extract the normalizer
    if hasattr(policy_nn, "actor_obs_normalizer"):
        normalizer = policy_nn.actor_obs_normalizer
    elif hasattr(policy_nn, "student_obs_normalizer"):
        normalizer = policy_nn.student_obs_normalizer
    else:
        normalizer = None

    # export policy to onnx/jit
    if isinstance(policy_nn, DepthActorCritic):
        print("[INFO] Skipping JIT/ONNX export for the multimodal depth policy.")
    else:
        export_model_dir = os.path.join(os.path.dirname(resume_path), "exported")
        export_policy_as_jit(policy_nn, normalizer=normalizer, path=export_model_dir, filename="policy.pt")
        export_policy_as_onnx(policy_nn, normalizer=normalizer, path=export_model_dir, filename="policy.onnx")

    dt = env.unwrapped.step_dt

    # reset environment
    obs = env.get_observations()
    timestep = 0
    reward_names = env.unwrapped.reward_manager.active_terms
    episode_rewards = torch.zeros(env.num_envs, dtype=torch.float64, device=env.device)
    episode_reward_components = torch.zeros(
        (env.num_envs, len(reward_names)), dtype=torch.float64, device=env.device
    )
    episode_steps = torch.zeros(env.num_envs, dtype=torch.long, device=env.device)
    finished = torch.zeros(env.num_envs, dtype=torch.bool, device=env.device)
    # simulate environment
    while simulation_app.is_running():
        start_time = time.time()
        # run everything in inference mode
        with torch.inference_mode():
            # agent stepping
            actions = policy(obs)
            # env stepping
            obs, rewards, dones, extras = env.step(actions)
            # Include the terminal step, then ignore auto-reset episodes for finished environments.
            active = ~finished
            episode_rewards[active] += rewards[active]
            step_reward_components = env.unwrapped.reward_manager._step_reward.double() * env.unwrapped.step_dt
            episode_reward_components[active] += step_reward_components[active]
            episode_steps[active] += 1
            finished |= dones.bool()
        timestep += 1

        # Wait for the first episode of every environment to finish.
        if finished.all().item():
            print(f"[INFO] All {env.num_envs} environments finished their first episode.")
            break

        # Recording length must not truncate episode statistics.
        if timestep >= env.max_episode_length:
            print(f"[INFO] Reached maximum episode length: {env.max_episode_length}")
            break

        # time delay for real-time evaluation
        sleep_time = dt - (time.time() - start_time)
        if args_cli.real_time and sleep_time > 0:
            time.sleep(sleep_time)

    completed = int(finished.sum().item())
    print(f"[INFO] Completed first episodes: {completed}/{env.num_envs}")
    if completed != env.num_envs:
        print("[INFO] Statistics include partial episodes for unfinished environments.")
    print("[RESULT] Reward component means:")
    for index, name in enumerate(reward_names):
        values = episode_reward_components[:, index]
        print(f"[RESULT] {name}: mean={values.mean().item():.6f}, std={values.std(unbiased=False).item():.6f}")
    component_sum_error = (episode_reward_components.sum(dim=1) - episode_rewards).abs().max().item()
    print(f"[RESULT] Reward component sum max error: {component_sum_error:.8f}")
    if env.num_envs == 1:
        print(f"[RESULT] Episode reward total: {episode_rewards[0].item():.6f}")
        print(f"[RESULT] Episode steps: {episode_steps[0].item()}")
    else:
        # Population standard deviation across the evaluated environments.
        steps = episode_steps.to(dtype=torch.float64)
        print(
            f"[RESULT] Episode reward total: mean={episode_rewards.mean().item():.6f}, "
            f"std={episode_rewards.std(unbiased=False).item():.6f}"
        )
        print(
            f"[RESULT] Episode steps: mean={steps.mean().item():.6f}, "
            f"std={steps.std(unbiased=False).item():.6f}"
        )

    # close the simulator
    env.close()


if __name__ == "__main__":
    # run the main function
    main()
    # close sim app
    simulation_app.close()
