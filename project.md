# Isaac Lab Ant 프로젝트 현황

최종 갱신: 2026-10-02

이 문서는 현재 저장소의 실제 코드를 기준으로 작성했다.

## 1. 프로젝트 목표

- Isaac Lab의 `ManagerBasedRLEnv` 환경을 사용한다.
- 학습 알고리즘은 RSL-RL PPO를 사용한다.
- Ant가 rough terrain과 서로 다른 마찰 조건에서도 안정적으로 전진하도록 학습한다.
- 진행 방향과 목표 위치는 body/world `+X` 방향이다.
- proprioception과 전방 depth image를 함께 policy observation으로 사용한다.

## 2. 현재 파일 구조와 역할

```text
ant/
├── command.txt                         # train/play/TensorBoard 명령어
├── PROJECT_STATUS.md                   # 현재 구현 및 진행 상황
├── scripts/rsl_rl/
│   ├── cli_args.py                     # 공통 RSL-RL CLI 인자
│   ├── train.py                        # PPO 학습 및 best_model 저장
│   ├── play.py                         # 재생, 고정 평가 reward, 속도 기록
│   └── play_one_episode.py             # 향후 결과 기록용 1회 평가 스크립트
└── source/ant/
    ├── __init__.py                     # `Ant-rl-v0` Gym 환경 등록
    ├── ant_env_cfg.py                  # scene/terrain/obs/event/reward/termination
    ├── rewards.py                      # 학습 reward 전체 계산
    ├── depth_obs.py                    # depth 전처리
    ├── depth_actor_critic.py           # depth CNN + actor/critic
    └── agents/rsl_rl_ppo_cfg.py        # PPO 및 policy 설정
```

## 3. 환경 설정

### Task 등록

- Gym ID: `Ant-rl-v0`
- Environment: `isaaclab.envs:ManagerBasedRLEnv`
- Environment config: `AntEnvCfg`
- Agent config: `AntPPORunnerCfg`

### 시뮬레이션

- 기본 환경 수: `256`
- episode 길이: `16.0 s`
- physics timestep: `1 / 120 s`
- decimation: `2`
- policy step: `1 / 60 s`
- action: 모든 Ant joint에 effort action 적용, scale `7.5`
- Ant USD는 contact sensor 사용을 위해 instanceable 버전이 아닌 `ant.usd`를 사용한다.

### Terrain

현재는 `ROUGH_TERRAINS_CFG`를 복사한 뒤 다음 다섯 terrain을 각각 확률 `0.2`로 사용한다.

- `pyramid_stairs`
- `pyramid_stairs_inv`
- `hf_pyramid_slope`
- `hf_pyramid_slope_inv`
- `boxes`

주요 값:

- terrain seed: `42`
- curriculum: 비활성화
- terrain size: `10 m x 10 m`
- rows/columns: `20 x 10`
- 계단 높이: `0.03 ~ 0.07 m`
- box 높이: `0.02 ~ 0.10 m`
- 경사도: `0.0 ~ 0.20`
- 중앙 platform 폭: `1.0 m`

주의: 초기 목표였던 **사각 높이 타일 한 종류만 사용하는 고정 terrain**과 현재 코드는 다르다. 현재는 계단, 역계단, 경사, 역경사, boxes가 섞인 rough terrain이다. 이것이 최종 실험 조건인지 다시 결정해야 한다.

### 마찰계수

- 바닥 static/dynamic friction: 모두 `1.0`
- combine mode: `multiply`
- 각 환경의 robot static friction: 시작 시 `0.3 ~ 1.0`에서 균등 분포로 한 번 추출
- robot dynamic friction: `0.8 * static friction`
- restitution: `0.0`

`random_friction`은 `startup` event이므로 episode reset마다 다시 추출하지 않는다. 한 번 생성된 각 환경은 실행이 끝날 때까지 같은 마찰계수를 유지한다.

## 4. Depth camera와 observation

### Depth camera

