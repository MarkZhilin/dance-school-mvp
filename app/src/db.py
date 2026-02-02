from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from typing import Iterable, List, Tuple


@dataclass(frozen=True)
class AdminRecord:
    tg_user_id: int
    name: str
    is_active: int


def _ensure_db_dir(db_path: str) -> None:
    directory = os.path.dirname(os.path.abspath(db_path))
    if directory:
        os.makedirs(directory, exist_ok=True)


def init_db(db_path: str) -> None:
    _ensure_db_dir(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS admins (
              tg_user_id INTEGER UNIQUE,
              name TEXT NOT NULL,
              is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
              created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        conn.commit()


def upsert_admin(db_path: str, tg_user_id: int, name: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO admins(tg_user_id, name, is_active)
            VALUES (?, ?, 1)
            ON CONFLICT(tg_user_id) DO UPDATE SET
              name = excluded.name,
              is_active = 1
            """,
            (tg_user_id, name),
        )
        conn.commit()


def deactivate_admin(db_path: str, tg_user_id: int) -> bool:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "UPDATE admins SET is_active = 0 WHERE tg_user_id = ?",
            (tg_user_id,),
        )
        conn.commit()
        return cur.rowcount > 0


def list_admins(db_path: str) -> Tuple[List[AdminRecord], List[AdminRecord]]:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "SELECT tg_user_id, name, is_active FROM admins ORDER BY name COLLATE NOCASE"
        )
        rows: Iterable[Tuple[int, str, int]] = cur.fetchall()

    active: List[AdminRecord] = []
    inactive: List[AdminRecord] = []
    for tg_user_id, name, is_active in rows:
        record = AdminRecord(tg_user_id=tg_user_id, name=name, is_active=is_active)
        if is_active:
            active.append(record)
        else:
            inactive.append(record)
    return active, inactive
