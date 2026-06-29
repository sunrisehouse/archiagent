"""archiagent CLI — 인터랙티브 REPL.

작업 폴더에 둔 자료 파일을 자연어로 가리키면 에이전트가 읽어 산출물을 작성한다.
저장 전에는 미리보기를 보여주고 y/n 확인을 받는다. 저장 기술은 사용자에게 드러내지 않는다.
"""

from __future__ import annotations

import sys

from archiagent.agent import Agent
from archiagent.model import FakeModel, get_default_model
from archiagent.store import SqliteStore


def _confirm(preview: str) -> bool:
    print(preview)
    try:
        ans = input("> (y/n) ").strip().lower()
    except EOFError:
        return False
    return ans in ("y", "yes", "ㅛ", "예")


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    project_dir = argv[0] if argv else "."

    model = get_default_model() or FakeModel()
    store = SqliteStore()  # 세션 메모리 저장(파일 경로를 주면 영속).
    agent = Agent(store, model, project_dir=project_dir)

    where = "실제 모델" if model.name == "claude" else "오프라인(예시) 모드"
    print(f"archiagent를 시작합니다 [{where}]. 무엇을 도와드릴까요? (종료: Ctrl-D)")
    while True:
        try:
            command = input("\n> ").strip()
        except EOFError:
            print()
            return 0
        if not command:
            continue
        print(agent.handle(command, confirm=_confirm))
