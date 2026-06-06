# ============================================================
#  image_finder.py — ищет красивые фото JDM машин
# ============================================================

import requests
import random
from config import UNSPLASH_ACCESS_KEY


UNSPLASH_API = "https://api.unsplash.com"

# Запасные запросы если основной не дал результатов
FALLBACK_QUERIES = [
    "jdm japanese car",
    "japanese sports car",
    "modified car japan",
    "drift car japan",
    "jdm tuner car",
]


def search_car_photo(query: str) -> str | None:
    """
    Ищет фото машины на Unsplash.
    
    Args:
        query: поисковый запрос, например "nissan skyline gtr r34 jdm"
    
    Returns:
        URL фото (str) или None если ничего не найдено
    """
    queries_to_try = [query] + FALLBACK_QUERIES

    for q in queries_to_try:
        url = _fetch_photo_url(q)
        if url:
            return url

    return None


def _fetch_photo_url(query: str) -> str | None:
    """Делает запрос к Unsplash API."""
    try:
        response = requests.get(
            f"{UNSPLASH_API}/search/photos",
            params={
                "query": query,
                "per_page": 15,
                "orientation": "landscape",  # горизонтальные фото лучше для Telegram
                "order_by": "relevant",
            },
            headers={
                "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}",
                "Accept-Version": "v1",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        if not results:
            return None

        # Берём случайное фото из топ-10 для разнообразия
        top_results = results[:10]
        photo = random.choice(top_results)

        # Используем regular размер — оптимален для Telegram
        photo_url = photo["urls"].get("regular") or photo["urls"].get("full")
        print(f"📸 Найдено фото: {photo_url[:60]}...")
        return photo_url

    except requests.exceptions.RequestException as e:
        print(f"⚠️  Ошибка УнсплашАпЉ: {e}")
        return None
    except (KeyError, IndexError) as e:
        print(f"⚠️  Ошибка парсинга ответа Unsplash: {e}")
        return None


def download_photo(url: str) -> bytes | None:
    """Скачивает фото по URL и возвращает байты — передать."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Ошибка скачивания фото: {e}")
        return None
