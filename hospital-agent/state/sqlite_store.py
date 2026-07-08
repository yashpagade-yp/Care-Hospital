from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SQLiteStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS auth_sessions (
                    telegram_user_id INTEGER PRIMARY KEY,
                    email TEXT,
                    patient_id TEXT,
                    role TEXT,
                    access_token TEXT,
                    token_type TEXT,
                    pending_email TEXT,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS flow_state (
                    telegram_user_id INTEGER PRIMARY KEY,
                    active_intent TEXT NOT NULL,
                    step TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS short_term_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_user_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def upsert_auth_session(
        self,
        *,
        telegram_user_id: int,
        email: str,
        patient_id: str | None,
        role: str,
        access_token: str,
        token_type: str,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO auth_sessions (
                    telegram_user_id, email, patient_id, role, access_token, token_type, pending_email, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, NULL, ?)
                ON CONFLICT(telegram_user_id) DO UPDATE SET
                    email = excluded.email,
                    patient_id = excluded.patient_id,
                    role = excluded.role,
                    access_token = excluded.access_token,
                    token_type = excluded.token_type,
                    pending_email = NULL,
                    updated_at = excluded.updated_at
                """,
                (
                    telegram_user_id,
                    email,
                    patient_id,
                    role,
                    access_token,
                    token_type,
                    self._now(),
                ),
            )

    def set_pending_login(self, telegram_user_id: int, email: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO auth_sessions (telegram_user_id, pending_email, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(telegram_user_id) DO UPDATE SET
                    pending_email = excluded.pending_email,
                    updated_at = excluded.updated_at
                """,
                (telegram_user_id, email, self._now()),
            )

    def get_auth_session(self, telegram_user_id: int) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM auth_sessions WHERE telegram_user_id = ?",
                (telegram_user_id,),
            ).fetchone()
        return dict(row) if row else {}

    def clear_auth_session(self, telegram_user_id: int) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM auth_sessions WHERE telegram_user_id = ?",
                (telegram_user_id,),
            )

    def set_flow_state(
        self,
        telegram_user_id: int,
        *,
        active_intent: str,
        step: str,
        payload: dict[str, Any],
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO flow_state (telegram_user_id, active_intent, step, payload_json, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(telegram_user_id) DO UPDATE SET
                    active_intent = excluded.active_intent,
                    step = excluded.step,
                    payload_json = excluded.payload_json,
                    updated_at = excluded.updated_at
                """,
                (
                    telegram_user_id,
                    active_intent,
                    step,
                    json.dumps(payload),
                    self._now(),
                ),
            )

    def get_flow_state(self, telegram_user_id: int) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM flow_state WHERE telegram_user_id = ?",
                (telegram_user_id,),
            ).fetchone()
        if not row:
            return {}
        result = dict(row)
        result["payload"] = json.loads(result.pop("payload_json"))
        return result

    def clear_flow_state(self, telegram_user_id: int) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM flow_state WHERE telegram_user_id = ?",
                (telegram_user_id,),
            )

    def add_short_term_memory(self, telegram_user_id: int, role: str, content: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO short_term_memory (telegram_user_id, role, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (telegram_user_id, role, content, self._now()),
            )
            connection.execute(
                """
                DELETE FROM short_term_memory
                WHERE id NOT IN (
                    SELECT id FROM short_term_memory
                    WHERE telegram_user_id = ?
                    ORDER BY id DESC
                    LIMIT 12
                )
                AND telegram_user_id = ?
                """,
                (telegram_user_id, telegram_user_id),
            )

    def get_recent_short_term_memory(self, telegram_user_id: int, limit: int = 6) -> list[dict[str, Any]]:
        if limit <= 0:
            return []
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT role, content, created_at
                FROM short_term_memory
                WHERE telegram_user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (telegram_user_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
