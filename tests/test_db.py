import importlib

import pytest

from risk_engine import analyze_contract


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    import db as module
    return importlib.reload(module)


def test_accounts_and_private_history(db):
    assert db.create_user("Alice", "password1") is None
    assert db.create_user("alice", "password1") == "That username is taken."
    assert db.create_user("bob", "short") is not None
    assert db.verify_user("ALICE", "password1") == "alice"
    assert db.verify_user("alice", "wrong") is None
    assert db.verify_user("nobody", "password1") is None

    db.create_user("bob", "password2")
    text = "The Provider may terminate immediately and without notice in its sole discretion."
    aid = db.save_analysis("alice", "a.txt", analyze_contract(text), text)
    assert [r["id"] for r in db.list_analyses("alice")] == [aid]
    assert db.get_analysis("alice", aid)["text"] == text
    assert db.get_analysis("bob", aid) is None  # other accounts cannot open it
    db.delete_analysis("bob", aid)
    assert db.get_analysis("alice", aid) is not None
    db.delete_analysis("alice", aid)
    assert db.list_analyses("alice") == []
