"""시나리오 5.2(변경 대응)·5.3(설계 질의응답)·5.4(산출물 출력) — FakeModel 결정적 검증.

5.1 로 산출물을 채운 뒤 이어서 진행한다. 사용자 노출 문구에 저장 기술 용어가 새지 않는지도 확인.
"""

from pathlib import Path

from archiagent.agent import Agent
from archiagent.model import FakeModel
from archiagent.schema import DERIVED_FROM, REQUIREMENT
from archiagent.store import SqliteStore
from archiagent.tools import kb_change_assess, kb_doc_export

EXAMPLES = str(Path(__file__).resolve().parents[1] / "examples" / "bank-nextgen")

FORBIDDEN = [
    "그래프", "graph", "노드", "node", "엣지", "edge",
    "upsert", "벡터", "vector", "DERIVED_FROM", "DESCRIBES", "sqlite",
]

_SETUP = [
    "이 rfp.md 를 읽고 요구사항 정의서를 작성해.",
    "이 interview.md 내용도 읽고 요구사항 정의서에 더해.",
    "현행 시스템 문서 current-system.md 를 읽고 현행 시스템 분석서를 작성해.",
    "요구사항과 현행 시스템 분석서를 기반으로 설계서를 작성해.",
]


def _agent():
    a = Agent(SqliteStore(), FakeModel(), project_dir=EXAMPLES)
    for c in _SETUP:
        a.handle(c)
    return a


def test_5_2_impact_named_requirement():
    a = _agent()
    resp = a.handle("R-4 무중단 요건이 바뀌면 영향도가 어떻게 돼?")
    assert "R-4" in resp
    assert "아키텍처 설계서" in resp           # 추적성 역추적으로 영향 산출물 식별
    assert "현행 시스템 분석서" in resp
    _no_leak(resp)


def test_5_2_reflect_adds_requirement_and_updates_design():
    a = _agent()
    assert a.store.count(REQUIREMENT) == 10
    resp = a.handle("change.md 의 변경을 요구사항 정의서와 설계서에 반영해.")
    assert a.store.count(REQUIREMENT) == 11   # R-11 추가
    # 설계 추적성도 11건으로 갱신
    assert len(a.store.edges(rel=DERIVED_FROM, src="doc:design")) == 11
    assert "반영" in resp
    _no_leak(resp)


def test_change_assess_judges_relevance():
    m = FakeModel()
    v1 = kb_change_assess(m, "재해 복구를 위해 클라우드 리전을 두 곳으로 이중화한다.")
    assert v1["relevant"] is True and v1["reason"]
    v2 = kb_change_assess(m, "담당자 이름 오타를 수정한다.")
    assert v2["relevant"] is False and v2["reason"]


def test_5_2_reflect_skips_design_when_irrelevant(tmp_path):
    # 설계와 무관한 변경은 요구로는 반영하되 설계서는 건드리지 않는다(모델 판단).
    a = _agent()
    before = len(a.store.edges(rel=DERIVED_FROM, src="doc:design"))
    (tmp_path / "memo.md").write_text("- 담당자 이름 오타를 수정한다.\n", encoding="utf-8")
    a.project_dir = tmp_path
    resp = a.handle("memo.md 의 변경을 반영해.")
    assert a.store.count(REQUIREMENT) == 11
    assert len(a.store.edges(rel=DERIVED_FROM, src="doc:design")) == before
    _no_leak(resp)


def test_5_3_design_qa_node_specs():
    a = _agent()
    resp = a.handle("운영 환경 노드마다 IP랑 CPU, 메모리, 디스크 크기를 정리해줘.")
    assert "core-01" in resp and "10.0.1.21" in resp
    assert "db-01" in resp
    _no_leak(resp)


def test_5_4_export_writes_html(tmp_path):
    a = _agent()
    a.out_dir = str(tmp_path)
    resp = a.handle("현재 산출물을 문서별로 HTML로 만들어.")
    files = {p.name for p in tmp_path.iterdir()}
    assert files == {"requirements.html", "current-system.html", "design.html"}
    req_html = (tmp_path / "requirements.html").read_text(encoding="utf-8")
    assert "클라우드" in req_html and "R-1" in req_html
    cur_html = (tmp_path / "current-system.html").read_text(encoding="utf-8")
    assert "10.0.1.21" in cur_html
    assert ".html" in resp
    _no_leak(resp)


def test_export_tool_reflects_latest_state(tmp_path):
    # 출력 내용은 저장된 산출물에서 오므로 항상 최신과 같다.
    a = _agent()
    a.handle("change.md 의 변경을 요구사항 정의서와 설계서에 반영해.")
    kb_doc_export(a.store, str(tmp_path))
    design_html = (tmp_path / "design.html").read_text(encoding="utf-8")
    assert "R-11" in design_html  # 반영된 변경이 출력물에도 반영됨


def _no_leak(text: str) -> None:
    low = text.lower()
    for term in FORBIDDEN:
        assert term.lower() not in low, f"사용자 노출 문구에 내부 용어 누출: {term!r}"
