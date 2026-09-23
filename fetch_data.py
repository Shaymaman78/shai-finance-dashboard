"""
שליפת נתונים: מזג אוויר (Open-Meteo, ללא צורך במפתח API) ומחירי מניות (yfinance).
"""

import csv
import math
import os
import time
from datetime import datetime

import requests
import yfinance as yf
from curl_cffi import requests as cffi_requests

import config

# סשן עם התחזות לדפדפן אמיתי (curl_cffi impersonate) - Yahoo Finance נוטה לחסום
# או להחזיר תגובות חלקיות/NaN לבקשות "פשוטות" מסקריפטים, ובמיוחד מ-IP-ים של
# שירותי CI כמו GitHub Actions. זה לא פותר חסימת IP מוחלטת, אבל מפחית משמעותית
# את הסיכוי לתגובה חלקית שקטה (ראה גם _is_valid_close ו-_retry_fetch).
_SESSION = cffi_requests.Session(impersonate="chrome")


def ensure_data_dir():
    os.makedirs(config.DATA_DIR, exist_ok=True)


def _is_valid_close(hist):
    """בודק שיש שורות ושהמחיר האחרון הוא מספר אמיתי (לא NaN) - hist.empty לבדו לא מספיק:
    Yahoo Finance לפעמים מחזיר שורה קיימת עם ערכי OHLC של NaN (תגובה חלקית/חסימה שקטה)."""
    if hist.empty:
        return False
    try:
        return not math.isnan(float(hist["Close"].iloc[-1]))
    except (ValueError, TypeError):
        return False


def _fetch_history(ticker, period, interval, retries=2, delay=2.0):
    """כמו yf.Ticker(ticker).history(...), עם סשן שמתחזה לדפדפן וניסיון חוזר קצר
    אם התגובה ריקה/NaN - הרבה מקרי הכישלון של Yahoo Finance הם זמניים/רועשים."""
    last_hist = None
    for attempt in range(retries):
        hist = yf.Ticker(ticker, session=_SESSION).history(period=period, interval=interval)
        last_hist = hist
        if _is_valid_close(hist):
            return hist
        if attempt < retries - 1:
            time.sleep(delay)
    return last_hist


def fetch_weather():
    """שולף את תחזית מזג האוויר של היום עבור המיקום שהוגדר ב-config."""
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={config.LATITUDE}&longitude={config.LONGITUDE}"
        "&daily=temperature_2m_max,temperature_2m_min,weathercode"
        "&timezone=Asia/Jerusalem"
    )
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    data = response.json()

    daily = data["daily"]
    return {
        "date": daily["time"][0],
        "temp_max": daily["temperature_2m_max"][0],
        "temp_min": daily["temperature_2m_min"][0],
        "weathercode": daily["weathercode"][0],
    }


def fetch_stock_prices():
    """שולף את מחיר הסגירה האחרון עבור כל טיקר בתיק הנוכחי (config.get_tickers())."""
    prices = {}
    for ticker in config.get_tickers():
        try:
            hist = _fetch_history(ticker, period="1d", interval="1d")
            if _is_valid_close(hist):
                prices[ticker] = round(float(hist["Close"].iloc[-1]), 2)
            else:
                prices[ticker] = None
                print(f"לא נמצאו נתונים תקינים (ריק או NaN) עבור {ticker}")
        except Exception as e:
            print(f"שגיאה בשליפת {ticker}: {e}")
            prices[ticker] = None
    return prices


# טווחי זמן זמינים לכל מניה - (period, interval) לפי מגבלות yfinance/Yahoo Finance.
# הרזולוציה הכי גבוהה שקיימת בחינם היא דקה אחת (1m), ורק לכמה ימים אחורה.
RANGE_CONFIGS = {
    "1D": ("1d", "1m"),
    "1W": ("5d", "1m"),
    "1M": ("1mo", "1h"),
    "3M": ("3mo", "1d"),
    "6M": ("6mo", "1d"),
    "1Y": ("1y", "1d"),
}


def fetch_stock_ranges():
    """
    שולף עבור כל טיקר את כל 6 טווחי הזמן (1D/1W/1M/3M/6M/1Y) בבת אחת.
    כל טווח מכיל: dates, open, high, low, close, volume.
    לתשומת לב: זו קריאה כבדה יחסית (6 קריאות רשת לכל טיקר), עשויה לקחת קצת זמן.
    """
    empty = {"dates": [], "open": [], "high": [], "low": [], "close": [], "volume": []}
    all_ranges = {}
    for ticker in config.get_tickers():
        all_ranges[ticker] = {}
        for range_key, (period, interval) in RANGE_CONFIGS.items():
            try:
                hist = _fetch_history(ticker, period=period, interval=interval)
                # מסננים שורות עם NaN בכל אחת מעמודות ה-OHLC - Yahoo Finance לפעמים
                # מחזיר שורות "קיימות" אבל עם ערכי מחיר חסרים (תגובה חלקית/חסימה שקטה)
                hist = hist.dropna(subset=["Open", "High", "Low", "Close"])
                if not hist.empty:
                    is_intraday = interval in ("1m", "5m", "15m", "30m", "1h")
                    date_format = "%Y-%m-%d %H:%M" if is_intraday else "%Y-%m-%d"
                    all_ranges[ticker][range_key] = {
                        "dates": [d.strftime(date_format) for d in hist.index],
                        "open": [round(float(x), 2) for x in hist["Open"]],
                        "high": [round(float(x), 2) for x in hist["High"]],
                        "low": [round(float(x), 2) for x in hist["Low"]],
                        "close": [round(float(x), 2) for x in hist["Close"]],
                        "volume": [int(x) for x in hist["Volume"]],
                    }
                else:
                    all_ranges[ticker][range_key] = dict(empty)
            except Exception as e:
                print(f"שגיאה בשליפת טווח {range_key} עבור {ticker}: {e}")
                all_ranges[ticker][range_key] = dict(empty)
    return all_ranges


