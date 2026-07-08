"""시연용 데모 플레이어 — 화면녹화하기 좋게 시나리오를 재생한다.

실제 에이전트가 실제 모델(구독)로 응답한다. 명령은 타이핑 애니메이션으로 보여주고,
저장 게이트는 자동으로 승인한다. 은행 차세대 시나리오(5.1~5.4)를 순서대로 시연한다.

사용법:
  python scripts/demo.py                # 실제 모델(있으면), 없으면 오프라인(예시)
  python scripts/demo.py --fake         # 오프라인(예시) 모드로 빠르게
  python scripts/demo.py --dir examples/bank-nextgen
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from archiagent.agent import Agent
from archiagent.model import FakeModel, get_default_model
from archiagent.store import SqliteStore

TYPE = 0.035   # 글자당 타이핑 지연(초)
PAUSE = 0.9    # 단계 사이 멈춤(초)


def _type(text: str, delay: float = TYPE) -> None:
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def _banner(title: str) -> None:
    print(f"\n\033[38;5;99m{'─' * 64}\033[0m")
    print(f"  \033[1m{title}\033[0m")
    print(f"\033[38;5;99m{'─' * 64}\033[0m")
    time.sleep(0.5)


def _confirm(preview: str) -> bool:
    print(preview)
    sys.stdout.write("> (y/n) ")
    sys.stdout.flush()
    time.sleep(0.6)
    _type("y", 0.06)
    time.sleep(0.3)
    return True


def _ask(agent: Agent, cmd: str) -> None:
    sys.stdout.write("\n\033[38;5;99m>\033[0m ")
    sys.stdout.flush()
    time.sleep(0.4)
    _type(cmd)
    time.sleep(0.4)
    print(agent.handle(cmd, confirm=_confirm))
    time.sleep(PAUSE)


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    fake = "--fake" in argv
    project = "examples/bank-nextgen"
    if "--dir" in argv:
        project = argv[argv.index("--dir") + 1]

    model = FakeModel() if fake else (get_default_model() or FakeModel())
    where = "실제 모델" if model.name == "claude" else "오프라인(예시) 모드"
    agent = Agent(SqliteStore(), model, project_dir=project, out_dir="out")

    print(f"\033[1marchiagent\033[0m 시연 — 은행 차세대 시스템 [{where}]")
    time.sleep(0.8)

    _banner("5.1 산출물 작성 — 분석 → 설계")
    _ask(agent, "이 rfp.md 를 읽고 요구사항 정의서를 작성해.")
    _ask(agent, "이 interview.md 내용도 읽고 요구사항 정의서에 더해.")
    _ask(agent, "현행 시스템 문서 current-system.md 를 읽고 현행 시스템 분석서를 작성해.")
    _ask(agent, "요구사항과 현행 시스템 분석서를 기반으로 설계서를 작성해.")

    _banner("5.2 변경 대응 — 영향도 + 판단 반영")
    _ask(agent, "R-4 무중단 요건이 바뀌면 영향도가 어떻게 돼?")
    _ask(agent, "change.md 의 변경을 요구사항 정의서와 설계서에 반영해.")

    _banner("5.3 설계 질의응답 — 운영 환경 사양")
    _ask(agent, "운영 환경 노드마다 IP랑 CPU, 메모리, 디스크 크기를 정리해줘.")

    _banner("5.4 산출물 출력 — 문서별 HTML")
    _ask(agent, "현재 산출물을 문서별로 HTML로 만들어.")

    print("\n\033[1m시연 종료.\033[0m")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
