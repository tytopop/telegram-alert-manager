import requests
import json
import asyncio
from utils.logger import monitor_logger

BANNED_LIST_URL = "https://gist.githubusercontent.com/tytopop/683d68f776e5dc1011a33aba510cf927/raw/127518932d3de72fc8714c8b472c56c9ae239649/gistfile1.txt"

banned_cache = set()

async def load_banned_list():
    global banned_cache
    try:
        r = requests.get(BANNED_LIST_URL, timeout=10)
        data = r.json()
        banned_cache = set(channel.lower().strip() for channel in data if channel)
        monitor_logger.info(f"Загружено {len(banned_cache)} запрещённых каналов")
    except Exception as e:
        monitor_logger.error(f"Ошибка загрузки списка: {e}")