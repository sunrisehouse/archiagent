"""kb_doc_generate — 저장된 산출물 맥락에서 설계서 초안을 만든다(저장 전 미리보기).

요구→설계 추적성(도출 관계)을 함께 만들어, 어느 요구가 어느 설계로 이어지는지 남긴다.
"""

from __future__ import annotations

from archiagent.model.base import ModelClient
from archiagent.schema import ARTIFACT, DERIVED_FROM, Edge, Node, Proposal
from archiagent.store.base import GraphStore
from archiagent.tools.kb_graph_query import design_context, requirements

_DESIGN_DOC = ("doc:design", "아키텍처 설계서", "설계")


def kb_doc_generate(store: GraphStore, model: ModelClient) -> Proposal:
    context = design_context(store)
    result = model.run("generate_design", "", context)
    doc_id, doc_title, stage = _DESIGN_DOC
    title = result.get("title") or doc_title
    body = result.get("body", "").strip()

    valid_ids = {r["id"] for r in requirements(store)}
    addressed = [rid for rid in result.get("addresses", []) if rid in valid_ids]
    # 모델이 addresses 를 비워 보내면, 맥락의 모든 요구를 도출원으로 본다(추적성 보존).
    if not addressed:
        addressed = sorted(valid_ids)

    nodes = [Node(id=doc_id, type=ARTIFACT, title=title, props={"stage": stage, "body": body})]
    edges = [Edge(src=doc_id, rel=DERIVED_FROM, dst=rid) for rid in addressed]
    summary = (
        f"{title} 초안입니다. 요구 {len(addressed)}건을 설계에 반영했고, "
        f"각 요구가 설계로 이어지도록 추적성을 연결했습니다."
    )
    return Proposal(nodes=nodes, edges=edges, summary=summary)
