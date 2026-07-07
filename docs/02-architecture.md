# 산출물 ② — 아키텍처 구성도 (콘텐츠)

> 콘텐츠 단일 소스. 슬라이드 디자인(`02-architecture.html`)은 이 MD를 입력으로 별도 입힌다.
> 슬라이드별: **목차 제목**(kicker) · **거버닝 메시지** · **내부 컨텐츠**.

---

## 1. 타이틀

- **목차 제목:** 산출물 ② · Architecture
- **거버닝 메시지:** archiagent는 Claude Agent SDK 기반 에이전트로 구성한다. Front와 Runtime, Model, MCP, Tools, Knowledge Base, Pipeline으로 이루어진다.
- **내부 컨텐츠:**
  - 제목: **아키텍처 구성도**

## 2. 전체 구성

- **목차 제목:** Overview
- **거버닝 메시지:** Chat UI가 Orchestrator를 호출하고, Orchestrator가 그래프 조회·작성 도구를 묶어 Graph DB와 Vector DB를 다룬다.
- **내부 컨텐츠:**
  - > 다이어그램: 6개 묶음으로 구성
  - ① Front — Chat UI · 그래프 뷰어
  - ② Agent Runtime (Claude Agent SDK) — Orchestrator Agent + 지식 그래프 subagent
  - ③ Model Provider — Anthropic Claude (Opus 4.8 / Sonnet 4.6 / Haiku 4.5)
  - ④ MCP Servers — Graph/KB MCP(내부)
  - ⑥ Knowledge Base — Graph DB · Vector DB
  - ⑦ Data Pipeline — 인제스트·LLM 추출·Upsert
  - 흐름: UI→Orchestrator→subagent→Graph/KB MCP→Graph/Vector DB / Orchestrator·subagent→Claude

## 3. ① Front — Front 구성

- **목차 제목:** ① Front
- **거버닝 메시지:** Front는 표현만 맡는다. 모든 추론과 조합은 Runtime이 담당한다.
- **내부 컨텐츠:** (카드)
  - **대화 뷰** — 아키텍트의 자연어 질의 입력 / 답변 출력. PoC에선 웹 챗 또는 CLI로 충분.
  - **그래프 뷰** — 서브그래프 시각화 (컴포넌트·의존성 관계)
  - **책임 분리** — Front는 표현만, 추론·조합은 Runtime

## 4. ② Agent Runtime — Orchestration · Instruction

- **목차 제목:** ② Agent Runtime
- **거버닝 메시지:** Orchestrator가 의도를 분해하고 라우팅하며, 지식 그래프 subagent가 설계 산출물을 조회·작성해 응답을 합성한다.
- **내부 컨텐츠:**
  - **Orchestration 부문:**
    - SDK `query()` 루프 진입점
    - 의도 분해 → 시나리오 라우팅(작성/영향도/Q&A)
    - 지식 그래프 조회·작성 = subagent
    - 정지 조건: 최대 반복 · 실패 시 graceful degrade
    - 비가역 작업(그래프 쓰기)은 `AskUserQuestion` 확인
  - **Agent Instruction · Prompt:**
    - Orchestrator: 역할·라우팅 휴리스틱
    - subagent: 그래프 모델·질의 패턴, "없으면 없다고", `concise|detailed`
    - 작성: As-Is 그래프 제약(노드 대수·용량) 읽어 ToBe 초안·충돌 경고
  - > 다이어그램(시퀀스): Architect→Orchestrator 질의 → subagent 그래프 조회(설계·추적성) → Orchestrator 합성 → 응답

## 5. ③④⑤ Provider · MCP · Tools — 모델 · MCP · 도구

- **목차 제목:** ③④⑤ Provider · MCP · Tools
- **거버닝 메시지:** `kb_*` 도구로 산출물을 다루며, 모델과 MCP와 도구를 용도별로 분리한다.
- **내부 컨텐츠:**
  - **③ Model Provider** (용도 | 모델):
    - 오케스트레이션·영향도(기본) | `claude-opus-4-8`
    - 라우틴 질의·요약 | `claude-sonnet-4-6`
    - 대량 엔티티 추출 | `claude-haiku-4-5`
  - **④ MCP Server:**
    - Graph/KB MCP — 우리 구현 (지식 그래프 subagent 백엔드)
  - **⑤ Tools** (도구 | 설명):
    - `kb_artifact_ingest` | 산출물 문서 → Artifact·엔티티 적재(확인)
    - `kb_doc_generate` | 그래프·대화 맥락 → 산출물 초안(작성·갱신)
    - `kb_graph_query` | 의존성·패턴·추적성 탐색
    - `kb_graph_upsert` | 노드·엣지 갱신(확인)
    - `kb_vector_search` | 자연어 의미검색

## 6. ⑥ Knowledge Base — 그래프 데이터 모델

- **목차 제목:** ⑥ Knowledge Base
- **거버닝 메시지:** Artifact와 설계 엔티티를 노드로 저장하고, 요구→설계→테스트 추적성을 엣지로 연결한다.
- **내부 컨텐츠:**
  - > 다이어그램: Artifact(요구·분석·설계·테스트) —DERIVED_FROM→ Artifact / —DEFINES→ Service·Component(DEPENDS_ON, EXPOSES API, STORES_IN Datastore, OWNED_BY Team) / ADR·Decision —AFFECTS→ Service / Artifact -.VALIDATES.-> Service
  - **Graph DB** (예: Neo4j): Artifact 노드는 `phase`·`type` 속성으로 SI 단계 표현. DERIVED_FROM으로 요구→설계→테스트 추적성, DEFINES/VALIDATES로 설계 엔티티 연결.
  - **Vector DB** (예: pgvector/Qdrant): 문서 청크·노드 설명 임베딩 → 자연어 질의를 그래프 진입점으로 변환.

## 7. ⑦ Data Pipeline — 작성·적재 → 그래프, 그리고 최신 유지

- **목차 제목:** ⑦ Data Pipeline
- **거버닝 메시지:** 작성과 적재로 Artifact와 추적성을 채워 Graph DB와 Vector DB를 항상 최신으로 유지한다.
- **내부 컨텐츠:**
  - > 다이어그램: 대화·인터뷰 → 초안(kb_doc_generate) →승인→ Upsert / 기존 SI 산출물 → LLM 추출(Haiku) → Upsert(Artifact 노드 + 추적성 엣지) → Graph/Vector DB
  - **작성·적재** (`kb_doc_generate` · `kb_artifact_ingest`): 작성 — 대화·인터뷰→초안→승인 후 Upsert. 적재 — 기존 문서→LLM 추출→Artifact+추적성 Upsert.

## 8. Open Questions — 남은 결정

- **목차 제목:** Open
- **거버닝 메시지:** 기획 의도와 시나리오는 산출물 ① `01-product-brief.html`을 참고한다.
- **내부 컨텐츠:**
  - Graph DB / Vector DB 제품 선정 (Neo4j vs 대안, pgvector vs Qdrant)
  - Front 형태(웹 챗 vs CLI) 확정
  - 인제스트 대상 산출물 포맷 범위 (Markdown/Confluence/PPT 등)
