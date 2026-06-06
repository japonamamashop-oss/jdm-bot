# ============================================================
#  scheduler.py — планировщик постов каждые 3 часа
# ============================================================

import schedule
import time
import threading
from datetime import datetime
from config import POST_INTERVAL_HOURS
from generator import generate_post_with_retry
from publisher import publish_post

# Стиль канала (загружается один раз при запуске)
_channel_style = ""


def set_channel_style(style: str):
    """Устанавливает описание стиля канала."""
    global _channel_style
    _channel_style = style


def _job():
    """Задача: генерирует и публикует один пост."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*50}")
    print(f"⏰ [{now}] Запускаю генерацию поста...")

    try:
        post_data = generate_post_with_retry(_channel_style)
        if post_data:
            publish_post(post_data)
        else:
            print("❌ Не удалось сгенерировать пост")
    except Exception as e:
        print(f"❌ Критическая ошибка в задаче: {e}")


def post_now():
    """Публикует пост прямо сейчас (для тестирования)."""
    print("🚀 Публикую пост вручную...")
    _job()


def start_scheduler():
    """Запускает планировщик в фоне."""
    interval_minutes = POST_INTERVAL_HOURS * 60
    
    print(f"⏱️  Планировщик запущен: пост каждые {POST_INTERVAL_HOURS} часа(ов)")
    print(f"   Следующий пост через {POST_INTERVAL_HOURS} ч.")

    schedule.every(interval_minutes).minutes.do(_job)

    def run_loop():
        while True:
            schedule.run_pending()
            time.sleep(30)  # проверяем каждые 30 секунд

    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()
    return thread


def get_next_post_time() -> str:
    """Возвращает время следующего поста."""
    jobs = schedule.get_jobs()
    if jobs:
        next_run = jobs[0].next_run
        return next_run.strftime("%H:%M:%S")
    return "неизвестно"
