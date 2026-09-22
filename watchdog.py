"""
"כלב שמירה" על תקינות הצנרת עצמה - נפרד לגמרי מ-main.py, עם תזמון משלו
(ראה .github/workflows/watchdog.yml), כדי שגם אם main.py נשבר לגמרי (למשל
yfinance משנה API, או כל תקלה אחרת) עדיין תגיע התראה שמשהו לא בסדר.
בכוונה לא מייבא yfinance/price_alerts - כדי שתקלה שם לא תפיל גם את הבודק הזה.
"""

import os
from datetime import datetime, timezone

import requests

import config
import notify

API_BASE = "https://api.github.com"
STALE_THRESHOLD_HOURS = 3  # אם אין הרצה מוצלחת של update.yml בפרק הזמן הזה - מתריעים
ALERT_COOLDOWN_HOURS = 12  # לא שולחים שוב אם כבר התרענו לאחרונה והבעיה עדיין נמשכת
LAST_WATCHDOG_ALERT_FILE = f"{config.DATA_DIR}/last_watchdog_alert.txt"
UPDATE_WORKFLOW_FILE = "update.yml"


def _repo_and_token():
    repo = os.environ.get("GITHUB_REPOSITORY") or config.GITHUB_REPO
    token = os.environ.get("GITHUB_TOKEN")
    return repo, token


def _headers(token):
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}


def get_last_successful_update_time(repo, token):
    """מחזיר את זמן הסיום (UTC) של ההרצה המוצלחת האחרונה של update.yml, או None אם אין אף אחת."""
    url = f"{API_BASE}/repos/{repo}/actions/workflows/{UPDATE_WORKFLOW_FILE}/runs"
    params = {"status": "success", "per_page": 1}
    resp = requests.get(url, headers=_headers(token), params=params, timeout=15)
    resp.raise_for_status()
    runs = resp.json().get("workflow_runs", [])
    if not runs:
        return None
    finished_at = runs[0]["updated_at"]  # ISO 8601 UTC, למשל "2026-09-22T17:20:29Z"
    return datetime.fromisoformat(finished_at.replace("Z", "+00:00"))


def check_watchdog():
    repo, token = _repo_and_token()
    if not token:
        return  # הרצה מקומית - אין GITHUB_TOKEN, מדלגים בשקט

    last_success = get_last_successful_update_time(repo, token)
    now = datetime.now(timezone.utc)
    if last_success is not None:
        hours_since = (now - last_success).total_seconds() / 3600
        if hours_since < STALE_THRESHOLD_HOURS:
            print(f"תקין - ההרצה המוצלחת האחרונה הייתה לפני {hours_since:.1f} שעות.")
            return

    last_alert = None
    if os.path.isfile(LAST_WATCHDOG_ALERT_FILE):
        with open(LAST_WATCHDOG_ALERT_FILE, encoding="utf-8") as f:
            try:
                last_alert = datetime.fromisoformat(f.read().strip())
            except ValueError:
                last_alert = None
    if last_alert is not None and (now - last_alert).total_seconds() / 3600 < ALERT_COOLDOWN_HOURS:
        print("הבעיה כבר דווחה לאחרונה - שומרים על cooldown, לא שולחים שוב.")
        return

    if last_success is not None:
        body = (
            f"לא זוהתה הרצה מוצלחת של עדכון הדשבורד ב-{STALE_THRESHOLD_HOURS} השעות האחרונות.\n"
            f"ההרצה המוצלחת האחרונה הייתה ב-{last_success.strftime('%Y-%m-%d %H:%M UTC')}.\n\n"
            f"כדאי לבדוק את ה-Actions בריפו: https://github.com/{repo}/actions"
        )
    else:
        body = (
            "לא נמצאה אף הרצה מוצלחת של עדכון הדשבורד עד כה.\n\n"
            f"כדאי לבדוק את ה-Actions בריפו: https://github.com/{repo}/actions"
        )
    notify.send_email("⚠️ שי פיננס - הדשבורד לא מתעדכן", body)
    print("נשלחה התראת watchdog.")

    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(LAST_WATCHDOG_ALERT_FILE, "w", encoding="utf-8") as f:
        f.write(now.isoformat())


if __name__ == "__main__":
    check_watchdog()
