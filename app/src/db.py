from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple


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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS clients (
              client_id    INTEGER PRIMARY KEY AUTOINCREMENT,
              full_name    TEXT NOT NULL,
              phone        TEXT NOT NULL,
              tg_user_id   INTEGER,
              tg_username  TEXT,
              birth_date   TEXT,
              comment      TEXT,
              created_at   TEXT NOT NULL DEFAULT (datetime('now')),
              status       TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive'))
            );
            """
        )
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_clients_phone ON clients(phone);")
        conn.execute("CREATE INDEX IF NOT EXISTS ix_clients_tg_user_id ON clients(tg_user_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS ix_clients_tg_username ON clients(tg_username);")
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


def is_admin_active(db_path: str, tg_user_id: int) -> bool:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "SELECT 1 FROM admins WHERE tg_user_id = ? AND is_active = 1 LIMIT 1",
            (tg_user_id,),
        )
        return cur.fetchone() is not None


def get_client_by_phone(db_path: str, phone: str) -> Optional[Tuple[int, str, str, Optional[str], Optional[str], Optional[str]]]:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            SELECT client_id, full_name, phone, tg_username, birth_date, comment
            FROM clients
            WHERE phone = ?
            LIMIT 1
            """,
            (phone,),
        )
        return cur.fetchone()


def get_client_by_tg_username(
    db_path: str, tg_username: str
) -> Optional[Tuple[int, str, str, Optional[str], Optional[str], Optional[str]]]:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            SELECT client_id, full_name, phone, tg_username, birth_date, comment
            FROM clients
            WHERE lower(ltrim(tg_username, '@')) = ?
            LIMIT 1
            """,
            (tg_username.lower(),),
        )
        return cur.fetchone()


def get_client_by_id(
    db_path: str, client_id: int
) -> Optional[Tuple[int, str, str, Optional[str], Optional[str], Optional[str]]]:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            SELECT client_id, full_name, phone, tg_username, birth_date, comment
            FROM clients
            WHERE client_id = ?
            LIMIT 1
            """,
            (client_id,),
        )
        return cur.fetchone()


def search_clients_by_name(
    db_path: str, query: str, limit: int = 11
) -> List[Tuple[int, str, str]]:
    query = query.strip()
    if not query:
        return []
    normalized = query.casefold()
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            SELECT client_id, full_name, phone
            FROM clients
            """,
        )
        rows = cur.fetchall()
    matched = [row for row in rows if normalized in row[1].casefold()]
    matched.sort(key=lambda row: row[1].casefold())
    return matched[:limit]


def create_client(
    db_path: str,
    full_name: str,
    phone: str,
    tg_user_id: Optional[int],
    tg_username: Optional[str],
    birth_date: Optional[str],
    comment: Optional[str],
) -> int:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO clients(full_name, phone, tg_user_id, tg_username, birth_date, comment)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (full_name, phone, tg_user_id, tg_username, birth_date, comment),
        )
        conn.commit()
        return int(cur.lastrowid)
