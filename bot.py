# ============================================================
#  bot.py — главный файл запуска бота
#           + полное Telegram-управление через inline-кнопки
# ============================================================

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TELEGRAM_BOT_TOKEN
import analytics
import bot_settings
import scheduler
from style_analyzer import analyze_channel_style

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


# ─── Auth ─────────────────────────────────────────────────────────────────────

def _is_admin(message_or_call) -> bool:
    """Проверяет, является ли пользователь администратором."""
    if hasattr(message_or_call, "chat"):
        chat_id = message_or_call.chat.id
    else:
        chat_id = message_or_call.message.chat.id

    admin_id = analytics.get_admin_chat_id()
    return admin_id is None or chat_id == admin_id


# ─── Keyboards ────────────────────────────────────────────────────────────────

def _main_kb() -> InlineKeyboardMarkup:
    settings = bot_settings.load()
    is_posting = settings.get("is_posting", True)
    pause_label = "⏸ Пауза" if is_posting else "▶️ Возобновить"
    pause_cb = "pause" if is_posting else "resume"

    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📝 Пост сейчас", callback_data="post_now"),
        InlineKeyboardButton("📊 Аналитика", callback_data="analytics"),
    )
    kb.add(
        InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
        InlineKeyboardButton("📋 Расписание", callback_data="schedule_info"),
    )
    kb.add(
        InlineKeyboardButton(pause_label, callback_data=pause_cb),
        InlineKeyboardButton("📈 Статус", callback_data="status"),
    )
    return kb


def _settings_kb() -> InlineKeyboardMarkup:
    settings = bot_settings.load()
    ppd = settings.get("posts_per_day", 1)
    photos = settings.get("photos_per_post", 1)

    kb = InlineKeyboardMarkup(row_width=3)
    kb.row(InlineKeyboardButton(f"📅 Постов в день: {ppd}", callback_data="noop"))
    kb.row(
        InlineKeyboardButton("➖", callback_data="ppd_dec"),
        InlineKeyboardButton(f"  {ppd}  ", callback_data="noop"),
        InlineKeyboardButton("➕", callback_data="ppd_inc"),
    )
    kb.row(InlineKeyboardButton("🖼 Фото в посте:", callback_data="noop"))
    kb.row(
        InlineKeyboardButton("1 фото" + (" ✓" if photos == 1 else ""), callback_data="photos_1"),
        InlineKeyboardButton("3 фото" + (" ✓" if photos == 3 else ""), callback_data="photos_3"),
    )
    kb.row(InlineKeyboardButton("◀️ Назад в меню", callback_data="main_menu"))
    return kb


def _back_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("◀️ Назад в меню", callback_data="main_menu"))
    return kb


# ─── Status text ──────────────────────────────────────────────────────────────

def _status_text() -> str:
    settings = bot_settings.load()
    is_posting = settings.get("is_posting", True)
    ppd = settings.get("posts_per_day", 1)
    photos = settings.get("photos_per_post", 1)
    status_icon = "✅" if is_posting else "⏸"

    return (
        f"📊 <b>Статус бота</b>\n\n"
        f"{status_icon} Автопостинг: {'Активен' if is_posting else 'На паузе'}\n"
        f"📅 Постов в день: <b>{ppd}</b>\n"
        f"🖼 Фото в посте: <b>{photos}</b>"
    )


# ─── Commands ─────────────────────────────────────────────────────────────────

@bot.message_handler(commands=["start"])
def cmd_start(message):
    admin_id = analytics.get_admin_chat_id()
    if admin_id is None:
        analytics.set_admin_chat_id(message.chat.id)
        bot_settings.set_value("admin_chat_id", message.chat.id)
        intro = "✅ <b>Вы зарегистрированы как администратор!</b>\n\n"
    else:
        intro = ""

    bot.send_message(
        message.chat.id,
        f"{intro}🚗 <b>JDM Bot — управление</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=_main_kb(),
    )


@bot.message_handler(commands=["menu"])
def cmd_menu(message):
    bot.send_message(
        message.chat.id,
        "🚗 <b>Главное меню</b>",
        parse_mode="HTML",
        reply_markup=_main_kb(),
    )


@bot.message_handler(commands=["status"])
def cmd_status(message):
    bot.send_message(
        message.chat.id,
        _status_text(),
        parse_mode="HTML",
        reply_markup=_back_kb(),
    )


@bot.message_handler(commands=["post", "next"])
def cmd_post(message):
    if not _is_admin(message):
        return
    bot.send_message(message.chat.id, "⏳ Генерирую и публикую пост...")
    ok = scheduler.post_now()
    if ok:
        bot.send_message(message.chat.id, "✅ Пост опубликован!", reply_markup=_main_kb())
    else:
        bot.send_message(message.chat.id, "❌ Ошибка при публикации. Проверьте логи Railway.", reply_markup=_main_kb())


@bot.message_handler(commands=["pause"])
def cmd_pause(message):
    if not _is_admin(message):
        return
    bot_settings.set_value("is_posting", False)
    bot.send_message(message.chat.id, "⏸ Автопостинг поставлен на паузу.", reply_markup=_main_kb())


@bot.message_handler(commands=["resume"])
def cmd_resume(message):
    if not _is_admin(message):
        return
    bot_settings.set_value("is_posting", True)
    bot.send_message(message.chat.id, "▶️ Автопостинг возобновлён.", reply_markup=_main_kb())


@bot.message_handler(commands=["analytics"])
def cmd_analytics(message):
    report = analytics.get_daily_report()
    bot.send_message(message.chat.id, report, parse_mode="HTML", reply_markup=_back_kb())


