import os
import time
import requests
import json

# --- НАСТРОЙКИ ---
TELEGRAM_TOKEN = "8717717565:AAEwrbJp2OZ9Azt3uoy9fNR6hGZcEJpKL3Y" 
WEB_APP_URL = "https://cryptolord6999.github.io/salon-app/" 

# !!! ВСТАВЬ СЮДА ID КАНАЛА (с -100 в начале) !!!
# Пример: CHANNEL_ID = "-1001234567890"
CHANNEL_ID = "-1003932293179" 

if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "ВСТАВЬ_СЮДА_СВОЙ_ТОКЕН":
    print("❌ ОШИБКА: Вставь токен бота в код!")
    exit()
if CHANNEL_ID == "ВСТАВЬ_СЮДА_ID_КАНАЛА":
    print("⚠️ ПРЕДУПРЕЖДЕНИЕ: Ты не вставил ID канала. Заявки придут только тебе в ЛС.")
    # Для теста продублируем заявки тебе в ЛС, если канал не настроен
    USE_CHANNEL = False
else:
    USE_CHANNEL = True

print(f"✅ БОТ ЗАПУЩЕН!")
print(f"📱 Web App: {WEB_APP_URL}")
if USE_CHANNEL:
    print(f"📢 Канал заявок: {CHANNEL_ID}")
else:
    print("📢 Режим тестирования: заявки приходят в ЛС создателю.")

# --- КЛАВИАТУРА ---
def get_main_keyboard():
    return {
        "inline_keyboard": [[{"text": "📱 Записаться онлайн", "web_app": {"url": WEB_APP_URL}}]]
    }

def get_admin_keyboard(booking_id):
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Подтвердить", "callback_data": f"confirm_{booking_id}"},
                {"text": "❌ Отменить", "callback_data": f"cancel_{booking_id}"}
            ]
        ]
    }

# --- ФУНКЦИИ ОТПРАВКИ ---
def send_message(chat_id, text, reply_markup=None, parse_mode="Markdown"):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        data = resp.json()
        if not data.get("ok"):
            print(f"⚠️ Ошибка TG API: {data.get('description')}")
        return data
    except Exception as e:
        print(f"⚠️ Ошибка сети: {e}")

# --- ГЛАВНЫЙ ЦИКЛ ---
last_update_id = 0
bookings_db = {} # Храним данные о заявках в памяти
booking_counter = 0

# Получим ID владельца (первое сообщение от тебя), чтобы дублировать уведомления
OWNER_ID = None 

