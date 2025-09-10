from telethon import TelegramClient
from telethon.tl.types import Channel
from telethon.sessions import StringSession
from utils.crypto import decrypt_session
from utils.logger import monitor_logger

async def check_user_subscriptions(user_id, api_id, api_hash, encrypted_session, bot_token):
    from telegram import Bot
    bot = Bot(token=bot_token)

    session_str = decrypt_session(encrypted_session)
    client = TelegramClient(StringSession(session_str), api_id, api_hash)

    try:
        await client.connect()
        if not await client.is_user_authorized():
            monitor_logger.warning(f"Пользователь {user_id} не авторизован")
            return

        known = set()
        async for dialog in client.iter_dialogs():
            entity = dialog.entity
            if isinstance(entity, Channel) and entity.username:
                username = entity.username.lower()
                if username in banned_cache and username not in known:
                    await bot.send_message(user_id, f"🚨 Подписан на запрещённый канал: @{entity.username}")
                    known.add(username)
                    monitor_logger.info(f"Алерт для {user_id}: @{entity.username}")

    except Exception as e:
        monitor_logger.error(f"Ошибка проверки {user_id}: {e}")
    finally:
        await client.disconnect()