@bot.message_handler(commands=["schedule"])
def cmd_schedule(message):
    info = scheduler.get_schedule_info()
    bot.send_message(message.chat.id, info, parse_mode="HTML", reply_markup=_back_kb())


@bot.message_handler(commands=["settings"])
def cmd_settings(message):
    if not _is_admin(message):
        return
    bot.send_message(
        message.chat.id,
        "⚙️ <b>Настройки</b>",
        parse_mode="HTML",
        reply_markup=_settings_kb(),
    )


# ─── Inline callbacks ─────────────────────────────────────────────────────────

@bot.callback_query_handler(func=lambda c: True)
def handle_callback(call):
    data = call.data
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    if data == "noop":
        bot.answer_callback_query(call.id)
        return

    if data == "main_menu":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "🚗 <b>Главное меню</b>",
            chat_id, msg_id,
            parse_mode="HTML",
            reply_markup=_main_kb(),
        )

    elif data == "settings":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "⚙️ <b>Настройки</b>",
            chat_id, msg_id,
            parse_mode="HTML",
            reply_markup=_settings_kb(),
        )

    elif data == "ppd_inc":
        s = bot_settings.load()
        new_val = min(s.get("posts_per_day", 1) + 1, 24)
        bot_settings.set_value("posts_per_day", new_val)
        bot.answer_callback_query(call.id, f"Постов в день: {new_val}")
        bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=_settings_kb())

    elif data == "ppd_dec":
        s = bot_settings.load()
        new_val = max(s.get("posts_per_day", 1) - 1, 1)
        bot_settings.set_value("posts_per_day", new_val)
        bot.answer_callback_query(call.id, f"Постов в день: {new_val}")
        bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=_settings_kb())

    elif data == "photos_1":
        bot_settings.set_value("photos_per_post", 1)
        bot.answer_callback_query(call.id, "1 фото на пост ✓")
        bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=_settings_kb())

    elif data == "photos_3":
        bot_settings.set_value("photos_per_post", 3)
        bot.answer_callback_query(call.id, "3 фото на пост ✓")
        bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=_settings_kb())

    elif data == "pause":
        bot_settings.set_value("is_posting", False)
        bot.answer_callback_query(call.id, "⏸ Автопостинг на паузе")
        bot.edit_message_text(
            "⏸ Автопостинг поставлен на паузу.\n\n🚗 <b>Главное меню</b>",
            chat_id, msg_id,
            parse_mode="HTML",
            reply_markup=_main_kb(),
        )

    elif data == "resume":
        bot_settings.set_value("is_posting", True)
        bot.answer_callback_query(call.id, "▶️ Возобновлён!")
        bot.edit_message_text(
            "▶️ Автопостинг возобновлён.\n\n🚗 <b>Главное меню</b>",
            chat_id, msg_id,
            parse_mode="HTML",
            reply_markup=_main_kb(),
        )

    elif data == "status":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            _status_text(),
            chat_id, msg_id,
            parse_mode="HTML",
            reply_markup=_back_kb(),
        )

    elif data == "schedule_info":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            scheduler.get_schedule_info(),
            chat_id, msg_id,
            parse_mode="HTML",
            reply_markup=_back_kb(),
        )

    elif data == "analytics":
        bot.answer_callback_query(call.id)
        report = analytics.get_daily_report()
        bot.send_message(chat_id, report, parse_mode="HTML", reply_markup=_back_kb())

    elif data == "post_now":
        bot.answer_callback_query(call.id, "⏳ Публикую...")
        bot.send_message(chat_id, "⏳ Генерирую и публикую пост...")
        ok = scheduler.post_now()
        if ok:
            bot.send_message(chat_id, "✅ Пост опубликован!", reply_markup=_main_kb())
        else:
            bot.send_message(chat_id, "❌ Ошибка при публикации. Проверьте логи Railway.", reply_markup=_main_kb())

    else:
        bot.answer_callback_query(call.id)


# ─── Reaction tracking ────────────────────────────────────────────────────────

@bot.channel_post_handler(content_types=["text", "photo"])
def _track_channel_post(message):
    pass  # Трекинг происходит в publisher.py через analytics.save_post


def _handle_reaction_update(update):
    try:
        if hasattr(update, "message_reaction_count"):
            r = update.message_reaction_count
            total = sum(rc.count for rc in r.reactions) if r.reactions else 0
            if total > 0:
                analytics.add_reactions(r.message_id, total)
        elif hasattr(update, "message_reaction"):
            r = update.message_reaction
            analytics.add_reactions(r.message_id, 1)
    except Exception as e:
        print(f"Reaction update error: {e}")


# ─── Entry point ──────────────────────────────────────────────────────────────

def start_bot():
    """Запускает Telegram-бота (polling)."""
    print("Bot started, polling...")
    print("Commands: /start /menu /status /post /pause /resume /analytics /schedule /settings")
    bot.infinity_polling(
        allowed_updates=[
            "message",
            "channel_post",
            "message_reaction",
            "message_reaction_count",
            "callback_query",
        ],
        timeout=60,
        long_polling_timeout=60,
    )


if __name__ == "__main__":
    import threading

    print("Analyzing channel style...")
    try:
        style = analyze_channel_style()
        scheduler.set_channel_style(style)
    except Exception as e:
        print(f"Style analysis failed: {e}")
        scheduler.set_channel_style("")

    scheduler.start_scheduler()
    start_bot()
