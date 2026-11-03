"""Human-reviewed skill change proposals with isolated staging.

Active skills are read-only. This module snapshots a skill, stages proposed
content elsewhere, validates the diff, and records explicit approval.
It intentionally does not publish or install changes.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import re
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(UTC).isoformat()


class SkillProposalStore:
    """Proposal lifecycle backed by SQLite; staging never writes active skills."""

    def __init__(self, database: str | Path, skills_dir: str | Path = "skills",
                 staging_dir: str | Path | None = None) -> None:
        self.database = str(database)
        self.skills_dir = Path(skills_dir).expanduser().resolve()
        self.staging_dir = Path(staging_dir or (self.skills_dir.parent / ".loop-maker-staging"))
        self.staging_dir = self.staging_dir.expanduser().resolve()
        if self.database != ":memory:":
            Path(self.database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self._memory = sqlite3.connect(":memory:") if self.database == ":memory:" else None
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS skill_proposals (
                id TEXT PRIMARY KEY, skill_path TEXT NOT NULL, rationale TEXT NOT NULL,
                observation_ids_json TEXT NOT NULL, original_content TEXT NOT NULL,
                proposed_content TEXT NOT NULL, original_sha256 TEXT NOT NULL,
                status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                staged_path TEXT, validation_json TEXT
            )""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_skill_proposals_status ON skill_proposals(status)")

    def _connect(self) -> sqlite3.Connection:
        db = self._memory or sqlite3.connect(self.database, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout = 10000")
        return db

    def _safe_skill_file(self, relative_path: str) -> Path:
        candidate = Path(relative_path)
        if candidate.is_absolute() or not candidate.parts or ".." in candidate.parts:
            raise ValueError("skill_path must be a relative path inside skills_dir")
        if candidate.suffix.lower() not in {".md", ".markdown"}:
            raise ValueError("only Markdown skill files can be proposed")
        current = self.skills_dir
        for part in candidate.parts:
            current = current / part
            if current.is_symlink():
                raise ValueError("symlinks are not allowed in skill paths")
        resolved = current.resolve()
        if not resolved.is_relative_to(self.skills_dir):
            raise ValueError("skill_path escapes skills_dir")
        if not resolved.is_file():
            raise ValueError("skill file does not exist")
        return resolved

    def create_proposal(self, *, skill_path: str, proposed_content: str,
                        rationale: str, observation_ids: list[str]) -> dict[str, Any]:
        if not rationale.strip() or not proposed_content.strip():
            raise ValueError("rationale and proposed_content are required")
        if len(proposed_content.encode("utf-8")) > 256_000:
            raise ValueError("proposed_content exceeds the 256 KB limit")
        if not observation_ids or not all(isinstance(x, str) and x.strip() for x in observation_ids):
            raise ValueError("at least one valid supporting observation ID is required")
        path = self._safe_skill_file(skill_path)
        original = path.read_text(encoding="utf-8")
        if original == proposed_content:
            raise ValueError("proposed_content is identical to the active skill")
        proposal_id = f"prop_{uuid.uuid4().hex}"
        now = _now()
        record = {
            "id": proposal_id, "skill_path": skill_path, "rationale": rationale.strip(),
            "observation_ids": list(dict.fromkeys(observation_ids)),
            "original_sha256": hashlib.sha256(original.encode("utf-8")).hexdigest(),
            "status": "proposed", "created_at": now, "updated_at": now,
        }
        with self._connect() as db:
            db.execute("""INSERT INTO skill_proposals
                (id, skill_path, rationale, observation_ids_json, original_content,
                 proposed_content, original_sha256, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'proposed', ?, ?)""",
                (proposal_id, skill_path, record["rationale"], json.dumps(record["observation_ids"]),
                 original, proposed_content, record["original_sha256"], now, now))
        return record

    def _get_row(self, proposal_id: str) -> sqlite3.Row:
        with self._connect() as db:
            row = db.execute("SELECT * FROM skill_proposals WHERE id=?", (proposal_id,)).fetchone()
        if row is None:
            raise ValueError("proposal_not_found")
        return row

    @staticmethod
    def _decode(row: sqlite3.Row) -> dict[str, Any]:
        item = dict(row)
        item["observation_ids"] = json.loads(item.pop("observation_ids_json"))
        item.pop("original_content", None)
        item.pop("proposed_content", None)
        item["validation"] = json.loads(item.pop("validation_json")) if item.get("validation_json") else None
        return item

    def get_proposal(self, proposal_id: str) -> dict[str, Any]:
        return self._decode(self._get_row(proposal_id))

    def list_proposals(self, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        if not 1 <= limit <= 200:
            raise ValueError("limit must be between 1 and 200")
        if status and status not in {"proposed", "staged", "validated", "approved", "rejected"}:
            raise ValueError("invalid proposal status")
        with self._connect() as db:
            if status:
                rows = db.execute("SELECT * FROM skill_proposals WHERE status=? ORDER BY created_at DESC LIMIT ?",
                                  (status, limit)).fetchall()
            else:
                rows = db.execute("SELECT * FROM skill_proposals ORDER BY created_at DESC LIMIT ?",
                                  (limit,)).fetchall()
        return [self._decode(row) for row in rows]

    def stage_proposal(self, proposal_id: str) -> dict[str, Any]:
        row = self._get_row(proposal_id)
        if row["status"] not in {"proposed", "staged", "validated"}:
            raise ValueError("only proposed, staged or validated proposals can be staged")
        active_path = self._safe_skill_file(row["skill_path"])
        current = active_path.read_text(encoding="utf-8")
        current_hash = hashlib.sha256(current.encode("utf-8")).hexdigest()
        if current_hash != row["original_sha256"]:
            raise ValueError("active_skill_changed_since_proposal; create a new proposal")
        target_dir = (self.staging_dir / proposal_id).resolve()
        if not target_dir.is_relative_to(self.staging_dir) or target_dir.exists():
            raise ValueError("staging destination is invalid or already exists")
        target = target_dir / Path(row["skill_path"]).name
        target_dir.mkdir(parents=True, exist_ok=False)
        target.write_text(row["proposed_content"], encoding="utf-8")
        with self._connect() as db:
            db.execute("UPDATE skill_proposals SET status='staged', staged_path=?, updated_at=? WHERE id=?",
                       (str(target), _now(), proposal_id))
        return {"proposal_id": proposal_id, "status": "staged", "staged_path": str(target)}

    def diff_proposal(self, proposal_id: str) -> dict[str, Any]:
        row = self._get_row(proposal_id)
        diff = "".join(difflib.unified_diff(
            row["original_content"].splitlines(keepends=True),
            row["proposed_content"].splitlines(keepends=True),
            fromfile=f"active/{row['skill_path']}", tofile=f"proposed/{row['skill_path']}",
        ))
        return {"proposal_id": proposal_id, "diff": diff}

    def validate_proposal(self, proposal_id: str) -> dict[str, Any]:
        row = self._get_row(proposal_id)
        checks = {
            "markdown_file": row["skill_path"].endswith((".md", ".markdown")),
            "non_empty": bool(row["proposed_content"].strip()),
            "size_limit": len(row["proposed_content"].encode("utf-8")) <= 256_000,
            "has_frontmatter": row["proposed_content"].startswith("---\n"),
            "has_skill_name": bool(re.search(r"(?m)^name:\\s*\\S+", row["proposed_content"])),
            "has_supporting_observations": bool(json.loads(row["observation_ids_json"])),
        }
        active_unchanged = False
        try:
            active = self._safe_skill_file(row["skill_path"]).read_text(encoding="utf-8")
            active_unchanged = hashlib.sha256(active.encode("utf-8")).hexdigest() == row["original_sha256"]
        except (OSError, ValueError):
            pass
        checks["active_skill_unchanged"] = active_unchanged
        valid = all(checks.values())
        result = {"valid": valid, "checks": checks,
                  "note": "Structural checks only; no skill execution or semantic quality guarantee."}
        status = "validated" if valid and row["status"] in {"staged", "validated"} else row["status"]
        with self._connect() as db:
            db.execute("UPDATE skill_proposals SET status=?, validation_json=?, updated_at=? WHERE id=?",
                       (status, json.dumps(result), _now(), proposal_id))
        return {"proposal_id": proposal_id, **result, "status": status}

    def approve_proposal(self, proposal_id: str, *, approved: bool) -> dict[str, Any]:
        row = self._get_row(proposal_id)
        if row["status"] != "validated":
            raise ValueError("proposal must pass validation before human approval")
        status = "approved" if approved else "rejected"
        with self._connect() as db:
            db.execute("UPDATE skill_proposals SET status=?, updated_at=? WHERE id=?",
                       (status, _now(), proposal_id))
        return {"proposal_id": proposal_id, "status": status,
                "published": False, "note": "Approval records a human decision; publication is not implemented."}

    def close(self) -> None:
        if self._memory is not None:
            self._memory.close()
            self._memory = None
