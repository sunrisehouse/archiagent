#!/usr/bin/env bash
# archiagent 개발 환경 1회 셋업: 패키지를 editable 로 설치(+ 테스트 의존성).
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m pip install -e ".[dev]" -q
echo "설치 완료. 테스트: pytest -q   |   실행: archiagent examples/bank-nextgen"
