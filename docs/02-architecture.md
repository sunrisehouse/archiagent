# 산출물 ② — 아키텍처 구성도 (콘텐츠)

> 콘텐츠 단일 소스. 슬라이드 디자인(`02-architecture.html`)은 이 MD를 입력으로 별도 입힌다.
> 슬라이드별: **목차 제목**(kicker) · **거버닝 메시지** · **내부 컨텐츠**.

---

## 1. 타이틀

- **목차 제목:** 산출물 ② · Architecture
- **거버닝 메시지:** archiagent — Claude Agent SDK 기반 멀티 에이전트 구성. Front · Runtime · Model · MCP · Tools · Knowledge Base · Pipeline.
- **내부 컨텐츠:**
  - 제목: **아키텍처 구성도**
  - 메모: Agent B(시스템 상태)는 외부 팀·별도 스택 → **MCP 연계 계약**으로 추상화

## 2. 전체 구성

- **목차 제목:** Overview
- **거버닝 메시지:** Chat UI → Orchestrator → (Agent A subagent · Agent B MCP tool) → Graph/Vector DB, 외부 관측 상태는 Reconcile로 동기화하는 전체 흐름.
- **내부 컨텐츠:**
  - > 다이어그램: 7개 묶음으로 구성
  - ① Front — Chat UI · 그래프 뷰어 · 설계·실제 차이 리포트
  - ② Agent Runtime (Claude Agent SDK) — Orchestrator Agent + Agent A(subagent)
  - ③ Model Provider — Anthropic Claude (Opus 4.8 / Sonnet 4.6 / Haiku 4.5)
  - ④ MCP Servers — Graph/KB MCP(내부) · System State MCP = Agent B(외부)
  - ⑥ Knowledge Base — Graph DB · Vector DB
  - ⑦ Data Pipeline — 인제스트·LLM 추출·Upsert · 관측 동기화·Reconcile
  - 흐름: UI→Orchestrator→Agent A→Graph/KB MCP→Graph/Vector DB / Orchestrator·Agent A→Claude / Orchestrator -. tool .-> Agent B / Agent B -. observed .-> Reconcile → Graph DB

## 3. ① Front — Front 구성

- **목차 제목:** ① Front
- **거버닝 메시지:** Front는 **표현만**. 모든 추론·조합은 Runtime이 담당.
- **내부 컨텐츠:** (카드)
  - **대화 뷰** — 아키텍트의 자연어 질의 입력 / 답변 출력. PoC에선 웹 챗 또는 CLI로 충분.
  - **그래프 뷰** — Agent A의 서브그래프 시각화 (컴포넌트·의존성 관계)
  - **설계·실제 차이 리포트 뷰** — 설계 vs 실제 비교 결과 (추가/누락/불일치)
  - **책임 분리** — Front는 표현만, 추론·조합은 Runtime

## 4. ② Agent Runtime — Orchestration · Instruction

- **목차 제목:** ② Agent Runtime
- **거버닝 메시지:** Orchestrator가 의도를 분해·라우팅하고, 설계는 Agent A·실제는 Agent B에서 받아 비교·합성한다.
- **내부 컨텐츠:**
  - **Orchestration 부문:**
    - SDK `query()` 루프 진입점
    - 의도 분해 → 시나리오 라우팅(설계·실제 차이/영향도/Q&A)
    - Agent A = subagent, Agent B = MCP tool
    - 정지 조건: 최대 반복 · 실패 시 graceful degrade
    - 비가역 작업(그래프 쓰기)은 `AskUserQuestion` 확인
  - **Agent Instruction · Prompt:**
    - Orchestrator: 역할·라우팅 휴리스틱·"설계는 A, 실제는 B"
    - Agent A: 그래프 모델·질의 패턴, "없으면 없다고", `concise|detailed`
    - 작성: As-Is 그래프 제약(노드 대수·용량) 읽어 ToBe 초안·충돌 경고
  - > 다이어그램(시퀀스): Architect→Orchestrator 질의 → Agent A 설계 토폴로지(intended) → Agent B 실제 상태(observed) → Orchestrator 비교·합성 → 통합 응답

## 5. ③④⑤ Provider · MCP · Tools — 모델 · MCP · 도구

