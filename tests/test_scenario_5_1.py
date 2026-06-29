"""시나리오 5.1 (산출물 작성) 엔드투엔드 — FakeModel 로 결정적 검증.

은행 차세대 시드 파일을 그대로 써서, 4개 명령으로 요구사항 정의서·현행 시스템 분석서·설계서가
저장되고 요구→설계 추적성이 연결되는지 확인한다. 또한 사용자에게 보이는 문구에 저장 기술
내부 용어가 새지 않는지 검증한다(설계 원칙).
"""

from pathlib import Path

from archiagent.agent import Agent
from archiagent.model import FakeModel
from archiagent.schema import ARTIFACT, DERIVED_FROM, REQUIREMENT, SYSTEM_NODE
from archiagent.store import SqliteStore

EXAMPLES = str(Path(__file__).resolve().parents[1] / "examples" / "bank-nextgen")

COMMANDS = [
    "이 rfp.md 를 읽고 요구사항 정의서를 작성해.",
    "이 interview.md 내용을 읽고 요구사항 정의서에 빠진 내용을 더해.",
    "현행 시스템 문서 current-system.md 를 읽고 현행 시스템 분석서를 작성해.",
    "요구사항과 현행 시스템 분석서를 기반으로 설계서를 작성해.",
]

# 사용자에게 절대 보이면 안 되는 저장 기술 내부 용어.
FORBIDDEN = [
    "그래프", "graph", "노드", "node", "엣지", "edge",
    "upsert", "벡터", "vector", "DERIVED_FROM", "DESCRIBES", "sqlite",
]


def _run_all():
    store, model = SqliteStore(), FakeModel()
    agent = Agent(store, model, project_dir=EXAMPLES)
    seen_text: list[str] = []

    def confirm(preview: str) -> bool:
        seen_text.append(preview)  # 게이트 미리보기도 사용자 노출 텍스트
        return True

    for cmd in COMMANDS:
        seen_text.append(agent.handle(cmd, confirm=confirm))
    return store, seen_text


def test_artifacts_and_traceability_created():
    store, _ = _run_all()
    # 요구 10건 (RFP 5 + 인터뷰 5), 연속 ID
    reqs = sorted((n.id for n in store.nodes(REQUIREMENT)), key=lambda x: int(x[2:]))
    assert reqs == [f"R-{i}" for i in range(1, 11)]
    # 현행 서버 3대
    assert store.count(SYSTEM_NODE) == 3
    # 산출물 3종: 요구사항 정의서·현행 시스템 분석서·아키텍처 설계서
    artifact_ids = {n.id for n in store.nodes(ARTIFACT)}
    assert {"doc:requirements", "doc:current-system", "doc:design"} <= artifact_ids
    # 요구→설계 추적성: 요구 10건 모두 연결
    assert len(store.edges(rel=DERIVED_FROM, src="doc:design")) == 10


def test_responses_use_document_language_only():
    _, seen_text = _run_all()
    blob = "\n".join(seen_text)
    assert "저장했습니다" in blob  # 문서 수준 표현으로 응답
    low = blob.lower()
    for term in FORBIDDEN:
        assert term.lower() not in low, f"사용자 노출 문구에 내부 용어 누출: {term!r}"
