# ============================================================
#  publisher.py — публикует посты в Telegram канал
# ============================================================

import telebot
import requests
import io
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID
from image_finder import search_car_photo, download_photo

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


def publish_post(post_data: dict) -> bool:
    """
    Публикует пост с фото в Telegram канал.
    
    Args:
        post_data: словарь с ключами 'text', 'car', 'search_query'
    
    Returns:
        True если успешно, False если ошибка
    """
    text = post_data.get("text", "")
    search_query = post_data.get("search_query", "jdm japanese car")
    car = post_data.get("car", "Unknown")

    print(f"\n📤 Публикую пост про {car}...")

    # Ищем фото
    photo_url = search_car_photo(search_query)

    if photo_url:
        success = _publish_with_photo(text, photo_url)
    else:
        print("⚠️  Фото не найдено, публикую только текст")
        success = _publish_text_only(text)

    if success:
        print(f"✅ Пост про {car} опубликован!")
    else:
        print(f"❌ Не удалось опубликовать пост про {car}")

    return success


def _publish_with_photo(text: str, photo_url: str) -> bool:
    """Публикует фото с подписью."""
    try:
        # Скачиваем фото
        photo_bytes = download_photo(photo_url)

        if photo_bytes:
            # Публикуем как файл (лучшее качество)
            photo_file = io.BytesIO(photo_bytes)
            photo_file.name = "photo.jpg"

            bot.send_photo(
                chat_id=TELEGRAM_CHANNEL_ID,
                photo=photo_file,
                caption=text[:1024],  # Telegram лимит для подписи к фотп
                parse_mode="HTML",
            )
        else:
            # Если не скачали — пробуем по URL напрямую
            bot.send_photo(
                chat_id=TELEGRAM_CHANNEL_ID,
                photo=photo_url,
                caption=text[:1024],
                parse_mode="HTML",
            )
        return True

    except Exception as e:
        print(f"⚠️  Ошибка публикации с фото: {e}")
        # Пробуем без фото
        return _publish_text_only(text)


def _publish_text_only(text: str) -> bool:
    """Публикует только текст."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHANNEL_ID,
            text=text[:4096],  # Telegram лимит для текстового сообщения
            parse_mode="HTML",
        )
        return True
    except Exception as e:
        print(f"❌ Ошибка публикации текста: {e}")
        return False


def test_connection() -> bool:
    """Проверяет подключение к Telegram."""
    try:
        bot_info = bot.get_me()
        print(f"✅ Бот подключён: @{bot_info.username}")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к Telegram: {e}")
        return False
