"""오케스트레이터 — 자연어 요청을 의도로 해석해 도구를 호출하고, 저장 전 사람 확인 게이트를 건다.

사용자에게 보이는 모든 문구는 문서 수준 언어만 쓴다(저장 기술 용어 금지). 슬라이스(5.1)에서는
의도를 규칙 기반으로 라우팅한다: 요구사항 작성 / 현행 분석 / 설계서 작성.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from archiagent.model.base import ModelClient
from archiagent.store.base import GraphStore
from archiagent.tools import kb_artifact_ingest, kb_doc_generate, kb_graph_upsert

# 항상 저장을 승인하는 기본 게이트(테스트·자동 모드용).
ALWAYS: Callable[[str], bool] = lambda _preview: True

_MD = re.compile(r"([\w./-]+\.md)")


class Agent:
    MAX_STEPS = 8  # 정지 조건: 한 요청이 무한히 돌지 않도록.

    def __init__(self, store: GraphStore, model: ModelClient, project_dir: str = ".") -> None:
        self.store = store
        self.model = model
        self.project_dir = Path(project_dir)

    def handle(self, command: str, confirm: Callable[[str], bool] = ALWAYS) -> str:
        intent, filename = self._route(command)
        if intent == "ingest_current_system":
            return self._ingest(filename, "current_system", confirm)
        if intent == "ingest_requirements":
            return self._ingest(filename, "requirements", confirm)
        if intent == "generate_design":
            return self._design(confirm)
        return (
            "이런 것을 도와드릴 수 있습니다: 요구사항 정의서 작성(예: \"이 rfp.md 읽고 "
            "요구사항 정의서 작성해\"), 현행 시스템 분석서 작성, 요구·현행 기반 설계서 작성."
        )

    # --- 의도 라우팅 ---
    def _route(self, command: str) -> tuple[str, str | None]:
        m = _MD.search(command)
        filename = m.group(1) if m else None
        low = command.lower()
        if filename and ("현행" in command or "current" in filename.lower()):
            return "ingest_current_system", filename
        if filename and (
            "요구사항" in command
            or "요구" in command
            or "rfp" in low
            or "인터뷰" in command
            or "interview" in filename.lower()
        ):
            return "ingest_requirements", filename
        if "설계서" in command and ("작성" in command or "기반" in command or "만들" in command):
            return "generate_design", None
        return "help", filename

    # --- 핸들러 ---
    def _ingest(self, filename: str | None, kind: str, confirm: Callable[[str], bool]) -> str:
        if not filename:
            return "어떤 파일을 읽을지 알려주세요(예: rfp.md)."
        path = self.project_dir / filename
        if not path.exists():
            return f"파일을 찾지 못했습니다: {filename}"
        proposal = kb_artifact_ingest(self.store, self.model, path.read_text(encoding="utf-8"), kind)
        if confirm(f"{proposal.summary}\n이 내용을 저장할까요?"):
            kb_graph_upsert(self.store, proposal)
            doc = proposal.nodes[0].title
            return f"{doc}를 저장했습니다."
        return "저장하지 않았습니다."

    def _design(self, confirm: Callable[[str], bool]) -> str:
        proposal = kb_doc_generate(self.store, self.model)
        if confirm(f"{proposal.summary}\n이 내용을 저장할까요?"):
            kb_graph_upsert(self.store, proposal)
            return "아키텍처 설계서를 저장하고, 요구사항과의 추적성을 연결했습니다."
        return "저장하지 않았습니다."
