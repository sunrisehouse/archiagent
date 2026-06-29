from archiagent.model import FakeModel
from archiagent.schema import ARTIFACT, DERIVED_FROM, REQUIREMENT, SYSTEM_NODE
from archiagent.store import SqliteStore
from archiagent.tools import (
    kb_artifact_ingest,
    kb_doc_generate,
    kb_graph_upsert,
    next_requirement_id,
)

RFP = "# RFP\n- 클라우드 전환\n- MSA 전환\n- 모니터링 체계\n"
CUR = (
    "# 현행\n- 업무 서버 core-01 (IP 10.0.1.21, vCPU 8, 메모리 32GB, 디스크 500GB)\n"
    "- 온프레미스 모놀리식\n"
)


def test_ingest_requirements_proposes_but_does_not_write():
    store, model = SqliteStore(), FakeModel()
    proposal = kb_artifact_ingest(store, model, RFP, "requirements")
    # 미리보기만 — 저장 전에는 비어 있어야 한다(사람 확인 게이트).
    assert store.count(REQUIREMENT) == 0
    assert sum(1 for n in proposal.nodes if n.type == REQUIREMENT) == 3
    kb_graph_upsert(store, proposal)
    assert store.count(REQUIREMENT) == 3
    assert next_requirement_id(store) == 4  # 다음은 R-4


def test_ingest_requirements_continues_ids_on_merge():
    store, model = SqliteStore(), FakeModel()
    kb_graph_upsert(store, kb_artifact_ingest(store, model, RFP, "requirements"))
    kb_graph_upsert(
        store, kb_artifact_ingest(store, model, "# 인터뷰\n- 무중단 배포\n", "requirements")
    )
    ids = sorted(n.id for n in store.nodes(REQUIREMENT))
    assert ids == ["R-1", "R-2", "R-3", "R-4"]  # 이어 붙음, 중복 없음


def test_ingest_current_system_parses_specs():
    store, model = SqliteStore(), FakeModel()
    kb_graph_upsert(store, kb_artifact_ingest(store, model, CUR, "current_system"))
    sysnodes = store.nodes(SYSTEM_NODE)
    assert len(sysnodes) == 1
    assert sysnodes[0].id == "core-01"
    assert sysnodes[0].props["ip"] == "10.0.1.21"


def test_doc_generate_links_traceability():
    store, model = SqliteStore(), FakeModel()
    kb_graph_upsert(store, kb_artifact_ingest(store, model, RFP, "requirements"))
    proposal = kb_doc_generate(store, model)
    kb_graph_upsert(store, proposal)
    design = [n for n in store.nodes(ARTIFACT) if n.id == "doc:design"]
    assert design and design[0].props["stage"] == "설계"
    # 요구 3건 모두에 추적성(DERIVED_FROM)이 연결되어야 한다.
    assert len(store.edges(rel=DERIVED_FROM, src="doc:design")) == 3
