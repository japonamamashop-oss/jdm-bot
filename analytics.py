# ============================================================
#  analytics.py — аналитика постов: трекинг реакций и просмотров
# ============================================================

import json
import os
import re
from datetime import datetime, date

POSTS_LOG = "posts_log.json"
_admin_chat_id = None


def set_admin_chat_id(chat_id: int):
    global _admin_chat_id
    _admin_chat_id = chat_id


def get_admin_chat_id():
    return _admin_chat_id


def count_emojis(text: str) -> int:
    emoji_pattern = re.compile(
        "[\\U0001F600-\\U0001F64F"
        "\\U0001F300-\\U0001F5FF"
        "\\U0001F680-\\U0001F6FF"
        "\\U0001F1E0-\\U0001F1FF"
        "\\U00002702-\\U000027B0"
        "\\U000024C2-\\U0001F251]+",
        flags=re.UNICODE
    )
    return len(emoji_pattern.findall(text))


def save_post(car: str, message_ids: list, text: str, photo_count: int = 1):
    """Сохраняет информацию о новом посте."""
    log = _load()
    log.append({
        "car": car,
        "message_ids": message_ids if isinstance(message_ids, list) else [message_ids],
        "timestamp": datetime.now().isoformat(),
        "date": date.today().isoformat(),
        "features": {
            "length": len(text),
            "emoji_count": count_emojis(text),
            "line_count": text.count('\n'),
            "hashtag_count": text.count('#'),
            "photo_count": photo_count,
        },
        "reactions": 0,
        "views": 0,
    })
    _save(log)


def add_reactions(message_id: int, count: int):
    """Обновляет счётчик реакций для поста по message_id."""
    log = _load()
    updated = False
    for post in log:
        if message_id in post.get("message_ids", []):
            post["reactions"] = max(post.get("reactions", 0), count)
            updated = True
            break
    if updated:
        _save(log)


def update_views(message_id: int, views: int):
    """Обновляет счётчик просмотров для поста по message_id."""
    log = _load()
    updated = False
    for post in log:
        if message_id in post.get("message_ids", []):
            post["views"] = max(post.get("views", 0), views)
            updated = True
            break
    if updated:
        _save(log)


def update_views_batch(views_map: dict):
    """Обновляет просмотры для нескольких постов сразу. views_map = {message_id: views}"""
    log = _load()
    changed = False
    for post in log:
        for msg_id in post.get("message_ids", []):
            if msg_id in views_map:
                new_views = views_map[msg_id]
                if new_views > post.get("views", 0):
                    post["views"] = new_views
                    changed = True
    if changed:
        _save(log)


def _engagement_score(post: dict) -> float:
    """Комбинированный скор: реакции + просмотры (взвешенно)."""
    reactions = post.get("reactions", 0)
    views = post.get("views", 0)
    return reactions * 10 + views * 0.1


def get_performance_hints() -> dict:
    """Возвращает подсказки стиля на основе топ постов по реакциям и просмотрам."""
    log = _load()
    with_data = [p for p in log if p.get("reactions", 0) > 0 or p.get("views", 0) > 0]
    if len(with_data) < 3:
        return {}

    top = sorted(with_data, key=_engagement_score, reverse=True)[:5]

    avg_emoji = sum(p["features"].get("emoji_count", 0) for p in top) / len(top)
    avg_length = sum(p["features"].get("length", 0) for p in top) / len(top)
    avg_photos = sum(p["features"].get("photo_count", 1) for p in top) / len(top)
    avg_lines = sum(p["features"].get("line_count", 0) for p in top) / len(top)

    return {
        "preferred_emoji_count": round(avg_emoji),
        "preferred_length": round(avg_length),
        "prefer_multi_photo": avg_photos > 1.3,
        "preferred_line_count": round(avg_lines),
    }


def get_daily_report() -> str:
    """Генерирует текстовый отчёт за сегодня с реакциями и просмотрами."""
    log = _load()
    today = date.today().isoformat()
    today_posts = [p for p in log if p.get("date") == today]

    if not today_posts:
        return "📊 Сегодня постов ещё не было."

    sorted_posts = sorted(today_posts, key=_engagement_score, reverse=True)
    best = sorted_posts[0]
    total_reactions = sum(p.get("reactions", 0) for p in today_posts)
    total_views = sum(p.get("views", 0) for p in today_posts)

    medals = ["🥇", "🥈", "🥉"]
    lines2 = [
        f"📊 <b>Аналитика за {today}</b>",
        "",
        f"📝 Постов: <b>{len(today_posts)}</b>",
        f"👁 Просмотров всего: <b>{total_views}</b>",
        f"🔥 Реакций всего: <b>{total_reactions}</b>",
        f"🏆 Лучший: <b>{best['car']}</b> — {best.get('reactions', 0)} реакц. / {best.get('views', 0)} просм.",
        "",
        "<b>Все посты:</b>",
    ]
    for i, p in enumerate(sorted_posts):
        medal = medals[i] if i < 3 else f"{i+1}."
        lines2.append(
            f"{medal} {p['car']}: "
            f"👁{p.get('views', 0)} | "
            f"🔥{p.get('reactions', 0)} | "
            f"{p['features'].get('emoji_count', 0)} эмодзи | "
            f"{p['features'].get('photo_count', 1)} фото"
        )

    hints = get_performance_hints()
    if hints:
        lines2 += [
            "",
            "💡 <b>Что нравится подписчикам:</b>",
            f"• Эмодзи: ~{hints.get('preferred_emoji_count', '?')} шт.",
            f"• Длина текста: ~{hints.get('preferred_length', '?')} симв.",
            f"• Несколько фото: {'✅' if hints.get('prefer_multi_photo') else '❌'}",
            "",
            "🤖 Следующие посты адаптируются автоматически.",
        ]

    return "\n".join(lines2)


def get_all_tracked_message_ids() -> list:
    """Возвращает все message_id из лога за последние 50 постов."""
    log = _load()
    result = []
    for post in log[-50:]:
        result.extend(post.get("message_ids", []))
    return result


def _load() -> list:
    if os.path.exists(POSTS_LOG):
        try:
            with open(POSTS_LOG, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save(log: list):
    with open(POSTS_LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
