# ============================================================
#  bot.py — главный файл запуска бота
#
#  Запуск:  python bot.py
#  Тест:    python bot.py --test
# ============================================================

import sys
import time
import telebot
from datetime import datetime

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, POST_INTERVAL_HOURS
from style_analyzer import analyze_channel_style
from generator import generate_post_with_retry
from publisher import publish_post, test_connection
from scheduler import set_channel_style, start_scheduler, post_now, get_next_post_time

# ---- Telegram бот для команд управления ----
admin_bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


@admin_bot.message_handler(commands=["start"])
def cmd_start(message):
    admin_bot.reply_to(
        message,
        "🚗 JDM Bot запущен!\n\n"
        "Команды:\n"
        "/post — опубликовать пост прямо сейчас\n"
        "/next — когда следующий пост\n"
        "/status — статус бота\n"
        "/stop — остановить бота",
    )


@admin_bot.message_handler(commands=["post"])
def cmd_post(message):
    admin_bot.reply_to(message, "⏳ Генерирую пост...")
    post_now()
    admin_bot.reply_to(message, "✅ Пост опубликован!")


@admin_bot.message_handler(commands=["next"])
def cmd_next(message):
    next_time = get_next_post_time()
    admin_bot.reply_to(
        message,
        f"⏰ Следующий автопост в: {next_time}\n"
        f"Интервал: каждые {POST_INTERVAL_HOURS} ч."
    )


@admin_bot.message_handler(commands=["status"])
def cmd_status(message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    next_time = get_next_post_time()
    admin_bot.reply_to(
        message,
        f"✅ Бот работает\n"
        f"🕐 Время: {now}\n"
        f"📅 Следующий пост: {next_time}\n"
        f"📢 Канал: {TELEGRAM_CHANNEL_ID}"
    )


def run_test_mode():
    """Тестовый режим — генерирует и публикует один пост и выходит."""
    print("\n🧪 ТЕСТОВЫЙ РЕЖИМ")
    print("=" * 50)

    # Проверяем подключение
    if not test_connection():
        print("❌ Проверь TELEGRAM_BOT_TOKEN в config.py")
        sys.exit(1)

    # Анализируем стиль
    print("\n📊 Анализируем стиль канала...")
    style = analyze_channel_style()
    print(f"\n--- Стиль ---\n{style[:200]}...\n")

    # Генерируем пост
    print("✍️  Генерируем пост...")
    post_data = generate_post_with_retry(style)
    
    print(f"\n--- Сгенерированный пост ---")
    print(f"🚗 Машина: {post_data['car']}")
    print(f"🔍 Запрос фото: {post_data['search_query']}")
    print(f"\n{post_data['text']}")
    print("-" * 50)

    # Спрашиваем подтверждение
    answer = input("\n📤 Опубликовать этот пост? (y/n): ").strip().lower()
    if answer == "y":
        publish_post(post_data)
    else:
        print("❌ Публикация отменена")

    print("\n✅ Тест завершён!")


def run_bot():
    """Основной режим — бот работает непрерывно."""
    print("\n🚗 JDM AUTO POSTER BOT")
    print("=" * 50)
    print(f"📢 Канал: {TELEGRAM_CHANNEL_ID}")
    print(f"⏱️  Интервал постов: каждые {POST_INTERVAL_HOURS} ч.")

    # Проверяем Telegram
    if not test_connection():
        print("\n❌ Ошибка подключения. Проверь config.py")
        sys.exit(1)

    # Анализируем стиль канала
    print("\n📊 Анализируем стиль твоего канала...")
    style = analyze_channel_style()
    set_channel_style(style)

    # Публикуем первый пост сразу при запуске
    print("\n🚀 Публикую первый пост...")
    post_now()

    # Запускаем планировщик
    start_scheduler()

    print(f"\n✅ Бот запущен! Следующий пост через {POST_INTERVAL_HOURS} ч.")
    print("   Управление через Telegram: /post /next /status")
    print("   Остановка: Ctrl+C\n")

    # Запускаем прослушивание команд (в главном потоке)
    try:
        admin_bot.polling(non_stop=True, interval=1)
    except KeyboardInterrupt:
        print("\n\n🛑 Бот остановлен")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        time.sleep(5)
        run_bot()  # перезапуск при ошибке


# ---- Точка входа ----
if __name__ == "__main__":
    if "--test" in sys.argv:
        run_test_mode()
    else:
        run_bot()
