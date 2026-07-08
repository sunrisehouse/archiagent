"""시연용 데모 플레이어 — 화면녹화하기 좋게 시나리오를 재생한다.

실제 에이전트가 실제 모델(구독)로 응답한다. 명령은 타이핑 애니메이션으로 보여주고,
저장 게이트는 자동으로 승인한다. 은행 차세대 시나리오(5.1~5.4)를 순서대로 시연한다.

사용법:
  python scripts/demo.py                # 실제 모델(있으면), 없으면 오프라인(예시)
  python scripts/demo.py --fake         # 오프라인(예시) 모드로 빠르게
  python scripts/demo.py --slow         # 타이핑 더 천천히
  python scripts/demo.py --fast         # 타이핑 빠르게
  python scripts/demo.py --dir examples/bank-nextgen
"""

from __future__ import annotations

import itertools
import random
import sys
import threading
import time
from pathlib import Path

from archiagent.agent import Agent
from archiagent.model import FakeModel, get_default_model
from archiagent.store import SqliteStore

TYPE = 0.07    # 글자당 기본 타이핑 지연(초)
PAUSE = 0.9    # 단계 사이 멈춤(초)
SPEED = 1.0    # 타이핑 속도 배율(작을수록 빠름) — --slow/--fast 로 조절
_TTY = sys.stdout.isatty()


def _type(text: str) -> None:
    """사람이 치는 것처럼 글자마다 속도를 불규칙하게, 띄어쓰기·문장부호에서 살짝 쉰다."""
    base = TYPE * SPEED
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        d = base * random.uniform(0.55, 1.7)   # 글자마다 흔들림
        if ch == " ":
            d += base * 1.3
        elif ch in ".,?!…":
            d += base * 2.5
        time.sleep(d)
    print()


class Spinner:
    """모델이 응답하는 동안(정지 구간) 도는 표시. 게이트 때는 pause 로 잠시 멈춘다.

    TTY 가 아니면(파이프 등) 아무것도 하지 않는다.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active = False
        self._paused = False
        self._thread: threading.Thread | None = None

    def _spin(self) -> None:
        frames = itertools.cycle("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏")
        while self._active:
            with self._lock:
                if not self._paused:
                    sys.stdout.write(f"\r\033[38;5;99m{next(frames)}\033[0m 처리 중…  ")
                    sys.stdout.flush()
            time.sleep(0.09)

    def start(self) -> None:
        if not _TTY:
            return
        self._active = True
        self._paused = False
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def pause(self) -> None:
        if not _TTY:
            return
        with self._lock:
            self._paused = True
            sys.stdout.write("\r\033[K")
            sys.stdout.flush()

    def resume(self) -> None:
        with self._lock:
            self._paused = False

    def stop(self) -> None:
        self._active = False
        if self._thread:
            self._thread.join()
            self._thread = None
        if _TTY:
            sys.stdout.write("\r\033[K")
            sys.stdout.flush()


_spinner = Spinner()


def _banner(title: str) -> None:
    print(f"\n\033[38;5;99m{'─' * 64}\033[0m")
    print(f"  \033[1m{title}\033[0m")
    print(f"\033[38;5;99m{'─' * 64}\033[0m")
    time.sleep(0.5)


def _confirm(preview: str) -> bool:
    _spinner.pause()
    print(preview)
    sys.stdout.write("> (y/n) ")
    sys.stdout.flush()
    time.sleep(0.6)
    _type("y")
    time.sleep(0.3)
    _spinner.resume()
    return True


def _ask(agent: Agent, cmd: str) -> None:
    sys.stdout.write("\n\033[38;5;99m>\033[0m ")
    sys.stdout.flush()
    time.sleep(0.4)
    _type(cmd)
    time.sleep(0.3)
    _spinner.start()
    resp = agent.handle(cmd, confirm=_confirm)
    _spinner.stop()
    print(resp)
    time.sleep(PAUSE)


def main(argv: list[str] | None = None) -> int:
    global SPEED
    argv = argv if argv is not None else sys.argv[1:]
    fake = "--fake" in argv
    if "--slow" in argv:
        SPEED = 1.7
    elif "--fast" in argv:
        SPEED = 0.5
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
