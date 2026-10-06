#!/usr/bin/env bash
# isaaclab conda 환경에서 이 저장소를 설치하고 play_one_episode.py를 실행한다.
# 사용법: conda activate isaaclab && bash setup_and_play.sh

set -eo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${REPO_DIR}"

# 1. 활성화된 conda 환경에 Isaac Lab이 셋팅되어 있는지 확인
if [ -z "${CONDA_PREFIX}" ]; then
    echo "[ERROR] 활성화된 conda 환경이 없습니다. Isaac Lab이 설치된 conda 환경을 activate 후 실행하세요." >&2
    exit 1
fi

python - <<'EOF'
import importlib.util
import sys

required = ["isaacsim", "isaaclab", "isaaclab_rl", "isaaclab_tasks", "rsl_rl"]
missing = [name for name in required if importlib.util.find_spec(name) is None]
if missing:
    print(f"[ERROR] 현재 conda 환경에 Isaac Lab 셋팅이 되어 있지 않습니다. 누락된 모듈: {', '.join(missing)}", file=sys.stderr)
    sys.exit(1)
EOF

# 2. 패키지 설치
python -m pip install -e .
