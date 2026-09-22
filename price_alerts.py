"""
התראות מחיר לפי דרישה - לא רק המניות בתיק. המשתמש פותח Issue ב-GitHub
(טופס מוכן, מקושר מהדשבורד) עם טיקר, מחיר יעד וכיוון. בכל הרצה בודקים את
כל ה-Issues הפתוחים עם התווית price-alert, ואם המחיר הנוכחי חצה את היעד -
שולחים מייל וסוגרים את ה-Issue.
פועל רק כשרצים דרך GitHub Actions (צריך GITHUB_TOKEN ו-GITHUB_REPOSITORY
שמוגדרים שם אוטומטית) - בהרצה מקומית פשוט לא עושה כלום.
"""

import os
import re

import requests
import yfinance as yf

import config
import notify

API_BASE = "https://api.github.com"
OWNER_LOGIN = config.GITHUB_REPO.split("/")[0]


def _repo_and_token():
    repo = os.environ.get("GITHUB_REPOSITORY") or config.GITHUB_REPO
    token = os.environ.get("GITHUB_TOKEN")
    return repo, token


def _headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }


def fetch_current_price(ticker):
    """כמו fetch_data.fetch_stock_prices, אבל לטיקר בודד כלשהו - לא רק אלה שב-config.TICKERS."""
    try:
        hist = yf.Ticker(ticker).history(period="1d")
        if not hist.empty:
            return round(float(hist["Close"].iloc[-1]), 2)
    except Exception as e:
        print(f"שגיאה בשליפת מחיר עבור {ticker}: {e}")
    return None


def get_open_alert_issues(repo, token):
    url = f"{API_BASE}/repos/{repo}/issues"
    params = {"state": "open", "labels": "price-alert", "per_page": 100}
    resp = requests.get(url, headers=_headers(token), params=params, timeout=15)
    resp.raise_for_status()
    # מתעלמים מ-issues שלא נפתחו על ידי בעל הריפו, כדי שאף אחד אחר (הריפו ציבורי) לא יוכל להציף
    return [issue for issue in resp.json() if issue.get("user", {}).get("login") == OWNER_LOGIN]


def parse_alert(issue):
    """מפרק את גוף ה-Issue (שנוצר מטופס מובנה) לשדות טיקר/מחיר יעד/כיוון."""
    body = issue.get("body") or ""
    ticker_match = re.search(r"###\s*טיקר\s*\n+([^\n]+)", body)
    price_match = re.search(r"###\s*מחיר יעד\s*\n+([^\n]+)", body)
    direction_match = re.search(r"###\s*כיוון\s*\n+([^\n]+)", body)
    if not (ticker_match and price_match and direction_match):
        return None
    try:
        ticker = ticker_match.group(1).strip().upper()
        target_price = float(price_match.group(1).strip())
        direction = "above" if "מעל" in direction_match.group(1) else "below"
        return {"ticker": ticker, "target_price": target_price, "direction": direction}
    except ValueError:
        return None


def close_issue(repo, token, issue_number, comment):
    """
    מגיב וסוגר Issue. בודקים את קוד התשובה של שתי הקריאות (raise_for_status) -
    בלי זה, כשל שקט בסגירה משאיר את ה-Issue פתוח ואת ההתראה מתפעילה שוב
    בהרצה הבאה (בעוד 15 דקות), ושוב, ושוב - ספאם מיילים בלי סימן לתקלה.
    """
    comment_resp = requests.post(
        f"{API_BASE}/repos/{repo}/issues/{issue_number}/comments",
        headers=_headers(token),
        json={"body": comment},
        timeout=15,
    )
    comment_resp.raise_for_status()
    close_resp = requests.patch(
        f"{API_BASE}/repos/{repo}/issues/{issue_number}",
        headers=_headers(token),
        json={"state": "closed"},
        timeout=15,
    )
    close_resp.raise_for_status()


def check_price_alerts():
    """עובר על כל התראות המחיר הפתוחות, שולח מייל וסוגר Issue לכל אחת שהתנאי שלה התקיים."""
    repo, token = _repo_and_token()
    if not token:
        return 0  # הרצה מקומית - אין GITHUB_TOKEN, מדלגים בשקט

    issues = get_open_alert_issues(repo, token)
    triggered = 0
    for issue in issues:
        alert = parse_alert(issue)
        if not alert:
            continue
        current = fetch_current_price(alert["ticker"])
        if current is None:
            continue
        hit = (alert["direction"] == "above" and current >= alert["target_price"]) or (
            alert["direction"] == "below" and current <= alert["target_price"]
        )
        if not hit:
            continue

        direction_he = "מעל" if alert["direction"] == "above" else "מתחת ל"
        body = (
            f"{alert['ticker']} הגיע ל-${current:.2f}, {direction_he} היעד שהגדרת "
            f"(${alert['target_price']:.2f}).\n\nזה הזמן להחליט אם להיכנס/לצאת - "
            "ההתראה הזו נסגרה אוטומטית, אפשר לפתוח חדשה בדשבורד."
        )
        notify.send_email(f"שי פיננס - התראת מחיר: {alert['ticker']}", body)
        try:
            close_issue(
                repo, token, issue["number"],
                f"✅ ההתראה הופעלה: {alert['ticker']} = ${current:.2f}. נשלח מייל, ה-Issue נסגר אוטומטית.",
            )
        except Exception as e:
            print(
                f"אזהרה: נשלח מייל עבור {alert['ticker']} אבל סגירת Issue #{issue['number']} נכשלה ({e}) - "
                "ייתכן שההתראה תופעל שוב בהרצה הבאה"
            )
        triggered += 1
    return triggered
