import os
import time
import requests
import json

# --- НАСТРОЙКИ ---
TELEGRAM_TOKEN = "8717717565:AAEkk0Xb1qXRCeXkZIypzpWNTwEva9PsiYg" 
WEB_APP_URL = "https://cryptolord6999.github.io/salon-app/" 
OWNER_ID = 5209879075  # Твой ID (из логов)

if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "ВСТАВЬ_СЮДА_СВОЙ_ТОКЕН":
    print("❌ ОШИБКА: Вставь токен бота в код!")
    exit()

print(f"✅ БОТ ЗАПУЩЕН! Владелец: {OWNER_ID}")
print(f"📱 Web App: {WEB_APP_URL}")

# --- КЛАВИАТУРА МЕНЮ ---
def get_main_keyboard():
    keyboard = {
        "inline_keyboard": [
            [{"text": "📱 Записаться онлайн", "web_app": {"url": WEB_APP_URL}}]
        ]
    }
    return keyboard

def get_admin_keyboard(booking_id):
    # Кнопки для подтверждения записи владельцем
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Подтвердить", "callback_data": f"confirm_{booking_id}"},
                {"text": "❌ Отменить", "callback_data": f"cancel_{booking_id}"}
            ]
        ]
    }
    return keyboard

# --- ЛОГИКА ОТВЕТОВ ---
def get_text_response(text):
    text = text.lower()
    if "цена" in text or "стоит" in text:
        return "💇‍♀️ Прайс:\n- Стрижка: 1500₽\n- Маникюр: 2000₽\n\nНажми кнопку ниже, чтобы записаться!"
    elif "привет" in text or "/start" in text:
        return "Здравствуйте! Я администратор салона 'Альфа'.\nВыберите услугу через приложение:"
    else:
        return "Я пока не понимаю. Нажмите кнопку '📱 Записаться онлайн'."

# --- ОТПРАВКА СООБЩЕНИЙ ---
def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown" # Используем безопасный Markdown
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        data = resp.json()
        if not data.get("ok"):
            print(f"⚠️ Ошибка отправки: {data}")
        return data
    except Exception as e:
        print(f"⚠️ Исключение: {e}")

# --- ЗАПУСК ---
last_update_id = 0
bookings_db = {} # Простая память для хранения заявок (id -> данные)
booking_counter = 0

while True:
    try:
        # 1. Получаем обновления
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        params = {"offset": last_update_id + 1, "timeout": 10}
        resp = requests.get(url, params=params, timeout=15)
        
        if resp.status_code != 200:
            time.sleep(5)
            continue
            
        data = resp.json()
        if not data.get("ok"):
            time.sleep(5)
            continue

        updates = data.get("result", [])
        
        for update in updates:
            last_update_id = update["update_id"]
            
            # --- СЦЕНАРИЙ 1: Обычное текстовое сообщение ---
            if "message" in update and "text" in update["message"]:
                chat_id = update["message"]["chat"]["id"]
                text = update["message"]["text"]
                
                print(f"📩 Текст от {chat_id}: {text}")
                
                # Ответ клиенту
                reply = get_text_response(text)
                keyboard = get_main_keyboard() if "/start" in text or "цена" in text else None
                send_message(chat_id, reply, keyboard)

            # --- СЦЕНАРИЙ 2: Данные из Web App (Запись) ---
            elif "message" in update and "web_app_data" in update["message"]:
                chat_id = update["message"]["chat"]["id"]
                raw_data = update["message"]["web_app_data"]["data"]
                
                print(f"🚀 ДАННЫЕ ИЗ APP: {raw_data}")
                
                try:
                    booking = json.loads(raw_data)
                    name = booking.get('name', 'Аноним')
                    service = booking.get('service', 'Услуга')
                    time_slot = booking.get('time', 'Время')
                    price = booking.get('price', 0)
                    
                    booking_counter += 1
                    bid = booking_counter
                    bookings_db[bid] = booking
                    
                    # 1. Ответ КЛИЕНТУ
                    client_msg = (
                        f"✅ *Заявка принята!*\n\n"
                        f"👤 Имя: {name}\n"
                        f"💇‍♀️ Услуга: {service}\n"
                        f"⏰ Время: {time_slot}\n"
                        f"💰 Цена: {price}₽\n\n"
                        f"Ожидайте подтверждения администратора..."
                    )
                    send_message(chat_id, client_msg)
                    
                    # 2. Уведомление ВЛАДЕЛЬЦУ (тебе)
                    admin_msg = (
                        f"🔥 *НОВАЯ ЗАПИСЬ!* #{bid}\n\n"
                        f"👤 Клиент: {name} (ID: {chat_id})\n"
                        f"💇‍♀️ Услуга: {service}\n"
                        f"⏰ Время: {time_slot}\n"
                        f"💰 Цена: {price}₽\n\n"
                        f"Подтвердите запись:"
                    )
                    send_message(OWNER_ID, admin_msg, get_admin_keyboard(bid))
                    
                except Exception as e:
                    print(f"❌ Ошибка парсинга JSON: {e}")
                    send_message(chat_id, "⚠️ Произошла ошибка при сохранении. Попробуйте еще раз.")

            # --- СЦЕНАРИЙ 3: Нажатие кнопок администратора (Callback) ---
            elif "callback_query" in update:
                call_id = update["callback_query"]["id"]
                chat_id = update["callback_query"]["message"]["chat"]["id"]
                data = update["callback_query"]["data"]
                msg_id = update["callback_query"]["message"]["message_id"]
                
                print(f"🔘 Нажата кнопка: {data}")
                
                if data.startswith("confirm_") or data.startswith("cancel_"):
                    bid = int(data.split("_")[1])
                    booking = bookings_db.get(bid)
                    
                    if booking:
                        is_confirmed = data.startswith("confirm_")
                        status = "ПОДТВЕРЖДЕНА ✅" if is_confirmed else "ОТМЕНЕНА ❌"
                        
                        # Обновляем сообщение админа
                        new_text = f"{update['callback_query']['message']['text']}\n\nСтатус: {status}"
                        
                        # Убираем кнопки у админа
                        requests.post(
                            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/editMessageText",
                            json={"chat_id": chat_id, "message_id": msg_id, "text": new_text, "parse_mode": "Markdown"}
                        )
                        
                        # Сообщаем клиенту
                        client_chat = booking.get('original_chat_id', chat_id) # В реальном проекте надо хранить chat_id клиента
                        # Для теста шлем тебе же, так как original_chat_id не сохраняли в простой версии
                        notify_msg = f"Ваша запись на {booking['time']} {status} администратором!"
                        send_message(chat_id, notify_msg) # Шлем туда, где нажал кнопку (для теста)
                        
                        # Ответ телеграму, что кнопка нажата
                        requests.post(
                            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery",
                            json={"callback_query_id": call_id, "text": "Готово!"}
                        )
                    else:
                         requests.post(
                            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery",
                            json={"callback_query_id": call_id, "text": "Заявка не найдена"}
                        )

        time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Остановка бота...")
        break
    except Exception as e:
        print(f"❌ Глобальная ошибка: {e}")
        time.sleep(5)