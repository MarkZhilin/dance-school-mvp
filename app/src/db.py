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
            CREATE TABLE IF NOT EXISTS groups (
              group_id     INTEGER PRIMARY KEY AUTOINCREMENT,
              name         TEXT NOT NULL,
              trainer_name TEXT,
              capacity     INTEGER NOT NULL DEFAULT 0 CHECK (capacity >= 0),
              room_name    TEXT,
              is_active    INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1))
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schedule (
              schedule_id  INTEGER PRIMARY KEY AUTOINCREMENT,
              group_id     INTEGER NOT NULL REFERENCES groups(group_id) ON DELETE CASCADE,
              day_of_week  INTEGER NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
              time_hhmm    TEXT NOT NULL,
              duration_min INTEGER NOT NULL CHECK (duration_min > 0),
              is_active    INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1))
            );
            """
        )
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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS client_groups (
              client_id   INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
              group_id    INTEGER NOT NULL REFERENCES groups(group_id) ON DELETE CASCADE,
              status      TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive')),
              since_date  TEXT NOT NULL DEFAULT (date('now')),
              until_date  TEXT,
              PRIMARY KEY (client_id, group_id)
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS visits (
              visit_id     INTEGER PRIMARY KEY AUTOINCREMENT,
              visit_date   TEXT NOT NULL,
              group_id     INTEGER NOT NULL REFERENCES groups(group_id),
              schedule_id  INTEGER REFERENCES schedule(schedule_id),
              client_id    INTEGER NOT NULL REFERENCES clients(client_id),
              status       TEXT NOT NULL CHECK (status IN ('booked','attended','noshow','cancelled')),
              created_by   INTEGER,
              created_at   TEXT NOT NULL DEFAULT (datetime('now')),
              comment      TEXT
            );
            """
        )
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_visits_unique
              ON visits(visit_date, group_id, schedule_id, client_id);
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS ix_visits_date_group ON visits(visit_date, group_id);")
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


def list_active_groups(db_path: str) -> List[Tuple[int, str, Optional[str], int, Optional[str]]]:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            SELECT group_id, name, trainer_name, capacity, room_name
            FROM groups
            WHERE is_active = 1
            ORDER BY name COLLATE NOCASE
            """
        )
        return cur.fetchall()


def create_group(
    db_path: str,
    name: str,
    trainer_name: Optional[str] = None,
    capacity: int = 0,
    room_name: Optional[str] = None,
) -> int:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO groups(name, trainer_name, capacity, room_name, is_active)
            VALUES (?, ?, ?, ?, 1)
            """,
            (name, trainer_name, capacity, room_name),
        )
        conn.commit()
        return int(cur.lastrowid)


def upsert_client_group_active(db_path: str, client_id: int, group_id: int) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO client_groups(client_id, group_id, status)
            VALUES (?, ?, 'active')
            ON CONFLICT(client_id, group_id) DO UPDATE SET
              status = 'active',
              until_date = NULL
            """,
            (client_id, group_id),
        )
        conn.commit()


def visit_exists(db_path: str, date: str, group_id: int, client_id: int) -> bool:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            SELECT 1
            FROM visits
            WHERE visit_date = ? AND group_id = ? AND client_id = ? AND schedule_id IS NULL
            LIMIT 1
            """,
            (date, group_id, client_id),
        )
        return cur.fetchone() is not None


def create_single_visit_booked(
    db_path: str, date: str, group_id: int, client_id: int, created_by: Optional[int]
) -> bool:
    if visit_exists(db_path, date, group_id, client_id):
        return False
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO visits(visit_date, group_id, schedule_id, client_id, status, created_by)
            VALUES (?, ?, NULL, ?, 'booked', ?)
            """,
            (date, group_id, client_id, created_by),
        )
        conn.commit()
    return True


def list_clients_for_attendance(
    db_path: str, group_id: int, visit_date: str
) -> List[Tuple[int, str, str]]:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            SELECT client_id, full_name, phone FROM (
              SELECT c.client_id AS client_id, c.full_name AS full_name, c.phone AS phone
              FROM client_groups cg
              JOIN clients c ON c.client_id = cg.client_id
              WHERE cg.group_id = ? AND cg.status = 'active'
              UNION
              SELECT c.client_id AS client_id, c.full_name AS full_name, c.phone AS phone
              FROM visits v
              JOIN clients c ON c.client_id = v.client_id
              WHERE v.group_id = ? AND v.visit_date = ? AND v.status = 'booked'
            )
            ORDER BY full_name COLLATE NOCASE
            """,
            (group_id, group_id, visit_date),
        )
        return cur.fetchall()


def get_visit_by_date_group_client(
    db_path: str, visit_date: str, group_id: int, client_id: int
) -> Optional[Tuple[int, str]]:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            SELECT visit_id, status
            FROM visits
            WHERE visit_date = ? AND group_id = ? AND client_id = ? AND schedule_id IS NULL
            LIMIT 1
            """,
            (visit_date, group_id, client_id),
        )
        return cur.fetchone()


def upsert_visit_status(
    db_path: str,
    visit_date: str,
    group_id: int,
    client_id: int,
    status: str,
    created_by: Optional[int],
) -> None:
    existing = get_visit_by_date_group_client(db_path, visit_date, group_id, client_id)
    with sqlite3.connect(db_path) as conn:
        if existing:
            conn.execute(
                """
                UPDATE visits
                SET status = ?, created_by = ?
                WHERE visit_id = ?
                """,
                (status, created_by, existing[0]),
            )
        else:
            conn.execute(
                """
                INSERT INTO visits(visit_date, group_id, schedule_id, client_id, status, created_by)
                VALUES (?, ?, NULL, ?, ?, ?)
                """,
                (visit_date, group_id, client_id, status, created_by),
            )
        conn.commit()
