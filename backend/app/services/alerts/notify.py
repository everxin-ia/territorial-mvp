import os
import requests

def send_webhook(payload: dict) -> None:
    url = os.getenv("ALERT_WEBHOOK_URL", "").strip()
    if not url:
        return
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception:
        # MVP: swallow
        pass
