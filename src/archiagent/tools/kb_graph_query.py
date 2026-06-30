"""kb_graph_query — 산출물과 연관 관계를 조회한다(결정적, 모델 불필요).

추적성·영향도·질의응답의 사실 근거는 모두 여기서 나온다(모델 추측이 아니라 저장된 사실).
"""

from __future__ import annotations

from archiagent.schema import ARTIFACT, DERIVED_FROM, REQUIREMENT, SYSTEM_NODE
from archiagent.store.base import GraphStore


def requirements(store: GraphStore) -> list[dict]:
    return [{"id": n.id, "text": n.title} for n in store.nodes(REQUIREMENT)]


def system_nodes(store: GraphStore) -> list[dict]:
    return [{"id": n.id, **n.props} for n in store.nodes(SYSTEM_NODE)]


def next_requirement_id(store: GraphStore) -> int:
    """다음 요구 항목 번호(R-{n}). 멱등 적재를 위해 기존 개수에서 이어 붙인다."""
    nums = []
    for n in store.nodes(REQUIREMENT):
        if n.id.startswith("R-") and n.id[2:].isdigit():
            nums.append(int(n.id[2:]))
    return (max(nums) + 1) if nums else 1


def design_context(store: GraphStore) -> dict:
    """설계서 생성에 넘길 맥락(요구 + 현행)."""
    return {"requirements": requirements(store), "systems": system_nodes(store)}


def impact(store: GraphStore, req_id: str | None = None) -> dict:
    """변경 영향도 — 추적성(저장된 연결)을 역추적해 영향 받는 산출물을 찾는다.

    모델 추측이 아니라 저장된 도출 관계(설계 -DERIVED_FROM-> 요구)에서 계산한다.
    req_id 가 주어지면 그 요구가 이어진 설계 산출물을, 아니면(신규/미지정 변경)
    갱신이 필요한 산출물을 돌려준다.
    """
    titles = {n.id: n.title for n in store.nodes(ARTIFACT)}
    if req_id and store.get(req_id) is not None:
        req = store.get(req_id)
        impacted = [
            titles[e.src] for e in store.edges(rel=DERIVED_FROM, dst=req_id) if e.src in titles
        ]
        return {"requirement": {"id": req_id, "text": req.title}, "impacted": impacted}
    impacted = [titles[a] for a in ("doc:design",) if a in titles]
    return {"requirement": None, "impacted": impacted}
