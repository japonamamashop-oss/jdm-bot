# ============================================================
#  generator.py — генерирует посты через Groq AI
# ============================================================

from groq import Groq
import random
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
    if len(_recently_used) > 5:
        _recently_used.pop(0)
    return car


def generate_post(style_description: str, car_name: str = None) -> dict:
    if not car_name:
        car_name = pick_car()

    style_instruction = get_style_prompt(style_description)

    topics = [
        f"общий пост-знакомство с {car_name}, технические характеристики и история",
        f"легенды и мифы вокруг {car_name}, интересные факты",
        f"почему {car_name} стала культовой — культурное влияние",
        f"тюнинг-потенциал {car_name}, что делает с ней энтузиасты",
        f"сравнение эпох: {car_name} тогда и сейчас, рост цен и ценности",
        f"гоночное наследие {car_name} — участие в соревнованиях",
    ]
    topic = random.choice(topics)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": style_instruction},
            {"role": "user", "content": f"Напиши пост про: {topic}. Машина: {car_name}. Пиши только на русском языке. Пост должен быть готов к публикации в Telegram."}
        ],
        max_tokens=800,
    )

    post_text = response.choices[0].message.content.strip()

    car_parts = car_name.lower().replace("-", " ").split()
    search_query = " ".join(car_parts[:4]) + " jdm japan car"

    return {
        "text": post_text,
        "car": car_name,
        "search_query": search_query,
    }


def generate_post_with_retry(style_description: str, max_attempts: int = 3) -> dict:
    for attempt in range(max_attempts):
        try:
            return generate_post(style_description)
        except Exception as e:
            print(f"⚠️  Попытка {attempt + 1}/{max_attempts} не удалась: {e}")
            if attempt == max_attempts - 1:
                raise
    return {}
