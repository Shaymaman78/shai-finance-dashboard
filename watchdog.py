"""
"כלב שמירה" על תקינות הצנרת עצמה - נפרד לגמרי מ-main.py, עם תזמון משלו
(ראה .github/workflows/watchdog.yml), כדי שגם אם main.py נשבר לגמרי (למשל
yfinance משנה API, או כל תקלה אחרת) עדיין תגיע התראה שמשהו לא בסדר.
בכוונה לא מייבא yfinance/price_alerts - כדי שתקלה שם לא תפיל גם את הבודק הזה.

בודק שתי שכבות נפרדות שכל אחת יכולה להישבר בלי שהשנייה תבחין בזה:
1. שה-workflow שמעדכן את הנתונים (update.yml) באמת רץ בהצלחה לאחרונה.
2. שה-Pages Deployment (הפרסום של index.html לאתר החי) באמת הצליח לאחרונה -
   גם אם update.yml מצליח מושלם, פריסת Pages היא תהליך נפרד שיכול להיכשל
   בפני עצמו (מכסה, שגיאת build וכו') בלי שאף בדיקה אחרת תבחין בזה.
"""

import os
from datetime import datetime, timezone

import requests

import config
import notify

API_BASE = "https://api.github.com"
STALE_THRESHOLD_HOURS = 3  # אם אין הרצה/פריסה מוצלחת בפרק הזמן הזה - מתריעים
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


def get_pages_build_status(repo, token):
    """מחזיר מידע על בניית ה-GitHub Pages האחרונה, או None אם השליפה עצמה נכשלה."""
    url = f"{API_BASE}/repos/{repo}/pages/builds/latest"
    resp = requests.get(url, headers=_headers(token), timeout=15)
    if resp.status_code != 200:
        return None
    data = resp.json()
    return {
        "status": data.get("status"),
        "error": (data.get("error") or {}).get("message"),
        "updated_at": datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")),
    }


def check_watchdog():
    repo, token = _repo_and_token()
    if not token:
        return  # הרצה מקומית - אין GITHUB_TOKEN, מדלגים בשקט

    now = datetime.now(timezone.utc)
    problems = []

    last_success = get_last_successful_update_time(repo, token)
    if last_success is None:
        problems.append("לא נמצאה אף הרצה מוצלחת של עדכון הדשבורד עד כה.")
    else:
        hours_since = (now - last_success).total_seconds() / 3600
        if hours_since >= STALE_THRESHOLD_HOURS:
            problems.append(
                f"עדכון הדשבורד (update.yml) לא רץ בהצלחה ב-{hours_since:.1f} השעות האחרונות "
                f"(הרצה מוצלחת אחרונה: {last_success.strftime('%Y-%m-%d %H:%M UTC')})."
            )

    pages_info = get_pages_build_status(repo, token)
    if pages_info is None:
        problems.append("לא ניתן היה לבדוק את סטטוס פריסת GitHub Pages.")
    else:
        if pages_info["status"] == "errored":
            problems.append(f"פריסת GitHub Pages (האתר החי) נכשלה: {pages_info['error']}")
        else:
            pages_hours_since = (now - pages_info["updated_at"]).total_seconds() / 3600
            if pages_hours_since >= STALE_THRESHOLD_HOURS:
                problems.append(
                    f"פריסת GitHub Pages (האתר החי) לא התעדכנה ב-{pages_hours_since:.1f} השעות האחרונות."
                )

    if not problems:
        print("תקין - גם update.yml וגם פריסת Pages עדכניים.")
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

    body = "זוהו הבעיות הבאות בצנרת האוטומטית:\n\n" + "\n".join(f"- {p}" for p in problems)
    body += f"\n\nכדאי לבדוק את ה-Actions בריפו: https://github.com/{repo}/actions"
    notify.send_email("⚠️ שי פיננס - הדשבורד לא מתעדכן", body)
    print("נשלחה התראת watchdog.")

    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(LAST_WATCHDOG_ALERT_FILE, "w", encoding="utf-8") as f:
        f.write(now.isoformat())


if __name__ == "__main__":
    check_watchdog()
