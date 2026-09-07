import requests
import json
import time

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "8717717565:AAGDVp8ce7TUDFP0oTuMRoNe5NkSQp5DXhM"  # Токен от @BotFather
CHANNEL_ID = "-1003932293179"          # ID твоего канала (начинается с -100)
WEB_APP_URL = "https://cryptolord6999.github.io/salon-app/" # Ссылка на твой GitHub Pages
# =============================================

if BOT_TOKEN == "ВСТАВЬ_СЮДА_СВОЙ_ТОКЕН":
    print("❌ ОШИБКА: Ты не вставил токен бота в код!")
    exit()

print(f"✅ БОТ ЗАПУЩЕН!")
print(f"📡 Канал: {CHANNEL_ID}")
print(f"📱 Web App: {WEB_APP_URL}")
print("Ожидаю сообщения...")

def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if not resp.json().get("ok"):
            print(f"⚠️ Ошибка отправки: {resp.text}")
    except Exception as e:
        print(f"⚠️ Исключение: {e}")

# Клавиатура с кнопкой Web App
keyboard = {
    "inline_keyboard": [
        [{"text": "📱 Записаться онлайн", "web_app": {"url": WEB_APP_URL}}]
    ]
}

last_update_id = 0

while True:
    try:
        # Получаем обновления
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        params = {"offset": last_update_id + 1, "timeout": 10}
        
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code != 200:
            time.sleep(2)
            continue
            
        data = resp.json()
        if not data.get("ok"):
            time.sleep(2)
            continue

        updates = data.get("result", [])
        
        for update in updates:
            last_update_id = update["update_id"]
            
            # --- СЦЕНАРИЙ 1: Команда /start или текст ---
            if "message" in update and "text" in update["message"]:
                chat_id = update["message"]["chat"]["id"]
                text = update["message"]["text"]
                
                print(f"💬 Сообщение от {chat_id}: {text}")
                
                if text == "/start":
                    msg = "👋 Привет! Я автоматизированный администратор салона.\n\nНажми кнопку ниже, чтобы записаться на услугу:"
                    send_message(chat_id, msg, keyboard)
                elif "web_app_data" not in update["message"]:
                    send_message(chat_id, "Пожалуйста, используйте кнопку меню для записи.")

            # --- СЦЕНАРИЙ 2: Данные из Web App (Заявка) ---
            elif "message" in update and "web_app_data" in update["message"]:
                chat_id = update["message"]["chat"]["id"]
                raw_data = update["message"]["web_app_data"]["data"]
                username = update["message"]["from"].get("first_name", "Клиент")
                
                print(f"🔥 ПОЛУЧЕНЫ ДАННЫЕ ИЗ APP: {raw_data}")
                
                try:
                    booking = json.loads(raw_data)
                    
                    channel_text = (
                        f"🔥 <b>НОВАЯ ЗАПИСЬ!</b>\n\n"
                        f"👤 <b>Клиент:</b> {username} (<code>{chat_id}</code>)\n"
                        f"📝 <b>Данные:</b>\n"
                        f"   • Услуга: {booking.get('service')}\n"
                        f"   • Время: {booking.get('time')}\n"
                        f"   • Цена: {booking.get('price')}₽\n"
                        f"   • Имя: {booking.get('name')}\n\n"
                        f"📞 Свяжитесь с клиентом для подтверждения!"
                    )
                    
                    # 1. Отправляем в КАНАЛ
                    send_message(CHANNEL_ID, channel_text)
                    print("✅ Заявка отправлена в канал!")
                    
                    # 2. Отвечаем КЛИЕНТУ в личку
                    send_message(chat_id, "✅ <b>Заявка принята!</b>\nНаш администратор скоро свяжется с вами.")
                    
                except json.JSONDecodeError:
                    print("❌ Ошибка: Неверный формат JSON")
                    send_message(chat_id, "⚠️ Произошла ошибка при обработке. Попробуйте еще раз.")

        time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем.")
        break
    except Exception as e:
        print(f"❌ Глобальная ошибка: {e}")
        time.sleep(5)
