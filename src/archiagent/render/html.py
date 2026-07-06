"""산출물 → 문서별 HTML (시나리오 5.4 산출물 출력).

저장된 산출물 내용을 그대로 가져와 '문서' 형태의 HTML 로 만든다. 사용자에게는 산출물을
문서로 출력하는 것으로만 보이며, 저장 방식은 드러나지 않는다.
"""

from __future__ import annotations

import html
import re

from archiagent.schema import DERIVED_FROM, DESCRIBES
from archiagent.store.base import GraphStore

_DOC_REQ = "doc:requirements"
_DOC_CUR = "doc:current-system"
_DOC_DESIGN = "doc:design"

_PROJECT = "은행 차세대 시스템 구축"

_CSS = """
*{box-sizing:border-box}
:root{--bg:#f5f7fa;--surface:#ffffff;--ink:#141b2b;--muted:#5c6675;
--line:#e4e8f0;--accent:#1f52d6;--soft:#eef3ff;--shadow:rgba(20,30,60,.05)}
@media(prefers-color-scheme:dark){:root{--bg:#0e1320;--surface:#171f30;
--ink:#e7ecf5;--muted:#98a3b8;--line:#28324a;--accent:#7aa2ff;
--soft:#1a2540;--shadow:rgba(0,0,0,.3)}}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);
font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif;
line-height:1.72;-webkit-font-smoothing:antialiased}
.doc{max-width:880px;margin:0 auto;padding:0 22px 96px}
.cover{padding:60px 0 26px;border-bottom:1px solid var(--line)}
.eyebrow{color:var(--accent);font-weight:700;font-size:.76rem;
letter-spacing:.14em;text-transform:uppercase;margin:0}
.title{font-size:2.1rem;line-height:1.15;letter-spacing:-.02em;margin:.5rem 0 .8rem}
.meta{display:flex;flex-wrap:wrap;gap:6px 22px;color:var(--muted);font-size:.86rem;margin:0}
.meta span{display:inline-flex;gap:.4rem}
.meta b{color:var(--ink);font-weight:600}
section{background:var(--surface);border:1px solid var(--line);border-radius:16px;
padding:24px 28px;margin:20px 0;box-shadow:0 1px 3px var(--shadow)}
section>h2:first-child{margin-top:0}
h2{font-size:1.16rem;margin:1.6rem 0 .9rem;padding-bottom:.55rem;
border-bottom:1px solid var(--line);letter-spacing:-.01em}
h3{font-size:1rem;color:var(--accent);margin:1.3rem 0 .35rem}
p{margin:.55rem 0}ul{margin:.4rem 0;padding-left:1.15rem}li{margin:.3rem 0}
table{border-collapse:collapse;width:100%;margin:.9rem 0;font-size:.9rem}
th,td{border:1px solid var(--line);padding:.6rem .75rem;text-align:left;vertical-align:top}
th{background:var(--soft);font-weight:600}
.reqlist{list-style:none;padding:0;margin:0;display:grid;gap:10px}
.reqlist li{display:grid;grid-template-columns:auto 1fr;gap:14px;align-items:baseline;
padding:14px 16px;border:1px solid var(--line);border-radius:12px;background:var(--surface)}
.badge{display:inline-block;background:var(--accent);color:#fff;font-weight:700;
font-size:.72rem;padding:4px 10px;border-radius:999px;white-space:nowrap}
@media(prefers-color-scheme:dark){.badge{color:#0e1320}}
.trace{background:var(--soft);border-color:transparent}
.trace .chips{display:flex;flex-wrap:wrap;gap:7px;margin-top:.5rem}
.note{color:var(--muted);font-size:.86rem;margin-top:.6rem}
@media print{body{background:#fff}section{box-shadow:none;break-inside:avoid;border-radius:0}}
""".strip()


def _document(eyebrow: str, title: str, meta: list[tuple[str, str]], inner: str) -> str:
    t = html.escape(title)
    meta_html = "".join(
        f"<span>{html.escape(k)} <b>{html.escape(v)}</b></span>" for k, v in meta
    )
    return (
        "<!doctype html><html lang='ko'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{t}</title><style>{_CSS}</style></head><body><div class='doc'>"
        f"<header class='cover'><p class='eyebrow'>{html.escape(eyebrow)}</p>"
        f"<h1 class='title'>{t}</h1><p class='meta'>{meta_html}</p></header>"
        f"{inner}</div></body></html>"
    )


def _req_num(node_id: str) -> int:
    return int(node_id[2:]) if node_id.startswith("R-") and node_id[2:].isdigit() else 0


