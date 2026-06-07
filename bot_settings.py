# ============================================================
#  bot_settings.py — персистентные настройки бота
# ============================================================

import json
import os

SETTINGS_FILE = "bot_settings.json"

_defaults = {
    "posts_per_day": 1,
    "photos_per_post": 1,
    "is_posting": True,
    "admin_chat_id": None,
}


def load() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, encoding="utf-8") as f:
                data = json.load(f)
                return {**_defaults, **data}
        except Exception:
            pass
    return dict(_defaults)


def save(settings: dict):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def get(key: str, default=None):
    return load().get(key, _defaults.get(key, default))


def set_value(key: str, value):
    s = load()
    s[key] = value
    save(s)
