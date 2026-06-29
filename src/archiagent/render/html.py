"""산출물 → 문서별 HTML 출력 (시나리오 5.4 시작점, 슬라이스 후순위).

저장된 산출물 내용을 그대로 가져와 단순 HTML 로 만든다. 사용자에게는 '산출물을 문서로 출력'으로만 보인다.
"""

from __future__ import annotations

import html

from archiagent.schema import Node


def render_document(node: Node) -> str:
    body = node.props.get("body", "")
    rows = "".join(
        f"<p>{html.escape(line)}</p>" for line in body.splitlines() if line.strip()
    )
    return (
        f"<!doctype html><meta charset='utf-8'><title>{html.escape(node.title)}</title>"
        f"<h1>{html.escape(node.title)}</h1>{rows}"
    )
