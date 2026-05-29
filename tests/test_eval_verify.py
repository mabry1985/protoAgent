from evals import verify
from knowledge import KnowledgeStore


def test_kb_snapshot_restore_deletes_new_chunks(monkeypatch, tmp_path):
    monkeypatch.setenv("KNOWLEDGE_DB_PATH", str(tmp_path / "agent.db"))

    store = KnowledgeStore()
    baseline_id = store.add_chunk("baseline eval verify row", domain="eval")
    assert baseline_id is not None

    snapshot = verify.kb_snapshot()
    late_id = store.add_chunk("late eval verify row", domain="eval")
    assert late_id is not None
    assert verify.find_chunk_containing("late eval verify row", domain="eval")

    deleted = verify.restore_kb_snapshot(snapshot, settle_s=0)

    assert deleted >= 1
    assert verify.find_chunk_containing("baseline eval verify row", domain="eval")
    assert verify.find_chunk_containing("late eval verify row", domain="eval") is None


def test_delete_session_summary(monkeypatch, tmp_path):
    from graph.middleware import memory

    monkeypatch.setattr(memory, "MEMORY_PATH", str(tmp_path))
    session_file = tmp_path / "eval-session.json"
    session_file.write_text("{}", encoding="utf-8")

    verify.delete_session_summary("eval-session")

    assert not session_file.exists()
