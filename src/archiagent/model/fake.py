"""FakeModel — 모델 호출 없이 입력에서 결정적으로 결과를 도출한다.

테스트 기본값. 네트워크·자격·구독 한도 소모가 전혀 없다. 하드코딩이 아니라 입력
(불릿 목록, 'IP ...' 줄)을 가볍게 파싱해 만들기 때문에 시드 데이터가 바뀌어도 따라온다.
"""

from __future__ import annotations

import re
from typing import Any


class FakeModel:
    name = "fake"

    def run(self, kind: str, content: str, context: dict | None = None) -> dict[str, Any]:
        if kind == "extract_requirements":
            return {"requirements": [{"text": t} for t in _bullets(content)]}
        if kind == "extract_current_system":
            return {"systems": _parse_systems(content), "note": _note(content)}
        if kind == "generate_design":
            return _design(context or {})
        raise ValueError(f"unknown kind: {kind}")


def _bullets(text: str) -> list[str]:
    items = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(("- ", "* ")):
            items.append(s[2:].strip())
    return items


def _parse_systems(text: str) -> list[dict[str, str]]:
    systems = []
    for line in text.splitlines():
        if "IP" not in line:
            continue
        name = re.search(r"\b([a-zA-Z]+-\d+)\b", line)
        ip = re.search(r"IP\s*([\d.]+)", line)
        cpu = re.search(r"(vCPU\s*\d+)", line)
        mem = re.search(r"메모리\s*([\w]+)", line)
        disk = re.search(r"디스크\s*([\w]+)", line)
        if name:
            systems.append(
                {
                    "name": name.group(1),
                    "ip": ip.group(1) if ip else "",
                    "cpu": cpu.group(1) if cpu else "",
                    "memory": mem.group(1) if mem else "",
                    "disk": disk.group(1) if disk else "",
                }
            )
    return systems


def _note(text: str) -> str:
    for line in text.splitlines():
        s = line.strip().lstrip("- ").strip()
        if s and "IP" not in s and not s.startswith("#"):
            return s
    return ""


def _design(context: dict) -> dict[str, Any]:
    reqs = context.get("requirements", [])  # [{id, text}]
    systems = context.get("systems", [])    # [{id, ...}]
    ids = [r["id"] for r in reqs]
    lines = ["요구사항과 현행 시스템 분석서를 기반으로 작성한 설계 초안입니다.", ""]
    for r in reqs:
        lines.append(f"- {r['id']}: {r['text']} → 해당 요구를 설계에 반영한다.")
    if systems:
        names = ", ".join(s["id"] for s in systems)
        lines.append("")
        lines.append(f"현행 운영 환경({names})을 기준으로 전환·구성한다.")
    return {"title": "아키텍처 설계서", "body": "\n".join(lines), "addresses": ids}
