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
import analytics

admin_bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


@admin_bot.message_handler(commands=["start"])
def cmd_start(message):
    analytics.set_admin_chat_id(message.chat.id)
    admin_bot.reply_to(
        message,
        "JDM Bot started!\n\n"
        "Commands:\n"
        "/post - post now\n"
        "/next - next post time\n"
        "/status - bot status\n"
        "/analytics - today analytics",
        parse_mode="HTML"
    )


@admin_bot.message_handler(commands=["post"])
def cmd_post(message):
    analytics.set_admin_chat_id(message.chat.id)
    admin_bot.reply_to(message, "Generating post...")
    post_now()
    admin_bot.reply_to(message, "Post published!")


@admin_bot.message_handler(commands=["next"])
def cmd_next(message):
    next_time = get_next_post_time()
    admin_bot.reply_to(
        message,
        f"Next post: <b>{next_time}</b>\nInterval: every {POST_INTERVAL_HOURS}h.",
        parse_mode="HTML"
    )


@admin_bot.message_handler(commands=["status"])
def cmd_status(message):
    analytics.set_admin_chat_id(message.chat.id)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    next_time = get_next_post_time()
    hints = analytics.get_performance_hints()

    hints_text = ""
    if hints:
        hints_text = (
            f"\n\n<b>Style adaptation:</b>\n"
            f"- Emoji: ~{hints.get('preferred_emoji_count', '?')}\n"
            f"- Length: ~{hints.get('preferred_length', '?')} chars\n"
            f"- Multi-photo: {'yes' if hints.get('prefer_multi_photo') else 'no'}"
        )

    admin_bot.reply_to(
        message,
        f"<b>Bot running</b>\n"
        f"{now}\n"
        f"Next post: {next_time}\n"
        f"Channel: {TELEGRAM_CHANNEL_ID}"
        f"{hints_text}",
        parse_mode="HTML"
    )


@admin_bot.message_handler(commands=["analytics"])
def cmd_analytics(message):
    analytics.set_admin_chat_id(message.chat.id)
    report = analytics.get_daily_report()
    admin_bot.reply_to(message, report, parse_mode="HTML")


def _handle_reaction_update(update):
    """Обрабатывает обновления реакций на посты канала."""
    try:
        if hasattr(update, 'message_reaction_count'):
            r = update.message_reaction_count
            msg_id = r.message_id
            total = sum(reaction.count for reaction in r.reactions)
            if total > 0:
                analytics.add_reactions(msg_id, total)
                print(f"Reactions: msg {msg_id} = {total}")
        elif hasattr(update, 'message_reaction'):
            r = update.message_reaction
            msg_id = r.message_id
            new_count = len(r.new_reaction)
            if new_count > 0:
                analytics.add_reactions(msg_id, new_count)
    except Exception as e:
        print(f"Reaction update error: {e}")


def run_test_mode():
    """Тестовый режим."""
    print("\nTEST MODE")
    print("=" * 50)

    if not test_connection():
        print("Check TELEGRAM_BOT_TOKEN in config.py")
        sys.exit(1)

    print("\nAnalyzing channel style...")
    style = analyze_channel_style()
    print(f"\n--- Style ---\n{style[:200]}...\n")

    print("Generating post...")
    post_data = generate_post_with_retry(style)

    print(f"\n--- Generated post ---")
    print(f"Car: {post_data['car']}")
    print(f"Search: {post_data['search_query']}")
    print(f"Photos: {post_data.get('photo_count', 1)}")
    print(f"\n{post_data['text']}")
    print("-" * 50)

    answer = input("\nPublish this post? (y/n): ").strip().lower()
    if answer == "y":
        publish_post(post_data)
    else:
        print("Cancelled")

    print("\nTest complete!")


def run_bot():
    """Основной режим."""
    print("\nJDM AUTO POSTER BOT")
    print("=" * 50)
    print(f"Channel: {TELEGRAM_CHANNEL_ID}")
    print(f"Interval: every {POST_INTERVAL_HOURS}h.")

    if not test_connection():
        print("\nConnection error. Check config.py")
        sys.exit(1)

    print("\nAnalyzing channel style...")
    style = analyze_channel_style()
    set_channel_style(style)

    print("\nPosting first post...")
    post_now()

    start_scheduler()

    print(f"\nBot running! Next post in {POST_INTERVAL_HOURS}h.")
    print("Commands: /post /next /status /analytics\n")

    try:
        @admin_bot.middleware_handler(update_types=['message_reaction_count', 'message_reaction'])
        def reaction_middleware(bot_instance, update):
            _handle_reaction_update(update)
    except Exception:
        pass

    try:
        admin_bot.polling(
            non_stop=True,
            interval=1,
            allowed_updates=[
                "message",
                "channel_post",
                "message_reaction",
                "message_reaction_count",
            ]
        )
    except KeyboardInterrupt:
        print("\nBot stopped")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        time.sleep(5)
        run_bot()


if __name__ == "__main__":
    if "--test" in sys.argv:
        run_test_mode()
    else:
        run_bot()
