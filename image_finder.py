# ============================================================
#  image_finder.py — поиск фото точно под модель машины
#  ВАЖНО: никогда не возвращает generic fallback-фото.
#         Лучше None (текстовый пост), чем фото другой машины.
# ============================================================

import requests
import random
from config import UNSPLASH_ACCESS_KEY

UNSPLASH_API = "https://api.unsplash.com"

# Кураторские запросы для каждой JDM машины из JDM_CARS.
# Несколько вариантов от самого точного к менее точному.
# Если ни один не даёт результат — возвращаем None.
_CAR_PHOTO_QUERIES = {
    "Nissan Skyline GT-R R32": ["nissan skyline r32 gtr", "nissan skyline r32", "nissan gtr r32"],
    "Nissan Skyline GT-R R33": ["nissan skyline r33 gtr", "nissan skyline r33", "nissan gtr r33"],
    "Nissan Skyline GT-R R34": ["nissan skyline r34 gtr", "nissan r34 gtr", "nissan skyline r34"],
    "Toyota Supra MK4 A80": ["toyota supra mk4", "toyota supra a80", "toyota supra 2jz"],
    "Toyota AE86 Trueno": ["toyota ae86 trueno", "toyota corolla ae86", "ae86 drift"],
    "Honda NSX NA1": ["honda nsx na1", "honda nsx sports car", "acura nsx"],
    "Honda Civic EK9 Type R": ["honda civic type r ek9", "honda civic type r", "honda civic ek"],
    "Honda Integra DC2 Type R": ["honda integra type r dc2", "honda integra type r", "acura integra type r"],
    "Mazda RX-7 FD3S": ["mazda rx7 fd3s", "mazda rx-7 fd", "mazda rx7 rotary"],
    "Mazda RX-7 FC3S": ["mazda rx7 fc3s", "mazda rx-7 fc", "mazda rx7"],
    "Mazda MX-5 NA Miata": ["mazda miata na", "mazda mx5 na roadster", "mazda miata roadster"],
    "Subaru Impreza WRX STI GC8": ["subaru impreza wrx sti gc8", "subaru impreza gc8", "subaru wrx sti rally"],
    "Subaru Impreza WRX STI GDB": ["subaru impreza wrx sti gdb", "subaru impreza sti blue", "subaru wrx sti"],
    "Mitsubishi Lancer Evolution VI": ["mitsubishi lancer evolution vi", "mitsubishi evo 6", "mitsubishi lancer evo"],
    "Mitsubishi Lancer Evolution IX": ["mitsubishi lancer evolution ix", "mitsubishi evo 9", "mitsubishi lancer evo"],
    "Mitsubishi 3000GT VR4": ["mitsubishi 3000gt vr4", "mitsubishi 3000gt twin turbo", "mitsubishi gto"],
    "Nissan 180SX": ["nissan 180sx jdm", "nissan 180sx drift", "nissan 180sx"],
    "Nissan Silvia S13": ["nissan silvia s13", "nissan 240sx s13", "nissan silvia drift"],
    "Nissan Silvia S14": ["nissan silvia s14", "nissan 200sx s14", "nissan silvia"],
    "Nissan Silvia S15": ["nissan silvia s15", "nissan 200sx s15", "nissan silvia s15 drift"],
    "Toyota Chaser JZX100": ["toyota chaser jzx100", "toyota chaser 1jz", "toyota chaser"],
    "Toyota Mark II JZX90": ["toyota mark ii jzx90", "toyota markii jzx", "toyota mark2"],
    "Toyota Soarer Z30": ["toyota soarer z30", "toyota soarer", "lexus sc300 jdm"],
    "Lexus IS300 Altezza": ["toyota altezza is300", "lexus is300", "toyota altezza"],
    "Nissan 300ZX Z32": ["nissan 300zx z32", "nissan 300zx fairlady z", "nissan 300zx"],
    "Mazda Cosmo": ["mazda cosmo rotary", "mazda cosmo sport", "mazda cosmo"],
    "Honda S2000 AP1": ["honda s2000 ap1", "honda s2000 roadster", "honda s2000"],
    "Acura Integra GSR": ["acura integra gsr", "honda integra gsr", "acura integra"],
    "Subaru Legacy BH5": ["subaru legacy gt turbo", "subaru legacy wagon gt", "subaru legacy"],
    "Toyota Celica GT-Four ST205": ["toyota celica gt-four st205", "toyota celica gt4", "toyota celica"],
}


def search_car_photo(car_name_or_query: str) -> str | None:
    """
    Ищет фото конкретной машины.
    Сначала пробует кураторские запросы, затем авто-варианты.
    Возвращает None если конкретная машина не найдена — никакого generic fallback.
    """
    # 1. Кураторские запросы (самые точные)
    curated = _CAR_PHOTO_QUERIES.get(car_name_or_query, [])
    for query in curated:
        url = _unsplash_one(query)
        if url:
            print(f"   Photo found (curated): '{query}'")
            return url

    # 2. Авто-варианты из имени машины (без generic fallback)
    base = car_name_or_query.strip()
    parts = base.split()
    auto_variants = [base]
    if len(parts) >= 3:
        auto_variants.append(f"{parts[0]} {parts[1]}")

    for query in auto_variants:
        url = _unsplash_one(query)
        if url:
            print(f"   Photo found (auto): '{query}'")
            return url

    print(f"   No specific photo found for: '{car_name_or_query}'")
    return None  # НЕ возвращаем generic — лучше текстовый пост


def search_multiple_photos(car_name_or_query: str, count: int = 3) -> list:
    """
    Возвращает несколько фото одной машины (для медиагруппы).
    Строго той же модели — никакого fallback на другую машину.
    """
    urls = []

    curated = _CAR_PHOTO_QUERIES.get(car_name_or_query, [])
    for query in curated:
        if len(urls) >= count:
            break
        results = _unsplash_many(query, count=count + 3)
        for url in results:
            if url not in urls:
                urls.append(url)
            if len(urls) >= count:
                break

    if len(urls) < count:
        base = car_name_or_query.strip()
        parts = base.split()
        if len(parts) >= 3:
            fallback_q = f"{parts[0]} {parts[1]}"
            for url in _unsplash_many(fallback_q, count=count + 3):
                if url not in urls:
                    urls.append(url)
                if len(urls) >= count:
                    break

    result = urls[:count]
    if result:
        print(f"   Found {len(result)} photos for: '{car_name_or_query}'")
    else:
        print(f"   No photos found for: '{car_name_or_query}'")
    return result


# ─── Internal helpers ─────────────────────────────────────────────────────────

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
