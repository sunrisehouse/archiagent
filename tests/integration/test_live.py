"""실제 Claude 모델로 5.1 흐름 검증 (구독 OAuth 또는 API 키 필요).

자격(= `claude` CLI 사용 가능)이 없으면 자동 skip. 실모델 출력은 변동적이므로 느슨하게 단언한다.
실행: pytest -m integration
"""

from pathlib import Path

import pytest

from archiagent.agent import Agent
from archiagent.model import get_default_model
from archiagent.schema import ARTIFACT, DERIVED_FROM, REQUIREMENT, SYSTEM_NODE
from archiagent.store import SqliteStore

EXAMPLES = str(Path(__file__).resolve().parents[2] / "examples" / "bank-nextgen")

pytestmark = pytest.mark.integration


@pytest.fixture
def live_agent():
    model = get_default_model()
    if model is None:
        pytest.skip("실모델 자격 없음 (claude CLI / 구독 OAuth 미설정)")
    return Agent(SqliteStore(), model, project_dir=EXAMPLES)


def test_live_5_1_end_to_end(live_agent):
    store = live_agent.store
    live_agent.handle("이 rfp.md 를 읽고 요구사항 정의서를 작성해.")
    live_agent.handle("이 interview.md 내용도 읽고 요구사항 정의서에 더해.")
    live_agent.handle("현행 시스템 문서 current-system.md 를 읽고 현행 시스템 분석서를 작성해.")
    resp = live_agent.handle("요구사항과 현행 시스템 분석서를 기반으로 설계서를 작성해.")

    assert store.count(REQUIREMENT) >= 5      # 최소 RFP 5건
    assert store.count(SYSTEM_NODE) >= 1      # 현행 서버 추출
    assert any(n.id == "doc:design" for n in store.nodes(ARTIFACT))
    assert len(store.edges(rel=DERIVED_FROM, src="doc:design")) >= 1  # 추적성 연결
    assert "저장" in resp
