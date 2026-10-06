# Ant RL — HeightScan Ablation

Isaac Lab의 Ant locomotion 환경에서 **HeightScan**, **foot contact observation**, **reward shaping**이 rough-terrain locomotion에 미치는 영향을 비교한 실험이다.

이 README는 `observation-ablation` 브랜치의 실험 설정과 artifact를 기준으로, 아래 세 모델만 정리한다.

1. **Height**
2. **Height + Contact**
3. **Height + Contact + Modified Reward**

> 실험 source와 checkpoint는 `observation-ablation` 브랜치에 보존되어 있다.

---

## 1. 실험 구성

| 모델 | Observation | 입력 차원 | Reward |
|---|---|---:|---|
| **Height** | 59-D proprio + 63-D HeightScan | **122-D** | Stock |
| **Height + Contact** | 59-D proprio + 63-D HeightScan + 4-D foot contact | **126-D** | Stock |
| **Height + Contact + Modified Reward** | 59-D proprio + 63-D HeightScan + 4-D foot contact | **126-D** | Modified |

비교 목적은 다음과 같다.

- **Height → Height + Contact**: explicit foot-contact observation 추가 효과
- **Height + Contact → Height + Contact + Modified Reward**: observation을 고정하고 reward 변경 효과

---

## 2. 공통 환경

### Simulation

| 항목 | 설정 |
|---|---|
| Environment | Isaac Lab `ManagerBasedRLEnv` |
| Robot | Ant |
| Physics dt | `1/120 s` |
| Decimation | `2` |
| Control frequency | `60 Hz` |
| Episode length | `16 s` / 최대 `960 steps` |
| Action | 8-D joint effort |
| Action scale | `7.5` |
| Termination | Timeout 또는 `bad_orientation(pi/2)` |

### Terrain

`ROUGH_TERRAINS_CFG`를 기반으로 다음 5종 terrain을 각각 20% 비율로 사용한다.

| Terrain | 범위 |
|---|---|
| Stairs | step height `0.03 ~ 0.07 m` |
| Inverted stairs | step height `0.03 ~ 0.07 m` |
| Boxes | height `0.02 ~ 0.10 m` |
| Slope | slope `0.0 ~ 0.20` |
| Inverted slope | slope `0.0 ~ 0.20` |

공통 설정:

- patch size: `10 x 10 m`
- layout: `20 x 10 = 200 patches`
- terrain seed: `42`
- curriculum: off
- central platform width: `1.0 m`

### Friction randomization

- ground static/dynamic friction: `1.0`
- robot static friction: `Uniform(0.3, 1.0)`
- robot dynamic friction: `0.8 x static friction`
- friction은 startup 시 environment별로 한 번 추출된다.

### Reset

세 ablation run의 저장된 training config에는 다음 reset/event만 존재한다.

- `reset_base`
- `reset_robot_joints`
- `random_friction`

따라서 **이 세 모델의 원래 학습에는 episode마다 terrain patch를 다시 선택하는 `reselect_terrain` event가 없다.**

현재 `main`의 environment와 실험 당시 `observation-ablation` environment가 달라질 수 있으므로 재현 시 이 차이를 확인해야 한다.

---

## 3. Observation

### 3.1 Proprioception — 59-D

세 모델이 공통으로 사용하는 proprioception은 다음 항목으로 구성된다.

- base linear velocity
- base angular velocity
- base yaw / roll
- target까지의 angle
- up projection
- heading projection
- normalized joint position
- scaled joint velocity
- 4개 발의 incoming wrench
- previous action

`base_height`는 포함하지 않는다.

### 3.2 HeightScan — 63-D

Torso에 yaw-aligned RayCaster를 부착해 주변 terrain 높이를 측정한다.

| 항목 | 설정 |
|---|---|
| Sensor | `RayCasterCfg` |
| Parent body | torso |
| Grid | `9 x 7` |
| Resolution | `0.2 m` |
| Scan size | `1.6 x 1.2 m` |
| Number of rays | **63** |
| Offset | `(0.8, 0.0, 20.0)` |
| Height offset | `0.5` |
| Clip | `[-1, 1]` |

Height model의 최종 입력:

```text
59-D proprio + 63-D HeightScan = 122-D
```

### 3.3 Foot contact — 4-D

Height + Contact 계열은 네 발의 binary contact state를 추가한다.

순서:

```text
front_left_foot
front_right_foot
left_back_foot
right_back_foot
```

각 발에 대해 현재 world-frame contact force의 norm이 `1 N`보다 크면 1, 아니면 0으로 표현한다.

```text
59-D proprio + 63-D HeightScan + 4-D Contact = 126-D
```

이 4-D contact observation은 proprioception에 이미 포함된 **24-D incoming foot wrench와 별개의 feature**다.

---

## 4. Policy / PPO

세 모델 모두 HeightScan을 CNN 없이 직접 MLP 입력에 concatenate한다.

```text
Observation
    -> Actor MLP  [400, 200, 100]
    -> Critic MLP [400, 200, 100]
```

공통 PPO 설정:

| 항목 | 값 |
|---|---:|
| Parallel environments | 4096 |
| Rollout steps / env | 32 |
| Iterations | 1000 |
| Total transitions | 131,072,000 |
| Training seed | 42 |
| Learning rate | `5e-4` |
| Schedule | adaptive |
| Gamma | `0.99` |
| Lambda | `0.95` |
| PPO epochs | 5 |
| Mini-batches | 4 |
| Clip parameter | `0.2` |
| Entropy coefficient | `0.0` |
| Desired KL | `0.01` |
| Max grad norm | `1.0` |
| Observation normalization | off |

