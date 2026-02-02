# Telegram Admin Bot (MVP)

## Быстрый запуск
1) Создайте и активируйте виртуальное окружение:
   - Windows PowerShell:
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - macOS/Linux:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

2) Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

3) Заполните `.env` (можно скопировать из `.env.example`):
   - `BOT_TOKEN`
   - `OWNER_TG_USER_ID`
   - `DB_PATH`
   - `TZ`

4) Запустите бота:
   ```bash
   python app/src/main.py
   ```
