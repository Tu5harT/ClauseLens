"""SQLite accounts + saved analyses. Passwords are salted PBKDF2 hashes.

shortcut: SQLite file on local disk (lost on ephemeral hosts), contract text stored
unencrypted; use a mounted volume (DATA_DIR) or Postgres + encryption when it matters.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
from contextlib import closing
from pathlib import Path

DB_PATH = Path(os.environ.get("DATA_DIR", Path(__file__).parent / "data")) / "app.db"
_USERNAME = re.compile(r"^[a-z0-9_.-]{3,32}$")
_ITERATIONS = 200_000


def _run(sql: str, args: tuple = ()):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        with conn:
            conn.execute("PRAGMA foreign_keys = ON")
            return conn.execute(sql, args).fetchall()


_run("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, salt TEXT NOT NULL, pw_hash TEXT NOT NULL)")
_run(
    """CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL REFERENCES users(username),
        filename TEXT NOT NULL,
        created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        overall_score INTEGER NOT NULL,
        overall_level TEXT NOT NULL,
        high INTEGER NOT NULL, medium INTEGER NOT NULL, low INTEGER NOT NULL,
        text TEXT NOT NULL)"""
)


try:
    _run("ALTER TABLE analyses ADD COLUMN pdf BLOB")  # original PDF, so highlights can be re-drawn
except sqlite3.OperationalError:
    pass


def _hash(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS).hex()


def create_user(username: str, password: str) -> str | None:
    """Return an error message, or None on success."""
    username = username.strip().lower()
    if not _USERNAME.match(username):
        return "Username must be 3-32 characters: letters, numbers, . _ -"
    if len(password) < 8:
        return "Password must be at least 8 characters."
    salt = secrets.token_bytes(16)
    try:
        _run("INSERT INTO users VALUES (?, ?, ?)", (username, salt.hex(), _hash(password, salt)))
    except sqlite3.IntegrityError:
        return "That username is taken."
    return None


def verify_user(username: str, password: str) -> str | None:
    """Return the normalised username if the credentials match."""
    username = username.strip().lower()
    rows = _run("SELECT salt, pw_hash FROM users WHERE username = ?", (username,))
    salt, expected = (rows[0]["salt"], rows[0]["pw_hash"]) if rows else ("00" * 16, "")
    ok = hmac.compare_digest(_hash(password, bytes.fromhex(salt)), expected)  # same work either way
    return username if rows and ok else None


def save_analysis(username: str, filename: str, report, text: str, pdf: bytes | None = None) -> int:
    lv = report.level_counts
    rows = _run(
        "INSERT INTO analyses (username, filename, overall_score, overall_level, high, medium, low, text, pdf) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id",
        (username, filename, report.overall_score, report.overall_level, lv["High"], lv["Medium"], lv["Low"], text, pdf),
    )
    return rows[0]["id"]


def list_analyses(username: str):
    return _run(
        "SELECT id, filename, created, overall_score, overall_level, high, medium, low "
        "FROM analyses WHERE username = ? ORDER BY id DESC",
        (username,),
    )


def get_analysis(username: str, analysis_id: int):
    rows = _run("SELECT * FROM analyses WHERE id = ? AND username = ?", (analysis_id, username))
    return rows[0] if rows else None


def delete_analysis(username: str, analysis_id: int) -> None:
    _run("DELETE FROM analyses WHERE id = ? AND username = ?", (analysis_id, username))