def fetch_stock_fundamentals():
    """
    שולף נתוני יסוד ודירוג אנליסטים לכל טיקר.
    חשוב: recommendationKey הוא ממוצע דירוגים של אנליסטים חיצוניים בשוק (מ-Yahoo Finance),
    לא דעה של הכלי הזה או שלי.
    """
    fundamentals = {}
    for ticker in config.get_tickers():
        try:
            info = yf.Ticker(ticker, session=_SESSION).info
            fundamentals[ticker] = {
                "pe_ratio": info.get("trailingPE"),
                "market_cap": info.get("marketCap"),
                "analyst_recommendation": info.get("recommendationKey"),
                "analyst_count": info.get("numberOfAnalystOpinions"),
                "target_mean_price": info.get("targetMeanPrice"),
            }
        except Exception as e:
            print(f"שגיאה בשליפת נתוני יסוד עבור {ticker}: {e}")
            fundamentals[ticker] = {}
    return fundamentals


def fetch_market_news(max_per_ticker=2):
    """
    שולף כותרות חדשות אמיתיות מ-Yahoo Finance לכל טיקר (דרך yfinance).
    זה מקור אמיתי וחינמי - לא סנטימנט מרשתות חברתיות (זה דורש API בתשלום שאין לנו גישה אליו).
    """
    all_news = []
    for ticker in config.get_tickers():
        try:
            stock = yf.Ticker(ticker, session=_SESSION)
            news_items = stock.news or []
            for item in news_items[:max_per_ticker]:
                # מבנה ה-news של yfinance משתנה בין גרסאות - תומכים בשני הפורמטים המוכרים
                content = item.get("content", item)
                title = content.get("title") or item.get("title")
                publisher = (
                    content.get("provider", {}).get("displayName")
                    if isinstance(content.get("provider"), dict)
                    else item.get("publisher")
                )
                link = (
                    content.get("canonicalUrl", {}).get("url")
                    if isinstance(content.get("canonicalUrl"), dict)
                    else item.get("link")
                )
                # תאריך פרסום - תומכים גם בפורמט timestamp (ישן) וגם ISO string (חדש)
                date_str = ""
                pub_date = content.get("pubDate") or content.get("displayTime")
                if pub_date:
                    try:
                        date_str = datetime.fromisoformat(pub_date.replace("Z", "+00:00")).strftime("%d/%m/%Y")
                    except (ValueError, AttributeError):
                        date_str = ""
                if not date_str:
                    timestamp = item.get("providerPublishTime")
                    if timestamp:
                        try:
                            date_str = datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y")
                        except (ValueError, OSError):
                            date_str = ""
                if title:
                    all_news.append(
                        {
                            "ticker": ticker,
                            "title": title,
                            "publisher": publisher or "Yahoo Finance",
                            "link": link or "",
                            "date": date_str,
                        }
                    )
        except Exception as e:
            print(f"שגיאה בשליפת חדשות עבור {ticker}: {e}")
    return all_news


def fetch_exchange_rates():
    """
    שולף שערי חליפין אמיתיים מול השקל: דולר, יורו, לירה שטרלינג, ין יפני.
    מחזיר dict {"USD": rate, "EUR": rate, "GBP": rate, "JPY": rate} - כל rate הוא
    כמה שקלים שווה יחידה אחת של אותו מטבע. None אם שליפה נכשלה לאותו מטבע.
    """
    rates = {}
    try:
        hist = _fetch_history("ILS=X", period="1d", interval="1d")
        usd_ils_rate = round(float(hist["Close"].iloc[-1]), 4) if _is_valid_close(hist) else None
    except Exception as e:
        print(f"שגיאה בשליפת שער דולר-שקל: {e}")
        usd_ils_rate = None
    rates["USD"] = usd_ils_rate

    # שאר המטבעות נשלפים מול הדולר (הטיקרים של Yahoo נותנים "כמות מהמטבע ליחידת דולר"),
    # ואז ממירים לשקל דרך הדולר.
    cross_tickers = {"EUR": "EUR=X", "GBP": "GBP=X", "JPY": "JPY=X"}
    for currency, ticker_symbol in cross_tickers.items():
        try:
            hist = _fetch_history(ticker_symbol, period="1d", interval="1d")
            per_usd = float(hist["Close"].iloc[-1]) if _is_valid_close(hist) else None
            if per_usd and usd_ils_rate:
                rates[currency] = round(usd_ils_rate / per_usd, 4)
            else:
                rates[currency] = None
        except Exception as e:
            print(f"שגיאה בשליפת שער {currency}-שקל: {e}")
            rates[currency] = None
    return rates


def append_weather_history(weather):
    """מוסיף שורת מזג אוויר להיסטוריה, בלי לדרוס נתונים קודמים."""
    ensure_data_dir()
    file_exists = os.path.isfile(config.WEATHER_HISTORY_FILE)
    with open(config.WEATHER_HISTORY_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["date", "temp_min", "temp_max", "weathercode"])
        writer.writerow(
            [weather["date"], weather["temp_min"], weather["temp_max"], weather["weathercode"]]
        )


def append_stock_history(prices):
    """מוסיף שורת מחירים להיסטוריה, בלי לדרוס נתונים קודמים."""
    ensure_data_dir()
    today = datetime.now().strftime("%Y-%m-%d")
    file_exists = os.path.isfile(config.STOCK_HISTORY_FILE)
    with open(config.STOCK_HISTORY_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["date", "ticker", "price"])
        for ticker, price in prices.items():
            if price is not None:
                writer.writerow([today, ticker, price])
