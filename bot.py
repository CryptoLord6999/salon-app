import os
import time
import requests
import json
from datetime import datetime

# --- НАСТРОЙКИ ---
TELEGRAM_TOKEN = "8717717565:AAEkk0Xb1qXRCeXkZIypzpWNTwEva9PsiYg" 
WEB_APP_URL = "https://cryptolord6999.github.io/salon-app/" 
OWNER_ID = 5209879075  # Твой ID (из логов)

# Простая "база данных" в памяти для статистики (для MVP)
stats = {
    "total_leads": 0,
    "bookings_today": 0,
    "revenue_potential": 0
}

if TELEGRAM_TOKEN == "ВСТАВЬ_СЮДА_СВОЙ_ТОКЕН" or TELEGRAM_TOKEN == "":
    print("⚠️ РЕЖИМ СИМУЛЯЦИИ")
    SIMULATION_MODE = True
else:
    SIMULATION_MODE = False
    print(f"✅ БОТ ЗАПУЩЕН! Владелец: {OWNER_ID}")

# --- ФУНКЦИИ ОТВЕТОВ ---
def get_bot_response(text):
    text = text.lower()
    if "цена" in text or "стоит" in text:
        return "💰 Прайс:\n• Стрижка — 1500₽\n• Маникюр — 2000₽\n\nНажмите кнопку ниже, чтобы записаться онлайн!"
    elif "запиши" in text or "да" in text:
        return "📅 Выберите удобное время в приложении по кнопке ниже 👇"
    elif "привет" in text or "/start" in text:
        return f"Здравствуйте! Я ассистент салона 'Альфа'.\n\nМы работаем ежедневно с 10:00 до 22:00.\n\n✍️ Записаться можно через приложение:"
    else:
        return "Я пока учусь. Воспользуйтесь меню или кнопкой 'Записаться онлайн'."

# --- КЛАВИАТУРЫ ---
def get_main_keyboard():
    # Кнопка Web App + Кнопка для владельца (скрытая логика)
    keyboard = {
        "inline_keyboard": [
            [{"text": "📱 Записаться онлайн", "web_app": {"url": WEB_APP_URL}}]
        ]
    }
    return keyboard

def get_owner_actions_keyboard(booking_data):
    # Кнопки подтверждения для владельца
    callback_data = json.dumps({"action": "confirm_booking", "data": booking_data})
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Подтвердить", "callback_data": callback_data},
                {"text": "❌ Отклонить", "callback_data": json.dumps({"action": "reject"})}
            ],
            [{"text": "📞 Позвонить клиенту", "url": "tel:+79990000000"}] # Заглушка
        ]
    }
    return keyboard

def get_admin_menu_keyboard():
    keyboard = {
        "inline_keyboard": [
            [{"text": "📊 Статистика", "callback_data": "get_stats"}],
            [{"text": "⚙️ Настройки салона", "callback_data": "settings"}]
        ]
    }
    return keyboard

# --- ОТПРАВКА СООБЩЕНИЙ ---
def send_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
    if SIMULATION_MODE:
        print(f"[MSG to {chat_id}]: {text}")
        return
    
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
        return resp.json()
    except Exception as e:
        print(f"Error sending message: {e}")

# --- ОБРАБОТКА ДЕЙСТВИЙ ВЛАДЕЛЬЦА ---
def handle_callback(query_id, chat_id, data):
    try:
        action_data = json.loads(data)
        action = action_data.get("action")

        if action == "get_stats":
            msg = f"📊 <b>Статистика салона</b>\n\n"
            msg += f"Всего лидов: {stats['total_leads']}\n"
            msg += f"Записей сегодня: {stats['bookings_today']}\n"
            msg += f"Потенциал выручки: {stats['revenue_potential']}₽"
            send_message(chat_id, msg)
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery", json={"callback_query_id": query_id})

        elif action == "confirm_booking":
            booking = action_data.get("data", {})
            client_name = booking.get("name", "Клиент")
            
            # Тут можно добавить логику сохранения в БД
            msg = f"✅ <b>Заявка подтверждена!</b>\nМастер уведомлен.\nКлиент: {client_name}"
            send_message(chat_id, msg)
            
            # Уведомление клиенту (если бы мы знали его chat_id, но пока просто лог)
            print(f"Бронь подтверждена для {client_name}")
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery", json={"callback_query_id": query_id, "text": "Подтверждено!"})

        elif action == "reject":
            send_message(chat_id, "❌ Заявка отклонена.")
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery", json={"callback_query_id": query_id, "text": "Отклонено"})
            
        elif action == "settings":
            send_message(chat_id, "⚙️ <b>Настройки</b>\n\nЗдесь можно открыть/закрыть салон.\n(Функция в разработке)")
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery", json={"callback_query_id": query_id})

    except Exception as e:
        print(f"Callback error: {e}")

