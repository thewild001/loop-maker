"""SQLite session journal; other stores can implement this interface."""
from __future__ import annotations
import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

class SessionStore:
    def __init__(self, database: str = "loop-maker.sqlite3") -> None:
        self.database = database
        self._memory_connection = sqlite3.connect(":memory:") if database == ":memory:" else None
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = self._memory_connection or sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY, agent_id TEXT NOT NULL,
                    objective TEXT NOT NULL, mode TEXT NOT NULL,
                    status TEXT NOT NULL, converged INTEGER NOT NULL DEFAULT 0,
                    output TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS iterations (
                    session_id TEXT NOT NULL, iteration INTEGER NOT NULL,
                    output TEXT NOT NULL, accepted INTEGER NOT NULL,
                    usage_json TEXT NOT NULL, metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL, PRIMARY KEY (session_id, iteration)
                );
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL,
                    iteration INTEGER NOT NULL, code TEXT NOT NULL,
                    message TEXT NOT NULL, created_at TEXT NOT NULL
                );
            """)

    def start_session(self, session_id: str, agent_id: str, objective: str, mode: str) -> None:
        now = _now()
        with self._connect() as db:
            db.execute("""INSERT INTO sessions
                (session_id, agent_id, objective, mode, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'RUNNING', ?, ?)""",
                (session_id, agent_id, objective, mode, now, now))

    def record_iteration(self, session_id: str, iteration: int, output: str,
                         accepted: bool, usage: dict[str, Any] | None = None,
                         metadata: dict[str, Any] | None = None) -> None:
        with self._connect() as db:
            exists = db.execute("SELECT 1 FROM sessions WHERE session_id=?", (session_id,)).fetchone()
            if not exists:
                raise KeyError(f"Unknown session: {session_id}")
            db.execute("INSERT INTO iterations VALUES (?, ?, ?, ?, ?, ?, ?)",
                (session_id, iteration, output, int(accepted), json.dumps(usage or {}),
                 json.dumps(metadata or {}), _now()))

    def record_error(self, session_id: str, iteration: int, code: str, message: str) -> None:
        with self._connect() as db:
            db.execute("""INSERT INTO errors
                (session_id, iteration, code, message, created_at) VALUES (?, ?, ?, ?, ?)""",
                (session_id, iteration, code, message, _now()))

    def finish_session(self, session_id: str, status: str, converged: bool, output: str) -> None:
        with self._connect() as db:
            db.execute("""UPDATE sessions SET status=?, converged=?, output=?, updated_at=?
                WHERE session_id=?""", (status, int(converged), output, _now(), session_id))

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM sessions WHERE session_id=?", (session_id,)).fetchone()
            if not row:
                return None
            session = dict(row)
            session["iterations"] = [
                {**dict(item), "accepted": bool(item["accepted"]),
                 "usage": json.loads(item.pop("usage_json")),
                 "metadata": json.loads(item.pop("metadata_json"))}
                for item in db.execute(
                    "SELECT * FROM iterations WHERE session_id=? ORDER BY iteration", (session_id,)
                ).fetchall()
            ]
            session["errors"] = [
                dict(item) for item in db.execute(
                    "SELECT * FROM errors WHERE session_id=? ORDER BY id", (session_id,)
                ).fetchall()
            ]
            return session

    def close(self) -> None:
        if self._memory_connection is not None:
            self._memory_connection.close()
            self._memory_connection = None
