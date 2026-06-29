"""경량 인컨테이너 저장소 — SQLite 한 파일(또는 메모리)로 산출물·연관 관계 보관.

외부 서비스·도커 없이 동작하므로 컨테이너에서 바로 개발·테스트된다. 인터페이스만 맞추면
나중에 Neo4j/pgvector 같은 실제품으로 교체할 수 있다.
"""

from __future__ import annotations

import json
import sqlite3

from archiagent.schema import Edge, Node


class SqliteStore:
    def __init__(self, path: str = ":memory:") -> None:
        self._db = sqlite3.connect(path)
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS nodes ("
            "id TEXT PRIMARY KEY, type TEXT, title TEXT, props TEXT)"
        )
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS edges ("
            "src TEXT, rel TEXT, dst TEXT, UNIQUE(src, rel, dst))"
        )
        self._db.commit()

    def upsert(self, nodes: list[Node], edges: list[Edge]) -> None:
        for n in nodes:
            self._db.execute(
                "INSERT INTO nodes(id, type, title, props) VALUES(?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET type=excluded.type, "
                "title=excluded.title, props=excluded.props",
                (n.id, n.type, n.title, json.dumps(n.props, ensure_ascii=False)),
            )
        for e in edges:
            self._db.execute(
                "INSERT OR IGNORE INTO edges(src, rel, dst) VALUES(?,?,?)",
                (e.src, e.rel, e.dst),
            )
        self._db.commit()

    def _row_to_node(self, row: tuple) -> Node:
        return Node(id=row[0], type=row[1], title=row[2], props=json.loads(row[3] or "{}"))

    def nodes(self, type: str | None = None) -> list[Node]:
        if type is None:
            cur = self._db.execute("SELECT id, type, title, props FROM nodes ORDER BY id")
        else:
            cur = self._db.execute(
                "SELECT id, type, title, props FROM nodes WHERE type=? ORDER BY id", (type,)
            )
        return [self._row_to_node(r) for r in cur.fetchall()]

    def get(self, node_id: str) -> Node | None:
        cur = self._db.execute(
            "SELECT id, type, title, props FROM nodes WHERE id=?", (node_id,)
        )
        row = cur.fetchone()
        return self._row_to_node(row) if row else None

    def edges(
        self, rel: str | None = None, src: str | None = None, dst: str | None = None
    ) -> list[Edge]:
        clauses, params = [], []
        for col, val in (("rel", rel), ("src", src), ("dst", dst)):
            if val is not None:
                clauses.append(f"{col}=?")
                params.append(val)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        cur = self._db.execute(f"SELECT src, rel, dst FROM edges{where}", params)
        return [Edge(src=r[0], rel=r[1], dst=r[2]) for r in cur.fetchall()]

    def count(self, type: str | None = None) -> int:
        return len(self.nodes(type))
