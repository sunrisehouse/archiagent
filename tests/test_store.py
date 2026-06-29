from archiagent.schema import REQUIREMENT, Edge, Node
from archiagent.store import SqliteStore


def test_upsert_and_query():
    store = SqliteStore()
    store.upsert(
        [Node(id="R-1", type=REQUIREMENT, title="클라우드 전환")],
        [Edge(src="doc:requirements", rel="DESCRIBES", dst="R-1")],
    )
    assert store.count(REQUIREMENT) == 1
    assert store.get("R-1").title == "클라우드 전환"
    assert store.edges(rel="DESCRIBES", dst="R-1")


def test_upsert_is_idempotent():
    store = SqliteStore()
    n = Node(id="R-1", type=REQUIREMENT, title="원본")
    store.upsert([n], [])
    store.upsert([Node(id="R-1", type=REQUIREMENT, title="수정")], [])
    assert store.count(REQUIREMENT) == 1  # 중복 노드 없음
    assert store.get("R-1").title == "수정"
    e = Edge(src="a", rel="R", dst="b")
    store.upsert([], [e])
    store.upsert([], [e])
    assert len(store.edges(rel="R")) == 1  # 중복 엣지 없음
