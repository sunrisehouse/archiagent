"""ClaudeModel — 실제 Claude 모델 호출.

`claude` CLI 를 비대화(--print) 모드로 서브프로세스 호출한다. CLI 가 Claude Code 의 인증을
그대로 쓰므로, **Claude Max 구독 OAuth** 만으로 동작한다(별도 API 키 불필요). 이 컨테이너는
인증된 Claude Code 안이라 구독으로 호출된다.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any

from archiagent.prompts import INSTRUCTIONS, SYSTEM_PROMPT

# 작업별 모델: 추출은 가볍게(Haiku), 설계 생성은 균형(Sonnet).
_MODEL_BY_KIND = {
    "extract_requirements": "claude-haiku-4-5",
    "extract_current_system": "claude-haiku-4-5",
    "generate_design": "claude-sonnet-4-6",
    "assess_change": "claude-sonnet-4-6",  # 판단(추론)
}


class ClaudeModel:
    name = "claude"

    def __init__(self, cli: str = "claude", timeout: int = 180) -> None:
        self._cli = cli
        self._timeout = timeout

    @classmethod
    def if_available(cls) -> "ClaudeModel | None":
        """`claude` CLI 가 있으면 인스턴스, 없으면 None(호출 측이 FakeModel 로 폴백)."""
        return cls() if shutil.which("claude") else None

    def run(self, kind: str, content: str, context: dict | None = None) -> dict[str, Any]:
        instruction = INSTRUCTIONS[kind]
        payload = content if context is None else json.dumps(context, ensure_ascii=False)
        base = f"{SYSTEM_PROMPT}\n\n[작업]\n{instruction}\n\n[입력]\n{payload}"
        model = _MODEL_BY_KIND.get(kind, "claude-sonnet-4-6")
        # 실모델이 가끔 설명문을 섞어 JSON 파싱이 실패한다. 더 강하게 다시 요청(총 2회).
        strict = "\n\n[중요] 인사·설명·요약 없이, 첫 글자가 '{' 인 JSON 객체 하나만 출력하라."
        last = ""
        for attempt in range(2):
            prompt = base + (strict if attempt else "")
            out = subprocess.run(
                [self._cli, "--print", "--model", model, prompt],
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
            if out.returncode != 0:
                raise RuntimeError(f"claude CLI 실패: {out.stderr.strip()[:300]}")
            last = out.stdout
            try:
                return _extract_json(last)
            except ValueError:
                continue
        raise ValueError(f"모델이 JSON 을 반환하지 않았습니다: {last[:200]}")


def _extract_json(text: str) -> dict[str, Any]:
    """모델 출력에서 첫 JSON 객체를 안전하게 추출한다(코드펜스·서론 텍스트 허용)."""
    s = text.strip()
    if "```" in s:  # ```json ... ``` 펜스 제거
        parts = s.split("```")
        for p in parts:
            p = p.lstrip()
            if p.startswith("json"):
                p = p[4:]
            p = p.strip()
            if p.startswith("{"):
                s = p
                break
    start = s.find("{")
    if start == -1:
        raise ValueError(f"JSON 을 찾지 못함: {text[:200]}")
    # 표준 파서로 첫 JSON 객체만 디코드한다. 문자열 값 안의 중괄호·이스케이프를
    # 정확히 처리하므로, 본문에 { } 가 들어가도 깨지지 않는다(뒤따르는 텍스트는 무시).
    try:
        obj, _ = json.JSONDecoder().raw_decode(s[start:])
        return obj
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 파싱 실패({e.msg}): {text[:200]}") from e
