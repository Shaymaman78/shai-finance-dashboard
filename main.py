"""
הסקריפט הראשי - מריצים אותו כדי לעדכן את הדשבורד.
מריצים: python main.py
"""

import fetch_data
import build_dashboard
import notify
import price_alerts


def main():
    print("שולף מזג אוויר...")
    weather = fetch_data.fetch_weather()
    fetch_data.append_weather_history(weather)

    print("שולף מחירי מניות...")
    prices = fetch_data.fetch_stock_prices()
    fetch_data.append_stock_history(prices)

    print("שולף היסטוריית מניות לכל טווחי הזמן (1D/1W/1M/3M/6M/1Y)...")
    print("(זה עשוי לקחת דקה-שתיים, יש הרבה קריאות רשת)")
    stock_ranges = fetch_data.fetch_stock_ranges()

    print("שולף נתוני יסוד ודירוגי אנליסטים...")
    fundamentals = fetch_data.fetch_stock_fundamentals()

    print("שולף כותרות חדשות...")
    news = fetch_data.fetch_market_news()

    print("שולף שערי חליפין (דולר, יורו, לירה שטרלינג, ין)...")
    exchange_rates = fetch_data.fetch_exchange_rates()

    print("בונה את הדשבורד...")
    ticker_stats = build_dashboard.build(weather, prices, stock_ranges, fundamentals, news, exchange_rates)

    print("בודק אם הגיע הזמן לסיכום היומי...")
    try:
        if notify.send_daily_summary_if_needed(ticker_stats):
            print("נשלח סיכום יומי.")
        else:
            print("עדיין לא הגיע זמן הסיכום היומי, או שכבר נשלח היום.")
    except Exception as e:
        print(f"שליחת הסיכום היומי נכשלה: {e}")

    print("בודק התראות מחיר לפי דרישה (Issues מתויגים price-alert)...")
    try:
        triggered = price_alerts.check_price_alerts()
        print(f"{triggered} התראות מחיר הופעלו." if triggered else "אין התראות מחיר שהתקיימו כרגע.")
    except Exception as e:
        print(f"בדיקת התראות המחיר נכשלה: {e}")

    print("סיימנו! פתח/י את dashboard.html בדפדפן כדי לראות את התוצאה.")


if __name__ == "__main__":
    main()