---

## 5. Reward

### Stock Reward

**Height**와 **Height + Contact**는 동일한 Isaac Lab Ant stock reward를 사용한다.

| Component | Weight |
|---|---:|
| progress | 1.0 |
| alive | 0.5 |
| upright | 0.1 |
| move_to_target | 0.5 |
| action_l2 | -0.005 |
| energy | -0.05 |
| joint_pos_limits | -0.1 |

따라서 두 모델의 차이는 **4-D contact observation의 유무뿐**이다.

### Modified Reward

**Height + Contact + Modified Reward**는 observation은 그대로 유지하고 reward만 변경한다.

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

추가된 목적은 contact 유지, foot slip 감소, joint motion 및 control effort 억제다.

> Observation-side Contact와 Reward-side Contact는 정의가 다르다. Observation은 현재 contact-force norm > 1 N의 4-D binary 값이고, Modified Reward의 contact/slip 계산은 reward용 contact sensor를 사용한다.

---

## 6. Checkpoint

각 실험은 training 중 기록된 **highest mean return** checkpoint를 `best_model.pt`로 선택했다.

| 모델 | Best iteration | Training mean return |
|---|---:|---:|
| Height | 804 | 53.0052 |
| Height + Contact | 972 | 53.8264 |
| Height + Contact + Modified Reward | 788 | 107.4448 |

Modified Reward는 Stock Reward와 scale 및 term이 다르므로 **training mean return 107.44를 Stock 모델의 53.xx와 직접 비교하면 안 된다.**

Checkpoint 위치:

```text
observation-ablation/
└── experiments/observation_ablation/
    ├── heightscan_4096x32x1000/checkpoints/best_model.pt
    ├── heightscan_contact_stock_4096x32x1000/checkpoints/best_model.pt
    └── heightscan_contact_modified_4096x32x1000/checkpoints/best_model.pt
```

---

## 7. 동일 Reward 기준 평가

현재 `scripts/rsl_rl/play_one_episode.py`는 checkpoint의 observation 구조를 자동 판별한 뒤, 세 모델을 **동일한 Stock 7-term evaluation reward**로 평가한다.

평가 조건:

- environments: 100
- 각 environment의 첫 episode만 사용
- 최대 episode 길이: 960 steps
- terminal step 포함
- auto-reset 이후 episode는 제외
- 표준편차: population std

### 평가 결과

| Metric | Height | Height + Contact | Height + Contact + Modified |
|---|---:|---:|---:|
| Progress | 58.090 ± 31.014 | 56.040 ± 29.086 | **60.503 ± 28.118** |
| Alive | 5.950 ± 2.913 | 6.105 ± 2.823 | **6.409 ± 2.666** |
| Upright | 1.034 ± 0.560 | 1.103 ± 0.582 | **1.121 ± 0.549** |
| Move to target | 4.945 ± 2.666 | 5.150 ± 2.797 | **5.469 ± 2.794** |
| Action L2 | -2.764 ± 10.952 | **-0.496 ± 1.580** | -0.958 ± 2.827 |
| Energy | -6.986 ± 3.699 | **-6.114 ± 3.358** | -7.393 ± 3.326 |
| Joint pos limits | -3.376 ± 2.151 | **-2.096 ± 1.873** | -3.878 ± 1.959 |
| **Total reward** | 56.894 ± 31.797 | 59.692 ± 30.703 | **61.273 ± 28.546** |
| **Episode steps** | 714.44 ± 349.10 | 732.97 ± 338.38 | **769.45 ± 319.46** |

이 평가는 세 모델 모두 같은 reward 정의를 사용하므로 Total Reward를 동일 기준으로 비교할 수 있다.

현재 결과에서는:

- Contact 추가 후 Total Reward와 평균 episode length가 증가했다.
- Modified Reward로 학습한 모델은 동일 Stock evaluation 기준에서도 세 모델 중 가장 높은 Total Reward와 평균 episode length를 기록했다.
- 단일 training seed 결과이므로 일반적인 통계적 유의성을 의미하지는 않는다.

---

## 8. 실행

### 설치

```bash
python -m pip install -e .
```

### 한 episode 평가

`play_one_episode.py`는 checkpoint의 actor input dimension과 `depth_encoder` 존재 여부를 확인해 Height / Height+Contact 구조를 자동 구성한다.

```bash
python scripts/rsl_rl/play_one_episode.py \
  --task Ant-rl-v0 \
  --num_envs 100 \
  --checkpoint <CHECKPOINT_PATH> \
  --headless
```

### 영상 저장

한 episode 전체 최대 길이는 960 control steps다.

```bash
python scripts/rsl_rl/play_one_episode.py \
  --task Ant-rl-v0 \
  --num_envs 1 \
  --checkpoint <CHECKPOINT_PATH> \
  --video \
  --video_length 960
```

영상은 checkpoint run directory 아래의 `videos/play/`에 저장된다.

---

## 9. 관련 브랜치

세 ablation 모델의 source, saved config, checkpoint, evaluation artifact:

- [observation-ablation branch](https://github.com/dding222/ant_rl/tree/observation-ablation)
- [observation ablation experiments](https://github.com/dding222/ant_rl/tree/observation-ablation/experiments/observation_ablation)
