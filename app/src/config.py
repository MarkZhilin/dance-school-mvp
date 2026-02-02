from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import find_dotenv, load_dotenv


@dataclass(frozen=True)
class Config:
    bot_token: str
    owner_tg_user_id: int
    db_path: str
    tz: str


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def load_env() -> Config:
    dotenv_path = find_dotenv(usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path)
    else:
        load_dotenv()

    bot_token = _require_env("BOT_TOKEN")
    owner_tg_user_id_raw = _require_env("OWNER_TG_USER_ID")
    db_path = _require_env("DB_PATH")
    tz = _require_env("TZ")

    try:
        owner_tg_user_id = int(owner_tg_user_id_raw)
    except ValueError as exc:
        raise RuntimeError("OWNER_TG_USER_ID must be an integer") from exc

    return Config(
        bot_token=bot_token,
        owner_tg_user_id=owner_tg_user_id,
        db_path=db_path,
        tz=tz,
    )
