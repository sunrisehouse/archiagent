"""모델 인터페이스.

도구는 `run(kind, content, context)` 한 메서드로 구조화 출력(dict)을 받는다.
kind 는 작업 종류(extract_requirements / extract_current_system / generate_design).
구현은 교체 가능: FakeModel(결정적, 테스트 기본) ↔ ClaudeModel(실제 호출, 구독/키).
"""

from __future__ import annotations

from typing import Any, Protocol


class ModelClient(Protocol):
    name: str

    def run(self, kind: str, content: str, context: dict | None = None) -> dict[str, Any]:
        ...
