# TECH_MVP_FOR_CODEX.md
Дата: 2026-02-01  
Проект: MVP система учета школы танцев — Telegram админ-бот + SQLite + отчёты/Excel

Этот файл — **единое техническое ТЗ** для вайбкодинга (Codex/LLM).
Он включает: PROMPT + методы + правила + чек-лист готовности.

---

## SOURCE OF TRUTH
1) `specs/dance_school_db_schema_rev4.md` — схема БД (defer + owner/admin)  
2) `specs/dance_school_admin_bot_mvp_rev2.md` — бизнес/UI (кнопки/потоки/отчёты)  
3) `specs/TECH_MVP_FOR_CODEX.md` — этот документ

---

## MUST правила
- Telegram only.
- 2 типа посещений: monthly(pass) и single.
- Monthly pass: 1 группа, unlimited, date-based (start/end), календарный месяц.
- Payments: cash/transfer/qr/defer.
  - Deferred: method=defer, status=deferred, due_date optional.
  - Closing deferred: status->paid, method->cash/transfer/qr, pay_date=actual date.
  - Revenue/profit counts ONLY status='paid'.
- No pass freeze.
- No duplicates by phone.
- Owner/admin roles:
  - owner tg_user_id задаётся через ENV OWNER_TG_USER_ID.
  - owner видит кнопку 👑 Админы и управляет admin users (add/disable/list).
- “Single without payment” report is mandatory (visits LEFT JOIN payments by visit_id).
- Reports must include Deferred + Deferred_Overdue.
- Excel to owner by admin request; default period: this month.

---

## ENV
- BOT_TOKEN
- DB_PATH
- OWNER_TG_USER_ID
- (optional) SEED_FIRST_ADMIN_TG_USER_ID

---

## Admin auth
- Middleware: allow only tg_user_id in admins where is_active=1.
- /start: shows user tg_user_id; if allowed → menu, else “access denied”.

---

## Owner menu 👑 Admins
- Add admin: tg_user_id + name → upsert admins(role='admin', is_active=1)
- Disable admin: select active admin (not owner) → set is_active=0
- List admins: owner + active + inactive

---

## PROMPT (вставлять целиком)
```text
ROLE: senior backend engineer.
Build MVP Telegram admin bot for dance school.

SOURCES OF TRUTH:
1) specs/dance_school_db_schema_rev4.md
2) specs/dance_school_admin_bot_mvp_rev2.md
3) specs/TECH_MVP_FOR_CODEX.md

STACK:
Python 3.11+, aiogram v3, SQLite, openpyxl.

MUST:
- Telegram only.
- Roles: owner/admin, owner tg_user_id from ENV OWNER_TG_USER_ID.
- Owner has 👑 Admins menu: add/disable/list admins.
- Two visit types: monthly(pass) and single.
- Monthly pass: one group, unlimited, date-based; calendar month; if mid-month: start=today end=last day.
- Payments: cash/transfer/qr/defer.
  - Deferred: method=defer status=deferred due_date optional.
  - Closing deferred: status->paid, method->cash/transfer/qr, pay_date=actual date.
  - Revenue/profit counts ONLY status='paid'.
- No pass freeze.
- No duplicates by phone.
- Single payments MUST have visit_id; create booked visit if absent.
- Reports include Singles_NoPayment + Deferred + Deferred_Overdue.
- Excel to owner by admin request; default period: this month.

DELIVER:
- bot handlers with FSM
- DB repo layer with required methods
- reports + excel generation
- seed: owner + expense categories
```
