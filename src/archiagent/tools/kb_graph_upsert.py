"""kb_graph_upsert — 미리보기(Proposal)를 저장한다. 사람 확인 게이트 통과 후에만 호출."""

from __future__ import annotations

from archiagent.schema import Proposal
from archiagent.store.base import GraphStore


def kb_graph_upsert(store: GraphStore, proposal: Proposal) -> None:
    store.upsert(proposal.nodes, proposal.edges)
