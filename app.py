import threading
import time
import requests
import json
from flask import Flask
import telebot

# -------------------------------
# 🔧 TELEGRAM CONFIG
# -------------------------------
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"  # Вставь сюда токен своего бота
bot = telebot.TeleBot(BOT_TOKEN)

# --- Game Service Configuration ---
FIREBASE_API_KEY = 'AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM'
FIREBASE_LOGIN_URL = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={FIREBASE_API_KEY}"
RANK_URL = "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating4"


def login(email, password):
    """Login imitation (stub mode still prepares token)."""
    print(f"🔐 Logging in: {email}")
    time.sleep(0.5)
    fake_token = "FAKE_TOKEN_12345"
    print("✅ Login successful! (stub mode)")
    return fake_token


def set_rank(token):
    """Rank King function with safe stub."""
    print("👑 Applying rank...")
    rating_data = {k: 100000 for k in [
        "cars", "car_fix", "car_collided", "car_exchange", "car_trade", "car_wash",
        "slicer_cut", "drift_max", "drift", "cargo", "delivery", "taxi", "levels", "gifts",
        "fuel", "offroad", "speed_banner", "reactions", "police", "run", "real_estate",
        "t_distance", "treasure", "block_post", "push_ups", "burnt_tire", "passanger_distance"
    ]}
    rating_data["time"] = 10000000000
    rating_data["race_win"] = 3000

    payload = {"data": json.dumps({"RatingData": rating_data})}

    # -----------------------------
    # 🔒 ЗАГЛУШКА (Safe Stub Mode)
    # -----------------------------
    print("\n🚫 Stub mode enabled — request NOT sent.")
    print(json.dumps(payload, indent=4))
    print("✅ Rank request simulated safely.\n")
    return True


# -------------------------------
# 🤖 TELEGRAM BOT HANDLERS
# -------------------------------

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message,
                 "👋 Привет!\nИспользуй команду:\n"
                 "`/rank email пароль`\n\n"
                 "Скрипт выполнит вход и симулирует применение ранга.",
                 parse_mode="Markdown")


@bot.message_handler(commands=['rank'])
def rank_command(message):
    try:
        parts = message.text.split()
        if len(parts) != 3:
            bot.reply_to(message, "❌ Формат: `/rank email пароль`", parse_mode="Markdown")
            return

        email = parts[1]
        password = parts[2]

        bot.reply_to(message, "🔐 Выполняю логин...")

        token = login(email, password)

        if not token:
            bot.reply_to(message, "❌ Ошибка входа.")
            return

        bot.reply_to(message, "👑 Применяю ранг (заглушка)...")

        result = set_rank(token)

        if result:
            bot.reply_to(message, "✅ Готово! (симуляция выполнена)")
        else:
            bot.reply_to(message, "❌ Ошибка при выполнении.")

    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {e}")


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
