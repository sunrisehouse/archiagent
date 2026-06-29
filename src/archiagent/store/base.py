"""저장소 인터페이스.

산출물과 연관 관계를 보관·조회한다. 구현은 교체 가능하다(지금은 SQLite, 나중에 Neo4j 등).
이 인터페이스는 내부 전용이며 사용자에게 노출되지 않는다.
"""

from __future__ import annotations

from typing import Protocol

from archiagent.schema import Edge, Node


class GraphStore(Protocol):
    def upsert(self, nodes: list[Node], edges: list[Edge]) -> None: ...

    def nodes(self, type: str | None = None) -> list[Node]: ...

    def get(self, node_id: str) -> Node | None: ...

    def edges(
        self, rel: str | None = None, src: str | None = None, dst: str | None = None
    ) -> list[Edge]: ...

    def count(self, type: str | None = None) -> int: ...
