"""
עדכון תיק (הוספה/הסרה של מניות) לפי דרישה - בלי צורך במחשב. המשתמש פותח Issue
ב-GitHub (טופס מוכן, מקושר מהדשבורד) עם פעולה (הוסף/הסר), טיקר, ואם מוסיפים -
מחיר כניסה וכמות. בכל הרצה, לפני שליפת הנתונים, בודקים Issues פתוחים עם
התווית portfolio-change, מעדכנים את data/portfolio.json בהתאם, ומסמנים כטופלו.
פועל רק ב-GitHub Actions (צריך GITHUB_TOKEN) - בהרצה מקומית לא עושה כלום.
"""

import os
import re

import requests

import config

API_BASE = "https://api.github.com"
OWNER_LOGIN = config.GITHUB_REPO.split("/")[0]


def _repo_and_token():
    repo = os.environ.get("GITHUB_REPOSITORY") or config.GITHUB_REPO
    token = os.environ.get("GITHUB_TOKEN")
    return repo, token


def _headers(token):
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}


def get_open_portfolio_issues(repo, token):
    url = f"{API_BASE}/repos/{repo}/issues"
    params = {"state": "open", "labels": "portfolio-change", "per_page": 100}
    resp = requests.get(url, headers=_headers(token), params=params, timeout=15)
    resp.raise_for_status()
    # מתעלמים מ-issues שלא נפתחו על ידי בעל הריפו, כדי שאף אחד אחר (הריפו ציבורי) לא יוכל לשנות את התיק
    return [issue for issue in resp.json() if issue.get("user", {}).get("login") == OWNER_LOGIN]


def _parse_number(raw):
    if raw is None:
        return None
    raw = raw.strip()
    if not raw or raw == "_No response_":
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def parse_change(issue):
    """מפרק את גוף ה-Issue (שנוצר מטופס מובנה) לשדות פעולה/טיקר/מחיר כניסה/כמות."""
    body = issue.get("body") or ""
    action_match = re.search(r"###\s*פעולה\s*\n+([^\n]+)", body)
    ticker_match = re.search(r"###\s*טיקר\s*\n+([^\n]+)", body)
    price_match = re.search(r"###\s*מחיר כניסה[^\n]*\n+([^\n]+)", body)
    qty_match = re.search(r"###\s*כמות מניות[^\n]*\n+([^\n]+)", body)
    if not (action_match and ticker_match):
        return None
    action = "add" if "הוסף" in action_match.group(1) else "remove"
    ticker = ticker_match.group(1).strip().upper()
    entry_price = _parse_number(price_match.group(1)) if price_match else None
    quantity = _parse_number(qty_match.group(1)) if qty_match else None
    return {"action": action, "ticker": ticker, "entry_price": entry_price, "quantity": quantity}


def close_issue(repo, token, issue_number, comment):
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


def apply_portfolio_changes():
    """
    מעבד את כל בקשות עדכון התיק הפתוחות ומעדכן את data/portfolio.json בהתאם.
    מחזיר True אם התיק השתנה (כדי ש-main.py ידע לשלוף נתונים גם למניה חדשה
    שנוספה הרגע, באותה הרצה ממש).
    """
    repo, token = _repo_and_token()
    if not token:
        return False  # הרצה מקומית - אין GITHUB_TOKEN, מדלגים בשקט

    issues = get_open_portfolio_issues(repo, token)
    if not issues:
        return False

    portfolio = config.load_portfolio()
    changed = False

    for issue in issues:
        change = parse_change(issue)
        if not change:
            continue
        ticker = change["ticker"]

        try:
            if change["action"] == "add":
                if change["entry_price"] is None:
                    close_issue(repo, token, issue["number"], f"❌ לא נוסף - חסר מחיר כניסה תקין עבור {ticker}.")
                    continue
                portfolio[ticker] = {
                    "entry_price": change["entry_price"],
                    "quantity": change["quantity"],
                }
                changed = True
                qty_text = f", כמות {change['quantity']:g}" if change["quantity"] is not None else " (בלי כמות - יוצג רק באחוזים בסיכומים)"
                close_issue(
                    repo, token, issue["number"],
                    f"✅ {ticker} נוסף לתיק: מחיר כניסה ${change['entry_price']:.2f}{qty_text}. הדשבורד יתעדכן בהרצה הזו.",
                )
            else:  # remove
                if ticker in portfolio:
                    del portfolio[ticker]
                    changed = True
                    close_issue(repo, token, issue["number"], f"✅ {ticker} הוסר מהתיק. הדשבורד יתעדכן בהרצה הזו.")
                else:
                    close_issue(repo, token, issue["number"], f"⚠️ {ticker} לא נמצא בתיק - לא היה מה להסיר.")
        except Exception as e:
            print(f"אזהרה: עיבוד בקשת עדכון תיק ב-Issue #{issue['number']} נכשל חלקית: {e}")

    if changed:
        config.save_portfolio(portfolio)
    return changed