# --- ГЛАВНЫЙ ЦИКЛ ---
if SIMULATION_MODE:
    print("Запустите симуляцию ввода данных...")
else:
    URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    last_update_id = 0
    
    # Отправляем приветствие владельцу при старте (опционально)
    # send_message(OWNER_ID, "🤖 Бот-партнер запущен и готов к работе!", get_admin_menu_keyboard())

    while True:
        try:
            params = {"offset": last_update_id + 1, "timeout": 10}
            resp = requests.get(URL, params=params, timeout=15)
            data = resp.json()

            if data.get("ok"):
                updates = data.get("result", [])
                
                for update in updates:
                    last_update_id = update["update_id"]
                    
                    # 1. Обычные сообщения
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"]
                        
                        print(f"📩 От {chat_id}: {text}")
                        
                        # Если пишет владелец - даем меню
                        if chat_id == OWNER_ID and text == "/start":
                            send_message(chat_id, "👋 <b>Панель управления салоном</b>\nВыберите действие:", get_admin_menu_keyboard())
                        else:
                            # Обычный ответ клиенту
                            reply = get_bot_response(text)
                            send_message(chat_id, reply, get_main_keyboard())

                    # 2. Данные из Web App (Запись)
                    elif "message" in update and "web_app_data" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        raw_data = update["message"]["web_app_data"]["data"]
                        
                        print(f"📲 NEW BOOKING: {raw_data}")
                        
                        try:
                            booking = json.loads(raw_data)
                            name = booking.get('name', 'Аноним')
                            service = booking.get('service', 'Услуга')
                            time_slot = booking.get('time', 'Время')
                            price = booking.get('price', 0)
                            
                            # Обновляем статистику
                            stats["total_leads"] += 1
                            stats["bookings_today"] += 1
                            stats["revenue_potential"] += int(price)
                            
                            # Формируем карточку для владельца
                            owner_text = f"🔥 <b>НОВАЯ ЗАПИСЬ!</b>\n\n"
                            owner_text += f"👤 Клиент: {name}\n"
                            owner_text += f"💇‍♀️ Услуга: {service}\n"
                            owner_text += f"⏰ Время: {time_slot}\n"
                            owner_text += f"💰 Цена: {price}₽\n\n"
                            owner_text += f"ID клиента: <code>{chat_id}</code>"
                            
                            # Отправляем владельцу с кнопками действий
                            send_message(OWNER_ID, owner_text, get_owner_actions_keyboard(booking))
                            
                            # Ответ клиенту
                            send_message(chat_id, f"✅ <b>{name}</b>, ваша заявка принята!\nОжидайте подтверждения от администратора.", parse_mode="HTML")
                            
                        except Exception as e:
                            print(f"Ошибка парсинга брони: {e}")
                            send_message(chat_id, "⚠️ Произошла ошибка при записи. Попробуйте позже.")

                    # 3. Нажатия кнопок (Callback Query)
                    elif "callback_query" in update:
                        query = update["callback_query"]
                        q_id = query["id"]
                        q_chat_id = query["message"]["chat"]["id"]
                        q_data = query["data"]
                        
                        print(f"🔘 Callback: {q_data}")
                        handle_callback(q_id, q_chat_id, q_data)

            time.sleep(1)

        except KeyboardInterrupt:
            print("\nОстановка...")
            break
        except Exception as e:
            print(f"Global Error: {e}")
            time.sleep(5)
