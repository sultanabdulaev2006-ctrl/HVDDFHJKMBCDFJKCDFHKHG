import threading
import os
import requests
import json
from flask import Flask
import telebot

# -------------------------------
# TELEGRAM CONFIG
# -------------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не задан! Проверьте переменные окружения на Render.")

bot = telebot.TeleBot(BOT_TOKEN)

# --- Game Service Configuration ---
FIREBASE_API_KEY = 'AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM'
FIREBASE_LOGIN_URL = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={FIREBASE_API_KEY}"
RANK_URL = "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating4"

# -------------------------------
# LOGIN FUNCTION
# -------------------------------
def login(email, password):
    payload = {
        "clientType": "CLIENT_TYPE_ANDROID",
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    headers = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12)",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(FIREBASE_LOGIN_URL, headers=headers, json=payload)
        data = response.json()
        if response.status_code == 200 and "idToken" in data:
            return data["idToken"]
        else:
            return None
    except:
        return None

# -------------------------------
# SET RANK FUNCTION (РЕАЛЬНО)
# -------------------------------
def set_rank(token):
    rating_data = {k: 100000 for k in [
        "cars", "car_fix", "car_collided", "car_exchange", "car_trade", "car_wash",
        "slicer_cut", "drift_max", "drift", "cargo", "delivery", "taxi", "levels", "gifts",
        "fuel", "offroad", "speed_banner", "reactions", "police", "run", "real_estate",
        "t_distance", "treasure", "block_post", "push_ups", "burnt_tire", "passanger_distance"
    ]}
    rating_data["time"] = 10000000000
    rating_data["race_win"] = 3000

    payload = {"data": json.dumps({"RatingData": rating_data})}
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "okhttp/3.12.13"
    }

    response = requests.post(RANK_URL, headers=headers, json=payload)
    return response.status_code == 200

# -------------------------------
# TELEGRAM BOT HANDLERS
# -------------------------------
user_states = {}  # Хранит текущее состояние каждого пользователя

def send_welcome(user_id):
    """Отправляем приветствие для нового или повторного аккаунта"""
    user_states[user_id] = {"step": "await_email"}
    bot.send_message(user_id, "📧 Введи gmail")

@bot.message_handler(commands=['start'])
def start(message):
    send_welcome(message.from_user.id)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    text = message.text.strip()
    chat_id = message.chat.id

    if user_id not in user_states:
        send_welcome(user_id)
        return

    state = user_states[user_id]

    if state["step"] == "await_email":
        state["email"] = text
        state["step"] = "await_password"
        msg = bot.reply_to(message, "🔒 Введи пароль")
        state["last_msg_ids"] = [message.message_id, msg.message_id]

    elif state["step"] == "await_password":
        email = state["email"]
        password = text
        messages_to_delete = state.get("last_msg_ids", [])
        messages_to_delete.append(message.message_id)

        msg_login = bot.reply_to(message, "🔐 Выполняю логин...")
        messages_to_delete.append(msg_login.message_id)

        token = login(email, password)
        if not token:
            msg_error = bot.reply_to(message, "❌ Ошибка входа. Попробуй другой аккаунт.")
            messages_to_delete.append(msg_error.message_id)
        else:
            msg_rank = bot.reply_to(message, "👑 Rang устанавливается...")
            messages_to_delete.append(msg_rank.message_id)

            success = set_rank(token)
            if success:
                msg_done = bot.reply_to(message, f"✅ RANG установлен!")
            else:
                msg_done = bot.reply_to(message, "❌ Ошибка при установке.")
            messages_to_delete.append(msg_done.message_id)

        # Сбрасываем состояние пользователя
        user_states.pop(user_id)

        # Через 2 секунды удаляем все сообщения и оставляем только приветствие
        def cleanup():
            for msg_id in messages_to_delete:
                try:
                    bot.delete_message(chat_id, msg_id)
                except:
                    pass
            send_welcome(user_id)

        threading.Timer(2.0, cleanup).start()  # удаляем через 2 секунды

# -------------------------------
# THREAD FOR TELEGRAM BOT (LONG POLLING)
# -------------------------------
def bot_thread():
    bot.infinity_polling()

# ------------------------
