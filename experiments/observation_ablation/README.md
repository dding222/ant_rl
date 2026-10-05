# Terrain Observation Ablation: HeightScan vs DepthCam

본 프로젝트는 `Isaac-Ant-v0`를 기반으로, 복잡한 지형에서도 주변 terrain 정보를 활용해 안정적으로 이동할 수 있는 PPO policy를 개발하고 비교하는 것을 목표로 한다. Robot 구조와 기본 control framework는 유지하면서, terrain perception 방식과 observation 구성, reward 설계를 단계적으로 변경하였다.

특히 terrain 정보를 직접 높이값으로 제공하는 HeightScan과 depth image를 CNN으로 처리하는 DepthCam을 비교하여, 서로 다른 terrain representation이 Ant locomotion에 미치는 영향을 분석하고자 한다. 비교의 공정성을 위해 동일한 terrain/environment, PPO 설정, seed, training budget을 공통 기준으로 고정하였다. Stage 1에서는 Stock Reward 조건에서 두 perception 방식을 비교하고, Stage 2에서는 동일한 Contact observation + Modified Reward 조건에서도 비교를 반복하도록 실험을 구성하였다.

Modified Reward는 단순한 전진 보상 위주의 학습에서 반복적인 jumping/hopping 형태의 이동이 나타나는 경향을 완화하고, ground contact, foot slip, joint motion, control effort를 함께 고려하도록 reward objective를 확장하기 위해 도입하였다. 각 조건에서는 return뿐 아니라 displacement, episode duration, fall/timeout, reward decomposition을 함께 기록해 locomotion 특성을 분석한다.

## 연구 목적

본 실험의 핵심 질문은 같은 학습 조건에서 HeightScan과 DepthCam 중 어떤 terrain representation이 Ant locomotion에 더 효과적인가이다. 이를 Stock Reward 조건과 Contact + Modified Reward 조건에서 각각 비교한다.

## 전체 실험 구성

| Stage | HeightScan 조건 | DepthCam 조건 | Reward |
|---|---|---|---|
| Stage 1 | HeightScan | DepthCam | Stock Isaac-Ant reward |
| Stage 2 | HeightScan + Contact | DepthCam + Contact | Modified reward |

Stage 1은 terrain representation을 비교하는 기본 조건이다. Stage 2에서는 두 조건에 동일한 explicit Contact observation과 Modified Reward를 적용한 뒤 비교를 반복한다. 각 stage에서 비교하려는 변수는 terrain representation이며, 센서별 encoder 차이는 허용한다.

> **비교 원칙:** Stage 1과 Stage 2는 reward 구성과 scale이 다르므로 total return 값의 차이를 직접적인 성능 향상량으로 해석하지 않는다. 공통 protocol이 일치하는지 확인한 뒤 **같은 stage 안에서** HeightScan과 DepthCam을 비교한다. Stage 간 물리적 지표는 참고할 수 있지만, 이 실험만으로 Contact와 reward 변경의 개별 효과를 분리할 수는 없다.

## 공통 학습 조건

다음 조건은 두 stage에 공통으로 적용한다. 진행 예정인 DepthCam 실험도 동일한 protocol을 따라야 한다.

| 항목 | 설정 |
|---|---|
| 학습 환경 | Team1 rough terrain |
| Terrain 종류 | 5종, 각 비율 0.2 |
| Terrain 배치 | 20 × 10 patches |
| Patch 크기 | 10 × 10 m |
| Training seed | 42 |
| Terrain seed | 42 |
| 병렬 환경 수 | 4096 |
| 환경별 iteration당 rollout steps | 32 |
| 학습 iterations | 1000 |
| 총 transitions | 131,072,000 |
| Physics dt | 1/120 s |
| Control dt | 1/60 s |
| Episode 길이 | 16 s / 960 steps |
| Action | 8-D joint effort |
| Action scale | 7.5 |
| Actor/Critic post-feature MLP | [400, 200, 100], ELU |
| Resume | 사용 안 함 |

기존 Team1 root reset을 유지하며, joint position은 ±0.2, joint velocity는 ±0.1 범위로 초기화한다. 종료 조건은 timeout 또는 `body_z_down(pi/2)`이며, map boundary나 torso height에 따른 종료 조건은 추가하지 않는다.

완료된 두 HeightScan 실험의 PPO 설정은 동일하다. Learning rate는 0.0005 (adaptive), gamma는 0.99, lambda는 0.95, clip은 0.2, entropy coefficient는 0, value-loss coefficient는 1이다. Clipped value loss를 사용하며, 5 epochs, 4 minibatches, desired KL 0.01, max gradient norm 1로 설정했다. 초기 Gaussian noise std는 1이며 actor/critic observation normalization은 사용하지 않는다.

