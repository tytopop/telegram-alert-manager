import asyncio
import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from db.database import DB_PATH
from core.banned_loader import load_banned_list, banned_cache
from core.telegram_client import check_user_subscriptions
from utils.logger import monitor_logger
from dotenv import load_dotenv
import os

load_dotenv()

async def monitor_all_users():
    await load_banned_list()
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, api_id, api_hash, session_data FROM users")
    users = cursor.fetchall()
    conn.close()

    tasks = []
    for user in users:
        user_id, api_id, api_hash, session_data = user
        task = check_user_subscriptions(user_id, api_id, api_hash, session_data, os.getenv("BOT_TOKEN"))
        tasks.append(task)

    await asyncio.gather(*tasks, return_exceptions=True)

async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(monitor_all_users, 'interval', minutes=5)
    scheduler.start()
    monitor_logger.info("Мониторинг запущен (проверка каждые 5 минут)")

    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == '__main__':
    asyncio.run(main())