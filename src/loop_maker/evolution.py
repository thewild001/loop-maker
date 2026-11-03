"""Persistent, privacy-conscious observation registry for skill evolution.

The Evolution Engine is deliberately separate from the Loop Maker session journal.
It records sanitized observations; it does not modify skills or execute observed content.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CATEGORIES = {
    "user-correction", "repeated-error", "successful-strategy",
    "tool-failure", "instruction-gap", "decision", "other",
}
SENSITIVITY = {"public", "internal", "restricted"}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


class EvolutionStore:
    """SQLite-backed observation store with a small, stable public API."""

    def __init__(self, database: str | Path = "loop-maker-evolution.sqlite3") -> None:
        self.database = str(database)
        self._memory = sqlite3.connect(":memory:") if self.database == ":memory:" else None
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        db = self._memory or sqlite3.connect(self.database, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout = 10000")
        return db

    def _initialize(self) -> None:
        if self.database != ":memory:":
            Path(self.database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("PRAGMA journal_mode = WAL")
            db.execute("""
                CREATE TABLE IF NOT EXISTS observations (
                    id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    session_id TEXT,
                    domain TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    context_json TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    sensitivity TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_observations_created ON observations(created_at)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_observations_domain_category ON observations(domain, category)")

    def add_observation(
        self,
        *,
        description: str,
        domain: str,
        category: str,
        source: str = "host-agent",
        session_id: str | None = None,
        evidence: list[str] | None = None,
        context: dict[str, Any] | None = None,
        confidence: float = 0.5,
        sensitivity: str = "internal",
        observation_id: str | None = None,
    ) -> dict[str, Any]:
        description = description.strip()
        domain = domain.strip()
        source = source.strip()
        if not description or not domain or not source:
            raise ValueError("description, domain and source are required")
        if category not in CATEGORIES:
            raise ValueError(f"category must be one of: {', '.join(sorted(CATEGORIES))}")
        if sensitivity not in SENSITIVITY:
            raise ValueError(f"sensitivity must be one of: {', '.join(sorted(SENSITIVITY))}")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not isinstance(evidence or [], list) or not all(isinstance(item, str) for item in (evidence or [])):
            raise ValueError("evidence must be a list of strings")
        if not isinstance(context or {}, dict):
            raise ValueError("context must be an object")
        record = {
            "id": observation_id or f"obs_{uuid.uuid4().hex}",
            "source": source,
            "session_id": session_id,
            "domain": domain,
            "category": category,
            "description": description,
            "evidence": evidence or [],
            "context": context or {},
            "confidence": float(confidence),
            "sensitivity": sensitivity,
            "created_at": _now(),
        }
        with self._connect() as db:
            db.execute(
                """INSERT INTO observations
                (id, source, session_id, domain, category, description, evidence_json,
                 context_json, confidence, sensitivity, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (record["id"], record["source"], record["session_id"], record["domain"],
                 record["category"], record["description"], _json(record["evidence"]),
                 _json(record["context"]), record["confidence"], record["sensitivity"],
                 record["created_at"]),
            )
        return record

    @staticmethod
    def _decode(row: sqlite3.Row) -> dict[str, Any]:
        item = dict(row)
        item["evidence"] = json.loads(item.pop("evidence_json"))
        item["context"] = json.loads(item.pop("context_json"))
        return item

    def get_observation(self, observation_id: str) -> dict[str, Any] | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM observations WHERE id=?", (observation_id,)).fetchone()
            return self._decode(row) if row else None

    def list_observations(
        self,
        *,
        domain: str | None = None,
        category: str | None = None,
        session_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        if not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        clauses: list[str] = []
        params: list[Any] = []
        for column, value in (("domain", domain), ("category", category), ("session_id", session_id)):
            if value is not None:
                clauses.append(f"{column}=?")
                params.append(value)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as db:
            rows = db.execute(
                f"SELECT * FROM observations {where} ORDER BY created_at DESC LIMIT ?",
                (*params, limit),
            ).fetchall()
        return [self._decode(row) for row in rows]

    def observation_groups(self, *, min_occurrences: int = 2, limit: int = 50) -> list[dict[str, Any]]:
        """Return deterministic candidate groups, not claims of proven causal patterns."""
        if min_occurrences < 2:
            raise ValueError("min_occurrences must be at least 2")
        observations = self.list_observations(limit=500)
        groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
        for item in observations:
            skill = item["context"].get("skill", "")
            groups[(item["domain"], item["category"], str(skill))].append(item)
        result = []
        for (domain, category, skill), items in groups.items():
            if len(items) >= min_occurrences:
                result.append({
                    "domain": domain,
                    "category": category,
                    "skill": skill or None,
                    "occurrences": len(items),
                    "observation_ids": [item["id"] for item in items],
                    "latest_at": items[0]["created_at"],
                    "confidence_mean": round(sum(item["confidence"] for item in items) / len(items), 3),
                    "interpretation": "candidate-pattern; requires human review",
                })
        result.sort(key=lambda group: (-group["occurrences"], group["domain"], group["category"]))
        return result[:limit]

    def close(self) -> None:
        if self._memory is not None:
            self._memory.close()
            self._memory = None
