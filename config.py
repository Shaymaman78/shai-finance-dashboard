"""
הגדרות הדשבורד - כאן משנים מה עוקבים אחריו, בלי לגעת בשאר הקוד.
"""

import json
import os

# ריפו ה-GitHub שמריץ את הדשבורד - לבניית קישורי Issue מוכנים (התראת מחיר, עדכון תיק)
GITHUB_REPO = "Shaymaman78/shai-finance-dashboard"

# מיקום למזג אוויר (חיפה כברירת מחדל - אפשר לשנות)
LOCATION_NAME = "חיפה"
LATITUDE = 32.7940
LONGITUDE = 34.9896

# נתיבי קבצים
DATA_DIR = "data"
STOCK_HISTORY_FILE = f"{DATA_DIR}/stock_history.csv"
WEATHER_HISTORY_FILE = f"{DATA_DIR}/weather_history.csv"
DASHBOARD_FILE = "dashboard.html"
PORTFOLIO_FILE = f"{DATA_DIR}/portfolio.json"


def load_portfolio():
    """
    טוען את התיק הנוכחי מקובץ JSON: {"TICKER": {"entry_price": ..., "quantity": ...}, ...}.
    זה מקור האמת היחיד לרשימת המניות שעוקבים אחריהן - נטען מחדש מהדיסק בכל קריאה
    (לא נשמר בזיכרון), כדי לשקף מיד שינוי שבוצע באותה הרצה (ראה portfolio_manager.py:
    אפשר להוסיף/להסיר מניה דרך הדשבורד, והשינוי חל עוד באותה הרצה של main.py).
    """
    if not os.path.isfile(PORTFOLIO_FILE):
        return {}
    with open(PORTFOLIO_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_portfolio(portfolio):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
        json.dump(portfolio, f, ensure_ascii=False, indent=2)


def get_tickers():
    return list(load_portfolio().keys())


def get_entry_price(ticker):
    entry = load_portfolio().get(ticker)
    return entry.get("entry_price") if entry else None


def get_quantity(ticker):
    entry = load_portfolio().get(ticker)
    return entry.get("quantity") if entry else None
