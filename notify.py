"""
התראות מייל על תנודות חדות במניות שבמעקב, וסיכום רווח/הפסד יומי בסוף יום המסחר.
נשלח מייל התראה רק כשיש משהו לדווח עליו - לא בכל הרצה.
פרטי ההתחברות ל-Gmail מגיעים ממשתני סביבה (להרצה ב-GitHub Actions) עם נפילה
לקובץ email_secrets.py המקומי (להרצה מהמחשב) - כדי שאותו קוד יעבוד בשני המקומות.
"""

import os
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText

import config

PCT_ALERT_THRESHOLD = 5.0  # אחוז שינוי יומי שמעליו שולחים התראה
DAILY_SUMMARY_UTC_HOUR = 20  # ~23:00 בישראל / סגירת שוק ארה"ב - שולחים בהרצה הראשונה אחרי השעה הזו (UTC)
LAST_SUMMARY_FILE = f"{config.DATA_DIR}/last_summary_date.txt"


def _get_credentials():
    address = os.environ.get("GMAIL_ADDRESS")
    password = os.environ.get("GMAIL_APP_PASSWORD")
    if address and password:
        return address, password
    import email_secrets  # קובץ מקומי בלבד - לא קיים בריפו ב-GitHub

    return email_secrets.GMAIL_ADDRESS, email_secrets.GMAIL_APP_PASSWORD


def check_alerts(ticker_stats):
    """
    מקבל את ticker_stats שמוחזר מ-build_dashboard.build() ובודק שני תנאים:
    - שינוי יומי חד (מעל/מתחת ל-PCT_ALERT_THRESHOLD%)
    - RSI קיצוני (קניית/מכירת יתר)
    מחזיר רשימת שורות טקסט להתראה (ריקה אם אין מה לדווח).
    """
    lines = []
    for stat in ticker_stats:
        ticker = stat["ticker"]
        pct = stat["pct"]
        if pct is not None and abs(pct) >= PCT_ALERT_THRESHOLD:
            direction = "עלייה" if pct > 0 else "ירידה"
            lines.append(f"{ticker}: {direction} חדה של {pct:+.2f}% היום")
        if stat["rsi_overbought"]:
            lines.append(f"{ticker}: RSI מצביע על קניית יתר")
        if stat["rsi_oversold"]:
            lines.append(f"{ticker}: RSI מצביע על מכירת יתר")
    return lines


def build_daily_summary(ticker_stats):
    """
    בונה טקסט סיכום רווח/הפסד לפי מחיר כניסה מול מחיר נוכחי, בדולרים אמיתיים
    לפי הכמות שהוגדרה ב-config.QUANTITIES. מניה בלי כמות מוצגת רק באחוזים.
    """
    lines = []
    total_value = 0.0
    total_cost = 0.0
    missing_qty = []

    for stat in ticker_stats:
        ticker = stat["ticker"]
        entry = config.ENTRY_PRICES.get(ticker)
        current = stat.get("latest_price")
        if entry is None or current is None:
            continue
        pct = (current - entry) / entry * 100 if entry else 0
        qty = config.QUANTITIES.get(ticker)
        if qty:
            cost = entry * qty
            value = current * qty
            gain = value - cost
            total_cost += cost
            total_value += value
            lines.append(f"{ticker}: {gain:+.2f}$ ({pct:+.2f}%) | {qty:g} מניות, שווי {value:.2f}$")
        else:
            missing_qty.append(ticker)
            lines.append(f"{ticker}: {pct:+.2f}% (אין כמות מוגדרת - לא נספר בסה\"כ)")

    summary = "\n".join(lines)
    if total_cost:
        total_gain = total_value - total_cost
        total_pct = total_gain / total_cost * 100
        summary += f"\n\nסה\"כ תיק (למניות עם כמות ידועה): {total_gain:+.2f}$ ({total_pct:+.2f}%) | שווי כולל {total_value:.2f}$"
    if missing_qty:
        summary += f"\n\nחסרה כמות עבור: {', '.join(missing_qty)} - עדכן ב-config.QUANTITIES כדי שייכנסו לסה\"כ."
    return summary


def send_email(subject, body):
    address, password = _get_credentials()
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = address
    msg["To"] = address

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(address, password)
        server.send_message(msg)


def send_alerts_if_needed(ticker_stats):
    lines = check_alerts(ticker_stats)
    if not lines:
        return False
    body = "התראות מהדשבורד שלך:\n\n" + "\n".join(lines)
    send_email("שי פיננס - התראת מסחר", body)
    return True


def send_daily_summary_if_needed(ticker_stats):
    """
    שולח סיכום יומי פעם אחת ביום, בהרצה הראשונה אחרי סגירת שוק ארה"ב.
    נשען על קובץ סמן (LAST_SUMMARY_FILE) כדי לא לשלוח פעמיים באותו יום,
    כי הסקריפט רץ כל 15 דקות.
    """
    now = datetime.now(timezone.utc)
    if now.hour < DAILY_SUMMARY_UTC_HOUR:
        return False

    today_str = now.strftime("%Y-%m-%d")
    last_sent = None
    if os.path.isfile(LAST_SUMMARY_FILE):
        with open(LAST_SUMMARY_FILE, encoding="utf-8") as f:
            last_sent = f.read().strip()
    if last_sent == today_str:
        return False

    body = f"סיכום רווח/הפסד ליום {today_str}:\n\n" + build_daily_summary(ticker_stats)
    send_email("שי פיננס - סיכום יומי", body)

    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(LAST_SUMMARY_FILE, "w", encoding="utf-8") as f:
        f.write(today_str)
    return True
