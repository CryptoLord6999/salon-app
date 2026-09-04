import os
import time
import requests
import json

# --- НАСТРОЙКИ ---
TELEGRAM_TOKEN = "8717717565:AAEkk0Xb1qXRCeXkZIypzpWNTwEva9PsiYg" # Вставь свой, если этот тестовый
WEB_APP_URL = "https://cryptolord6999.github.io/salon-app/" 

SIMULATION_MODE = False # Поставил False, так как токен есть

print(f"✅ БОТ ЗАПУЩЕН!")
print(f"📱 Web App: {WEB_APP_URL}")
print("Ожидаю сообщения... (Нажми Ctrl+C для стопа)")

def get_bot_response(user_text):
    text = user_text.lower()
    if "цена" in text or "стоит" in text:
        return "Стрижка — 1500₽, Маникюр — 2000₽. Жми кнопку ниже 👇"
    elif "запиши" in text or "да" in text:
        return "✅ Записал вас на завтра на 14:00!"
    elif "человек" in text or "админ" in text:
        return "🔄 Соединяю с администратором..."
    elif "привет" in text or "/start" in text:
        return "Здравствуйте! Я ИИ-ассистент салона 'Альфа'.\nЧем помочь?\n1️⃣ Цены\n2️⃣ Запись (кнопка ниже)"
    else:
        return "Я пока учусь. Нажмите '📱 Записаться онлайн'!"

def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML" # Разрешаем жирный шрифт и т.д.
    }
    
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)

    try:
        resp = requests.post(url, json=payload, timeout=10)
        data = resp.json()
        
        if data.get("ok"):
            print(f"💬 УСПЕШНО отправлено в {chat_id}")
            return True
        else:
            # Вот тут мы увидим реальную ошибку от Telegram!
            print(f"❌ ОШИБКА TELEGRAM API: {data.get('description')}")
            print(f"   Текст ошибки: {data}")
            return False
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА СОЕДИНЕНИЯ: {e}")
        return False

def get_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📱 Записаться онлайн", "web_app": {"url": WEB_APP_URL}}]
        ]
    }

# --- ГЛАВНЫЙ ЦИКЛ ---
URL_UPDATES = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
last_update_id = 0

while True:
    try:
        # 1. Получаем обновления
        params = {"offset": last_update_id + 1, "timeout": 10}
        resp = requests.get(URL_UPDATES, params=params, timeout=15)
        
        if resp.status_code != 200:
            print(f"⚠️ Не удалось получить обновления. Код: {resp.status_code}")
            time.sleep(2)
            continue
            
        data = resp.json()

        if data.get("ok"):
            updates = data.get("result", [])
            
            for update in updates:
                last_update_id = update["update_id"]
                
                # Обработка текста
                if "message" in update and "text" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    text = update["message"]["text"]
                    
                    print(f"📩 Получено: {text}")
                    
                    bot_reply = get_bot_response(text)
                    keyboard = get_keyboard()
                    
                    # Отправляем с проверкой ошибки
                    send_message(chat_id, bot_reply, keyboard)

                # Обработка данных из Web App
                elif "message" in update and "web_app_data" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    raw_data = update["message"]["web_app_data"]["data"]
                    print(f"📲 ДАННЫЕ ИЗ APP: {raw_data}")
                    
                    try:
                        booking = json.loads(raw_data)
                        msg = f"🔥 <b>НОВАЯ ЗАПИСЬ!</b>\n👤 {booking.get('name')}\n💇‍♀️ {booking.get('service')}\n⏰ {booking.get('time')}"
                        send_message(chat_id, msg)
                        
                        # Себе уведомление (замени ID на свой, если нужно)
                        # send_message(5209879075, f"Лид: {msg}")
                    except Exception as e:
                        print(f"Ошибка парсинга записи: {e}")

        time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Остановка бота...")
        break
    except Exception as e:
        print(f"❌ Глобальная ошибка: {e}")
        time.sleep(5)