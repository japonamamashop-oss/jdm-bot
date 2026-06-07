# ============================================================
#  generator.py — генерирует посты через Groq AI
#  Логика: сначала ищем фото → подтверждаем машину → пишем текст.
#  Гарантирует что фото и текст — про одну и ту же машину.
# ============================================================

import random
from groq import Groq
from config import GROQ_API_KEY, JDM_CARS
from style_analyzer import get_style_prompt
import image_finder

client = Groq(api_key=GROQ_API_KEY)

_recently_used = []


def pick_car() -> str:
    global _recently_used
    available = [c for c in JDM_CARS if c not in _recently_used]
    if not available:
        _recently_used = []
        available = JDM_CARS
    car = random.choice(available)
    _recently_used.append(car)
    if len(_recently_used) > 7:
        _recently_used.pop(0)
    return car


def _pick_car_with_photo(max_tries: int = 6) -> tuple:
    """
    Пытается найти машину для которой есть конкретное фото на Unsplash.
    Возвращает (car_name, photo_url).
    Если за max_tries попыток фото не найдено — возвращает (car, None).
    """
    tried = []
    for _ in range(max_tries):
        car = pick_car()
        if car in tried:
            continue
        tried.append(car)
        print(f"   Searching photo for: {car}")
        photo_url = image_finder.search_car_photo(car)
        if photo_url:
            print(f"   Confirmed car+photo: {car}")
            return car, photo_url

    car = pick_car()
    print(f"   No photo found after {max_tries} tries, text-only: {car}")
    return car, None


def generate_post(style_description: str, car_name: str = None,
                  performance_hints: dict = None,
                  force_photo_count: int = None) -> dict:

    photo_count = force_photo_count if force_photo_count is not None else 1
    use_multi = photo_count >= 3

    # ── Выбор машины и поиск фото ───────────────────────────────────────────
    if car_name:
        if use_multi:
            confirmed_photos = image_finder.search_multiple_photos(car_name, count=3)
            confirmed_photo = confirmed_photos[0] if confirmed_photos else None
        else:
            confirmed_photo = image_finder.search_car_photo(car_name)
            confirmed_photos = [confirmed_photo] if confirmed_photo else []
    else:
        if use_multi:
            car_name, confirmed_photo = _pick_car_with_photo(max_tries=6)
            if confirmed_photo:
                confirmed_photos = image_finder.search_multiple_photos(car_name, count=3)
                confirmed_photo = confirmed_photos[0] if confirmed_photos else None
            else:
                confirmed_photos = []
        else:
            car_name, confirmed_photo = _pick_car_with_photo(max_tries=6)
            confirmed_photos = [confirmed_photo] if confirmed_photo else []

    # ── Генерация текста ─────────────────────────────────────────────────────
    style_instruction = get_style_prompt(style_description, performance_hints)

    topics = [
        f"история создания {car_name}, культовый статус и технические характеристики",
        f"интересные факты о {car_name} — то чего не знают большинство",
        f"почему {car_name} стала иконой JDM-культуры — аниме, игры, кино",
        f"тюнинг-потенциал {car_name}: популярные апгрейды и рекорды мощности",
        f"история {car_name} на треке и в дрифте — гоночное наследие",
        f"стоимость {car_name} тогда и сейчас — почему цены выросли",
        f"редкие версии и спецификации {car_name} о которых мало кто знает",
    ]
    topic = random.choice(topics)

    multi_note = ""
    if use_multi:
        multi_note = "\nВАЖНО: к посту 3 фотографии. Упомяни внешний вид машины."

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": style_instruction},
            {
                "role": "user",
                "content": (
                    f"Напиши короткий пост (3-4 абзаца) про: {topic}. Машина: {car_name}.\n"
                    f"Правила:\n"
                    f"- Только русский язык\n"
                    f"- Много тематических эмодзи \U0001f525\u26a1\U0001f3c1\U0001f38c\U0001f697\U0001f409\U0001f4a8\U0001f527 в каждом абзаце\n"
                    f"- Короткие энергичные предложения\n"
                    f"- В конце хэштеги (5-7 штук)\n"
                    f"- Максимум 250 слов{multi_note}"
                )
            }
        ],
        max_tokens=450,
    )

    post_text = response.choices[0].message.content.strip()

    return {
        "text": post_text,
        "car": car_name,
        "search_query": car_name,
        "photo_count": photo_count,
        "confirmed_photo": confirmed_photo,
        "confirmed_photos": confirmed_photos,
    }


def generate_post_with_retry(style_description: str, performance_hints: dict = None,
                              force_photo_count: int = None,
                              max_attempts: int = 3) -> dict:
    for attempt in range(max_attempts):
        try:
            return generate_post(
                style_description,
                performance_hints=performance_hints,
                force_photo_count=force_photo_count,
            )
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_attempts} failed: {e}")
            if attempt == max_attempts - 1:
                raise
    return {}
