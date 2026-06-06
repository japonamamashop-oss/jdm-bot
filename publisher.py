# ============================================================
#  publisher.py — публикует посты в Telegram канал
# ============================================================

import telebot
import io
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID
from image_finder import search_car_photo, search_multiple_photos, download_photo
import analytics

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


def publish_post(post_data: dict) -> bool:
    """
    Публикует пост в Telegram канал.
    Поддерживает 1 фото или медиагруппу из 3 фото.
    """
    text = post_data.get("text", "")
    search_query = post_data.get("search_query", "jdm japanese car")
    car = post_data.get("car", "Unknown")
    photo_count = post_data.get("photo_count", 1)

    print(f%x\nPublishing post about {car} ({photo_count} photos)...")

    message_ids = []

    if photo_count >= 3:
        message_ids = _publish_media_group(text, search_query)
    else:
        photo_url = search_car_photo(search_query)
        msg = _publish_with_photo(text, photo_url) if photo_url else _publish_text_only(text)
        if msg:
            message_ids = [msg.message_id]

    success = bool(message_ids)

    if success:
        print(f%x\nPost about {car} published! (msg_id: {message_ids})")
        analytics.save_post(car, message_ids, text, photo_count=photo_count if photo_count >= 3 else 1)
    else:
        print(f%x\nFailed to publish post about {car}")

    return success


def _publish_media_group(text: str, search_query: str) -> list:
    """Публикует пост с 3 фотографиями как медиагруппу."""
    photo_urls = search_multiple_photos(search_query, count=3)

    if not photo_urls:
        print("No photos found, publishing text only")
        msg = _publish_text_only(text)
        return [msg.message_id] if msg else []

    try:
        media = []
        open_files = []

        for i, url in enumerate(photo_urls[:3]):
            photo_bytes = download_photo(url)
            if photo_bytes:
                f = io.BytesIO(photo_bytes)
                f.name = f"photo_{i}.jpg"
                open_files.append(f)
                if i == 0:
                    media.append(telebot.types.InputMediaPhoto(
                        media=f, caption=text[:1024], parse_mode="HTML"
                    ))
                else:
                    media.append(telebot.types.InputMediaPhoto(media=f))
            else:
                if i == 0:
                    media.append(telebot.types.InputMediaPhoto(
                        media=url, caption=text[:1024], parse_mode="HTML"
                    ))
                else:
                    media.append(telebot.types.InputMediaPhoto(media=url))

        if not media:
            msg = _publish_text_only(text)
            return [msg.message_id] if msg else []

        if len(media) == 1:
            msg = _publish_with_photo(text, photo_urls[0])
            return [msg.message_id] if msg else []

        messages = bot.send_media_group(chat_id=TELEGRAM_CHANNEL_ID, media=media)
        print(f%xMedia group of {len(messages)} photos published")
        return [m.message_id for m in messages]

    except Exception as e:
        print(f%xMedia group error: {e}, falling back to single photo")
        msg = _publish_with_photo(text, photo_urls[0]) if photo_urls else _publish_text_only(text)
        return [msg.message_id] if msg else []


def _publish_with_photo(text: str, photo_url: str):
    """Публикует фото с подписью."""
    try:
        photo_bytes = download_photo(photo_url)
        if photo_bytes:
            photo_file = io.BytesIO(photo_bytes)
            photo_file.name = "photo.jpg"
            return bot.send_photo(
                chat_id=TELEGRAM_CHANNEL_ID,
                photo=photo_file,
                caption=text[:1024],
                parse_mode="HTML",
            )
        else:
            return bot.send_photo(
                chat_id=TELEGRAM_CHANNEL_ID,
                photo=photo_url,
                caption=text[:1024],
                parse_mode="HTML",
            )
    except Exception as e:
        print(f"Photo publish error: {e}")
        return _publish_text_only(text)


def _publish_text_only(text: str):
    """Публикует только текст."""
    try:
        return bot.send_message(
            chat_id=TELEGRAM_CHANNEL_ID,
            text=text[:4096],
            parse_mode="HTML",
        )
    except Exception as e:
        print(f"Text publish error: {e}")
        return None


def test_connection() -> bool:
    """Проверяет подключение к Telegram."""
    try:
        bot_info = bot.get_me()
        print(f"Bot connected: @{bot_info.username}")
        return True
    except Exception as e:
        print(f"Telegram connection error: {e}")
        return False
