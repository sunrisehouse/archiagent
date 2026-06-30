"""산출물 → 문서별 HTML (시나리오 5.4 산출물 출력).

저장된 산출물 내용을 그대로 가져와 단순한 HTML 로 만든다. 사용자에게는 '산출물을 문서로
출력'으로만 보이며, 저장 방식은 드러나지 않는다.
"""

from __future__ import annotations

import html

from archiagent.schema import DERIVED_FROM, DESCRIBES
from archiagent.store.base import GraphStore

_DOC_REQ = "doc:requirements"
_DOC_CUR = "doc:current-system"
_DOC_DESIGN = "doc:design"


def _page(title: str, inner: str) -> str:
    t = html.escape(title)
    return (
        f"<!doctype html><meta charset='utf-8'><title>{t}</title>"
        f"<h1>{t}</h1>{inner}"
    )


def _req_num(node_id: str) -> int:
    return int(node_id[2:]) if node_id.startswith("R-") and node_id[2:].isdigit() else 0


def requirements_html(store: GraphStore) -> str:
    doc = store.get(_DOC_REQ)
    ids = [e.dst for e in store.edges(rel=DESCRIBES, src=_DOC_REQ)]
    items = sorted((store.get(i) for i in ids if store.get(i)), key=lambda n: _req_num(n.id))
    rows = "".join(
        f"<li><b>{html.escape(n.id)}</b> {html.escape(n.title)}</li>" for n in items
    )
    return _page(doc.title if doc else "요구사항 정의서", f"<ol>{rows}</ol>")


def current_system_html(store: GraphStore) -> str:
    doc = store.get(_DOC_CUR)
    ids = [e.dst for e in store.edges(rel=DESCRIBES, src=_DOC_CUR)]
    nodes = [store.get(i) for i in ids if store.get(i)]
    head = "<tr><th>서버</th><th>IP</th><th>CPU</th><th>메모리</th><th>디스크</th></tr>"
    body = "".join(
        "<tr>"
        + "".join(
            f"<td>{html.escape(str(v))}</td>"
            for v in (
                n.id,
                n.props.get("ip", ""),
                n.props.get("cpu", ""),
                n.props.get("memory", ""),
                n.props.get("disk", ""),
            )
        )
        + "</tr>"
        for n in nodes
    )
    note = doc.props.get("note", "") if doc else ""
    note_html = f"<p>{html.escape(note)}</p>" if note else ""
    return _page(
        doc.title if doc else "현행 시스템 분석서",
        f"<table border='1' cellpadding='4'>{head}{body}</table>{note_html}",
    )


def design_html(store: GraphStore) -> str:
    doc = store.get(_DOC_DESIGN)
    if doc is None:
        return _page("아키텍처 설계서", "<p>(내용 없음)</p>")
    body = doc.props.get("body", "")
    paras = "".join(
        f"<p>{html.escape(line)}</p>" for line in body.splitlines() if line.strip()
    )
    linked = sorted(
        (e.dst for e in store.edges(rel=DERIVED_FROM, src=_DOC_DESIGN)), key=_req_num
    )
    trace = (
        "<h2>요구 추적성</h2><p>이 설계가 반영한 요구: "
        + ", ".join(html.escape(r) for r in linked)
        + "</p>"
        if linked
        else ""
    )
    return _page(doc.title, paras + trace)
