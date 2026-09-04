import os
import time
import requests
import json
from urllib.parse import quote

# --- НАСТРОЙКИ ---
TELEGRAM_TOKEN = "8717717565:AAEkk0Xb1qXRCeXkZIypzpWNTwEva9PsiYg" 
# Сюда вставим ссылку на приложение после Шага 2 (пока оставь пустым или заглушкой)
WEB_APP_URL = "https://your-username.github.io/salon-app/" 

SIMULATION_MODE = TELEGRAM_TOKEN == "ВСТАВЬ_СЮДА_СВОЙ_ТОКЕН" or TELEGRAM_TOKEN == ""

if SIMULATION_MODE:
    print("⚠️ РЕЖИМ СИМУЛЯЦИИ (Нет токена)")
else:
    print(f"✅ БОТ ЗАПУЩЕН! Токен: {TELEGRAM_TOKEN[:10]}...")
    print(f"📱 Web App URL: {WEB_APP_URL}")
    print("Ожидаю сообщения...")

# --- ЛОГИКА ОТВЕТОВ ---
def get_bot_response(user_text):
    text = user_text.lower()
    if "цена" in text or "стоит" in text:
        return "Стрижка — 1500₽, Маникюр — 2000₽. Удобнее записаться через приложение? 👇"
    elif "запиши" in text or "да" in text:
        return "✅ Отлично! Записал вас на завтра на 14:00. Мастер ждет!"
    elif "человек" in text or "админ" in text:
        return "🔄 Соединяю с администратором... Он напишет вам через минуту."
    elif "привет" in text or "/start" in text:
        return "Здравствуйте! Я ИИ-ассистент салона 'Альфа'.\n\nЧем могу помочь?\n1️⃣ Узнать цены\n2️⃣ Записаться онлайн (кнопка ниже)"
    else:
        return "Я пока учусь. Попробуйте нажать кнопку '📱 Записаться онлайн' ниже!"

# --- КЛАВИАТУРА С WEB APP ---
def get_keyboard():
    # Кнопка, открывающая веб-приложение
    keyboard = {
        "inline_keyboard": [
            [{"text": "📱 Записаться онлайн", "web_app": {"url": WEB_APP_URL}}]
        ]
    }
    return keyboard

# --- ЗАПУСК ---
if SIMULATION_MODE:
    while True:
        try:
            user_input = input("👤 Клиент: ")
            if not user_input: continue
            response = get_bot_response(user_input)
            print(f"🤖 Бот: {response}\n")
        except KeyboardInterrupt: break
else:
    URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    last_update_id = 0
    
    # Отправляем приветствие при старте (опционально)
    # Можно отправить себе тестовое сообщение с кнопкой
    
    while True:
        try:
            params = {"offset": last_update_id + 1, "timeout": 10}
            resp = requests.get(URL, params=params, timeout=15)
            data = resp.json()

            if data.get("ok"):
                updates = data.get("result", [])
                
                for update in updates:
                    last_update_id = update["update_id"]
                    
                    # 1. Обработка обычного текста
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"]
                        
                        print(f"📩 Текст от {chat_id}: {text}")
                        
                        bot_reply = get_bot_response(text)
                        
                        # Отвечаем с кнопкой Web App
                        send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                        payload = {
                            "chat_id": chat_id, 
                            "text": bot_reply,
                            "reply_markup": json.dumps(get_keyboard())
                        }
                        requests.post(send_url, json=payload)
                        print(f"💬 Ответ: {bot_reply}")

                    # 2. Обработка данных из Web App (когда клиент записался в приложении)
                    elif "callback_query" in update:
                        # Это если будем использовать обычные кнопки (не Web App data)
                        pass
                    
                    # 3. Обработка данных, присланных из Web App (data)
                    # Telegram присылает это как message с полем web_app_data
                    elif "message" in update and "web_app_data" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        data_payload = update["message"]["web_app_data"]["data"]
                        
                        print(f"📲 ДАННЫЕ ИЗ ПРИЛОЖЕНИЯ: {data_payload}")
                        
                        # Парсим данные (ожидаем JSON: {"service": "...", "time": "..."} )
                        try:
                            booking = json.loads(data_payload)
                            service = booking.get('service', 'Услуга')
                            time_slot = booking.get('time', 'Время')
                            name = booking.get('name', 'Клиент')
                            
                            msg = f"🔥 <b>НОВАЯ ЗАПИСЬ!</b>\n\n👤 Клиент: {name}\n💇‍♀️ Услуга: {service}\n⏰ Время: {time_slot}\n\n✅ Менеджер свяжется для подтверждения."
                            
                            send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                            requests.post(send_url, json={
                                "chat_id": chat_id, 
                                "text": msg, 
                                "parse_mode": "HTML"
                            })
                            
                            # Уведомление владельцу (тебе)
                            OWNER_ID = 5209879075 # Твой ID из логов
                            owner_msg = f"⚡️ <b>ГОРЯЧИЙ ЛИД ИЗ APP</b>\n{name} записался на {service} ({time_slot})"
                            requests.post(send_url, json={
                                "chat_id": OWNER_ID, 
                                "text": owner_msg, 
                                "parse_mode": "HTML"
                            })
                            
                        except Exception as e:
                            print(f"Ошибка парсинга: {e}")

            time.sleep(1)

        except KeyboardInterrupt:
            print("\nОстановка...")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            time.sleep(5)