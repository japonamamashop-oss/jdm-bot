# ============================================================
#  image_finder.py — поиск фото точно под модель машины
#
#  Стратегия:
#  1. Wikipedia API — статья про конкретную машину, фото ВСЕГДА верное
#  2. Unsplash — кураторские запросы, красивые фото
#  3. None — лучше текстовый пост, чем фото другой машины
# ============================================================

import requests
import random
from config import UNSPLASH_ACCESS_KEY

UNSPLASH_API = "https://api.unsplash.com"
WIKI_API = "https://en.wikipedia.org/w/api.php"

# Wikipedia маппинг — точные названия статей для каждой машины из JDM_CARS.
_WIKI_TITLES = {
    "Nissan Skyline GT-R R32":        "Nissan Skyline GT-R",
    "Nissan Skyline GT-R R33":        "Nissan Skyline GT-R",
    "Nissan Skyline GT-R R34":        "Nissan Skyline GT-R",
    "Toyota Supra MK4 A80":           "Toyota Supra",
    "Toyota AE86 Trueno":             "Toyota AE86",
    "Honda NSX NA1":                  "Honda NSX",
    "Honda Civic EK9 Type R":         "Honda Civic Type R",
    "Honda Integra DC2 Type R":       "Honda Integra",
    "Mazda RX-7 FD3S":                "Mazda RX-7",
    "Mazda RX-7 FC3S":                "Mazda RX-7",
    "Mazda MX-5 NA Miata":            "Mazda MX-5 (NA)",
    "Subaru Impreza WRX STI GC8":     "Subaru Impreza",
    "Subaru Impreza WRX STI GDB":     "Subaru Impreza WRX STI",
    "Mitsubishi Lancer Evolution VI":  "Mitsubishi Lancer Evolution",
    "Mitsubishi Lancer Evolution IX":  "Mitsubishi Lancer Evolution",
    "Mitsubishi 3000GT VR4":          "Mitsubishi 3000GT",
    "Nissan 180SX":                   "Nissan 180SX",
    "Nissan Silvia S13":              "Nissan Silvia",
    "Nissan Silvia S14":              "Nissan Silvia",
    "Nissan Silvia S15":              "Nissan Silvia",
    "Toyota Chaser JZX100":           "Toyota Chaser",
    "Toyota Mark II JZX90":           "Toyota Mark II",
    "Toyota Soarer Z30":              "Toyota Soarer",
    "Lexus IS300 Altezza":            "Lexus IS",
    "Nissan 300ZX Z32":               "Nissan 300ZX",
    "Mazda Cosmo":                    "Mazda Cosmo",
    "Honda S2000 AP1":                "Honda S2000",
    "Acura Integra GSR":              "Honda Integra",
    "Subaru Legacy BH5":              "Subaru Legacy (third generation)",
    "Toyota Celica GT-Four ST205":    "Toyota Celica",
}

# Unsplash кураторские запросы (запасной вариант)
_UNSPLASH_QUERIES = {
    "Nissan Skyline GT-R R32": ["nissan skyline r32 gtr", "nissan skyline r32"],
    "Nissan Skyline GT-R R33": ["nissan skyline r33 gtr", "nissan skyline r33"],
    "Nissan Skyline GT-R R34": ["nissan skyline r34 gtr", "nissan r34 gtr"],
    "Toyota Supra MK4 A80":    ["toyota supra mk4", "toyota supra a80"],
    "Toyota AE86 Trueno":      ["toyota ae86 trueno", "toyota corolla ae86"],
    "Honda NSX NA1":           ["honda nsx na1", "honda nsx sports"],
    "Honda Civic EK9 Type R":  ["honda civic type r ek9", "honda civic type r"],
    "Honda Integra DC2 Type R":["honda integra type r dc2", "honda integra type r"],
    "Mazda RX-7 FD3S":         ["mazda rx7 fd3s", "mazda rx-7 fd"],
    "Mazda RX-7 FC3S":         ["mazda rx7 fc3s", "mazda rx-7"],
    "Mazda MX-5 NA Miata":     ["mazda miata na", "mazda mx5 roadster"],
    "Subaru Impreza WRX STI GC8": ["subaru impreza gc8", "subaru wrx sti rally"],
    "Subaru Impreza WRX STI GDB": ["subaru impreza wrx sti", "subaru sti blue"],
    "Mitsubishi Lancer Evolution VI": ["mitsubishi evo 6", "mitsubishi lancer evo"],
    "Mitsubishi Lancer Evolution IX": ["mitsubishi evo 9", "mitsubishi lancer evo ix"],
    "Mitsubishi 3000GT VR4":   ["mitsubishi 3000gt vr4", "mitsubishi 3000gt"],
    "Nissan 180SX":            ["nissan 180sx jdm", "nissan 180sx drift"],
    "Nissan Silvia S13":       ["nissan silvia s13", "nissan 240sx s13"],
    "Nissan Silvia S14":       ["nissan silvia s14", "nissan 200sx s14"],
    "Nissan Silvia S15":       ["nissan silvia s15", "nissan 200sx s15"],
    "Toyota Chaser JZX100":    ["toyota chaser jzx100", "toyota chaser"],
    "Toyota Mark II JZX90":    ["toyota mark ii jzx90", "toyota markii"],
    "Toyota Soarer Z30":       ["toyota soarer z30", "toyota soarer"],
    "Lexus IS300 Altezza":     ["toyota altezza is300", "lexus is300"],
    "Nissan 300ZX Z32":        ["nissan 300zx z32", "nissan 300zx"],
    "Mazda Cosmo":             ["mazda cosmo rotary", "mazda cosmo"],
    "Honda S2000 AP1":         ["honda s2000 ap1", "honda s2000"],
    "Acura Integra GSR":       ["acura integra gsr", "honda integra gsr"],
    "Subaru Legacy BH5":       ["subaru legacy gt turbo", "subaru legacy"],
    "Toyota Celica GT-Four ST205": ["toyota celica gt-four", "toyota celica"],
}


