# ============================================================
#  scheduler.py — планировщик постов каждые 2 часа
#                 + ежедневная аналитика в 22:00
#                 + обновление просмотров каждые 6 часов
# ============================================================

import schedule
import time
import threading
import telebot
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, POST_INTERVAL_HOURS, DAILY_ANALYTICS_HOUR
from generator import generate_post_with_retry
from publisher import publish_post
from style_analyzer import fetch_post_views
import analytics

_channel_style = ""


def set_channel_style(style: str):
    global _channel_style
    _channel_style = style


def _post_job():
    """Генерирует и публикует один пост с учётом аналитики."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*50}")
    print(f"[{now}] Running post job...")

    try:
        hints = analytics.get_performance_hints()
        if hints:
            print(f"   Analytics: emoji~{hints.get('preferred_emoji_count','?')}, "
                  f"length~{hints.get('preferred_length','?')}, "
                  f"multi_photo={'yes' if hints.get('prefer_multi_photo') else 'no'}")

        post_data = generate_post_with_retry(_channel_style, performance_hints=hints)
        if post_data:
            publish_post(post_data)
        else:
            print("Failed to generate post")
    except Exception as e:
        print(f"Critical error in post job: {e}")


def _views_update_job():
    """Обновляет просмотры для всех отслеживаемых постов."""
    print(f"\n{'='*50}")
    print("Updating post views from channel...")
    try:
        views_map = fetch_post_views(TELEGRAM_CHANNEL_ID)
        if views_map:
            analytics.update_views_batch(views_map)
            print(f"Views updated for {len(views_map)} posts")
        else:
            print("No views data fetched")
    except Exception as e:
        print(f"Views update error: {e}")


def _analytics_job():
    """Ежедневный анализ — сначала обновляем просмотры, потом отчёт."""
    print(f"\n{'='*50}")
    print("Running daily analytics...")

    _views_update_job()

    report = analytics.get_daily_report()
    print(report)

    admin_id = analytics.get_admin_chat_id()
    if admin_id:
        try:
            bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
            bot.send_message(chat_id=admin_id, text=report, parse_mode="HTML")
            print("Analytics sent to admin")
        except Exception as e:
            print(f"Failed to send analytics: {e}")


def post_now():
    """Публикует пост прямо сейчас."""
    print("Posting now...")
    _post_job()


def start_scheduler():
    """Запускает планировщик в фоновом потоке."""
    interval_minutes = POST_INTERVAL_HOURS * 60

    print(f"Scheduler started: post every {POST_INTERVAL_HOURS}h.")
    print(f"   Daily analytics at {DAILY_ANALYTICS_HOUR}:00")
    print(f"   Views update every 6h.")

    schedule.every(interval_minutes).minutes.do(_post_job)
    schedule.every().day.at(f"{DAILY_ANALYTICS_HOUR:02d}:00").do(_analytics_job)
    schedule.every(6).hours.do(_views_update_job)

    def run_loop():
        while True:
            schedule.run_pending()
            time.sleep(30)

    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()
    return thread


def get_next_post_time() -> str:
    """Возвращает время следующего поста."""
    jobs = [j for j in schedule.get_jobs() if hasattr(j, 'next_run') and j.next_run]
    if jobs:
        next_run = min(j.next_run for j in jobs)
        return next_run.strftime("%H:%M:%S")
    return "unknown"
