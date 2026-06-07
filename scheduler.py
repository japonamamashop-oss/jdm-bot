# ============================================================
#  scheduler.py — динамический планировщик постов
#                 1 пост в день по умолчанию,
#                 кол-во настраивается через бот
# ============================================================

import threading
import time
import telebot
from datetime import datetime, date
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, DAILY_ANALYTICS_HOUR
from generator import generate_post_with_retry
from publisher import publish_post
from style_analyzer import fetch_post_views
import analytics
import bot_settings

_channel_style = ''
_stop_event = threading.Event()
_thread = None


def set_channel_style(style: str):
    global _channel_style
    _channel_style = style


def _calculate_post_times(posts_per_day: int) -> list:
    if posts_per_day <= 0:
        return []
    start_min = 8 * 60
    end_min = 22 * 60
    span = end_min - start_min
    if posts_per_day == 1:
        mid = start_min + span // 2
        return [(mid // 60, mid % 60)]
    interval = span // (posts_per_day - 1)
    times = []
    for i in range(posts_per_day):
        total = start_min + i * interval
        times.append((total // 60, total % 60))
    return times


def get_schedule_info() -> str:
    settings = bot_settings.load()
    posts_per_day = settings.get('posts_per_day', 1)
    post_times = _calculate_post_times(posts_per_day)
    is_posting = settings.get('is_posting', True)
    photos = settings.get('photos_per_post', 1)
    status = '✅ Активен' if is_posting else '⏸ Пауза'
    times_str = ', '.join(f'{h:02d}:{m:02d}' for h, m in post_times) or '—'
    return (
        f'📋 <b>Расписание бота</b>\n\n'
        f'Статус: {status}\n'
        f'Постов в день: <b>{posts_per_day}</b>\n'
        f'Время постов: <b>{times_str}</b>\n'
        f'Фото в посте: <b>{photos}</b>\n'
        f'Аналитика: <b>{DAILY_ANALYTICS_HOUR}:00</b>'
    )


def _post_job():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'\n{"="*50}')
    print(f'[{now}] Running post job...')
    try:
        hints = analytics.get_performance_hints()
        settings = bot_settings.load()
        photos = settings.get('photos_per_post', 1)
        post_data = generate_post_with_retry(
            _channel_style,
            performance_hints=hints,
            force_photo_count=photos,
        )
        if post_data:
            publish_post(post_data)
        else:
            print('Failed to generate post')
    except Exception as e:
        print(f'Critical error in post job: {e}')


def _views_update_job():
    print('Updating post views...')
    try:
        views_map = fetch_post_views(TELEGRAM_CHANNEL_ID)
        if views_map:
            analytics.update_views_batch(views_map)
            print(f'Views updated for {len(views_map)} posts')
    except Exception as e:
        print(f'Views update error: {e}')


def _analytics_job():
    print(f'\n{"="*50}')
    print('Running daily analytics...')
    _views_update_job()
    report = analytics.get_daily_report()
    print(report)
    admin_id = analytics.get_admin_chat_id()
    if admin_id:
        try:
            bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
            bot.send_message(chat_id=admin_id, text=report, parse_mode='HTML')
            print('Analytics sent to admin')
        except Exception as e:
            print(f'Failed to send analytics: {e}')


def post_now():
    print('Manual post triggered...')
    _post_job()


def _run_loop():
    posted_keys = set()
    last_views_update = datetime.now()
    last_analytics_date = None
    while not _stop_event.is_set():
        try:
            now = datetime.now()
            today = date.today().isoformat()
            if not any(k.startswith(today) for k in posted_keys):
                posted_keys.clear()
            if (now.hour == DAILY_ANALYTICS_HOUR and
                    now.minute == 0 and
                    last_analytics_date != today):
                last_analytics_date = today
                _analytics_job()
            if (now - last_views_update).total_seconds() >= 6 * 3600:
                _views_update_job()
                last_views_update = now
            settings = bot_settings.load()
            if settings.get('is_posting', True):
                posts_per_day = settings.get('posts_per_day', 1)
                for hour, minute in _calculate_post_times(posts_per_day):
                    key = f'{today}_{hour:02d}:{minute:02d}'
                    if now.hour == hour and now.minute == minute and key not in posted_keys:
                        posted_keys.add(key)
                        _post_job()
                        break
        except Exception as e:
            print(f'Scheduler loop error: {e}')
        time.sleep(30)


def start_scheduler():
    global _thread, _stop_event
    _stop_event.clear()
    settings = bot_settings.load()
    posts_per_day = settings.get('posts_per_day', 1)
    post_times = _calculate_post_times(posts_per_day)
    times_str = ', '.join(f'{h:02d}:{m:02d}' for h, m in post_times)
    print(f'Scheduler started: {posts_per_day} post(s)/day at {times_str}')
    print(f'   Daily analytics at {DAILY_ANALYTICS_HOUR}:00')
    _thread = threading.Thread(target=_run_loop, daemon=True)
    _thread.start()
    return _thread