- sensor: `TiledCameraCfg`
- 부착 위치: `{ENV_REGEX_NS}/Robot/torso/DepthCamera`
- resolution: `64 x 48`
- update rate: `15 Hz`
- output: `distance_to_camera`
- clipping range: `0.1 ~ 5.0 m`
- 위치: torso 기준 `(0.25, 0.0, 0.12)`
- 방향: 진행 방향 `+X` 기준 약 `10°` 아래
- quaternion: `(0.9962, 0.0, 0.0872, 0.0)` (`w, x, y, z`)

`train.py`와 `play.py`는 depth observation을 위해 camera rendering을 항상 활성화한다.

### Depth 전처리

`depth_obs.normalized_depth()`가 다음 순서로 처리한다.

1. `NaN`, `+Inf`, `-Inf` 값을 유효 거리로 치환
2. depth를 `0.1 ~ 5.0 m`로 clamp
3. `[0, 1]` 범위로 정규화

Camera clipping과 observation normalization 모두 `0.1 ~ 5.0 m` 범위를 사용한다.

### Observation group

`policy` group에는 다음 proprioception이 들어간다.

- base linear/angular velocity
- base yaw/roll
- target까지의 angle
- up/heading projection
- normalized joint position
- scaled joint velocity
- 네 발의 incoming wrench
- previous action

`depth` group에는 `(48, 64, 1)` normalized depth image가 들어간다.

## 5. Depth policy 구조

기본 MLP actor-critic 대신 `DepthActorCritic`을 사용한다.

```text
depth image (48 x 64 x 1)
    -> Conv2d(1, 16, 5, stride=2)
    -> Conv2d(16, 32, 3, stride=2)
    -> Conv2d(32, 32, 3, stride=2)
    -> AdaptiveAvgPool2d(2, 2)
    -> Linear(128, 64)
    -> 64차원 depth embedding

proprioception + 64차원 depth embedding
    -> actor MLP [400, 200, 100]
    -> critic MLP [400, 200, 100]
```

- activation: `ELU`
- actor/critic observation normalization: 비활성화
- actor와 critic은 동일한 depth encoder 객체를 사용하지만, 각각의 forward에서 depth feature를 계산한다.
- 기존 depth 없는 MLP checkpoint와 network shape이 다르므로 그대로 이어서 학습할 수 없다.
- 현재 multimodal policy는 `play.py`에서 JIT/ONNX export를 건너뛴다.

## 6. 학습 reward

`RewardsCfg`에는 `total_reward` 하나만 등록되어 있다.

```python
total_reward = RewTerm(func=rewards.TotalReward, weight=1.0)
```

모든 항목은 `rewards.py`의 `TotalReward`에서 한 번에 계산한다. RewardManager가 최종 term에 `step_dt`를 적용하므로 `TotalReward.__call__()`은 전체 reward에 dt를 직접 곱하지 않는다.

현재 항목과 weight:

| 항목 | 계산 의미 | Weight |
|---|---|---:|
| progress | 이전/현재 target potential 차이 | `2.5` |
| alive | terminated가 아니면 1 | `0.5` |
| upright | up projection이 `0.93`보다 크면 1 | `0.05` |
| move_to_target | target 방향과 body heading 정렬 | `1.5` |
| foot_contact | 네 발 중 2개 이상 접촉하면 1 | `1.0` |
| action_l2 | action 제곱합 | `-0.005` |
| energy | `abs(action * joint_vel * gear_ratio)` 합 | `-0.15` |
| joint_velocity | joint velocity 제곱합 | `-0.001` |
| joint_pos_limits | normalized joint position의 `0.99` 초과분 | `-0.5` |
| foot_slip | 접촉 중인 발의 XY 속도 합 | `-0.07` |

접촉 판정은 최근 contact-force history에서 발별 수직 힘의 최대값이 `5 N`보다 큰지 확인한다.

각 weighted reward는 episode 동안 누적되어 TensorBoard의 다음 항목으로 기록된다.

