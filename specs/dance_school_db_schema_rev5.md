# MVP БД для школы танцев (SQLite)
??????: 2026-02-04 (rev5: **trainers** + **schedule**)

Ключевые решения MVP:
- Канал: **только Telegram**
- Дубликаты клиентов по телефону: **запрещены**
- Типы посещений: **месячный абонемент (постоянно)** и **разовое**
- **Месячный абонемент**: строго на 1 группу, **без лимита занятий**, учёт **по датам** (`start_date/end_date`), списаний нет  
  - если оформляем не с 1-го числа: `start_date = дата оформления/принятия оплаты`, `end_date = последний день текущего месяца`
- Оплаты: `cash / transfer / qr / defer(отсрочка)`
  - **Абонементную оплату без оформленного `passes` не принимаем**
  - **Отсрочка** = обязательство, НЕ попадает в выручку/прибыль до закрытия
  - **Закрытие отсрочки**: `status: deferred → paid`, `method: defer → cash|transfer|qr`, `pay_date = дата фактической оплаты`
- Заморозка абонемента: **не реализуем**
- Расходы: категории управляются из бота (`is_active`)
- Отчёты: контроль **«разовые без оплаты»** + **отсрочки/просроченные отсрочки**
- Директор = **owner** (главный админ): задаётся через ENV (TG ID), управляет админами

- Trainers: separate entity; groups.trainer_id syncs trainer_name.

---

## Статусы/правила (коротко)
### visits.status
- `booked` / `attended` / `noshow` / `cancelled`

### payments.purpose
- `pass` — оплата абонемента (обязателен `pass_id`, обязателен `group_id`)
- `single` — разовое (обязателен `group_id`, `pass_id` = NULL, **visit_id обязателен в MVP**)
- `other` — прочее (на будущее)

### payments.method + payments.status
- method: `cash | transfer | qr | defer`
- status: `paid | deferred | cancelled`
- выручка/прибыль считаются **только по status='paid'**

---

## Trainer sync rules
- On assign: UPDATE groups SET trainer_id=?, trainer_name=?
- On clear: UPDATE groups SET trainer_id=NULL, trainer_name=NULL
- On rename: UPDATE groups SET trainer_name=new_name WHERE trainer_id=...

## DDL (SQLite)

