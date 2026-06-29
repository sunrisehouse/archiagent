# archiagent

소프트웨어 아키텍트를 돕는 에이전트. SI 산출물을 **자연어로** 작성·변경·추적·출력한다.
사용자는 산출물과 그 연관 관계만 다루고, 뒤에서 무엇으로 저장하는지는 알 필요가 없다.

> 현재는 PoC다. 시나리오 **5.1(산출물 작성)** 을 끝까지 동작하는 버티컬 슬라이스로 구현했고,
> 외부 서비스 없이 이 환경에서 개발·테스트된다. 기획·아키텍처·시나리오 문서는 `docs/` 참고.

## 빠른 시작

```bash
bash scripts/setup.sh            # 패키지 editable 설치(+ 테스트 의존성)
pytest -q                        # 단위 + 5.1 e2e (오프라인, 모델 호출 0)
archiagent examples/bank-nextgen # 인터랙티브 실행
```

인터랙티브에서 예:

```
> 이 rfp.md 를 읽고 요구사항 정의서를 작성해.
> 이 interview.md 내용도 읽고 요구사항 정의서에 더해.
> 현행 시스템 문서 current-system.md 를 읽고 현행 시스템 분석서를 작성해.
> 요구사항과 현행 시스템 분석서를 기반으로 설계서를 작성해.
```

각 저장 전에 미리보기를 보여주고 `y/n` 확인을 받는다.

## 모델

- 기본(오프라인): 입력에서 결정적으로 산출물을 도출하는 예시 모델 — 모델 호출·자격 불필요.
- 실제 Claude 모델: `claude` CLI 가 있으면 자동 사용한다. **Claude Pro/Max 구독 OAuth** 로 동작하며
  별도 API 키가 필요 없다. (`ANTHROPIC_API_KEY` 가 있으면 그것을 우선 사용)
  - 실모델 검증: `pytest -m integration` (자격 없으면 자동 skip)

## 구조

```
src/archiagent/
  agent.py     오케스트레이터(의도 라우팅 + 사람 확인 게이트)
  schema.py    산출물·연관 관계 메타모델(내부)
  store/       저장소 인터페이스 + SQLite 구현(교체 가능)
  model/       모델 인터페이스 + 예시(FakeModel) + 실제(ClaudeModel, claude CLI)
  tools/       kb_artifact_ingest · kb_graph_query · kb_doc_generate · kb_graph_upsert
  prompts.py   시스템 프롬프트(SI 생애주기·단계별 산출물 지식 + 표현 규칙)
examples/bank-nextgen/   예시 시드(RFP·인터뷰·현행 시스템)
tests/                   단위 + 5.1 e2e (+ integration: 실모델)
```
