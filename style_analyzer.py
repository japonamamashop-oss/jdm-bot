# ============================================================
#  style_analyzer.py — анализирует стиль постов канала
# ============================================================

import re
import requests
from groq import Groq
from config import GROQ_API_KEY, EXAMPLE_POSTS, TELEGRAM_CHANNEL_ID

client = Groq(api_key=GROQ_API_KEY)


def fetch_channel_posts_web(channel_id: str, count: int = 15) -> list:
    """Получает последние посты из публичного Telegram-канала через t.me/s/"""
    try:
        username = channel_id.lstrip('@')
        url = f"https://t.me/s/{username}"
        response = requests.get(
            url, timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (compatible; TelegramBot)"}
        )
        response.raise_for_status()

        # Извлекаем текст постов из HTML
        pattern = r'class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>'
        matches = re.findall(pattern, response.text, re.DOTALL)

        posts = []
        for m in matches:
            clean = re.sub(r'<br\s*/?>', '\n', m)
            clean = re.sub(r'<[^>]+>', '', clean)
            clean = clean.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').strip()
            if len(clean) > 80:
                posts.append(clean)

        return posts[-count:] if posts else []

    except Exception as e:
        print(f"No posts fetched: {e}")
        return []


def analyze_channel_style() -> str:
    """Анализирует стиль канала по реальным постам (или примерам если канал пуст)."""
    real_posts = fetch_channel_posts_web(TELEGRAM_CHANNEL_ID, count=15)

    if real_posts:
        posts_source = real_posts
        source_label = f"последние {len(real_posts)} постов канала"
        print(f"   Анализирую {len(real_posts)} реальных постов канала...")
    else:
        posts_source = EXAMPLE_POSTS
        source_label = "примеры постов"
        print(f"   Использую примеры постов (реальных постов нет)...")

    posts_text = "\n\n---\n\n".join(posts_source)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": f"""Проанализируй стиль этих постов из Telegram-канала про JDM машины ({source_label}).

Посты:
{posts_text}

Дай детальный анализ:
1. Тон и эмоциональность — насколько восторженный/технический/разговорный
2. Структура — как начинается (зацепка), основная часть, концовка
3. Эмодзи — какие именно, сколько, где расположены (в начале строк / в конце / в заголовке)
4. Пробелы и отступы — как разбит текст на абзацы, есть ли пустые строки
5. Технические данные — как подаются характеристики
6. Хэштеги — количество, стиль, где стоят
7. Длина постов
8. Особые приёмы — обращения к читателю, риторические вопросы

Это резюме используется для генерации ПОХОЖИХ постов. Будь конкретен."""
            }
        ],
        max_tokens=1000,
    )

    style = response.choices[0].message.content
    print("Style analyzed OK")
    return style


def get_style_prompt(style_description: str, performance_hints: dict = None) -> str:
    """Формирует системный промпт с учётом аналитики."""

    hints_section = ""
    if performance_hints:
        parts = []
        if performance_hints.get("preferred_emoji_count"):
            parts.append(f"- Используй примерно {performance_hints['preferred_emoji_count']} эмодзи")
        if performance_hints.get("preferred_length"):
            parts.append(f"- Длина текста: примерно {performance_hints['preferred_length']} символов")
        if performance_hints.get("preferred_line_count"):
            parts.append(f"- Разбивай на {performance_hints['preferred_line_count']} абзацев")
        if parts:
            hints_section = "\nАДАПТАЦИЯ (что нравится подписчикам):\n" + "\n".join(parts) + "\n"

    return f"""Ты - автор Telegram-канала про JDM автомобили.
Пиши посты строго в следующем стиле:

{style_description}
{hints_section}
ПРАВИЛА:
- Только на русском языке
- Пост готов к публикации - без заголовков и вступления
- Точные технические характеристики
- Интересные факты и история
- Эмодзи в начале ключевых строк
- Пустые строки между смысловыми блоками
- Хэштеги в конце
- Не повторяй шаблонные фразы"""
