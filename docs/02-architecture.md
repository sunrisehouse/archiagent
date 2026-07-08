# 산출물 ② — 아키텍처 구성도 (콘텐츠)

> 콘텐츠 단일 소스. 슬라이드 디자인(`02-architecture.html`)은 이 MD를 입력으로 별도 입힌다.
> 🔗 렌더된 슬라이드: [02-architecture.html](https://sunrisehouse.github.io/archiagent/docs/02-architecture.html)
> 슬라이드별: **목차 제목**(kicker) · **거버닝 메시지** · **내부 컨텐츠**.
> 이 문서는 **실제로 구현된 구성만** 담는다. 아직 안 만든 것은 마지막 '후속'에 목록으로만 둔다.

---

## 1. 타이틀

- **목차 제목:** 산출물 ② · Architecture
- **거버닝 메시지:** archiagent는 단일 Python 에이전트다. 터미널로 대화하고, `kb_*` 도구로 산출물을 다루며, SQLite에 저장한다.
- **내부 컨텐츠:**
  - 제목: **아키텍처 구성도**
  - 메모: 현재 구현(PoC) 기준이다.

## 2. 구성도

- **목차 제목:** 구성도
- **거버닝 메시지:** 사용자가 터미널에서 에이전트와 직접 대화하고, 에이전트가 `kb_*` 함수를 호출해 SQLite에 저장한다.
- **내부 컨텐츠:**
  - > 구성도(계층·연결): 별도 프론트 앱이 없어 에이전트가 프론트를 겸한다.
  - ① Agent (단일 Python 클래스) — 터미널 REPL(입출력) · 정규식 라우팅 · 확인 게이트. 프론트 겸 오케스트레이션.
  - ② kb_* 도구 (순수 함수) — ingest · generate · query · upsert · export
  - ③ SQLite Store (인메모리, 교체 가능) — 산출물 · 요구 · 추적성
  - 곁: claude CLI(subprocess `--print`) — 추출 Haiku · 설계 Sonnet
  - 연결: 사용자(터미널) —대화(REPL)→ ① —함수 직접 호출→ ② —저장/조회→ ③ / ① ←모델 호출→ claude CLI

## 3. Agent — 라우팅 · 게이트

- **목차 제목:** Agent
- **거버닝 메시지:** 에이전트가 자연어 명령의 의도를 정규식으로 판별해 도구를 부르고, 저장 전 사람 확인을 받는다.
- **내부 컨텐츠:**
  - 진입: `archiagent` 콘솔 스크립트 → `cli.py` REPL(`input`/`print`)
  - 라우팅(`_route`): 정규식·키워드로 의도 판별 — 작성 / 영향도 / 반영 / 질의응답 / 출력
  - 핸들러가 알맞은 `kb_*` 도구를 호출한다.
  - 확인 게이트: 저장 등 비가역 작업 전 `y/n`
  - 정지: 규칙 기반이라 한 명령당 유한 단계로 끝난다.
  - 영향도·추적성·조회는 모델 없이 저장된 사실에서 **결정적**으로 계산한다.

## 4. Tools — kb_* 도구

- **목차 제목:** Tools
- **거버닝 메시지:** 산출물 작성·조회·저장·출력을 `kb_*` 순수 함수로 나눈다.
- **내부 컨텐츠:** (도구 | 하는 일)
  - `kb_artifact_ingest` | 문서를 읽어 산출물로 적재(확인 게이트 경유)
  - `kb_doc_generate` | 저장된 맥락으로 설계서 초안 생성
  - `kb_graph_query` | 요구·현행·추적성·영향도 조회(결정적)
  - `kb_graph_upsert` | 저장(노드·엣지 갱신, 확인)
  - `kb_doc_export` | 산출물을 문서별 HTML로 출력

## 5. 도구별 상세 — 입력 · 동작 · 출력

- **목차 제목:** 도구별 상세
- **거버닝 메시지:** 모델은 추출·생성·판단에만 쓰고, 쓰기는 `kb_graph_upsert` 하나로 모은다. 영향 범위(무엇이 걸리나)는 저장된 연결에서 역추적한다.
- **내부 컨텐츠:** (도구 | 입력 | 내부 동작 | 출력)
  - `kb_artifact_ingest` | 문서 텍스트 · kind | 모델로 추출 → 산출물·요구/서버 노드 + `DESCRIBES` 조립. R 번호는 이어 붙여 멱등 | `Proposal`(미리보기)
  - `kb_doc_generate` | (요구+현행 맥락) | 모델로 설계 본문 생성 + `addresses`로 요구→설계 `DERIVED_FROM` 연결 | `Proposal`(미리보기)
  - `kb_change_assess` | 변경 내용 | 모델이 이 변경을 설계서에 반영할지 판단(내용 판단) | `{relevant, reason}`
  - `kb_graph_query` | (선택) 요구 id | 결정적 조회 — 요구·서버 목록, 영향도는 `DERIVED_FROM` 역추적 | 목록 · 영향 산출물
  - `kb_graph_upsert` | `Proposal` | `store.upsert(nodes, edges)` 멱등 저장(게이트 통과 후에만) | 저장(반환 없음)
  - `kb_doc_export` | 출력 폴더 | store에 있는 산출물만 `render/html.py`로 렌더해 파일 저장 | (경로, 제목) 목록
  - 모델 사용은 `kb_artifact_ingest`(추출) · `kb_doc_generate`(생성) · `kb_change_assess`(판단) 셋. 나머지는 모델 없이 결정적.
  - 변경 반영: 변경은 요구로 항상 반영하되, 설계서에 반영할지는 `kb_change_assess`가 판단해 관련 있을 때만 설계를 갱신한다.

## 6. Store — SQLite

- **목차 제목:** Store
- **거버닝 메시지:** 산출물과 요구, 현행 서버, 그리고 그 사이 연결을 SQLite에 저장한다. 사용자에게 저장 방식은 드러내지 않는다.
- **내부 컨텐츠:**
  - 노드 3종: **ARTIFACT**(요구사항 정의서·현행 시스템 분석서·설계서) · **REQUIREMENT**(R-1..) · **SYSTEM_NODE**(운영 서버)
  - 연결 3종: **DERIVED_FROM**(설계→요구 추적성) · **DESCRIBES**(산출물→항목) · **DEFINES**(정의만, 후속)
  - 인메모리 기본이고, 인터페이스로 추상화해 교체 가능하다.
  - 사용자 노출 문구는 문서 수준 언어만 쓴다(그래프·노드 같은 저장 용어는 숨긴다).

## 7. Model — FakeModel / ClaudeModel

- **목차 제목:** Model
- **거버닝 메시지:** 추출·생성·판단에만 모델을 쓰고, 테스트는 모델 없이 돈다.
- **내부 컨텐츠:**
  - **FakeModel** — 결정적 응답, 테스트 기본(모델 호출 0회)
  - **ClaudeModel** — `claude` CLI(`--print`) subprocess 호출, Claude Max 구독 OAuth(API 키 불필요)
  - 작업별 모델: 추출 = `claude-haiku-4-5`, 설계 생성·판단 = `claude-sonnet-4-6`
  - 추출·생성·판단만 모델. 라우팅·영향 범위·조회·출력은 결정적 코드다.

## 8. 프롬프팅 — 시스템 프롬프트 · 작업 지시문

- **목차 제목:** 프롬프팅
- **거버닝 메시지:** 시스템 프롬프트에 SI 생애주기와 표현 규칙을 박고, 작업별 지시문으로 모델이 구조화 JSON을 내게 한다.
- **내부 컨텐츠:**
  - **시스템 프롬프트(`SYSTEM_PROMPT`)** — 세 가지를 박는다.
    - 도메인 지식 — SI 생애주기(분석·설계·개발·테스트·이행)와 단계별 산출물·도출 관계
    - 표현 규칙 — 그래프·노드·벡터 같은 저장 용어를 사용자에게 노출 금지, 문서 수준 언어만
    - 작업 방식 — 저장 전 "저장할까요?" 확인, 초안을 충실히 작성
  - **작업별 지시문(`INSTRUCTIONS`)** — 모델이 JSON만 내도록 강제한다.
    - `extract_requirements` → `{"requirements": [{"text": ...}]}`
    - `extract_current_system` → `{"systems": [{name, ip, cpu, memory, disk}], "note": ...}`
    - `generate_design` → `{"title", "body", "addresses": ["R-1", ...]}`
    - `assess_change` → `{"relevant": bool, "reason": ...}` (변경을 설계에 반영할지 판단)
  - 최종 프롬프트 = `SYSTEM_PROMPT` + `[작업]` 지시문 + `[입력]` 을 합쳐 claude CLI에 전달한다.

## 9. 후속 (아직 없음)

- **목차 제목:** 후속
- **거버닝 메시지:** 아래는 아직 없다. 필요와 측정 후에 붙인다.
- **내부 컨텐츠:**
  - Vector DB · 의미검색(`kb_vector_search`)
  - MCP 서버로 도구 분리
  - 웹 프론트 · 그래프 뷰어
  - Tier-2 산출물 타입 레지스트리, Neo4j 등 외부 저장소로 교체
