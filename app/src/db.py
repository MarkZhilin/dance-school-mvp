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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS passes (
              pass_id     INTEGER PRIMARY KEY AUTOINCREMENT,
              client_id   INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
              group_id    INTEGER NOT NULL REFERENCES groups(group_id) ON DELETE CASCADE,
              pass_type   TEXT NOT NULL DEFAULT 'monthly',
              start_date  TEXT NOT NULL,
              end_date    TEXT NOT NULL,
              is_active   INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
              price       INTEGER,
              comment     TEXT,
              created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS ix_passes_client_group
              ON passes(client_id, group_id, is_active);
            """
        )
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_passes_one_active_per_group
              ON passes(client_id, group_id)
              WHERE is_active = 1;
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS payments (
              pay_id       INTEGER PRIMARY KEY AUTOINCREMENT,
              pay_date     TEXT NOT NULL DEFAULT (date('now')),
              client_id    INTEGER REFERENCES clients(client_id),
              group_id     INTEGER REFERENCES groups(group_id),
              pass_id      INTEGER REFERENCES passes(pass_id),
              visit_id     INTEGER REFERENCES visits(visit_id),
              amount       INTEGER NOT NULL CHECK (amount > 0),
              method       TEXT NOT NULL CHECK (method IN ('cash','transfer','qr','defer')),
              status       TEXT NOT NULL DEFAULT 'paid' CHECK (status IN ('paid','deferred','cancelled')),
              purpose      TEXT NOT NULL CHECK (purpose IN ('pass','single','other')),
              due_date     TEXT,
              accepted_by  INTEGER,
              comment      TEXT,
              created_at   TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS ix_payments_date ON payments(pay_date);")
        conn.execute("CREATE INDEX IF NOT EXISTS ix_payments_client ON payments(client_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS ix_payments_group ON payments(group_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS ix_payments_visit ON payments(visit_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS ix_payments_status_due ON payments(status, due_date);")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS expense_categories (
              category_id INTEGER PRIMARY KEY AUTOINCREMENT,
              code        TEXT NOT NULL UNIQUE,
              name        TEXT NOT NULL,
              is_active   INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1))
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS ix_expense_categories_active ON expense_categories(is_active);")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
              expense_id   INTEGER PRIMARY KEY AUTOINCREMENT,
              exp_date     TEXT NOT NULL DEFAULT (date('now')),
              category_id  INTEGER NOT NULL REFERENCES expense_categories(category_id),
              amount       INTEGER NOT NULL CHECK (amount > 0),
              method       TEXT NOT NULL CHECK (method IN ('cash','transfer','qr')),
              comment      TEXT,
              created_by   INTEGER,
              created_at   TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS ix_expenses_date ON expenses(exp_date);")
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


def get_active_pass(
    db_path: str, client_id: int, group_id: int, on_date: Optional[str] = None
) -> Optional[Tuple[int, str, str, int, Optional[int], Optional[str]]]:
    with sqlite3.connect(db_path) as conn:
        if on_date:
            cur = conn.execute(
                """
                SELECT pass_id, start_date, end_date, is_active, price, comment
                FROM passes
                WHERE client_id = ? AND group_id = ? AND is_active = 1
                  AND start_date <= ? AND end_date >= ?
                LIMIT 1
                """,
                (client_id, group_id, on_date, on_date),
            )
        else:
            cur = conn.execute(
                """
                SELECT pass_id, start_date, end_date, is_active, price, comment
                FROM passes
                WHERE client_id = ? AND group_id = ? AND is_active = 1
                LIMIT 1
                """,
                (client_id, group_id),
            )
        return cur.fetchone()


def create_pass(
    db_path: str,
    client_id: int,
    group_id: int,
    start_date: str,
    end_date: str,
    is_active: int,
    price: Optional[int] = None,
    comment: Optional[str] = None,
) -> int:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO passes(client_id, group_id, start_date, end_date, is_active, price, comment)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (client_id, group_id, start_date, end_date, is_active, price, comment),
        )
        conn.commit()
        return int(cur.lastrowid)


def get_pass_by_id(db_path: str, pass_id: int) -> Optional[Tuple]:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "SELECT * FROM passes WHERE pass_id = ? LIMIT 1",
            (pass_id,),
        )
        return cur.fetchone()


def get_group_by_id(db_path: str, group_id: int) -> Optional[Tuple[int, str]]:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "SELECT group_id, name FROM groups WHERE group_id = ? LIMIT 1",
            (group_id,),
        )
        return cur.fetchone()


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


def get_or_create_single_visit(
    db_path: str, client_id: int, group_id: int, visit_date: str, created_by: Optional[int]
) -> int:
    existing = get_visit_by_date_group_client(db_path, visit_date, group_id, client_id)
    if existing:
        return int(existing[0])
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO visits(visit_date, group_id, schedule_id, client_id, status, created_by)
            VALUES (?, ?, NULL, ?, 'booked', ?)
            """,
            (visit_date, group_id, client_id, created_by),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_active_passes(
    db_path: str, client_id: int, group_id: int, on_date: Optional[str] = None
) -> List[Tuple[int, str, str, Optional[int], Optional[str]]]:
    with sqlite3.connect(db_path) as conn:
        if on_date:
            cur = conn.execute(
                """
                SELECT pass_id, start_date, end_date, price, comment
                FROM passes
                WHERE client_id = ? AND group_id = ? AND is_active = 1
                  AND start_date <= ? AND end_date >= ?
                ORDER BY start_date DESC
                """,
                (client_id, group_id, on_date, on_date),
            )
        else:
            cur = conn.execute(
                """
                SELECT pass_id, start_date, end_date, price, comment
                FROM passes
                WHERE client_id = ? AND group_id = ? AND is_active = 1
                ORDER BY start_date DESC
                """,
                (client_id, group_id),
            )
        return cur.fetchall()


def create_payment_single(
    db_path: str,
    client_id: int,
    group_id: int,
    visit_id: int,
    amount: int,
    method: str,
    status: str,
    due_date: Optional[str],
    accepted_by: Optional[int],
    comment: Optional[str] = None,
) -> int:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO payments(
              client_id, group_id, visit_id, amount, method, status, purpose,
              due_date, accepted_by, comment
            )
            VALUES (?, ?, ?, ?, ?, ?, 'single', ?, ?, ?)
            """,
            (client_id, group_id, visit_id, amount, method, status, due_date, accepted_by, comment),
        )
        conn.commit()
        return int(cur.lastrowid)


def create_payment_pass(
    db_path: str,
    client_id: int,
    group_id: int,
    pass_id: int,
    amount: int,
    method: str,
    status: str,
    due_date: Optional[str],
    accepted_by: Optional[int],
    comment: Optional[str] = None,
) -> int:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO payments(
              client_id, group_id, pass_id, amount, method, status, purpose,
              due_date, accepted_by, comment
            )
            VALUES (?, ?, ?, ?, ?, ?, 'pass', ?, ?, ?)
            """,
            (client_id, group_id, pass_id, amount, method, status, due_date, accepted_by, comment),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_deferred_payments_by_client(
    db_path: str, client_id: int
) -> List[Tuple[int, int, str, Optional[int], Optional[str], Optional[str], str]]:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            SELECT p.pay_id, p.amount, p.purpose, p.group_id, g.name, p.due_date, p.created_at
            FROM payments p
            LEFT JOIN groups g ON g.group_id = p.group_id
            WHERE p.client_id = ? AND p.status = 'deferred' AND p.method = 'defer'
            ORDER BY p.created_at DESC
            """,
            (client_id,),
        )
        return cur.fetchall()


def get_payment_by_id(db_path: str, pay_id: int) -> Optional[Tuple]:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "SELECT * FROM payments WHERE pay_id = ? LIMIT 1",
            (pay_id,),
        )
        return cur.fetchone()


def close_deferred_payment(
    db_path: str, pay_id: int, new_method: str, pay_date: str, accepted_by: Optional[int]
) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            UPDATE payments
            SET status = 'paid', method = ?, pay_date = ?, accepted_by = ?
            WHERE pay_id = ?
            """,
            (new_method, pay_date, accepted_by, pay_id),
        )
        conn.commit()