def search_car_photo(car_name: str) -> str | None:
    """
    Ищет фото конкретной машины.
    1. Wikipedia — фото ВСЕГДА правильной машины
    2. Unsplash  — красивые фото, как запасной вариант
    3. None      — если ничего не найдено
    """
    # 1. Wikipedia (гарантированно правильная машина)
    wiki_title = _WIKI_TITLES.get(car_name)
    if wiki_title:
        url = _wikipedia_photo(wiki_title)
        if url:
            print(f"   Photo found (Wikipedia): '{wiki_title}'")
            return url

    # 2. Unsplash кураторские запросы
    for query in _UNSPLASH_QUERIES.get(car_name, []):
        url = _unsplash_one(query)
        if url:
            print(f"   Photo found (Unsplash): '{query}'")
            return url

    print(f"   No photo found for: '{car_name}'")
    return None


def search_multiple_photos(car_name: str, count: int = 3) -> list:
    """
    Возвращает несколько фото одной машины.
    Wikipedia даёт 1 фото, остальные добираем из Unsplash.
    """
    urls = []

    # 1. Wikipedia как первое фото
    wiki_title = _WIKI_TITLES.get(car_name)
    if wiki_title:
        wiki_url = _wikipedia_photo(wiki_title)
        if wiki_url:
            urls.append(wiki_url)

    # 2. Дополняем из Unsplash
    for query in _UNSPLASH_QUERIES.get(car_name, []):
        if len(urls) >= count:
            break
        results = _unsplash_many(query, count=count + 3)
        for u in results:
            if u not in urls:
                urls.append(u)
            if len(urls) >= count:
                break

    result = urls[:count]
    if result:
        print(f"   Found {len(result)} photos for: '{car_name}'")
    else:
        print(f"   No photos found for: '{car_name}'")
    return result


# ── Wikipedia ──────────────────────────────────────────────────────────────────

def _wikipedia_photo(article_title: str, width: int = 960) -> str | None:
    """Возвращает thumbnail из Wikipedia статьи."""
    try:
        resp = requests.get(
            WIKI_API,
            params={
                "action": "query",
                "titles": article_title,
                "prop": "pageimages",
                "piprop": "thumbnail",
                "pithumbsize": width,
                "format": "json",
            },
            timeout=8,
        )
        if resp.status_code != 200:
            return None
        pages = resp.json().get("query", {}).get("pages", {})
        for page in pages.values():
            src = page.get("thumbnail", {}).get("source")
            if src:
                return src
    except Exception as e:
        print(f"   Wikipedia error for '{article_title}': {e}")
    return None


# ── Unsplash ───────────────────────────────────────────────────────────────────

def _unsplash_one(query: str) -> str | None:
    results = _unsplash_many(query, count=8)
    return random.choice(results) if results else None


def _unsplash_many(query: str, count: int = 8) -> list:
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
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        print(f"   Photo download error: {e}")
        return None