Checkpoint 선택 규칙은 학습 전에 고정한다. 해당 stage의 training reward를 기준으로 **완료된 episode의 logged training mean return이 가장 높은 checkpoint**를 선택한다. 선택된 checkpoint와 마지막 iteration의 checkpoint를 모두 보존한다.

### 공통 평가 조건

| 항목 | 설정 |
|---|---|
| 평가 환경 | 동일한 Team1 terrain 설정 |
| Evaluation seed | 24 |
| 평가 환경 수 | 100 |
| Policy action | Deterministic mean action |
| 평가 episode | 각 환경의 첫 episode만 사용 |
| 평가 reward | 해당 stage의 training reward와 동일 |

두 HeightScan 평가 모두 100/100 환경의 첫 episode가 완료됐으며, 동일한 terrain mesh와 환경별 terrain 배정을 사용했다. Terminal reward는 포함하고 reset 이후 reward는 제외한다. Displacement는 종료 시점과 초기 시점의 world-X 차이로 정의한다. 모든 표준편차는 **population std** (`ddof=0`)이다. Reward decomposition은 control dt를 포함한 실제 weighted contribution을 episode별로 누적하고, 공식 episode return과 일치하는지 검증한다.

## Observation 설계

### HeightScan

| 항목 | 설정 |
|---|---|
| Proprio | 기존 Team1 59-D interface |
| HeightScan | 63-D |
| Stage 1 actor/critic 입력 | 122-D |
| 부착 위치 / 정렬 | Torso 부착 / yaw 정렬 |
| Ray pattern | 9 × 7 하향 rays |
| Ray 간격 | 0.2 m |
| Offset | `(0.8, 0, 20)` |
| Height 계산 | `sensor_z - hit_z - 0.5` |
| Scale / clipping | 1 / `[-1, 1]` |
| CNN | 사용 안 함 |
| Empirical observation normalization | 사용 안 함 |

### HeightScan + Contact

Stage 2에서는 proprio, HeightScan, Contact를 연결해 **59-D proprio + 63-D HeightScan + 4-D Contact = 126-D actor/critic 입력**으로 사용한다. HeightScan 전처리는 그대로 유지한다.

Contact feature 순서는 다음과 같다.

1. `front_left_foot`
2. `front_right_foot`
3. `left_back_foot`
4. `right_back_foot`

Explicit Contact observation은 현재 **world-frame net-force norm > 1 N** 여부를 **float32 binary**로 표현한다. History length는 **0**이며, 추가 clipping이나 normalization은 적용하지 않는다. 상세 정의는 [공통 Contact specification](shared/contact_observation.json)을 따른다.

HeightScan과 explicit Contact는 기존 IsaacLab_RS HeightScan+Contact 구현을 참고해 통합했다. Observation-side Contact와 reward-side foot contact는 정의가 다르며, reward-side 정의는 아래 Stage 2에 별도로 설명한다.

### DepthCam

- Terrain representation: depth camera + CNN.
- Proprio interface: 공통 Team1 59-D interface.
- Stage 2 Contact: 동일한 공통 4-D 정의.
- 상세 runtime 차원과 결과: **TBD**.

입력 차원을 맞추기 위한 dummy feature는 추가하지 않는다. Representation에 따라 sensor encoder의 parameter 수와 출력 feature 차원은 달라질 수 있다.

## Stage 1 — Stock Reward 비교

Reward를 Isaac-Ant Stock Reward로 고정하고, 추가적인 task-specific shaping이나 weight tuning 없이 terrain representation 차이에 집중한다.

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

학습과 평가 모두 canonical Isaac-Ant stock reward 함수와 weight를 그대로 사용한다. Team1 custom reward term은 활성화하지 않는다.

### Stage 1 결과

| 지표 | HeightScan + Stock | DepthCam + Stock |
|---|---:|---:|
| Return 평균 ± 표준편차 | 61.3354 ± 31.2305 | TBD |
| Displacement 평균 ± 표준편차 | 60.5140 ± 29.1880 m | TBD |
| Episode duration 평균 ± 표준편차 | 12.1947 ± 5.5930 s | TBD |
| 평균 전진 속도 | 4.4506 m/s | TBD |
| Fall | 41/100 | TBD |
| Timeout | 59/100 | TBD |
| ≥2 m | 87/100 | TBD |
| ≥5 m | 87/100 | TBD |
| ≥10 m | 86/100 | TBD |
| Out-of-terrain-X | 28/100 | TBD |

Return 최솟값/최댓값: **-18.0859 / 98.2898**.

### Stage 1 Reward Decomposition

각 값은 평균 ± population std로 표시한다.

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

## Stage 2 — Contact + Modified Reward 비교