def get_defer_summary(
    db_path: str, client_id: int, today: str
) -> Tuple[int, int, Optional[str], int]:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            SELECT
              COUNT(*) AS cnt,
              COALESCE(SUM(amount), 0) AS total_amount,
              MIN(due_date) AS nearest_due,
              COALESCE(SUM(CASE WHEN due_date IS NOT NULL AND date(due_date) < date(?) THEN 1 ELSE 0 END), 0) AS overdue_cnt
            FROM payments
            WHERE client_id = ? AND method = 'defer' AND status = 'deferred'
            """,
            (today, client_id),
        )
        row = cur.fetchone()
    if not row:
        return 0, 0, None, 0
    return int(row[0] or 0), int(row[1] or 0), row[2], int(row[3] or 0)


def list_expense_categories(db_path: str, include_inactive: bool) -> List[Tuple[int, str, int]]:
    with sqlite3.connect(db_path) as conn:
        if include_inactive:
            cur = conn.execute(
                """
                SELECT category_id, name, is_active
                FROM expense_categories
                ORDER BY name COLLATE NOCASE
                """
            )
        else:
            cur = conn.execute(
                """
                SELECT category_id, name, is_active
                FROM expense_categories
                WHERE is_active = 1
                ORDER BY name COLLATE NOCASE
                """
            )
        return cur.fetchall()


def _normalize_category_code(name: str) -> str:
    base = "".join(ch.lower() if ch.isalnum() else "_" for ch in name.strip())
    base = base.strip("_") or "category"
    while "__" in base:
        base = base.replace("__", "_")
    return base


def _ensure_unique_category_code(db_path: str, base: str) -> str:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("SELECT code FROM expense_categories WHERE code LIKE ?", (f"{base}%",))
        existing = {row[0] for row in cur.fetchall()}
    if base not in existing:
        return base
    index = 2
    while f"{base}_{index}" in existing:
        index += 1
    return f"{base}_{index}"


def create_expense_category(db_path: str, name: str) -> int:
    code = _ensure_unique_category_code(db_path, _normalize_category_code(name))
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO expense_categories(code, name, is_active) VALUES (?, ?, 1)",
            (code, name),
        )
        conn.commit()
        return int(cur.lastrowid)


def rename_expense_category(db_path: str, category_id: int, new_name: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE expense_categories SET name = ? WHERE category_id = ?",
            (new_name, category_id),
        )
        conn.commit()


def set_expense_category_active(db_path: str, category_id: int, is_active: bool) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE expense_categories SET is_active = ? WHERE category_id = ?",
            (1 if is_active else 0, category_id),
        )
        conn.commit()


def create_expense(
    db_path: str,
    exp_date: str,
    category_id: int,
    amount: int,
    method: str,
    comment: Optional[str],
    created_by: Optional[int],
) -> int:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO expenses(exp_date, category_id, amount, method, comment, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (exp_date, category_id, amount, method, comment, created_by),
        )
        conn.commit()
        return int(cur.lastrowid)


def get_last_expense(db_path: str, created_by: int) -> Optional[Tuple[int, str, int, int, str, Optional[str]]]:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            SELECT expense_id, exp_date, category_id, amount, method, comment
            FROM expenses
            WHERE created_by = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (created_by,),
        )
        return cur.fetchone()


def list_expenses(
    db_path: str, date_from: str, date_to: str, category_id: Optional[int] = None, limit: int = 100
) -> List[Tuple[int, str, int, str, int, str, Optional[str]]]:
    with sqlite3.connect(db_path) as conn:
        if category_id is None:
            cur = conn.execute(
                """
                SELECT e.expense_id, e.exp_date, e.category_id, c.name, e.amount, e.method, e.comment
                FROM expenses e
                JOIN expense_categories c ON c.category_id = e.category_id
                WHERE e.exp_date BETWEEN ? AND ?
                ORDER BY e.exp_date DESC, e.expense_id DESC
                LIMIT ?
                """,
                (date_from, date_to, limit),
            )
        else:
            cur = conn.execute(
                """
                SELECT e.expense_id, e.exp_date, e.category_id, c.name, e.amount, e.method, e.comment
                FROM expenses e
                JOIN expense_categories c ON c.category_id = e.category_id
                WHERE e.exp_date BETWEEN ? AND ? AND e.category_id = ?
                ORDER BY e.exp_date DESC, e.expense_id DESC
                LIMIT ?
                """,
                (date_from, date_to, category_id, limit),
            )
        return cur.fetchall()


def get_expense_by_id(
    db_path: str, expense_id: int
) -> Optional[Tuple[int, str, int, str, int, str, Optional[str]]]:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            SELECT e.expense_id, e.exp_date, e.category_id, c.name, e.amount, e.method, e.comment
            FROM expenses e
            JOIN expense_categories c ON c.category_id = e.category_id
            WHERE e.expense_id = ?
            LIMIT 1
            """,
            (expense_id,),
        )
        return cur.fetchone()


def update_expense(
    db_path: str,
    expense_id: int,
    exp_date: Optional[str] = None,
    category_id: Optional[int] = None,
    amount: Optional[int] = None,
    method: Optional[str] = None,
    comment: Optional[str] = None,
) -> None:
    fields = []
    values: list = []
    if exp_date is not None:
        fields.append("exp_date = ?")
        values.append(exp_date)
    if category_id is not None:
        fields.append("category_id = ?")
        values.append(category_id)
    if amount is not None:
        fields.append("amount = ?")
        values.append(amount)
    if method is not None:
        fields.append("method = ?")
        values.append(method)
    if comment is not None:
        fields.append("comment = ?")
        values.append(comment)
    if not fields:
        return
    values.append(expense_id)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            f"UPDATE expenses SET {', '.join(fields)} WHERE expense_id = ?",
            tuple(values),
        )
        conn.commit()


def delete_expense(db_path: str, expense_id: int) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM expenses WHERE expense_id = ?", (expense_id,))
        conn.commit()
