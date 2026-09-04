import os
import time
import requests
import json
from urllib.parse import quote

# --- НАСТРОЙКИ ---
TELEGRAM_TOKEN = "8717717565:AAEkk0Xb1qXRCeXkZIypzpWNTwEva9PsiYg" 
WEB_APP_URL = "https://cryptolord6999.github.io/salon-app/" 
OWNER_ID = 5209879075  # Твой ID (из логов)

if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "ВСТАВЬ_СЮДА_СВОЙ_ТОКЕН":
    print("❌ ОШИБКА: Вставь токен в код!")
    exit()

print(f"✅ БОТ ЗАПУЩЕН! Владелец: {OWNER_ID}")
print(f"📱 Web App: {WEB_APP_URL}")

# --- КЛАВИАТУРЫ ---
def get_main_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📱 Открыть запись", "web_app": {"url": WEB_APP_URL}}]
        ]
    }

def get_admin_keyboard(booking_id):
    # Кнопки для владельца: Подтвердить / Отменить
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Подтвердить", "callback_data": f"confirm_{booking_id}"},
                {"text": "❌ Отменить", "callback_data": f"cancel_{booking_id}"}
            ]
        ]
    }

def get_owner_menu():
    return {
        "inline_keyboard": [
            [{"text": "📊 Статистика", "callback_data": "stats"}],
            [{"text": "⚙️ Настройки", "callback_data": "settings"}]
        ]
    }

# --- ЛОГИКА ---
def handle_text_message(chat_id, text, message_id=None):
    print(f"📩 Текст от {chat_id}: {text}")

    # 1. Если пишет владелец команды
    if chat_id == OWNER_ID:
        if text == "/start":
            msg = f"👋 Привет, Владелец!\n\nЯ готов к работе.\nНажми кнопку ниже, чтобы открыть панель записи для клиентов."
            send_message(chat_id, msg, reply_markup=json.dumps(get_main_keyboard()))
            # Дополнительно покажем меню владельца
            time.sleep(0.5)
            send_message(chat_id, "🛠 Панель управления:", reply_markup=json.dumps(get_owner_menu()))
            return
        elif text == "/stats":
            send_message(chat_id, "📊 Статистика: Пока 0 записей за сегодня.")
            return
    
    # 2. Обычные клиенты
    if text == "/start":
        msg = "Здравствуйте! 👋\nЯ ИИ-ассистент салона 'Альфа'.\n\nЗаписаться можно за 30 секунд через приложение:"
        send_message(chat_id, msg, reply_markup=json.dumps(get_main_keyboard()))
    else:
        send_message(chat_id, "Чтобы записаться, нажмите кнопку 📱 Открыть запись внизу.")

def handle_web_app_data(chat_id, data_json):
    """Обрабатывает данные, прилетевшие из Web App"""
    print(f"🚀 ДАННЫЕ ИЗ APP: {data_json}")
    
    try:
        data = json.loads(data_json)
        
        if data.get("action") != "booking":
            return

        name = data.get("name", "Аноним")
        service = data.get("service", "Услуга")
        price = data.get("price", 0)
        time_slot = data.get("time", "Время")
        date = data.get("date", "Завтра")
        
        booking_id = str(int(time.time()))[-6:] # Уникальный ID заявки
        
        # Формируем сообщение для ВЛАДЕЛЬЦА
        owner_text = (
            f"🔥 <b>НОВАЯ ЗАПИСЬ #{booking_id}</b>\n\n"
            f"👤 <b>Клиент:</b> {name}\n"
            f"💇‍♀️ <b>Услуга:</b> {service}\n"
            f"💰 <b>Цена:</b> {price}₽\n"
            f"📅 <b>Дата:</b> {date} в {time_slot}\n\n"
            f"Требуется подтверждение!"
        )
        
        # Отправляем владельцу с кнопками
        send_message(OWNER_ID, owner_text, reply_markup=json.dumps(get_admin_keyboard(booking_id)), parse_mode="HTML")
        
        # Формируем сообщение для КЛИЕНТА
        client_text = (
            f"✅ <b>Заявка принята!</b>\n\n"
            f"{name}, вы записаны на <b>{service}</b>.\n"
            f"⏰ Время: {date}, {time_slot}.\n\n"
            f"Администратор скоро подтвердит запись."
        )
        send_message(chat_id, client_text, parse_mode="HTML")
        
        print(f"✅ Заявка #{booking_id} успешно обработана!")

    except Exception as e:
        print(f"❌ Ошибка обработки JSON: {e}")
        send_message(chat_id, "Произошла ошибка при записи. Попробуйте еще раз или напишите администратору.")

def send_message(chat_id, text, reply_markup=None, parse_mode=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code != 200:
            print(f"Ошибка отправки: {resp.text}")
    except Exception as e:
        print(f"Ошибка сети: {e}")

def handle_callback(callback_query_id, chat_id, data):
    """Обработка нажатий на кнопки (Подтвердить/Отменить)"""
    print(f"🔘 Нажата кнопка: {data}")
    
    if data.startswith("confirm_"):
        bid = data.split("_")[1]
        answer = "✅ Запись подтверждена! Мастер ждет клиента."
        edit_message_caption(chat_id, f"Заявка #{bid} подтверждена владельцем.")
        # Тут можно отправить клиенту: "Вас подтвердили!"
        
    elif data.startswith("cancel_"):
        bid = data.split("_")[1]
        answer = "❌ Запись отменена."
        edit_message_caption(chat_id, f"Заявка #{bid} отменена владельцем.")

    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery",
        json={"callback_query_id": callback_query_id, "text": answer}
    )

def edit_message_caption(chat_id, new_text):
    # Простая реализация редактирования последнего сообщения (для примера)
    # В продакшене нужно хранить message_id заявки
    pass 

# --- ГЛАВНЫЙ ЦИКЛ ---
last_update_id = 0
url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"

while True:
    try:
        params = {"offset": last_update_id + 1, "timeout": 10}
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()

        if data.get("ok"):
            updates = data.get("result", [])
            
            for update in updates:
                last_update_id = update["update_id"]
                
                # 1. Текстовые сообщения
                if "message" in update and "text" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    text = update["message"]["text"]
                    handle_text_message(chat_id, text)

                # 2. Данные из Web App
                elif "message" in update and "web_app_data" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    data_json = update["message"]["web_app_data"]["data"]
                    handle_web_app_data(chat_id, data_json)

                # 3. Нажатия на кнопки (Callback)
                elif "callback_query" in update:
                    cb = update["callback_query"]
                    chat_id = cb["message"]["chat"]["id"]
                    data = cb["data"]
                    handle_callback(cb["id"], chat_id, data)

        time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Остановка бота...")
        break
    except Exception as e:
        print(f"❌ Ошибка цикла: {e}")
        time.sleep(5)
