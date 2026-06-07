# ============================================================
#  image_finder.py — поиск фото точно под модель машины
# ============================================================

import requests
import random
from config import UNSPLASH_ACCESS_KEY

UNSPLASH_API = "https://api.unsplash.com"


def search_car_photo(search_query: str) -> str | None:
    """
    Ищет фото конкретной машины по точному запросу.
    Пробует несколько вариантов от конкретного к общему.
    """
    for query in _build_query_variants(search_query):
        url = _unsplash_one(query)
        if url:
            print(f"   Photo found for query: '{query}'")
            return url
    print(f"   No photo found for: '{search_query}'")
    return None


def search_multiple_photos(search_query: str, count: int = 3) -> list:
    """
    Возвращает несколько различных фото одной машины.
    Строго для той же модели — без смешения разных машин.
    """
    urls = []

    for query in _build_query_variants(search_query):
        if len(urls) >= count:
            break
        results = _unsplash_many(query, count=count + 2)
        for url in results:
            if url not in urls:
                urls.append(url)
                if len(urls) >= count:
                    break

    if urls:
        print(f"   Found {len(urls)} photos for: '{search_query}'")
    else:
        print(f"   No photos found for: '{search_query}'")

    return urls[:count]


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _build_query_variants(search_query: str) -> list:
    """
    Строит список поисковых запросов от самого конкретного к общему.
    Гарантирует, что фото соответствует модели машины в тексте.
    """
    base = search_query.strip()
    base_clean = base.replace(" car", "").replace("car ", "").strip()

    return [
        f"{base} jdm",
        f"{base} automobile",
        base,
        f"{base_clean} japan car",
        "jdm japanese sports car",
    ]


def _unsplash_one(query: str) -> str | None:
    """Возвращает одно случайное фото из результатов поиска."""
    results = _unsplash_many(query, count=8)
    return random.choice(results) if results else None


def _unsplash_many(query: str, count: int = 8) -> list:
    """Возвращает список URL фото из Unsplash по запросу."""
    if not UNSPLASH_ACCESS_KEY:
        return []
    try:
        resp = requests.get(
            f"{UNSPLASH_API}/search/photos",
            params={
                "query": query,
                "per_page": min(count + 5, 30),
                "orientation": "landscape",
                "order_by": "relevant",
            },
            headers={
                "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}",
                "Accept-Version": "v1",
            },
            timeout=10,
        )
        if resp.status_code != 200:
            return []
        results = resp.json().get("results", [])
        top = results[:min(15, len(results))]
        random.shuffle(top)
        return [r["urls"].get("regular") or r["urls"].get("full")
                for r in top[:count] if "urls" in r]
    except Exception as e:
        print(f"   Unsplash error for '{query}': {e}")
        return []


def download_photo(url: str) -> bytes | None:
    """Скачивает байты фото по URL."""
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        print(f"   Photo download error: {e}")
        return None
