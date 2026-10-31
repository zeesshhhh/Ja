"""Best-effort Telegram notifications; delivery failures must not stop paper trading."""
import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID


def send(text):
    if not (TELEGRAM_TOKEN and TELEGRAM_CHAT_ID):
        print(text)
        return True
    ok = True
    for i in range(0, len(text), 4000):
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                timeout=20,
                json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": text[i:i + 4000],
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
            )
            response.raise_for_status()
            if not response.json().get("ok", False):
                ok = False
        except (requests.RequestException, ValueError) as exc:
            ok = False
            print("Telegram notification failed:", exc)
    return ok