def _inline(text: str) -> str:
    """텍스트를 이스케이프하고 **굵게** 표기만 <b> 로 바꾼다."""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(text))


# --- 요구사항 정의서 ---
def requirements_html(store: GraphStore) -> str:
    doc = store.get(_DOC_REQ)
    ids = [e.dst for e in store.edges(rel=DESCRIBES, src=_DOC_REQ)]
    items = sorted((store.get(i) for i in ids if store.get(i)), key=lambda n: _req_num(n.id))
    rows = "".join(
        f"<li><span class='badge'>{html.escape(n.id)}</span>"
        f"<span>{_inline(n.title)}</span></li>"
        for n in items
    )
    inner = f"<section><ul class='reqlist'>{rows}</ul></section>"
    return _document(
        _PROJECT,
        doc.title if doc else "요구사항 정의서",
        [("단계", "분석"), ("요구 항목", f"{len(items)}건")],
        inner,
    )


# --- 현행 시스템 분석서 ---
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
    note_html = f"<p class='note'>{html.escape(note)}</p>" if note else ""
    inner = (
        "<section><h2>운영 환경 서버 사양</h2>"
        f"<table>{head}{body}</table>{note_html}</section>"
    )
    return _document(
        _PROJECT,
        doc.title if doc else "현행 시스템 분석서",
        [("단계", "분석"), ("서버", f"{len(nodes)}대")],
        inner,
    )


# --- 아키텍처 설계서 ---
def design_html(store: GraphStore) -> str:
    doc = store.get(_DOC_DESIGN)
    if doc is None:
        return _document(_PROJECT, "아키텍처 설계서", [("단계", "설계")],
                         "<section><p>(내용 없음)</p></section>")
    linked = sorted(
        (e.dst for e in store.edges(rel=DERIVED_FROM, src=_DOC_DESIGN)), key=_req_num
    )
    trace = ""
    if linked:
        chips = "".join(f"<span class='badge'>{html.escape(r)}</span>" for r in linked)
        trace = (
            "<section class='trace'><h2>요구 추적성</h2>"
            "<p>이 설계가 반영한 요구입니다.</p>"
            f"<div class='chips'>{chips}</div></section>"
        )
    body = _design_body_html(doc.props.get("body", ""))
    return _document(
        _PROJECT,
        doc.title,
        [("단계", "설계"), ("반영 요구", f"{len(linked)}건")],
        body + trace,
    )


def _design_body_html(text: str) -> str:
    """설계 본문의 가벼운 마크다운을 섹션 카드로 나눠 렌더링한다."""
    sections: list[str] = []
    parts: list[str] = []
    title: str | None = None
    started = False
    for block in _parse_blocks(text):
        if block[0] == "h" and block[1] == 2:
            if started or parts:
                sections.append(_section(title, parts))
            title, parts, started = block[2], [], True
        elif block[0] == "h":
            parts.append(f"<h3>{_inline(block[2])}</h3>")
        else:
            parts.append(block[1])
    if started or parts:
        sections.append(_section(title, parts))
    return "".join(sections)


def _section(title: str | None, parts: list[str]) -> str:
    head = f"<h2>{_inline(title)}</h2>" if title else ""
    return f"<section>{head}{''.join(parts)}</section>"


def _parse_blocks(text: str) -> list[tuple]:
    """마크다운을 (kind, ...) 블록으로 분해한다: ('h',level,title) 또는 ('html',string)."""
    blocks: list[tuple] = []
    lines = text.splitlines()
    i, n = 0, len(lines)
    while i < n:
        stripped = lines[i].strip()
        if not stripped or set(stripped) <= {"-"}:  # 빈 줄·구분선(---)은 건너뛴다.
            i += 1
        elif stripped.startswith("#"):
            level = min(len(stripped) - len(stripped.lstrip("#")), 3)
            blocks.append(("h", max(level, 2), stripped.lstrip("#").strip()))
            i += 1
        elif stripped.startswith(("- ", "* ")):
            items = []
            while i < n and lines[i].strip().startswith(("- ", "* ")):
                items.append(f"<li>{_inline(lines[i].strip()[2:])}</li>")
                i += 1
            blocks.append(("html", f"<ul>{''.join(items)}</ul>"))
        elif stripped.startswith("|") and stripped.endswith("|"):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            blocks.append(("html", _table(rows)))
        else:
            blocks.append(("html", f"<p>{_inline(stripped)}</p>"))
            i += 1
    return blocks


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
