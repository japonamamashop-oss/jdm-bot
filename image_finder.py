# ============================================================
#  image_finder.py — ищет красивые фото JDM машин
# ============================================================

import requests
import random
from config import UNSPLASH_ACCESS_KEY


UNSPLASH_API = "https://api.unsplash.com"

FALLBACK_QUERIES = [
    "jdm japanese car",
    "japanese sports car",
    "modified car japan",
    "drift car japan",
    "jdm tuner car",
]


def search_car_photo(query: str) -> str | None:
    """Ищет одно фото машины."""
    queries_to_try = [query] + FALLBACK_QUERIES
    for q in queries_to_try:
        urls = _fetch_photo_urls(q, count=1)
        if urls:
            return urls[0]
    return None


def search_multiple_photos(query: str, count: int = 3) -> list:
    """Ищет несколько разных фото для медиагруппы."""
    urls = _fetch_photo_urls(query, count=count + 5)
    result = urls[:count]

    for fallback in FALLBACK_QUERIES:
        if len(result) >= count:
            break
        extra = _fetch_photo_urls(fallback, count=2)
        for u in extra:
            if u not in result:
                result.append(u)

    return result[:count]


def _fetch_photo_urls(query: str, count: int = 10) -> list:
    """Делает запрос к Unsplash API, возвращает список URL."""
    try:
        response = requests.get(
            f"{UNSPLASH_API}/search/photos",
            params={
                "query": query,
                "per_page": min(30, max(count * 2, 15)),
                "orientation": "landscape",
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
            return []

        top = results[:min(15, len(results))]
        random.shuffle(top)

        urls = []
        for photo in top[:count]:
            url = photo["urls"].get("regular") or photo["urls"].get("full")
            if url:
                urls.append(url)

        if urls:
            print(f"Found {len(urls)} photos for '{query[:30]}'")
        return urls

    except requests.exceptions.RequestException as e:
        print(f"Unsplash API error: {e}")
        return []
    except (KeyError, IndexError) as e:
        print(f"Unsplash parse error: {e}")
        return []


def _fetch_photo_url(query: str) -> str | None:
    urls = _fetch_photo_urls(query, count=1)
    return urls[0] if urls else None


def download_photo(url: str) -> bytes | None:
    """Скачивает фото по URL и возвращает байты."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Download error: {e}")
        return None
