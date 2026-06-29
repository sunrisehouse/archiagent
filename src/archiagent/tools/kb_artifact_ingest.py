"""kb_artifact_ingest — 입력 문서를 읽어 산출물 초안을 만든다(저장 전 미리보기).

쓰기는 하지 않는다. 사람 확인 게이트를 통과하면 kb_graph_upsert 가 저장한다.
"""

from __future__ import annotations

from archiagent.model.base import ModelClient
from archiagent.schema import (
    ARTIFACT,
    DESCRIBES,
    REQUIREMENT,
    SYSTEM_NODE,
    Edge,
    Node,
    Proposal,
)
from archiagent.store.base import GraphStore
from archiagent.tools.kb_graph_query import next_requirement_id

# 산출물 종류 → (artifact 노드 id, 사람에게 보일 산출물 이름, SI 단계)
_REQ_DOC = ("doc:requirements", "요구사항 정의서", "분석")
_CUR_DOC = ("doc:current-system", "현행 시스템 분석서", "분석")


def kb_artifact_ingest(
    store: GraphStore, model: ModelClient, text: str, as_kind: str
) -> Proposal:
    if as_kind == "requirements":
        return _ingest_requirements(store, model, text)
    if as_kind == "current_system":
        return _ingest_current_system(store, model, text)
    raise ValueError(f"unknown as_kind: {as_kind}")


def _ingest_requirements(store: GraphStore, model: ModelClient, text: str) -> Proposal:
    result = model.run("extract_requirements", text)
    items = result.get("requirements", [])
    doc_id, doc_title, stage = _REQ_DOC
    nodes: list[Node] = [Node(id=doc_id, type=ARTIFACT, title=doc_title, props={"stage": stage})]
    edges: list[Edge] = []
    start = next_requirement_id(store)
    new_ids = []
    for i, item in enumerate(items):
        rid = f"R-{start + i}"
        new_ids.append(rid)
        nodes.append(Node(id=rid, type=REQUIREMENT, title=item.get("text", "").strip()))
        edges.append(Edge(src=doc_id, rel=DESCRIBES, dst=rid))
    listing = "\n".join(f"  {rid} {n.title}" for rid, n in zip(new_ids, nodes[1:]))
    summary = (
        f"{doc_title} 초안입니다. 요구 항목 {len(new_ids)}건"
        + (f" ({new_ids[0]} ~ {new_ids[-1]})" if new_ids else "")
        + (f".\n{listing}" if listing else ".")
    )
    return Proposal(nodes=nodes, edges=edges, summary=summary)


def _ingest_current_system(store: GraphStore, model: ModelClient, text: str) -> Proposal:
    result = model.run("extract_current_system", text)
    systems = result.get("systems", [])
    note = result.get("note", "").strip()
    doc_id, doc_title, stage = _CUR_DOC
    props = {"stage": stage}
    if note:
        props["note"] = note
    nodes: list[Node] = [Node(id=doc_id, type=ARTIFACT, title=doc_title, props=props)]
    edges: list[Edge] = []
    for sysinfo in systems:
        name = sysinfo.get("name", "").strip()
        if not name:
            continue
        spec = {k: sysinfo.get(k, "") for k in ("ip", "cpu", "memory", "disk")}
        nodes.append(Node(id=name, type=SYSTEM_NODE, title=name, props=spec))
        edges.append(Edge(src=doc_id, rel=DESCRIBES, dst=name))
    listing = "\n".join(
        f"  {n.id}  IP {n.props.get('ip','')} · {n.props.get('cpu','')} · "
        f"메모리 {n.props.get('memory','')} · 디스크 {n.props.get('disk','')}"
        for n in nodes[1:]
    )
    summary = f"{doc_title} 초안입니다. 서버 {len(nodes) - 1}대." + (f"\n{listing}" if listing else "")
    if note:
        summary += f"\n  {note}"
    return Proposal(nodes=nodes, edges=edges, summary=summary)