- **목차 제목:** ③④⑤ Provider · MCP · Tools
- **거버닝 메시지:** `kb_*`는 설계 · `state_*`는 실제 — 모델·MCP·도구를 용도로 분리하고 에이전트가 구분한다.
- **내부 컨텐츠:**
  - **③ Model Provider** (용도 | 모델):
    - 오케스트레이션·영향도(기본) | `claude-opus-4-8`
    - 라우틴 질의·요약 | `claude-sonnet-4-6`
    - 대량 엔티티 추출 | `claude-haiku-4-5`
  - **④ MCP Server:**
    - Graph/KB MCP — 우리 구현 (Agent A 백엔드)
    - System State MCP = Agent B(외부). 계약: `state_get_topology` · `state_get_component` · `state_list_running`
  - **⑤ Tools** (도구 | 설명):
    - `kb_artifact_ingest` | 산출물 문서 → Artifact·엔티티 적재(확인)
    - `kb_doc_generate` | 그래프·대화 맥락 → 산출물 초안(작성·갱신)
    - `kb_graph_query` | 의존성·패턴·추적성 탐색
    - `kb_graph_upsert` | 노드·엣지 갱신(확인)
    - `kb_vector_search` | 자연어 의미검색
    - `state_*` | Agent B 상태 계약
    - `compare_design_actual` | 설계 vs 관측 비교

## 6. ⑥ Knowledge Base — 그래프 데이터 모델

- **목차 제목:** ⑥ Knowledge Base
- **거버닝 메시지:** 설계 노드와 관측 노드(DeployedComponent)를 분리 저장 → 설계·실제 차이 비교의 기반.
- **내부 컨텐츠:**
  - > 다이어그램: Artifact(요구·분석·설계·테스트) —DERIVED_FROM→ Artifact / —DEFINES→ Service·Component(DEPENDS_ON, EXPOSES API, STORES_IN Datastore, OWNED_BY Team) / ADR·Decision —AFFECTS→ Service / Artifact -.VALIDATES.-> Service / Service -.DEPLOYED_AS.-> DeployedComponent(observed · Agent B)
  - **Graph DB** (예: Neo4j): Artifact 노드는 `phase`·`type` 속성으로 SI 단계 표현. DERIVED_FROM으로 요구→설계→테스트 추적성, DEFINES/VALIDATES로 설계 엔티티 연결. 설계 노드와 관측 노드(DeployedComponent) 분리 저장 → 설계·실제 차이 비교 기반.
  - **Vector DB** (예: pgvector/Qdrant): 문서 청크·노드 설명 임베딩 → 자연어 질의를 그래프 진입점으로 변환.

## 7. ⑦ Data Pipeline — 작성·적재 → 그래프, 그리고 최신 유지

- **목차 제목:** ⑦ Data Pipeline
- **거버닝 메시지:** 작성·적재로 Artifact·추적성을 채우고, Agent B 관측을 Reconcile해 Graph/Vector DB를 항상 최신으로 유지.
- **내부 컨텐츠:**
  - > 다이어그램: 대화·인터뷰 → 초안(kb_doc_generate) →승인→ Upsert / 기존 SI 산출물 → LLM 추출(Haiku) → Upsert(Artifact 노드 + 추적성 엣지) → Graph/Vector DB / Agent B observed → Reconcile(DeployedComponent 갱신) → Graph DB
  - **작성·적재** (`kb_doc_generate` · `kb_artifact_ingest`): 작성 — 대화·인터뷰→초안→승인 후 Upsert. 적재 — 기존 문서→LLM 추출→Artifact+추적성 Upsert.
  - **Reconcile(주기):** Agent B 관측 상태로 `DeployedComponent` 갱신 → 설계·실제 차이 항상 최신.

## 8. Open Questions — 남은 결정

- **목차 제목:** Open
- **거버닝 메시지:** 기획 의도·시나리오는 산출물 ① `01-product-brief.html` 참고.
- **내부 컨텐츠:**
  - Graph DB / Vector DB 제품 선정 (Neo4j vs 대안, pgvector vs Qdrant)
  - Front 형태(웹 챗 vs CLI) 확정
  - Agent B 연계 계약의 상세 스키마 — 외부 팀과 합의 필요
  - 인제스트 대상 산출물 포맷 범위 (Markdown/Confluence/PPT 등)