### Modified Reward 설계 이유

단순한 전진 보상 위주로 학습할 때 반복적인 jumping/hopping 형태의 이동이 나타나는 경향을 완화하고, 지면 접촉, foot slip, joint motion, control effort를 함께 고려하도록 reward objective를 확장하였다.

이는 reward shaping의 설계 목적이며, 개별 term의 효과가 검증됐다는 의미는 아니다. 두 조건은 동일한 Contact observation과 Team1 v3_depth Modified Reward를 **학습과 평가 모두에** 사용해야 한다. 같은 stage 안에서 비교하려는 변수는 terrain representation이다.

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

Stock Reward 대비 progress와 target-direction weight를 높이고, energy와 joint-limit penalty를 강화했다. Foot-contact reward, joint-velocity penalty, foot-slip penalty를 추가했으며, upright weight는 낮췄다. 이 실험만으로 개별 term의 인과적 효과를 분리할 수는 없다.

Team1 v3_depth의 `ant.rewards.TotalReward` 구현을 재사용하며, 저장된 training configuration과 component weight가 일치하는지 확인했다. Play용 evaluation reward는 사용하지 않는다.

### 공통 Contact 조건

Stage 2의 두 조건 모두 동일한 네 발을 대상으로 **world-frame net-force norm > 1 N** 여부를 **binary float32**로 관측하며, **history는 사용하지 않는다**.

> **Reward-side Contact의 별도 정의:** Foot-contact reward와 foot-slip penalty는 **3-frame 최대 vertical force > 5 N**을 사용한다. Contact bonus는 최소 두 발이 접촉할 때 부여하며, slip penalty는 접촉 중인 발의 XY 속도를 반영한다. Observation-side Contact와는 force 기준과 history 처리 방식이 다르다.

### Stage 2 결과

| 지표 | HeightScan + Contact + Modified | DepthCam + Contact + Modified |
|---|---:|---:|
| Return 평균 ± 표준편차 | 134.8413 ± 68.0187 | TBD |
| Displacement 평균 ± 표준편차 | 56.5627 ± 28.3639 m | TBD |
| Episode duration 평균 ± 표준편차 | 12.1187 ± 5.6815 s | TBD |
| 평균 전진 속도 | 4.0718 m/s | TBD |
| Fall | 43/100 | TBD |
| Timeout | 57/100 | TBD |
| ≥2 m | 86/100 | TBD |
| ≥5 m | 86/100 | TBD |
| ≥10 m | 84/100 | TBD |
| Out-of-terrain-X | 26/100 | TBD |

Return 최솟값/최댓값: **-0.2848 / 220.2166**.

### Stage 2 Reward Decomposition

각 값은 평균 ± population std로 표시한다. Total return을 직접 비교하려면 DepthCam 조건도 동일한 Modified Reward를 사용해야 한다.

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

## 비교 시 주의사항

> **Terrain 경계:** Team1 environment에는 map boundary 종료 조건이 없으므로 displacement와 progress에 생성된 terrain 범위를 벗어난 이동이 포함될 수 있다. 따라서 보고된 displacement 전체를 rough-terrain locomotion 거리로 해석하지 않는다.

| HeightScan 실험 | 종료 시 world-X가 terrain 범위를 벗어난 episode |
|---|---:|
| Stage 1: Stock | 28/100 |
| Stage 2: Contact + Modified | 26/100 |

생성된 terrain의 X 범위는 `[-102, 102]` m이다. 단일 seed 결과만으로 일반적인 통계적 유의성을 주장할 수 없으며, PPO 학습에는 확률적 변동이 존재한다.

### Protocol 및 결과 파일

| Stage | 공통 protocol | HeightScan 결과 |
|---|---|---|
| Stage 1 | [Stock protocol](protocol.json) | [Manifest 및 요약 결과](heightscan_4096x32x1000/manifest.json) |
| Stage 2 | [Contact + Modified protocol](shared/stage2_contact_modified_protocol.json) | [Manifest 및 요약 결과](heightscan_contact_modified_4096x32x1000/manifest.json) |

[이전 exploratory HeightScan run](heightscan/manifest.json)은 2048 × 32 × 10000 조건으로 수행했으며 참고 자료로 보존한다. 이 run은 위의 공통 학습 조건에 따른 비교 대상에 포함하지 않는다.

## 현재 진행 상태

| 실험 | 상태 |
|---|---|
| HeightScan + Stock | 완료 |
| DepthCam + Stock | 진행 예정 |
| HeightScan + Contact + Modified | 완료 |
| DepthCam + Contact + Modified | 진행 예정 |

DepthCam 결과는 해당 실험이 공통 protocol에 따라 완료되면 추가한다.
