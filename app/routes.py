from flask import Blueprint, request, render_template, redirect, url_for
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
import asyncio
import json
from dotenv import load_dotenv
from utils.crypto import encrypt_session
from db.database import DB_PATH
from utils.logger import main_logger

load_dotenv()

bp = Blueprint('main', __name__)

def get_db_connection():
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@bp.route('/')
def index():
    return render_template('index.html', bot_name=os.getenv("TELEGRAM_BOT_NAME", "AlertBot"))

@bp.route('/setup', methods=['POST'])
def setup():
    user_id = int(request.form['user_id'])
    api_id = int(request.form['api_id'])
    api_hash = request.form['api_hash']
    phone = request.form['phone']

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    client = TelegramClient(StringSession(), api_id, api_hash)
    loop.run_until_complete(client.connect())

    if not loop.run_until_complete(client.is_user_authorized()):
        loop.run_until_complete(client.send_code_request(phone))
        return render_template('verify.html', user_id=user_id, api_id=api_id, api_hash=api_hash, phone=phone)

    session_str = client.session.save()
    encrypted_session = encrypt_session(session_str)

    conn = get_db_connection()
    conn.execute(
        "INSERT OR REPLACE INTO users (user_id, api_id, api_hash, session_data, phone) VALUES (?, ?, ?, ?, ?)",
        (user_id, api_id, api_hash, encrypted_session, phone)
    )
    conn.commit()
    conn.close()

    from telegram import Bot
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    try:
        bot.send_message(user_id, "✅ Ваш аккаунт подключён к системе мониторинга!")
    except Exception as e:
        main_logger.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

    return render_template('success.html')

@bp.route('/verify', methods=['POST'])
def verify():
    user_id = int(request.form['user_id'])
    api_id = int(request.form['api_id'])
    api_hash = request.form['api_hash']
    phone = request.form['phone']
    code = request.form['code']
    password = request.form.get('password', None)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    client = TelegramClient(StringSession(), api_id, api_hash)
    loop.run_until_complete(client.connect())

    try:
        if password:
            loop.run_until_complete(client.sign_in(phone=phone, code=code, password=password))
        else:
            loop.run_until_complete(client.sign_in(phone=phone, code=code))

        session_str = client.session.save()
        encrypted_session = encrypt_session(session_str)

        conn = get_db_connection()
        conn.execute(
            "INSERT OR REPLACE INTO users (user_id, api_id, api_hash, session_data, phone) VALUES (?, ?, ?, ?, ?)",
            (user_id, api_id, api_hash, encrypted_session, phone)
        )
        conn.commit()
        conn.close()

        from telegram import Bot
        bot = Bot(token=os.getenv("BOT_TOKEN"))
        bot.send_message(user_id, "✅ Ваш аккаунт подключён к системе мониторинга!")

        return render_template('success.html')

    except SessionPasswordNeededError:
        return render_template('password.html', user_id=user_id, api_id=api_hash, phone=phone, code=code)
    except Exception as e:
        main_logger.error(f"Ошибка входа для {user_id}: {e}")
        return f"<h2>❌ Ошибка: {str(e)}</h2>"

@bp.route('/delete', methods=['GET', 'POST'])
def delete():
    if request.method == 'POST':
        user_id = int(request.form['user_id'])
        conn = get_db_connection()
        conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return "<h2>✅ Ваш аккаунт удалён из системы.</h2>"
    return render_template('delete.html')