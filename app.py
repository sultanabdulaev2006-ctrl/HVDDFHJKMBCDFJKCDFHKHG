import threading
import time
import os
import requests
import json
from flask import Flask
import telebot

# -------------------------------
# 🔧 TELEGRAM CONFIG
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
# 🔹 LOGIN (РЕАЛЬНЫЙ)
# -------------------------------
def login(email, password):
    """Login to CPM using Firebase API."""
    print(f"\n🔐 Logging in: {email}")
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
            print("✅ Login successful!")
            return data["idToken"]
        else:
            error_message = data.get("error", {}).get("message", "Unknown error during login.")
            print(f"❌ Login failed: {error_message}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return None

# -------------------------------
# 🔹 SET RANK (ЗАГЛУШКА)
# -------------------------------
def set_rank(token):
    """Set KING RANK using max rating data (stub)."""
    print("👑 Applying rank (stub)...")
    rating_data = {k: 100000 for k in [
        "cars", "car_fix", "car_collided", "car_exchange", "car_trade", "car_wash",
        "slicer_cut", "drift_max", "drift", "cargo", "delivery", "taxi", "levels", "gifts",
        "fuel", "offroad", "speed_banner", "reactions", "police", "run", "real_estate",
        "t_distance", "treasure", "block_post", "push_ups", "burnt_tire", "passanger_distance"
    ]}
    rating_data["time"] = 10000000000
    rating_data["race_win"] = 3000

    payload = {"data": json.dumps({"RatingData": rating_data})}

    # 🔒 SAFE MODE — реальный запрос НЕ отправляется
    print("\n🚫 Stub mode enabled — request NOT sent.")
    print(json.dumps(payload, indent=4))
    print("✅ Rank request simulated safely.\n")
    return True

# -------------------------------
# 🤖 TELEGRAM BOT HANDLERS
# -------------------------------
user_states = {}  # Хранит состояние диалога: "await_email" или "await_password"

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_states[user_id] = "await_email"
    bot.reply_to(message,
                 "👋 Привет!\nЧтобы выполнить Rank King, сначала введи свой email (Gmail):")


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, None)

    if state == "await_email":
        user_states[user_id] = {"email": message.text, "step": "await_password"}
        bot.reply_to(message, "🔒 Отлично! Теперь введи пароль от аккаунта:")
    elif state and isinstance(state, dict) and state.get("step") == "await_password":
        email = state["email"]
        password = message.text
        bot.reply_to(message, "🔐 Выполняю логин...")
        token = login(email, password)
        if not token:
            bot.reply_to(message, "❌ Ошибка входа. Попробуй ещё раз /start")
            user_states.pop(user_id)
            return
        bot.reply_to(message, "👑 Применяю ранг (заглушка)...")
        set_rank(token)
        bot.reply_to(message, "✅ Готово! (симуляция выполнена)")
        user_states.pop(user_id)
    else:
        bot.reply_to(message, "❌ Неизвестная команда. Введи /start для начала.")

# -------------------------------
# ▶️ THREAD FOR TELEGRAM BOT (LONG POLLING)
# -------------------------------
def bot_thread():
    bot.infinity_polling()

# -------------------------------
# 🌐 FLASK APP TO KEEP PROCESS ALIVE
# -------------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

if __name__ == "__main__":
    # Start bot in a separate thread
    t = threading.Thread(target=bot_thread)
    t.start()

    # Start Flask server (Render Web Service keeps process alive)
    app.run(host="0.0.0.0", port=10000)
