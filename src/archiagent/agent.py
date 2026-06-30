"""오케스트레이터 — 자연어 요청을 의도로 해석해 도구를 호출하고, 저장 전 사람 확인 게이트를 건다.

사용자에게 보이는 모든 문구는 문서 수준 언어만 쓴다(저장 기술 용어 금지).
지원 시나리오: 5.1 산출물 작성 / 5.2 변경 대응(영향도·반영) / 5.3 설계 질의응답 / 5.4 산출물 출력.
의도는 규칙 기반으로 라우팅한다.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from archiagent.model.base import ModelClient
from archiagent.store.base import GraphStore
from archiagent.tools import (
    impact,
    kb_artifact_ingest,
    kb_doc_export,
    kb_doc_generate,
    kb_graph_upsert,
    system_nodes,
)
from archiagent.schema import REQUIREMENT

# 항상 저장을 승인하는 기본 게이트(테스트·자동 모드용).
ALWAYS: Callable[[str], bool] = lambda _preview: True

_MD = re.compile(r"([\w./-]+\.md)")
_RID = re.compile(r"\bR-\d+\b")


class Agent:
    MAX_STEPS = 8  # 정지 조건: 한 요청이 무한히 돌지 않도록.

    def __init__(
        self,
        store: GraphStore,
        model: ModelClient,
        project_dir: str = ".",
        out_dir: str = "out",
    ) -> None:
        self.store = store
        self.model = model
        self.project_dir = Path(project_dir)
        self.out_dir = out_dir

    def handle(self, command: str, confirm: Callable[[str], bool] = ALWAYS) -> str:
        intent, kw = self._route(command)
        return getattr(self, f"_{intent}")(confirm=confirm, **kw)

    # --- 의도 라우팅 ---
    def _route(self, command: str) -> tuple[str, dict]:
        fm = _MD.search(command)
        filename = fm.group(1) if fm else None
        rm = _RID.search(command)
        req_id = rm.group(0) if rm else None
        low = command.lower()

        if "영향도" in command:
            return "impact", {"req_id": req_id}
        if "반영" in command:
            return "reflect", {"filename": filename or "change.md"}
        if ("html" in low) or ("출력" in command) or ("문서로" in command and "만들" in command):
            return "export", {}
        if not filename and any(k in command for k in ("운영 환경", "노드", "사양")):
            return "query_nodes", {}
        if filename and ("현행" in command or "current" in filename.lower()):
            return "ingest", {"filename": filename, "kind": "current_system"}
        if filename and (
            "요구" in command
            or "rfp" in low
            or "인터뷰" in command
            or "interview" in filename.lower()
        ):
            return "ingest", {"filename": filename, "kind": "requirements"}
        if "설계서" in command and ("작성" in command or "기반" in command or "만들" in command):
            return "design", {}
        return "help", {}

    # --- 핸들러 ---
    def _ingest(self, filename: str | None, kind: str, confirm: Callable[[str], bool]) -> str:
        text = self._read(filename)
        if text is None:
            return f"파일을 찾지 못했습니다: {filename}"
        proposal = kb_artifact_ingest(self.store, self.model, text, kind)
        if confirm(f"{proposal.summary}\n이 내용을 저장할까요?"):
            kb_graph_upsert(self.store, proposal)
            return f"{proposal.nodes[0].title}를 저장했습니다."
        return "저장하지 않았습니다."

    def _design(self, confirm: Callable[[str], bool]) -> str:
        proposal = kb_doc_generate(self.store, self.model)
        if confirm(f"{proposal.summary}\n이 내용을 저장할까요?"):
            kb_graph_upsert(self.store, proposal)
            return "아키텍처 설계서를 저장하고, 요구사항과의 추적성을 연결했습니다."
        return "저장하지 않았습니다."

    def _impact(self, req_id: str | None, confirm: Callable[[str], bool]) -> str:
        info = impact(self.store, req_id)  # 조회 — 게이트 없음
        if info["requirement"]:
            req = info["requirement"]
            arts = ", ".join(info["impacted"]) if info["impacted"] else "아직 연결된 설계 산출물 없음"
            return (
                f"{req['id']}({req['text']}) 변경의 영향 범위입니다.\n"
                f"  영향 받는 산출물: {arts}\n"
                f"  함께 볼 산출물: 현행 시스템 분석서"
            )
        tail = "아키텍처 설계서 재작성에 영향을 줍니다." if info["impacted"] else "이후 설계 작성에 반영됩니다."
        return f"이 변경은 요구사항 정의서 갱신과 {tail}\n  함께 볼 산출물: 현행 시스템 분석서"

    def _reflect(self, filename: str, confirm: Callable[[str], bool]) -> str:
        text = self._read(filename)
        if text is None:
            return f"변경 내용을 담은 파일을 찾지 못했습니다: {filename}"
        proposal = kb_artifact_ingest(self.store, self.model, text, "requirements")
        preview = (
            f"{proposal.summary}\n그리고 이 변경을 반영해 아키텍처 설계서를 갱신합니다."
            "\n이 내용을 저장할까요?"
        )
        if not confirm(preview):
            return "반영하지 않았습니다."
        kb_graph_upsert(self.store, proposal)
        kb_graph_upsert(self.store, kb_doc_generate(self.store, self.model))
        added = sum(1 for n in proposal.nodes if n.type == REQUIREMENT)
        return f"요구사항 정의서에 {added}건을 반영하고, 아키텍처 설계서를 갱신했습니다."

    def _query_nodes(self, confirm: Callable[[str], bool]) -> str:
        rows = system_nodes(self.store)  # 조회 — 게이트 없음
        if not rows:
            return "아직 현행 시스템 분석서가 없습니다."
        lines = ["운영 환경 서버 사양입니다."]
        for r in rows:
            lines.append(
                f"  {r['id']}  IP {r.get('ip','')} · {r.get('cpu','')} · "
                f"메모리 {r.get('memory','')} · 디스크 {r.get('disk','')}"
            )
        return "\n".join(lines)

    def _export(self, confirm: Callable[[str], bool]) -> str:
        written = kb_doc_export(self.store, self.out_dir)
        if not written:
            return "출력할 산출물이 없습니다."
        lines = ["다음 문서를 만들었습니다."]
        for path, title in written:
            lines.append(f"  {path}  ({title})")
        return "\n".join(lines)

    def _help(self, confirm: Callable[[str], bool]) -> str:
        return (
            "이런 것을 도와드릴 수 있습니다: 산출물 작성(요구사항 정의서·현행 시스템 분석서·설계서), "
            "변경 영향도 확인과 반영, 운영 환경 사양 정리, 산출물을 문서로 출력."
        )

    # --- 유틸 ---
    def _read(self, filename: str | None) -> str | None:
        if not filename:
            return None
        path = self.project_dir / filename
        return path.read_text(encoding="utf-8") if path.exists() else None
