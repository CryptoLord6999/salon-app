import requests
import json
import time

# --- НАСТРОЙКИ ---
TOKEN = "8717717565:AAEwrbJp2OZ9Azt3uoy9fNR6hGZcEJpKL3Y"  # Токен от @BotFather
OWNER_ID = 5209879075  # Твой ID (мы его уже знаем)
WEB_APP_URL = "https://cryptolord6999.github.io/salon-app/"

print(f"🚀 Бот запущен... Ожидаю заявки на {OWNER_ID}")

def send_msg(chat_id, text, buttons=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if buttons:
        data["reply_markup"] = json.dumps(buttons)
    
    r = requests.post(url, json=data)
    if not r.json().get("ok"):
        print(f"❌ Ошибка отправки: {r.text}")
    return r.json()

last_id = 0

while True:
    try:
        # Получаем обновления
        r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", 
                         params={"offset": last_id + 1, "timeout": 10})
        updates = r.json().get("result", [])
        
        for u in updates:
            last_id = u["update_id"]
            
            # 1. Обычное сообщение или /start
            if "message" in u and "text" in u["message"]:
                chat_id = u["message"]["chat"]["id"]
                text = u["message"]["text"]
                
                if text == "/start":
                    kb = {"inline_keyboard": [[{"text": "📱 Записаться онлайн", "web_app": {"url": WEB_APP_URL}}]]}
                    send_msg(chat_id, "👋 Привет! Я бот салона 'Альфа'.\nНажми кнопку ниже, чтобы записаться:", kb)
                else:
                    send_msg(chat_id, "Я пока учусь понимать только команды. Нажми /start")

            # 2. ДАННЫЕ ИЗ WEB APP (САМОЕ ВАЖНОЕ)
            elif "message" in u and "web_app_data" in u["message"]:
                chat_id = u["message"]["chat"]["id"]
                data_str = u["message"]["web_app_data"]["data"]
                
                print(f"✅ ПОЛУЧЕНЫ ДАННЫЕ: {data_str}")
                
                try:
                    data = json.loads(data_str)
                    name = data.get("name")
                    service = data.get("service")
                    time_s = data.get("time")
                    price = data.get("price")
                    
                    # Формируем красивое сообщение для ВЛАДЕЛЬЦА (тебя)
                    admin_text = (
                        f"🔥 <b>НОВАЯ ЗАПИСЬ!</b>\n\n"
                        f"👤 Клиент: {name}\n"
                        f"💇‍♀️ Услуга: {service}\n"
                        f"⏰ Время: {time_s}\n"
                        f"💰 Цена: {price}₽\n"
                        f"🆔 ID клиента: <code>{chat_id}</code>"
                    )
                    
                    # Отправляем ТЕБЕ (OWNER_ID)
                    send_msg(OWNER_ID, admin_text)
                    
                    # Отправляем подтверждение КЛИЕНТУ
                    send_msg(chat_id, f"✅ {name}, ваша заявка принята!\nМы свяжемся с вами для подтверждения записи на {time_s}.")
                    
                except Exception as e:
                    print(f"❌ Ошибка разбора JSON: {e}")
                    send_msg(OWNER_ID, f"⚠️ Ошибка получения данных: {e}\nДанные: {data_str}")

            # 3. Нажатие кнопок (если нужно будет подтверждать)
            elif "callback_query" in u:
                pass # Пока не используем

        time.sleep(1)
        
    except KeyboardInterrupt:
        print("🛑 Остановлено пользователем")
        break
    except Exception as e:
        print(f"⚠️ Общая ошибка: {e}")
        time.sleep(5)