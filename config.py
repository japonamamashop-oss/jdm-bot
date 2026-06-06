# ============================================================
#  config.py — все настройки бота
#  Локально: ключи задаются напрямую ниже
#  Railway: ключи берутся из переменных окружения (Variables)
# ============================================================

import os

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8805369476:AAF6lMEPY5WTBU4iheZbA3OUKaduyUEhnFo")
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "@jdm_live")

# --- Groq (для генерации текста) ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")

# --- Unsplash (для фото) ---
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "jugRzWl_QEpoNIs07Q5kINCA4s8nnAYiqXWxrKJpZ10")

# --- Расписание ---
POST_INTERVAL_HOURS = 2                     # постить каждые 2 часа
MULTI_PHOTO_CHANCE = 0.4                    # 40% постов с 3 фотографиями
DAILY_ANALYTICS_HOUR = 22                   # аналитика в 22:00

# --- Примеры постов твоего канала (вставь 2-3 своих поста сюда) ---
EXAMPLE_POSTS = [
    """
    🔥 Nissan Skyline GT-R R34 — легенда, которую не нужно представлять.

    Рядный 6-цилиндровый RB26DETT, 280 л.с. по паспорту (и все знают, что реально больше),
    полный привод ATTESA E-TS, Multi-Link Suspension — инженерный шедевр 90-х.

    Именно этот автомобиль стал символом целого поколения.
    Godzilla жива. 🐉

    #Nissan #SkylineGTR #R34 #JDM #японскиемашины
    """,
    """
    ⚡️ Toyota Supra MK4 — культ, легенда, икона.

    2JZ-GTE под капотом — один из самых надёжных и тюнингуемых моторов в истории.
    Стоковые 320 л.с. легко превращаются в 600+ при минимальных вложениях.

    Неслучайно эта машина стала звездой кино и аниме — она этого заслуживает. 🏌

    #Toyota #Supra #2JZ #JDM #TuningCars
    """,
]

# --- Список JDM машин для генерации постов ---
JDM_CARS = [
    "Nissan Skyline GT-R R32",
    "Nissan Skyline GT-R R33",
    "Nissan Skyline GT-R R34",
    "Toyota Supra MK4 A80",
    "Toyota AE86 Trueno",
    "Honda NSX NA1",
    "Honda Civic EK9 Type R",
    "Honda Integra DC2 Type R",
    "Mazda RX-7 FD3S",
    "Mazda RX-7 FC3S",
    "Mazda MX-5 NA Miata",
    "Subaru Impreza WRX STI GC8",
    "Subaru Impreza WRX STI GDB",
    "Mitsubishi Lancer Evolution VI",
    "Mitsubishi Lancer Evolution IX",
    "Mitsubishi 3000GT VR4",
    "Nissan 180SX",
    "Nissan Silvia S13",
    "Nissan Silvia S14",
    "Nissan Silvia S15",
    "Toyota Chaser JZX100",
    "Toyota Mark II JZX90",
    "Toyota Soarer Z30",
    "Lexus IS300 Altezza",
    "Nissan 300ZX Z32",
    "Mazda Cosmo",
    "Honda S2000 AP1",
    "Acura Integra GSR",
    "Subaru Legacy BH5",
    "Toyota Celica GT-Four ST205",
]
