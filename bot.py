import os
import time
import requests
import json

# --- НАСТРОЙКИ ---
TELEGRAM_TOKEN = "8717717565:AAEkk0Xb1qXRCeXkZIypzpWNTwEva9PsiYg" 
WEB_APP_URL = "https://cryptolord6999.github.io/salon-app/" 
OWNER_ID = 5209879075  # Твой ID (из логов)

if TELEGRAM_TOKEN == "ВСТАВЬ_СЮДА_СВОЙ_ТОКЕН" or TELEGRAM_TOKEN == "":
    print("⚠️ ОШИБКА: Вставь токен в код!")
    exit()

print(f"✅ БОТ ЗАПУЩЕН! Владелец: {OWNER_ID}")
print(f"📱 Web App: {WEB_APP_URL}")

# --- КЛАВИАТУРА МЕНЮ (ГЛАВНЫЙ ЭКРАН) ---
def get_main_keyboard():
    keyboard = {
        "inline_keyboard": [
            [{"text": "📱 Записаться онлайн", "web_app": {"url": WEB_APP_URL}}],
            [{"text": "📊 Статистика", "callback_data": "stats"}, {"text": "⚙️ Настройки", "callback_data": "settings"}]
        ]
    }
    return keyboard

# --- КЛАВИАТУРА ДЛЯ ВЛАДЕЛЬЦА (ПОДТВЕРЖДЕНИЕ) ---
def get_owner_actions(booking_id):
    keyboard = {
        "inline_keyboard": [
            [{"text": "✅ Подтвердить", "callback_data": f"confirm_{booking_id}"}, 
             {"text": "❌ Отменить", "callback_data": f"cancel_{booking_id}"}]
        ]
    }
    return keyboard

# --- ЛОГИКА ОТВЕТОВ КЛИЕНТУ ---
def get_client_reply(text):
    text = text.lower()
    if "цена" in text or "стоит" in text:
        return "💇‍♀️ Стрижка — 1500₽, Маникюр — 2000₽.\n\nЖми кнопку ниже, чтобы записаться!"
    elif "привет" in text or "/start" in text:
        return "Здравствуйте! Я ИИ-ассистент салона 'Альфа'.\n\nЧем могу помочь?\nВыберите действие ниже:"
    else:
        return "Я пока учусь понимать сложные вопросы. Лучше нажмите кнопку '📱 Записаться онлайн'!"

# --- ЗАПУСК ---
URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
last_update_id = 0

while True:
    try:
        # 1. Получаем обновления
        resp = requests.get(f"{URL}/getUpdates", params={"offset": last_update_id + 1, "timeout": 10}, timeout=15)
        data = resp.json()

        if not data.get("ok"):
            continue

        updates = data.get("result", [])
        
        for update in updates:
            last_update_id = update["update_id"]
            message = update.get("message")
            
            # --- СЦЕНАРИЙ 1: Обычное текстовое сообщение ---
            if message and "text" in message:
                chat_id = message["chat"]["id"]
                text = message["text"]
                
                print(f"📩 Текст от {chat_id}: {text}")
                
                reply = get_client_reply(text)
                
                # Отправляем ответ с главной клавиатурой
                requests.post(f"{URL}/sendMessage", json={
                    "chat_id": chat_id,
                    "text": reply,
                    "reply_markup": json.dumps(get_main_keyboard())
                })

            # --- СЦЕНАРИЙ 2: Данные из Web App (Запись клиента) ---
            elif message and "web_app_data" in message:
                chat_id = message["chat"]["id"]
                raw_data = message["web_app_data"]["data"]
                
                print(f"🚀 ДАННЫЕ ИЗ APP: {raw_data}")
                
                try:
                    booking = json.loads(raw_data)
                    name = booking.get('name', 'Клиент')
                    service = booking.get('service', 'Услуга')
                    price = booking.get('price', 0)
                    time_slot = booking.get('time', 'Время')
                    
                    # Уникальный ID заявки (время в секундах)
                    booking_id = int(time.time())
                    
                    # 1. Сообщение клиенту
                    client_msg = (
                        f"✅ <b>Заявка принята!</b>\n\n"
                        f"👤 {name}, вы записаны на:\n"
                        f"💇‍♀️ {service}\n"
                        f"⏰ {time_slot}\n"
                        f"💰 Цена: {price}₽\n\n"
                        f"Администратор скоро подтвердит запись."
                    )
                    
                    # Отправляем клиенту (без parse_mode, чтобы избежать ошибок, но теги <b> работают в MarkdownV2? Нет, уберем теги для надежности)
                    # Используем простой текст с эмодзи
                    safe_client_msg = f"✅ Заявка принята!\n\n{name}, вы записаны на:\n{service}\nВремя: {time_slot}\nЦена: {price}₽\n\nАдминистратор скоро подтвердит."
                    
                    requests.post(f"{URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": safe_client_msg
                    })

                    # 2. Уведомление владельцу (Тебе)
                    owner_msg = f"🔥 НОВАЯ ЗАПИСЬ! (ID: {booking_id})\n\nКлиент: {name}\nУслуга: {service}\nВремя: {time_slot}\nЦена: {price}₽"
                    
                    req_owner = requests.post(f"{URL}/sendMessage", json={
                        "chat_id": OWNER_ID,
                        "text": owner_msg,
                        "reply_markup": json.dumps(get_owner_actions(booking_id))
                    })
                    
                    if req_owner.ok:
                        print("✅ Уведомление владельцу отправлено")
                    else:
                        print(f"❌ Ошибка владельцу: {req_owner.text}")

                except Exception as e:
                    print(f"❌ Ошибка обработки JSON: {e}")
                    requests.post(f"{URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": "Произошла ошибка при обработке записи. Попробуйте еще раз или напишите администратору."
                    })

            # --- СЦЕНАРИЙ 3: Нажатие кнопок владельцем (Callback) ---
            elif "callback_query" in update:
                callback = update["callback_query"]
                c_chat_id = callback["message"]["chat"]["id"]
                c_msg_id = callback["message"]["message_id"]
                c_data = callback["data"]
                
                print(f"🔘 Callback: {c_data}")
                
                if c_data.startswith("confirm_"):
                    bid = c_data.split("_")[1]
                    # Редактируем сообщение владельца
                    requests.post(f"{URL}/editMessageText", json={
                        "chat_id": c_chat_id,
                        "message_id": c_msg_id,
                        "text": f"✅ Заявка #{bid} ПОДТВЕРЖДЕНА!\nМастер уведомлен.",
                        "reply_markup": None
                    })
                    # Можно отправить сообщение клиенту о подтверждении (нужно хранить chat_id клиента в БД, пока просто лог)
                    print(f"✅ Заявка {bid} подтверждена")

                elif c_data.startswith("cancel_"):
                    bid = c_data.split("_")[1]
                    requests.post(f"{URL}/editMessageText", json={
                        "chat_id": c_chat_id,
                        "message_id": c_msg_id,
                        "text": f"❌ Заявка #{bid} ОТМЕНЕНА.",
                        "reply_markup": None
                    })
                    print(f"❌ Заявка {bid} отменена")
                
                elif c_data == "stats":
                    requests.post(f"{URL}/answerCallbackQuery", json={
                        "callback_query_id": callback["id"],
                        "text": "Статистика: Пока нет данных (v1.0)",
                        "show_alert": True
                    })
                
                elif c_data == "settings":
                    requests.post(f"{URL}/answerCallbackQuery", json={
                        "callback_query_id": callback["id"],
                        "text": "Настройки салона (в разработке)",
                        "show_alert": True
                    })

        time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем.")
        break
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        time.sleep(5)