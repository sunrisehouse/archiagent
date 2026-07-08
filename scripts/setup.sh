#!/usr/bin/env bash
# archiagent 개발 환경 1회 셋업: 패키지를 editable 로 설치(+ 테스트 의존성).
set -euo pipefail
cd "$(dirname "$0")/.."
# 오래된 pip/setuptools 는 pyproject-only 프로젝트의 editable 설치(PEP 660)를 못 해
# 옛 방식으로 떨어지며 setup.cfg/setup.py 를 찾는다. 먼저 빌드 도구를 올린다.
# (시스템 관리형 환경에서 업그레이드가 막혀도 설치는 진행하도록 실패 무시.)
python3 -m pip install --upgrade pip setuptools -q || true
python3 -m pip install -e ".[dev]" -q
echo "설치 완료. 테스트: pytest -q   |   실행: archiagent examples/bank-nextgen"
