"""Tier-1 코어 메타스키마.

모든 산출물·요소는 Node 로, 그 사이 관계는 Edge 로 표현한다. 이 메타모델은 고정이며,
새 산출물 종류가 생겨도 같은 Node/Edge 위에 얹는다(Tier-2 레지스트리는 후속 단계).

주의: 여기서 쓰는 '노드/엣지'는 내부 구현 용어다. 사용자에게 보이는 문구에는
절대 노출하지 않는다(산출물·요구사항·추적성 같은 문서 수준 언어만 사용).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# --- Node 종류(내부) ---
ARTIFACT = "artifact"          # 문서 산출물 (요구사항 정의서, 현행 시스템 분석서, 설계서 ...)
REQUIREMENT = "requirement"    # 요구 항목 (R-1 ..)
SYSTEM_NODE = "system_node"    # 현행/운영 환경의 서버 등

# --- Edge 관계(내부) ---
DERIVED_FROM = "DERIVED_FROM"  # 설계서 -DERIVED_FROM-> 요구 (도출 관계 = 추적성)
DESCRIBES = "DESCRIBES"        # 산출물 -DESCRIBES-> 요구/서버 (해당 산출물이 담는 항목)
DEFINES = "DEFINES"            # 설계 -DEFINES-> 서비스/컴포넌트 (후속 단계용)

# SI 생애주기 단계 (도메인 지식 — 시스템 프롬프트와 일치)
STAGES = ("분석", "설계", "개발", "테스트", "이행")


@dataclass
class Node:
    id: str
    type: str
    title: str = ""
    props: dict[str, Any] = field(default_factory=dict)


@dataclass
class Edge:
    src: str
    rel: str
    dst: str


@dataclass
class Proposal:
    """저장 전 미리보기. 사람 확인 게이트를 통과해야 저장된다."""

    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    # 사용자에게 보여줄 문서 수준 요약(저장 기술 용어 금지)
    summary: str = ""
