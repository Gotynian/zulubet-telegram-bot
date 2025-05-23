from flask import Flask
import threading
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

app = Flask(__name__)

TOKEN = "7342759206:AAGIxUCxc0_cYgXC8AnKO53kMN3jlS454mA"
CHAT_ID = 293637253

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    response = requests.post(url, data=payload)
    if not response.ok:
        print("Ошибка при отправке в Telegram:", response.text)

def check_matches_and_notify():
    while True:
        try:
            url = "https://www.zulubet.com/"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")

            main_table = soup.select_one("table.content_tables.main_table")

            if not main_table:
                print("Не удалось найти таблицу матчей.")
            else:
                rows = main_table.find_all("tr")[2:]
                messages_to_send = []

                for row in rows:
                    try:
                        cells = row.find_all("td")
                        if len(cells) < 6:
                            continue

                        script_tag = cells[0].find("script")
                        raw_time = script_tag.string.strip().replace("mf_usertime('", "").replace("');", "") if script_tag else "?"

                        try:
                            dt = datetime.strptime(raw_time, "%m/%d/%Y, %H:%M") + timedelta(hours=2)
                            time_str = dt.strftime("%m/%d/%Y, %H:%M")
                        except Exception:
                            time_str = raw_time

                        match = cells[1].find("a").text.strip()

                        prediction_1_text = cells[3].text.strip()
                        prediction_x_text = cells[4].text.strip()
                        prediction_2_text = cells[5].text.strip()

                        def extract_percent(text):
                            return int(text.split(":")[1].replace("%", "").strip())

                        p1 = extract_percent(prediction_1_text)
                        px = extract_percent(prediction_x_text)
                        p2 = extract_percent(prediction_2_text)

                        if p1 >= 65 or px >= 65 or p2 >= 65:
                            line = f"🕰{time_str}  ⚽️ {match}  📈{p1}% - {px}% - {p2}%"
                            messages_to_send.append(line)

                    except Exception as e:
                        print("Ошибка при обработке строки:", e)

                if messages_to_send:
                    full_message = "\n".join(messages_to_send)
                    send_telegram_message(full_message)
                else:
                    print("Нет подходящих матчей для отправки.")
        except Exception as e:
            print("Ошибка в check_matches_and_notify:", e)

        time.sleep(1800)  # Ждём 30 минут

# Запускаем парсер в отдельном потоке, чтобы Flask мог работать
threading.Thread(target=check_matches_and_notify, daemon=True).start()

@app.route("/")
def home():
    return "Бот работает!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
