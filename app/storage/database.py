from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Any


def default_db_path() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    folder = Path(base) / "HardwareOptimizer"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "history.sqlite"


_SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    profile TEXT NOT NULL,
    games TEXT NOT NULL,
    scan_json TEXT NOT NULL,
    recommendations_json TEXT NOT NULL,
    report_path TEXT
);
CREATE TABLE IF NOT EXISTS recommendation_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending','applied','ignored')),
    updated_at TEXT NOT NULL
);
"""


class HistoryStore:
    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path) if db_path else default_db_path()
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _ensure_schema(self) -> None:
        with closing(self._connect()) as conn, conn:
            conn.executescript(_SCHEMA)

    def save_scan(
        self,
        profile_key: str,
        games: list[str],
        scan_dict: dict[str, Any],
        recommendations: list[dict[str, Any]],
        report_path: str | None = None,
    ) -> int:
        created_at = datetime.now().isoformat(timespec="seconds")
        with closing(self._connect()) as conn, conn:
            cur = conn.execute(
                "INSERT INTO scans(created_at, profile, games, scan_json, "
                "recommendations_json, report_path) VALUES (?,?,?,?,?,?)",
                (
                    created_at,
                    profile_key,
                    json.dumps(games),
                    json.dumps(scan_dict),
                    json.dumps(recommendations),
                    report_path,
                ),
            )
            scan_id = cur.lastrowid
            for rec in recommendations:
                conn.execute(
                    "INSERT INTO recommendation_status(scan_id, title, status, updated_at) "
                    "VALUES (?,?,?,?)",
                    (scan_id, rec.get("title", ""), "pending", created_at),
                )
            return int(scan_id)

    def list_scans(self, limit: int = 25) -> list[dict[str, Any]]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT id, created_at, profile, games, report_path FROM scans "
                "ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {
                "id": r[0],
                "created_at": r[1],
                "profile": r[2],
                "games": json.loads(r[3]),
                "report_path": r[4],
            }
            for r in rows
        ]

    def update_status(self, scan_id: int, title: str, status: str) -> None:
        if status not in {"pending", "applied", "ignored"}:
            raise ValueError("status inválido")
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "UPDATE recommendation_status SET status=?, updated_at=? "
                "WHERE scan_id=? AND title=?",
                (status, datetime.now().isoformat(timespec="seconds"), scan_id, title),
            )
