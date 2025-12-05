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
    # 🔹 Убираем заглушку, реально отправляем рейтинг
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

def send_welcome(user_id, message=None):
    user_states[user_id] = {"step": "await_email"}
    if message:
        bot.reply_to(message, "👋 Привет! Чтобы выполнить Rank King, сначала введи свой email (Gmail):")
    else:
        bot.send_message(user_id, "👋 Привет! Чтобы выполнить Rank King, сначала введи свой email (Gmail):")

@bot.message_handler(commands=['start'])
def start(message):
    send_welcome(message.from_user.id, message)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    text = message.text.strip()

    if user_id not in user_states:
        send_welcome(user_id, message)
        return

    state = user_states[user_id]

    if state["step"] == "await_email":
        state["email"] = text
        state["step"] = "await_password"
        bot.reply_to(message, "🔒 Отлично! Теперь введи пароль от аккаунта:")
    elif state["step"] == "await_password":
        email = state["email"]
        password = text
        bot.reply_to(message, "🔐 Выполняю логин...")
        token = login(email, password)
        if not token:
            bot.reply_to(message, "❌ Ошибка входа. Попробуй другой аккаунт.")
        else:
            bot.reply_to(message, "👑 Применяю Rank King...")
            success = set_rank(token)
            if success:
                bot.reply_to(message, f"✅ Rank King реально применён на аккаунт {email}!")
            else:
                bot.reply_to(message, "❌ Ошибка при применении ранга.")

        # Сбрасываем состояние, показываем только приветствие для нового аккаунта
        user_states.pop(user_id)
        send_welcome(user_id)

# -------------------------------
# THREAD FOR TELEGRAM BOT (LONG POLLING)
# -------------------------------
def bot_thread():
    bot.infinity_polling()

# -------------------------------
# FLASK APP TO KEEP PROCESS ALIVE
# -------------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

if __name__ == "__main__":
    t = threading.Thread(target=bot_thread)
    t.start()
    app.run(host="0.0.0.0", port=10000)
