# ============================================================
#  generator.py — генерирует посты через Groq AI
# ============================================================

import random
from groq import Groq
from config import GROQ_API_KEY, JDM_CARS
from style_analyzer import get_style_prompt

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


def generate_post(style_description: str, car_name: str = None,
                  performance_hints: dict = None,
                  force_photo_count: int = None) -> dict:
    if not car_name:
        car_name = pick_car()

    photo_count = force_photo_count if force_photo_count is not None else 1
    use_multi = photo_count >= 3

    style_instruction = get_style_prompt(style_description, performance_hints)

    topics = [
        f"общий пост-знакомство с {car_name}: история создания, технические характеристики, культовый статус",
        f"легенды, мифы и интересные факты о {car_name} — то чего не знают большинство",
        f"почему {car_name} стала иконой JDM-культуры — влияние аниме, игр, кино",
        f"тюнинг-потенциал {car_name}: популярные апгрейды и рекорды мощности",
        f"история {car_name} на треке и в дрифте — гоночное наследие",
        f"стоимость {car_name} тогда и сейчас — почему цены выросли и стоит ли покупать",
        f"редкие версии и спецификации {car_name} о которых мало кто знает",
    ]
    topic = random.choice(topics)

    multi_note = ""
    if use_multi:
        multi_note = "\nВАЖНО: к посту будет 3 фотографии. Добавь описание внешнего вида машины."

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": style_instruction},
            {
                "role": "user",
                "content": (
                    f"Напиши пост про: {topic}. Машина: {car_name}."
                    f"\nПиши только на русском. Пост готов к публикации."
                    f"{multi_note}"
                )
            }
        ],
        max_tokens=700,
    )

    post_text = response.choices[0].message.content.strip()
    search_query = car_name.strip()

    return {
        "text": post_text,
        "car": car_name,
        "search_query": search_query,
        "photo_count": photo_count,
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