while True:
    try:
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
            
            # Сохраняем ID владельца (кто первый написал /start)
            if OWNER_ID is None and "message" in update and "from_user" in update["message"]:
                if update["message"]["from_user"]["is_bot"] == False:
                    OWNER_ID = update["message"]["from_user"]["id"]
                    print(f"👤 Владелец определен: {OWNER_ID}")

            # 1. ОБЫЧНОЕ СООБЩЕНИЕ (Старт, Цены)
            if "message" in update and "text" in update["message"]:
                chat_id = update["message"]["chat"]["id"]
                text = update["message"]["text"]
                
                if "/start" in text:
                    send_message(chat_id, "👋 Привет! Я бот салона 'Альфа'.\nЗапишись онлайн за 1 минуту:", get_main_keyboard())
                elif "цена" in text.lower():
                    send_message(chat_id, "💰 Прайс:\n- Стрижка: 1500₽\n- Маникюр: 2000₽\n\nЖду вас!", get_main_keyboard())
                else:
                    # Игнорируем другие сообщения или можно добавить заглушку
                    pass

            # 2. ДАННЫЕ ИЗ WEB APP (НОВАЯ ЗАЯВКА)
            elif "message" in update and "web_app_data" in update["message"]:
                chat_id = update["message"]["chat"]["id"] # ID клиента
                raw_data = update["message"]["web_app_data"]["data"]
                
                print(f"🚀 ПОЛУЧЕНЫ ДАННЫЕ: {raw_data}")
                
                try:
                    booking = json.loads(raw_data)
                    name = booking.get('name', 'Аноним')
                    service = booking.get('service', 'Услуга')
                    time_slot = booking.get('time', 'Время')
                    price = booking.get('price', 0)
                    
                    booking_counter += 1
                    bid = booking_counter
                    # Сохраняем ID чата клиента, чтобы потом написать ему
                    bookings_db[bid] = {**booking, "client_chat_id": chat_id}
                    
                    # Формируем сообщение для КАНАЛА (или владельца)
                    target_chat = CHANNEL_ID if USE_CHANNEL else OWNER_ID
                    
                    msg_text = (
                        f"🔥 <b>НОВАЯ ЗАЯВКА #{bid}</b>\n\n"
                        f"👤 <b>Клиент:</b> {name}\n"
                        f"💇‍♀️ <b>Услуга:</b> {service}\n"
                        f"⏰ <b>Время:</b> {time_slot}\n"
                        f"💰 <b>Цена:</b> {price}₽\n\n"
                        f"ID клиента: <code>{chat_id}</code>"
                    )
                    
                    # Отправляем в канал с кнопками управления
                    response = send_message(target_chat, msg_text, get_admin_keyboard(bid), parse_mode="HTML")
                    
                    if response and response.get("ok"):
                        # Сообщаем клиенту, что заявка ушла
                        send_message(chat_id, f"✅ <b>{name}</b>, ваша заявка принята!\n\nМы скоро подтвердим запись в канале.", parse_mode="HTML")
                    else:
                        send_message(chat_id, "⚠️ Ошибка отправки. Попробуйте позже.", parse_mode="HTML")

                except Exception as e:
                    print(f"❌ Ошибка обработки JSON: {e}")
                    send_message(chat_id, "⚠️ Произошла ошибка. Перезагрузите приложение.")

            # 3. НАЖАТИЕ КНОПОК АДМИНА (Подтверждение/Отмена)
            elif "callback_query" in update:
                call_id = update["callback_query"]["id"]
                chat_id = update["callback_query"]["message"]["chat"]["id"]
                msg_id = update["callback_query"]["message"]["message_id"]
                data = update["callback_query"]["data"]
                
                print(f"🔘 Кнопка нажата: {data}")
                
                if data.startswith("confirm_") or data.startswith("cancel_"):
                    bid = int(data.split("_")[1])
                    booking = bookings_db.get(bid)
                    
                    if booking:
                        is_confirmed = data.startswith("confirm_")
                        status_emoji = "✅" if is_confirmed else "❌"
                        status_text = "ПОДТВЕРЖДЕНА" if is_confirmed else "ОТМЕНЕНА"
                        
                        # 1. Редактируем сообщение в канале (убираем кнопки, пишем статус)
                        new_text = (
                            f"{update['callback_query']['message']['text']}\n\n"
                            f"🛎 <b>СТАТУС: {status_text} {status_emoji}</b>"
                        )
                        
                        edit_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/editMessageText"
                        requests.post(edit_url, json={
                            "chat_id": chat_id,
                            "message_id": msg_id,
                            "text": new_text,
                            "parse_mode": "HTML"
                        })
                        
                        # 2. Пишем клиенту в ЛС
                        client_chat = booking.get("client_chat_id")
                        if client_chat:
                            notify_text = (
                                f"{status_emoji} <b>Ваша запись {status_text}!</b>\n\n"
                                f"Ждем вас {booking.get('time')} на услугу '{booking.get('service')}'."
                            )
                            send_message(client_chat, notify_text, parse_mode="HTML")
                        
                        # Ответ телеграму на нажатие кнопки
                        requests.post(
                            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery",
                            json={"callback_query_id": call_id, "text": "Готово!"}
                        )
                    else:
                         requests.post(
                            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery",
                            json={"callback_query_id": call_id, "text": "Заявка не найдена (истекла)"}
                        )

        time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Остановка...")
        break
    except Exception as e:
        print(f"❌ Глобальная ошибка: {e}")
        time.sleep(5)