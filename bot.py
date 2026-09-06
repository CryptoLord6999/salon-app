import os
import time
import requests
import json

# --- КОНФИГ ---
TOKEN = "8717717565:AAEwrbJp2OZ9Azt3uoy9fNR6hGZcEJpKL3Y"
WEB_APP_URL = "https://cryptolord6999.github.io/salon-app/"
OWNER_ID = 5209879075  # Твой ID

if not TOKEN or TOKEN == "ВСТАВЬ_СЮДА_СВОЙ_ТОКЕН":
    print("❌ Вставь токен в код!")
    exit()

print(f"✅ БОТ ЗАПУЩЕН. WebApp: {WEB_APP_URL}")

def send_msg(chat_id, text, buttons=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if buttons:
        payload["reply_markup"] = json.dumps(buttons)
    
    try:
        r = requests.post(url, json=payload, timeout=10)
        if not r.json().get("ok"):
            print(f"Ошибка TG: {r.text}")
    except Exception as e:
        print(f"Ошибка сети: {e}")

def get_keyboard():
    return {
        "inline_keyboard": [[{"text": "📱 Записаться онлайн", "web_app": {"url": WEB_APP_URL}}]]
    }

# --- ГЛАВНЫЙ ЦИКЛ ---
last_id = 0
bookings = {} # Хранилище заявок {id: data}
bid_counter = 0

while True:
    try:
        # 1. Получаем обновления
        updates = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/getUpdates",
            params={"offset": last_id + 1, "timeout": 20},
            timeout=25
        ).json()

        if not updates.get("ok"): continue

        for u in updates.get("result", []):
            last_id = u["update_id"]

            # СЦЕНАРИЙ А: Текст от пользователя
            if "message" in u and "text" in u["message"]:
                cid = u["message"]["chat"]["id"]
                txt = u["message"]["text"]
                
                if txt == "/start":
                    send_msg(cid, f"Привет! Я бот салона 'Альфа'.\nНажми кнопку ниже, чтобы записаться:", get_keyboard())
                elif "цена" in txt.lower():
                    send_msg(cid, "💰 Прайс:\n- Стрижка: 1500₽\n- Маникюр: 2000₽")
                else:
                    send_msg(cid, "Нажмите /start или кнопку ниже 👇", get_keyboard())

            # СЦЕНАРИЙ Б: Данные из Web App
            elif "message" in u and "web_app_data" in u["message"]:
                cid = u["message"]["chat"]["id"]
                raw = u["message"]["web_app_data"]["data"]
                print(f"📥 ДАННЫЕ: {raw}")
                
                try:
                    data = json.loads(raw)
                    if data.get("action") != "NEW_BOOKING": continue
                    
                    bid_counter += 1
                    bookings[bid_counter] = {**data, "client_id": cid}
                    
                    # Ответ клиенту
                    send_msg(cid, f"✅ <b>Заявка #{bid_counter} принята!</b>\n\nЖдите подтверждения администратора.")
                    
                    # Уведомление владельцу
                    admin_text = (
                        f"🔥 <b>НОВАЯ ЗАПИСЬ #{bid_counter}</b>\n\n"
                        f"👤 Клиент: {data['name']}\n"
                        f"💇‍♀️ Услуга: {data['service']} ({data['price']}₽)\n"
                        f"⏰ Время: {data['time']}\n\n"
                        f"ID клиента: <code>{cid}</code>"
                    )
                    # Кнопки для владельца
                    kb = {
                        "inline_keyboard": [
                            [{"text": "✅ Подтвердить", "callback_data": f"yes_{bid_counter}"},
                             {"text": "❌ Отмена", "callback_data": f"no_{bid_counter}"}]
                        ]
                    }
                    send_msg(OWNER_ID, admin_text, kb)
                    
                except Exception as e:
                    print(f"Ошибка парсинга: {e}")
                    send_msg(cid, "⚠️ Ошибка сохранения. Попробуйте снова.")

            # СЦЕНАРИЙ В: Нажатие кнопок владельцем
            elif "callback_query" in u:
                cq = u["callback_query"]
                cid = cq["message"]["chat"]["id"]
                mid = cq["message"]["message_id"]
                data = cq["data"]
                
                if "_" in data:
                    action, bid = data.split("_")
                    bid = int(bid)
                    booking = bookings.get(bid)
                    
                    if booking:
                        status = "✅ ПОДТВЕРЖДЕНО" if action == "yes" else "❌ ОТМЕНЕНО"
                        new_text = cq["message"]["text"] + f"\n\nСтатус: {status}"
                        
                        # Редактируем сообщение у владельца
                        requests.post(
                            f"https://api.telegram.org/bot{TOKEN}/editMessageText",
                            json={"chat_id": cid, "message_id": mid, "text": new_text, "parse_mode": "HTML"}
                        )
                        
                        # Пишем клиенту
                        client_msg = f"Ваша запись на {booking['time']} {status}."
                        send_msg(booking["client_id"], client_msg)
                        
                        # Ответ на нажатие кнопки
                        requests.post(
                            f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery",
                            json={"callback_query_id": cq["id"], "text": "Готово"}
                        )

        time.sleep(1)

    except KeyboardInterrupt:
        print("🛑 Стоп")
        break
    except Exception as e:
        print(f"Ошибка цикла: {e}")
        time.sleep(5)