# 진행 메모

세션 간 인수인계용. 다음 세션은 이 파일 → `git log` → `pytest -q` 순으로 온보딩한다.

## done
- PoC 뼈대 + 시나리오 5.1~5.4.
  - schema(메타모델) · store(SQLite, 교체 가능) · model(FakeModel/ClaudeModel) · tools(kb_*) · agent(라우팅+게이트) · cli.
  - 5.1 산출물 작성, 5.2 변경 대응(영향도 역추적 + 변경 반영), 5.3 설계 질의응답(운영 환경 서버 사양), 5.4 산출물 HTML 출력.
  - 영향도·조회·출력은 저장된 사실에서 결정적으로 계산(모델 추측 아님). 추출·생성에만 모델 사용.
  - 시스템 프롬프트에 SI 생애주기(분석·설계·개발·테스트·이행)·단계별 산출물·도출 관계 내장.
  - 사용자 노출 문구는 문서 수준 언어만(저장 기술 용어 숨김) — 테스트로 검증.
  - 실모델은 `claude` CLI(구독 OAuth)로 호출, API 키 불필요. 5.1~5.4 실모델 동작 확인.

## next (후속)
- 자유 질문형 설계 Q&A(모델 기반), kb_vector_search(의미검색), Tier-2 산출물 타입 레지스트리(측정 후).
- 인프라 에이전트(state_*)·compare_design_actual — 외부 팀/후속.
- SessionStart 훅(.claude/settings.json) 자동 설치: 현재 자동 모드에서 차단되어 미적용 → `scripts/setup.sh` 로 대체.

## 검증
- `pytest -q` (오프라인) 통과 = 슬라이스 정상.
- `pytest -m integration` = 실제 Claude 모델로 5.1 확인(자격 없으면 skip).
