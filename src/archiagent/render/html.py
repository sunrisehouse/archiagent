"""산출물 → 문서별 HTML (시나리오 5.4 산출물 출력).

저장된 산출물 내용을 그대로 가져와 단순한 HTML 로 만든다. 사용자에게는 '산출물을 문서로
출력'으로만 보이며, 저장 방식은 드러나지 않는다.
"""

from __future__ import annotations

import html
import re

from archiagent.schema import DERIVED_FROM, DESCRIBES
from archiagent.store.base import GraphStore

_DOC_REQ = "doc:requirements"
_DOC_CUR = "doc:current-system"
_DOC_DESIGN = "doc:design"

_STYLE = (
    "body{max-width:820px;margin:2.5rem auto;padding:0 1.25rem;"
    "font-family:-apple-system,'Segoe UI',sans-serif;line-height:1.7;color:#1f2933}"
    "h1{font-size:1.7rem;border-bottom:2px solid #3b82f6;padding-bottom:.4rem}"
    "h2{font-size:1.25rem;margin-top:2rem}h3{font-size:1.05rem;color:#3b3f47}"
    "table{border-collapse:collapse;width:100%;margin:1rem 0}"
    "th,td{border:1px solid #d2d6dc;padding:.5rem .7rem;text-align:left}"
    "th{background:#f3f4f6}li{margin:.25rem 0}"
    "b{color:#1d4ed8}.trace{background:#eff6ff;padding:.6rem .9rem;border-radius:6px}"
)


def _page(title: str, inner: str) -> str:
    t = html.escape(title)
    return (
        f"<!doctype html><meta charset='utf-8'><title>{t}</title>"
        f"<style>{_STYLE}</style><h1>{t}</h1>{inner}"
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
    linked = sorted(
        (e.dst for e in store.edges(rel=DERIVED_FROM, src=_DOC_DESIGN)), key=_req_num
    )
    trace = (
        "<h2>요구 추적성</h2><p class='trace'>이 설계가 반영한 요구: "
        + ", ".join(html.escape(r) for r in linked)
        + "</p>"
        if linked
        else ""
    )
    return _page(doc.title, _markdown(doc.props.get("body", "")) + trace)


def _markdown(text: str) -> str:
    """설계 본문의 가벼운 마크다운(제목·목록·표·문단)을 HTML 로 바꾼다."""
    out: list[str] = []
    lines = text.splitlines()
    i, n = 0, len(lines)
    while i < n:
        line = lines[i].rstrip()
        stripped = line.strip()
        if not stripped or set(stripped) <= {"-"}:  # 빈 줄·구분선(---)은 건너뛴다.
            i += 1
            continue
        if stripped.startswith("#"):
            level = min(len(stripped) - len(stripped.lstrip("#")), 3)
            level = max(level, 2)  # 문서 제목은 h1 이므로 본문 제목은 h2 부터.
            out.append(f"<h{level}>{_inline(stripped.lstrip('#').strip())}</h{level}>")
            i += 1
        elif stripped.startswith(("- ", "* ")):
            items = []
            while i < n and lines[i].strip().startswith(("- ", "* ")):
                items.append(f"<li>{_inline(lines[i].strip()[2:])}</li>")
                i += 1
            out.append(f"<ul>{''.join(items)}</ul>")
        elif stripped.startswith("|") and stripped.endswith("|"):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            out.append(_table(rows))
        else:
            out.append(f"<p>{_inline(stripped)}</p>")
            i += 1
    return "".join(out)


def _inline(text: str) -> str:
    """텍스트를 이스케이프하고 **굵게** 표기만 <b> 로 바꾼다."""
    escaped = html.escape(text)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)


def _cells(row: str) -> list[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]


def _is_separator(row: str) -> bool:
    return all(set(c) <= {"-", ":", " "} and c for c in _cells(row))


def _table(rows: list[str]) -> str:
    body = [r for r in rows if not _is_separator(r)]
    if not body:
        return ""
    head = "<tr>" + "".join(f"<th>{_inline(c)}</th>" for c in _cells(body[0])) + "</tr>"
    trs = "".join(
        "<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in _cells(r)) + "</tr>"
        for r in body[1:]
    )
    return f"<table>{head}{trs}</table>"
