import os
import time
import requests
import json

# --- НАСТРОЙКИ ---
TOKEN = "8717717565:AAEwrbJp2OZ9Azt3uoy9fNR6hGZcEJpKL3Y"
WEB_APP_URL = "https://cryptolord6999.github.io/salon-app/" # Ссылка на твой client-app
OWNER_ID = 5209879075  # Твой ID (куда придут заявки)

if TOKEN == "ВСТАВЬ_СЮДА_ТОКЕН_БОТА":
    print("❌ Вставь токен в код!")
    exit()

print(f"✅ Бот-оператор запущен. Ожидание лидов...")

def send_msg(chat_id, text, buttons=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if buttons:
        payload["reply_markup"] = json.dumps(buttons)
    try:
        r = requests.post(url, json=payload)
        return r.json()
    except Exception as e:
        print(f"Error: {e}")

def get_keyboard():
    return {
        "inline_keyboard": [[
            {"text": "📝 Записаться онлайн", "web_app": {"url": WEB_APP_URL}}
        ]]
    }

last_id = 0

while True:
    try:
        # Получаем обновления
        r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", 
                         params={"offset": last_id + 1, "timeout": 10})
        data = r.json()
        
        if not data.get("ok"): continue

        for update in data.get("result", []):
            last_id = update["update_id"]

            # 1. Команда /start от владельца или клиента
            if "message" in update and "text" in update["message"]:
                chat_id = update["message"]["chat"]["id"]
                text = update["message"]["text"]
                
                if text == "/start":
                    msg = "👋 Привет! Я бот-администратор салона.\n\n"
                    if chat_id == OWNER_ID:
                        msg += "🔐 <b>Панель владельца:</b>\nЗаявки будут приходить сюда.\nНажми кнопку ниже, чтобы протестировать форму."
                    else:
                        msg += "Запишитесь на услугу прямо сейчас!"
                    
                    send_msg(chat_id, msg, get_keyboard())

            # 2. Получение данных из Web App (ЛИД!)
            elif "message" in update and "web_app_data" in update["message"]:
                chat_id = update["message"]["chat"]["id"]
                raw_data = update["message"]["web_app_data"]["data"]
                
                try:
                    lead = json.loads(raw_data)
                    
                    if lead.get("type") == "NEW_LEAD":
                        # Формируем красивое сообщение для ВЛАДЕЛЬЦА
                        msg = (
                            f"🔥 <b>НОВАЯ ЗАЯВКА!</b>\n\n"
                            f"👤 <b>Клиент:</b> {lead['name']}\n"
                            f"📞 <b>Телефон:</b> {lead['phone']}\n"
                            f"💇‍♀️ <b>Услуга:</b> {lead['service']}\n"
                            f"⏰ <b>Время:</b> {lead['datetime']}\n"
                            f"🆔 <b>ID в TG:</b> {chat_id}\n"
                            f"👤 <b>Username:</b> @{lead['username']}"
                        )
                        
                        # Кнопки действий для владельца
                        keyboard = {
                            "inline_keyboard": [
                                [{"text": "✅ Подтвердить", "callback_data": f"ok_{chat_id}"},
                                 {"text": "❌ Отклонить", "callback_data": f"no_{chat_id}"}],
                                [{"text": "✍️ Написать клиенту", "user_select": {"query": ""}}] # В будущем можно улучшить
                            ]
                        }
                        
                        # Отправляем уведомление ВЛАДЕЛЬЦУ (OWNER_ID)
                        send_msg(OWNER_ID, msg, keyboard)
                        
                        # (Опционально) Можно отправить подтверждение и клиенту, если нужно
                        # send_msg(chat_id, "✅ Ваша заявка принята! Ждите звонка.")
                        
                        print(f"✅ Лид получен от {lead['name']}")

                except Exception as e:
                    print(f"Ошибка парсинга лида: {e}")

            # 3. Обработка кнопок владельца (Подтвердить/Отклонить)
            elif "callback_query" in update:
                call_id = update["callback_query"]["id"]
                chat_id = update["callback_query"]["message"]["chat"]["id"]
                data = update["callback_query"]["data"]
                msg_id = update["callback_query"]["message"]["message_id"]

                if data.startswith("ok_") or data.startswith("no_"):
                    client_chat_id = int(data.split("_")[1])
                    status = "ПОДТВЕРЖДЕНА ✅" if data.startswith("ok_") else "ОТКЛОНЕНА ❌"
                    
                    # Редактируем сообщение у владельца
                    new_text = update["callback_query"]["message"]["text"] + f"\n\nСтатус: {status}"
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/editMessageText",
                                  json={"chat_id": chat_id, "message_id": msg_id, "text": new_text, "parse_mode": "HTML"})
                    
                    # Пишем клиенту
                    reply_text = f"Здравствуйте! Ваша заявка {status}. Мы скоро свяжемся с вами."
                    send_msg(client_chat_id, reply_text)
                    
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery",
                                  json={"callback_query_id": call_id})

        time.sleep(1)
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(5)