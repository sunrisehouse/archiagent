"""kb_change_assess — 변경을 설계서에 반영해야 하는지 모델로 판단한다(쓰기 없음).

'무엇이 영향받나'(범위)는 kb_graph_query 가 저장된 연결에서 결정적으로 계산하고,
'설계에 반영할지'(내용 판단)는 여기서 모델이 판단한다.
"""

from __future__ import annotations

from archiagent.model.base import ModelClient


def kb_change_assess(model: ModelClient, change_text: str) -> dict:
    result = model.run("assess_change", change_text)
    return {
        "relevant": bool(result.get("relevant")),
        "reason": (result.get("reason") or "").strip(),
    }
