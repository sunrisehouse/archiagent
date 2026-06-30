"""kb_doc_export — 저장된 산출물을 문서별 HTML 파일로 출력한다(시나리오 5.4).

내용은 저장된 산출물에서 그대로 가져오므로 항상 최신 상태와 같다.
"""

from __future__ import annotations

import os

from archiagent.render.html import current_system_html, design_html, requirements_html
from archiagent.store.base import GraphStore

# (산출물 id, 파일 이름, 렌더 함수)
_PLAN = [
    ("doc:requirements", "requirements.html", requirements_html),
    ("doc:current-system", "current-system.html", current_system_html),
    ("doc:design", "design.html", design_html),
]


def kb_doc_export(store: GraphStore, out_dir: str) -> list[tuple[str, str]]:
    os.makedirs(out_dir, exist_ok=True)
    written: list[tuple[str, str]] = []
    for doc_id, fname, render in _PLAN:
        node = store.get(doc_id)
        if node is None:
            continue
        path = os.path.join(out_dir, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(render(store))
        written.append((path, node.title))
    return written