```text
Episode_Reward/progress
Episode_Reward/alive
Episode_Reward/upright
Episode_Reward/move_to_target
Episode_Reward/foot_contact
Episode_Reward/action_l2
Episode_Reward/energy
Episode_Reward/joint_velocity
Episode_Reward/joint_pos_limits
Episode_Reward/foot_slip
```

## 7. Reset과 termination

### Reset

- root pose/velocity의 추가 randomization 없음
- joint position offset: `-0.2 ~ 0.2`
- joint velocity offset: `-0.1 ~ 0.1`
- progress reward의 현재/이전 potential은 reset 위치에서 같은 값으로 초기화된다.

### Termination

- episode time-out
- body z-axis가 아래쪽을 향할 정도로 뒤집힘: `bad_orientation(limit_angle=pi/2)`
- torso minimum-height termination은 현재 주석 처리되어 비활성화 상태다.

## 8. PPO 설정과 checkpoint

- runner: `OnPolicyRunner` 기반 `BestModelRunner`
- rollout steps per environment: `32`
- 기본 max iterations: `1000`
- checkpoint save interval: `50`
- learning rate: `5e-4`, adaptive schedule
- gamma: `0.99`
- lambda: `0.95`
- PPO epochs: `5`
- mini-batches: `4`
- entropy coefficient: `0.0`

일반 checkpoint 외에 runner의 완료 episode 평균 reward가 이전 최고값을 넘으면 run 폴더에 `best_model.pt`를 저장한다. 저장 정보에는 해당 `mean_reward`가 포함된다.

주의: 재개 학습을 시작하면 `BestModelRunner.best_mean_reward`는 다시 `-inf`에서 시작한다. 이전 run의 최고 reward를 복구하여 비교하는 구조는 아직 없다.

학습 시작 시 다음 설정도 run 폴더에 저장된다.

- `params/env.yaml`
- `params/agent.yaml`
- `params/reward_weights.yaml`

## 9. Play와 평가

`play.py`는 학습 reward 대신 별도 `EvalRewardsCfg`를 environment 생성 전에 적용한다. 따라서 화면 재생 중 출력되는 episode total reward는 학습 reward와 다르다.

고정 평가 reward:

| 항목 | Weight |
|---|---:|
| progress | `1.0` |
| alive | `0.5` |
| upright | `0.1` |
| move_to_target | `0.5` |
| action_l2 | `-0.005` |
| energy | `-0.05` |

play 중 각 환경의 episode total reward를 누적하고, 모든 환경에서 완료된 episode가 하나씩 모일 때 다음 값을 출력한다.

- 각 environment의 episode total reward
- 모든 environment의 mean reward

`--record_vel`을 사용하면 episode별로 다음 값을 출력하고 CSV에 저장한다.

- mean forward velocity: world `+X` 속도 평균
- mean planar speed: XY 속력 평균
- episode duration
- 저장 위치: checkpoint run 폴더의 `play_episode_velocities.csv`

## 10. 실행 명령

상세 인자는 `command.txt`를 참고한다.

### 설치

```bash
python -m pip install -e .
```

### 최소 학습 확인

```bash
python scripts/rsl_rl/train.py \
  --task Ant-rl-v0 \
  --num_envs 4 \
  --max_iterations 1 \
  --headless
```

### 일반 학습 예시

```bash
python scripts/rsl_rl/train.py \
  --task Ant-rl-v0 \
  --num_envs 256 \
  --max_iterations 10000 \
  --headless
```

### Checkpoint 재생

```bash
python scripts/rsl_rl/play.py \
  --task Ant-rl-v0 \
  --num_envs 4 \
  --checkpoint logs/rsl_rl/ant/RUN_FOLDER/best_model.pt
```

### 속도 기록

```bash
python scripts/rsl_rl/play.py \
  --task Ant-rl-v0 \
  --num_envs 4 \
  --checkpoint logs/rsl_rl/ant/RUN_FOLDER/best_model.pt \
  --record_vel
```

