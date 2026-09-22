"""
הגדרות הדשבורד - כאן משנים מה עוקבים אחריו, בלי לגעת בשאר הקוד.
"""

# המניות/קרנות שעוקבים אחריהן
TICKERS = ["AMZN", "BE", "GOOG", "IBM", "MRVL", "MU", "NASA", "NOK", "PLPC", "SNDK", "TSLA"]

# מחיר הכניסה שלך לכל מניה (למניה בודדת, לא סה"כ) - לחישוב רווח/הפסד
ENTRY_PRICES = {
    "AMZN": 225.61,
    "BE": 294.81,
    "GOOG": 172.58,
    "IBM": 260.03,
    "MRVL": 278.90,
    "MU": 1052.52,
    "NASA": 36.52,
    "NOK": 14.65,
    "PLPC": 376.68,
    "SNDK": 1791.00,
    "TSLA": 332.30,
}

# כמות מניות בפועל שיש לך לכל טיקר - לחישוב סיכום רווח/הפסד בדולרים אמיתיים (בסיכום היומי במייל).
# מניה בלי כמות כאן תוצג באחוזים בלבד בסיכום, ולא תיכנס לסה"כ.
QUANTITIES = {
    "SNDK": 1.91,
}

# מיקום למזג אוויר (חיפה כברירת מחדל - אפשר לשנות)
LOCATION_NAME = "חיפה"
LATITUDE = 32.7940
LONGITUDE = 34.9896

# נתיבי קבצים
DATA_DIR = "data"
STOCK_HISTORY_FILE = f"{DATA_DIR}/stock_history.csv"
WEATHER_HISTORY_FILE = f"{DATA_DIR}/weather_history.csv"
DASHBOARD_FILE = "dashboard.html"