```sql
PRAGMA foreign_keys = ON;

-- ========= reference tables =========
CREATE TABLE IF NOT EXISTS groups (
  group_id     INTEGER PRIMARY KEY AUTOINCREMENT,
  name         TEXT NOT NULL,
  trainer_name TEXT,
  trainer_id   INTEGER,
  capacity     INTEGER NOT NULL DEFAULT 0 CHECK (capacity >= 0),
  room_name    TEXT,
  is_active    INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1))
);


CREATE TABLE IF NOT EXISTS trainers (
  trainer_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  full_name    TEXT NOT NULL,
  phone        TEXT,
  tg_user_id   INTEGER,
  tg_username  TEXT,
  is_active    INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
  created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS ix_trainers_active ON trainers(is_active);
CREATE UNIQUE INDEX IF NOT EXISTS ux_trainers_tg_user_id ON trainers(tg_user_id);

CREATE TABLE IF NOT EXISTS schedule (
  schedule_id  INTEGER PRIMARY KEY AUTOINCREMENT,
  group_id     INTEGER NOT NULL REFERENCES groups(group_id) ON DELETE CASCADE,
  day_of_week  INTEGER NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
  time_hhmm    TEXT NOT NULL,               -- "18:30"
  duration_min INTEGER NOT NULL CHECK (duration_min > 0),
  room_name    TEXT,
  valid_from   TEXT,
  valid_to     TEXT,
  is_active    INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
  created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS ix_schedule_group_weekday
  ON schedule(group_id, day_of_week);

CREATE UNIQUE INDEX IF NOT EXISTS ux_schedule_unique_slot
  ON schedule(group_id, day_of_week, time_hhmm);

-- ========= clients =========
CREATE TABLE IF NOT EXISTS clients (
  client_id    INTEGER PRIMARY KEY AUTOINCREMENT,
  full_name    TEXT NOT NULL,
  phone        TEXT NOT NULL,
  tg_user_id   INTEGER,                     -- stable Telegram id (если известен)
  tg_username  TEXT,                        -- @username (если известен)
  birth_date   TEXT,                        -- ISO "YYYY-MM-DD"
  comment      TEXT,
  created_at   TEXT NOT NULL DEFAULT (datetime('now')),
  status       TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive'))
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_clients_phone ON clients(phone);
CREATE INDEX IF NOT EXISTS ix_clients_tg_user_id ON clients(tg_user_id);
CREATE INDEX IF NOT EXISTS ix_clients_tg_username ON clients(tg_username);

-- client membership in groups (many-to-many)
CREATE TABLE IF NOT EXISTS client_groups (
  client_id   INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
  group_id    INTEGER NOT NULL REFERENCES groups(group_id) ON DELETE CASCADE,
  status      TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive')),
  since_date  TEXT NOT NULL DEFAULT (date('now')),
  until_date  TEXT,
  PRIMARY KEY (client_id, group_id)
);

-- ========= passes (месячные абонементы по датам, строго на 1 группу) =========
CREATE TABLE IF NOT EXISTS passes (
  pass_id     INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id   INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
  group_id    INTEGER NOT NULL REFERENCES groups(group_id) ON DELETE CASCADE,
  pass_type   TEXT NOT NULL DEFAULT 'monthly', -- MVP: monthly
  start_date  TEXT NOT NULL,                   -- "YYYY-MM-DD"
  end_date    TEXT NOT NULL,                   -- "YYYY-MM-DD"
  is_active   INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
  price       INTEGER,                         -- опционально (рубли)
  comment     TEXT,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS ix_passes_client_group
  ON passes(client_id, group_id, is_active);

-- Одновременно 1 активный абонемент на клиента+группу
CREATE UNIQUE INDEX IF NOT EXISTS ux_passes_one_active_per_group
  ON passes(client_id, group_id)
  WHERE is_active = 1;

-- ========= visits (разовые записи + факт посещения) =========
CREATE TABLE IF NOT EXISTS visits (
  visit_id     INTEGER PRIMARY KEY AUTOINCREMENT,
  visit_date   TEXT NOT NULL,   -- "YYYY-MM-DD"
  group_id     INTEGER NOT NULL REFERENCES groups(group_id),
  schedule_id  INTEGER REFERENCES schedule(schedule_id),
  client_id    INTEGER NOT NULL REFERENCES clients(client_id),
  status       TEXT NOT NULL CHECK (status IN ('booked','attended','noshow','cancelled')),
  created_by   INTEGER,         -- tg_user_id/admin id
  created_at   TEXT NOT NULL DEFAULT (datetime('now')),
  comment      TEXT
);

-- prevent duplicates: one client per group per date per schedule slot
CREATE UNIQUE INDEX IF NOT EXISTS ux_visits_unique
  ON visits(visit_date, group_id, schedule_id, client_id);

CREATE INDEX IF NOT EXISTS ix_visits_date_group ON visits(visit_date, group_id);

-- ========= payments =========
-- Важно:
-- - выручка считается ТОЛЬКО по status='paid'
-- - отсрочка: method='defer' + status='deferred' (+ due_date опц.)
-- - закрытие отсрочки: UPDATE -> status='paid', method=cash|transfer|qr, pay_date=дата фактической оплаты
CREATE TABLE IF NOT EXISTS payments (
  pay_id       INTEGER PRIMARY KEY AUTOINCREMENT,
  pay_date     TEXT NOT NULL DEFAULT (date('now')), -- дата фактической оплаты (для deferred обновляется при закрытии)
  client_id    INTEGER REFERENCES clients(client_id),
  group_id     INTEGER REFERENCES groups(group_id),
  pass_id      INTEGER REFERENCES passes(pass_id),
  visit_id     INTEGER REFERENCES visits(visit_id),
  amount       INTEGER NOT NULL CHECK (amount > 0),
  method       TEXT NOT NULL CHECK (method IN ('cash','transfer','qr','defer')),
  status       TEXT NOT NULL DEFAULT 'paid' CHECK (status IN ('paid','deferred','cancelled')),
  purpose      TEXT NOT NULL CHECK (purpose IN ('pass','single','other')),
  due_date     TEXT,            -- для отсрочки (опционально, YYYY-MM-DD)
  accepted_by  INTEGER,         -- tg_user_id/admin id
  comment      TEXT,
  created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS ix_payments_date ON payments(pay_date);
CREATE INDEX IF NOT EXISTS ix_payments_client ON payments(client_id);
CREATE INDEX IF NOT EXISTS ix_payments_group ON payments(group_id);
CREATE INDEX IF NOT EXISTS ix_payments_visit ON payments(visit_id);
CREATE INDEX IF NOT EXISTS ix_payments_status_due ON payments(status, due_date);

-- ========= expenses =========
CREATE TABLE IF NOT EXISTS expense_categories (
  category_id INTEGER PRIMARY KEY AUTOINCREMENT,
  code        TEXT NOT NULL UNIQUE,
  name        TEXT NOT NULL,
  is_active   INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1))
);

CREATE INDEX IF NOT EXISTS ix_expense_categories_active ON expense_categories(is_active);

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

CREATE INDEX IF NOT EXISTS ix_expenses_date ON expenses(exp_date);

-- ========= admins (owner/admin) =========
CREATE TABLE IF NOT EXISTS admins (
  admin_id     INTEGER PRIMARY KEY AUTOINCREMENT,
  full_name    TEXT NOT NULL,
  role         TEXT NOT NULL CHECK (role IN ('owner','admin')),
  tg_user_id   INTEGER,        -- Telegram ID (обязательно для доступа)
  tg_username  TEXT,
  is_active    INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
  created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_admins_tg_user_id ON admins(tg_user_id);
CREATE INDEX IF NOT EXISTS ix_admins_role_active ON admins(role, is_active);

-- ========= ops log (optional) =========
CREATE TABLE IF NOT EXISTS ops_log (
  op_id        INTEGER PRIMARY KEY AUTOINCREMENT,
  ts           TEXT NOT NULL DEFAULT (datetime('now')),
  actor_id     INTEGER,
  action       TEXT NOT NULL,
  entity_type  TEXT NOT NULL,
  entity_id    INTEGER,
  before_json  TEXT,
  after_json   TEXT
);

CREATE INDEX IF NOT EXISTS ix_ops_log_ts ON ops_log(ts);
```

---

## Seed: категории расходов (пример)
```sql
INSERT INTO expense_categories(code, name, is_active) VALUES
 ('salary','Зарплата',1),
 ('utilities','Коммуналка',1),
 ('taxes','Налоги',1),
 ('rent','Аренда',1),
 ('supplies','Хоз. расходы',1),
 ('marketing','Маркетинг',1),
 ('other','Прочее',1);
```

## Seed: owner (директор)
```sql
-- tg_user_id подставляется из ENV OWNER_TG_USER_ID в seed.py
INSERT INTO admins(full_name, role, tg_user_id, tg_username, is_active)
VALUES ('Евдокимов Игорь Александрович', 'owner', NULL, NULL, 1);
```