import os
import time
import requests
import json
from urllib.parse import quote

# --- НАСТРОЙКИ ---
TELEGRAM_TOKEN = "8717717565:AAEkk0Xb1qXRCeXkZIypzpWNTwEva9PsiYg" # Твой токен
WEB_APP_URL = "https://cryptolord6999.github.io/salon-app/" 
OWNER_ID = 5209879075 # Твой ID

# Простая "база данных" в памяти для статистики (для MVP)
# В реальном проекте тут была бы PostgreSQL
leads_db = []
salon_status = "open" # open / closed

def get_keyboard_main():
    """Клавиатура для клиента"""
    keyboard = {
        "inline_keyboard": [
            [{"text": "📱 Записаться онлайн", "web_app": {"url": WEB_APP_URL}}]
        ]
    }
    return keyboard

def get_keyboard_admin():
    """Клавиатура для владельца (Партнерский бот)"""
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "📊 Статистика", "callback_data": "action_stats"},
                {"text": "⚙️ Настройки", "callback_data": "action_settings"}
            ],
            [
                {"text": "📥 Выгрузить лиды", "callback_data": "action_leads"}
            ]
        ]
    }
    return keyboard

def send_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    
    try:
        resp = requests.post(url, json=payload)
        return resp.json()
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        return None

# --- ЛОГИКА БОТА ---
def handle_text(chat_id, text):
    # Если пишет владелец - показываем меню управления
    if chat_id == OWNER_ID:
        if text == "/start":
            msg = (
                f"👋 <b>Привет, Владелец!</b>\n\n"
                f"Это панель управления салоном 'Альфа'.\n"
                f"Статус салона: {'🟢 Открыт' if salon_status == 'open' else '🔴 Закрыт'}\n\n"
                f"Выберите действие:"
            )
            send_message(chat_id, msg, get_keyboard_admin())
            return
        
        # Команды владельца
        if text == "/stats":
            count = len([l for l in leads_db if l.get('status') == 'new'])
            send_message(chat_id, f"📊 <b>Статистика:</b>\nВсего лидов: {len(leads_db)}\nНовых: {count}")
            return
            
    # Если пишет клиент
    else:
        if text == "/start":
            msg = (
                f"Здравствуйте! 👋\n"
                f"Я ИИ-ассистент салона 'Альфа'.\n\n"
                f"Нажмите кнопку ниже, чтобы записаться онлайн за 30 секунд:"
            )
            send_message(chat_id, msg, get_keyboard_main())
            return

def handle_callback(chat_id, data, message_id):
    """Обработка нажатий на кнопки владельца"""
    if data == "action_stats":
        count_new = len([l for l in leads_db if l.get('status') == 'new'])
        count_all = len(leads_db)
        text = f"📊 <b>Статистика салона:</b>\n\nВсего записей: {count_all}\nОжидают подтверждения: {count_new}"
        send_message(chat_id, text)
        
    elif data == "action_settings":
        global salon_status
        salon_status = "closed" if salon_status == "open" else "open"
        status_text = "🟢 Открыт" if salon_status == "open" else "🔴 Закрыт"
        send_message(chat_id, f"⚙️ Статус салона изменен на: {status_text}")
        
    elif data == "action_leads":
        if not leads_db:
            send_message(chat_id, "📭 Лидов пока нет.")
            return
        
        # Формируем краткий отчет
        report = "📥 <b>Последние лиды:</b>\n\n"
        for lead in leads_db[-5:]: # Последние 5
            report += f"▪️ {lead['name']} на {lead['service']} ({lead['time']})\n"
        
        send_message(chat_id, report)

def handle_web_app_data(chat_id, data_str):
    """Обработка данных из TWA"""
    try:
        data = json.loads(data_str)
        if data.get('action') == 'booking':
            name = data.get('name')
            service = data.get('service')
            time_slot = data.get('time')
            price = data.get('price')
            
            # Сохраняем лид
            new_lead = {
                "name": name,
                "service": service,
                "time": time_slot,
                "price": price,
                "status": "new",
                "chat_id": chat_id
            }
            leads_db.append(new_lead)
            
            # Ответ клиенту
            msg_client = (
                f"✅ <b>{name}, вы записаны!</b>\n\n"
                f"💇‍♀️ Услуга: {service}\n"
                f"⏰ Время: {time_slot}\n"
                f"💰 Ориент. цена: {price}₽\n\n"
                f"Мы свяжемся с вами для подтверждения."
            )
            send_message(chat_id, msg_client)
            
            # Уведомление владельцу
            msg_owner = (
                f"🔥 <b>НОВАЯ ЗАПИСЬ!</b>\n\n"
                f"👤 Клиент: {name} (ID: {chat_id})\n"
                f"💇‍♀️ Услуга: {service}\n"
                f"⏰ Время: {time_slot}\n"
                f"💰 Цена: {price}₽\n\n"
                f"<i>Статус: Ожидает подтверждения</i>"
            )
            # Кнопки для владельца под сообщением
            admin_kb = {
                "inline_keyboard": [
                    [
                        {"text": "✅ Подтвердить", "callback_data": f"confirm_{len(leads_db)-1}"},
                        {"text": "❌ Отклонить", "callback_data": f"reject_{len(leads_db)-1}"}
                    ]
                ]
            }
            send_message(OWNER_ID, msg_owner, admin_kb)
            
    except Exception as e:
        print(f"Ошибка парсинга WebApp данных: {e}")
        send_message(chat_id, "⚠️ Произошла ошибка при записи. Попробуйте позже или напишите администратору.")

# --- ЗАПУСК ---
print(f"✅ БОТ ЗАПУЩЕН! Владелец: {OWNER_ID}")
print(f"📱 Web App URL: {WEB_APP_URL}")

URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
last_update_id = 0

while True:
    try:
        params = {"offset": last_update_id + 1, "timeout": 10}
        resp = requests.get(URL, params=params, timeout=15)
        data = resp.json()

        if data.get("ok"):
            updates = data.get("result", [])
            
            for update in updates:
                last_update_id = update["update_id"]
                
                # 1. Текстовые сообщения
                if "message" in update and "text" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    text = update["message"]["text"]
                    print(f"📩 Текст от {chat_id}: {text}")
                    handle_text(chat_id, text)

                # 2. Данные из Web App (внутри сообщения)
                elif "message" in update and "web_app_data" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    data_str = update["message"]["web_app_data"]["data"]
                    print(f"📲 WebApp Data от {chat_id}: {data_str}")
                    handle_web_app_data(chat_id, data_str)

                # 3. Нажатия на кнопки (Callback Query)
                elif "callback_query" in update:
                    query = update["callback_query"]
                    chat_id = query["message"]["chat"]["id"]
                    data = query["data"]
                    msg_id = query["message"]["message_id"]
                    
                    print(f"🔘 Callback от {chat_id}: {data}")
                    
                    # Проверяем, владелец ли жмет кнопку
                    if chat_id == OWNER_ID:
                        handle_callback(chat_id, data, msg_id)
                        # Обязательно подтверждаем получение callback, иначе Telegram будет ругаться
                        req_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery"
                        requests.post(req_url, json={"callback_query_id": query["id"]})
                    else:
                        # Если не владелец жмет кнопки админки (баг или взлом) - игнорируем
                        pass

        time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Остановка бота...")
        break
    except Exception as e:
        print(f"❌ Ошибка цикла: {e}")
        time.sleep(5)