### TensorBoard

```bash
tensorboard --logdir logs/rsl_rl/ant --port 6006
```

브라우저에서 `http://localhost:6006`에 접속한다.

## 11. 현재까지 완료된 작업

- [x] `Ant-rl-v0` custom task 등록
- [x] `ManagerBasedRLEnv + RSL-RL PPO` 학습 구조 정리
- [x] robot friction environment별 randomization
- [x] reward 계산을 `TotalReward` 하나로 통합
- [x] progress potential reset 동작 유지
- [x] contact reward와 foot-slip penalty 추가
- [x] 개별 weighted reward TensorBoard logging
- [x] body가 뒤집히면 terminate하는 조건 추가
- [x] 최고 평균 reward의 `best_model.pt` 저장
- [x] play에서 environment별 episode reward와 전체 평균 출력
- [x] play에서 episode 평균 전진 속도/평면 속력 CSV 기록
- [x] torso 전방 `TiledCameraCfg` 추가
- [x] depth normalization observation 추가
- [x] depth CNN embedding을 사용하는 custom actor-critic 추가
- [x] 카메라를 `+X` 기준 약 10° 아래로 조정

## 12. 다음 작업 및 확인 필요 사항

우선순위 순서로 정리했다.

1. **Terrain 실험 조건 확정**
   - 기존 목표인 square height tiles 한 종류로 돌아갈지, 현재 mixed rough terrain을 최종 조건으로 사용할지 결정한다.

2. **소규모 실행 검증**
   - 4개 이하 environment에서 camera output shape/range, observation shape, PPO 1 iteration을 확인한다.
   - 현재 문서 작성 과정에서는 Python syntax만 검사하며 학습과 simulator는 실행하지 않는다.

3. **Depth policy 성능/비용 확인**
   - camera rendering과 CNN 때문에 가능한 environment 수가 크게 줄 수 있다.
   - 256 env부터 GPU memory와 simulation FPS를 확인한 뒤 env 수를 늘린다.

4. **Reward scale 재검토**
   - `foot_contact=+1.0`이 정지 또는 발 끌기 행동을 과도하게 유도하는지 확인한다.
   - `foot_slip`, `energy`, `joint_velocity`가 전진 reward를 압도하는지 TensorBoard에서 비교한다.
   - reward를 바꾸기 전 각 실험의 weight 파일을 보존한다.

5. **평가 기준 확정**
   - 현재 play의 6개 fixed evaluation reward를 최종 지표로 사용할지 결정한다.
   - reward 외에도 평균 전진 속도, 이동 거리, fall rate, episode 길이를 함께 비교하는 것이 좋다.

6. **마찰 robustness 평가 도구 추가**
   - terrain/seed를 고정하고 friction을 여러 고정값으로 sweep한다.
   - training 범위의 양 끝과 범위 밖 값을 포함해 성능을 저장한다.

7. **`play_one_episode.py` 결과 기록 기능 정리**
   - 향후 학습 결과를 동일한 episode 단위로 기록하고 비교하기 위해 새로 받은 스크립트다.
   - 실제 결과 기록을 시작할 때 필요한 출력 항목과 저장 형식을 확정한다.

## 13. 알려진 주의점

- `contact_forces.debug_vis=True`라서 대규모 headless 학습 성능에 영향을 줄 수 있다.
- `play.py`의 evaluation reward에는 `joint_pos_limits`, contact, slip penalty가 없다. 이는 의도적으로 학습 reward와 분리한 현재 실험안이다.
- `play.py --video` 사용 시 지정한 `video_length`에 도달하면 play loop가 종료된다.
- `command.txt`의 영상 재생 예시 중 checkpoint가 폴더로 표시된 부분은 실제 `model_*.pt` 또는 `best_model.pt` 파일 경로로 바꿔야 한다.
- 저장소에는 수정된 log artifact와 아직 Git에 추가되지 않은 depth 관련 파일이 있으므로 commit 전에 `git status`를 확인해야 한다.
