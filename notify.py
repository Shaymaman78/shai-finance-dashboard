"""
התראות מייל על תנודות חדות במניות שבמעקב, וסיכום רווח/הפסד יומי בסוף יום המסחר.
נשלח מייל התראה רק כשיש משהו לדווח עליו - לא בכל הרצה.
פרטי ההתחברות ל-Gmail מגיעים ממשתני סביבה (להרצה ב-GitHub Actions) עם נפילה
לקובץ email_secrets.py המקומי (להרצה מהמחשב) - כדי שאותו קוד יעבוד בשני המקומות.
"""

import os
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo

import config

PCT_ALERT_THRESHOLD = 5.0  # אחוז שינוי יומי שמעליו שולחים התראה
MARKET_CLOSE_HOUR_ET = 16  # שעת סגירת שוק ארה"ב (4pm) בזמן מקומי של ניו יורק - ZoneInfo מתחשב אוטומטית ב-DST (EDT/EST)
LAST_SUMMARY_FILE = f"{config.DATA_DIR}/last_summary_date.txt"
DATA_FAILURE_COOLDOWN_HOURS = 3  # לא שולחים שוב אם כבר התרענו על כשל נתונים לאחרונה והבעיה נמשכת
LAST_DATA_FAILURE_ALERT_FILE = f"{config.DATA_DIR}/last_data_failure_alert.txt"


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
    לפי הכמות שהוגדרה בתיק (data/portfolio.json). מניה בלי כמות מוצגת רק באחוזים.
    """
    lines = []
    total_value = 0.0
    total_cost = 0.0
    missing_qty = []

    for stat in ticker_stats:
        ticker = stat["ticker"]
        entry = config.get_entry_price(ticker)
        current = stat.get("latest_price")
        if entry is None or current is None:
            continue
        pct = (current - entry) / entry * 100 if entry else 0
        qty = config.get_quantity(ticker)
        if qty is not None:
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
        summary += f"\n\nחסרה כמות עבור: {', '.join(missing_qty)} - עדכן דרך כפתור \"עדכון תיק\" בדשבורד כדי שייכנסו לסה\"כ."
    return summary


def build_daily_summary_html(ticker_stats, title):
    """
    כמו build_daily_summary, אבל כטבלת HTML מסודרת (במקום שורות טקסט) - קריאה בהרבה במייל.
    """
    rows_html = ""
    total_value = 0.0
    total_cost = 0.0
    missing_qty = []

    stats_by_ticker = {s["ticker"]: s for s in ticker_stats}
    for ticker in config.get_tickers():
        stat = stats_by_ticker.get(ticker)
        entry = config.get_entry_price(ticker)
        current = stat.get("latest_price") if stat else None
        if entry is None or current is None:
            continue
        diff = current - entry
        pct = (diff / entry) * 100 if entry else 0
        color = "#2e7d32" if diff >= 0 else "#c62828"
        sign = "+" if diff >= 0 else ""
        qty = config.get_quantity(ticker)

        if qty is not None:
            cost = entry * qty
            value = current * qty
            gain = value - cost
            total_cost += cost
            total_value += value
            qty_cell = f"{qty:g}"
            value_cell = f"${value:,.2f}"
            gain_cell = f'<span style="color:{color}">{sign}{gain:,.2f}$</span>'
        else:
            missing_qty.append(ticker)
            qty_cell = "—"
            value_cell = "—"
            gain_cell = "—"

        rows_html += f"""
        <tr>
          <td style="padding:8px 10px;border-bottom:1px solid #333;font-weight:bold">{ticker}</td>
          <td style="padding:8px 10px;border-bottom:1px solid #333">${entry:,.2f}</td>
          <td style="padding:8px 10px;border-bottom:1px solid #333">${current:,.2f}</td>
          <td style="padding:8px 10px;border-bottom:1px solid #333;color:{color}">{sign}{diff:,.2f}</td>
          <td style="padding:8px 10px;border-bottom:1px solid #333;color:{color}">{sign}{pct:.2f}%</td>
          <td style="padding:8px 10px;border-bottom:1px solid #333">{qty_cell}</td>
          <td style="padding:8px 10px;border-bottom:1px solid #333">{value_cell}</td>
          <td style="padding:8px 10px;border-bottom:1px solid #333">{gain_cell}</td>
        </tr>
        """

    total_row_html = ""
    if total_cost:
        total_gain = total_value - total_cost
        total_pct = total_gain / total_cost * 100
        total_color = "#2e7d32" if total_gain >= 0 else "#c62828"
        total_sign = "+" if total_gain >= 0 else ""
        total_row_html = f"""
        <tr>
          <td colspan="6" style="padding:10px;font-weight:bold;border-top:2px solid #666">סה"כ תיק</td>
          <td style="padding:10px;font-weight:bold;border-top:2px solid #666">${total_value:,.2f}</td>
          <td style="padding:10px;font-weight:bold;border-top:2px solid #666;color:{total_color}">{total_sign}{total_gain:,.2f}$ ({total_sign}{total_pct:.2f}%)</td>
        </tr>
        """

    missing_note_html = ""
    if missing_qty:
        missing_note_html = f"""
        <p style="color:#999;font-size:13px;margin-top:14px">
          חסרה כמות עבור: {", ".join(missing_qty)} - שווי כולל ורווח/הפסד בדולרים לא כוללים אותן.
        </p>
        """

    return f"""
    <html dir="rtl">
    <body style="background:#0a0a0a;color:#e8e8e8;font-family:Arial,sans-serif;padding:20px">
      <h2 style="color:#fff;margin-bottom:4px">{title}</h2>
      <table style="border-collapse:collapse;width:100%;font-size:14px;background:#121212">
        <thead>
          <tr style="background:#1a1a1a;text-align:right">
            <th style="padding:8px 10px">מניה</th>
            <th style="padding:8px 10px">מחיר כניסה</th>
            <th style="padding:8px 10px">מחיר נוכחי</th>
            <th style="padding:8px 10px">שינוי ($)</th>
            <th style="padding:8px 10px">שינוי (%)</th>
            <th style="padding:8px 10px">כמות</th>
            <th style="padding:8px 10px">שווי כולל</th>
            <th style="padding:8px 10px">רווח/הפסד</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
          {total_row_html}
        </tbody>
      </table>
      {missing_note_html}
    </body>
    </html>
    """


def send_email(subject, body, html=None):
    if html:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(body, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))
    else:
        msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject

    address, password = _get_credentials()
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


def send_data_failure_alert_if_needed(valid_count, total_count):
    """
    מתריע מיד - לא מחכה ל-watchdog שרץ כל 3 שעות - אם אף מניה לא חזרה עם מחיר
    תקין בהרצה הזו. זה קורה כש-yfinance/Yahoo Finance מחזירים תגובה חלקית (למשל
    חסימה שקטה של ה-IP של GitHub Actions) בלי שהתהליך עצמו נכשל - ה-watchdog
    לא תופס את זה כי מבחינתו ה-workflow "הצליח" (רץ עד הסוף בלי שגיאה).
    """
    if total_count == 0 or valid_count > 0:
        return False

    now = datetime.now(timezone.utc)
    last_alert = None
    if os.path.isfile(LAST_DATA_FAILURE_ALERT_FILE):
        with open(LAST_DATA_FAILURE_ALERT_FILE, encoding="utf-8") as f:
            try:
                last_alert = datetime.fromisoformat(f.read().strip())
            except ValueError:
                last_alert = None
    if last_alert is not None and (now - last_alert).total_seconds() / 3600 < DATA_FAILURE_COOLDOWN_HOURS:
        return False

    body = (
        f"כל {total_count} המניות חזרו בלי מחיר תקין בהרצה הזו (ריק או NaN).\n\n"
        "כנראה חסימה זמנית או תגובה חלקית מ-Yahoo Finance (קורה לפעמים ל-IP-ים "
        "של שירותי CI כמו GitHub Actions) - לא תקלה בקוד עצמו, וה-workflow עדיין "
        "\"הצליח\" מבחינת GitHub, לכן ה-watchdog לא תפס את זה.\n\n"
        "הדשבורד התעדכן אבל עם נתונים חסרים לכל המניות. אם זה נמשך כמה שעות, כדאי לבדוק ידנית."
    )
    send_email("⚠️ שי פיננס - שליפת מחירים נכשלה לגמרי", body)

    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(LAST_DATA_FAILURE_ALERT_FILE, "w", encoding="utf-8") as f:
        f.write(now.isoformat())
    return True


def send_daily_summary_if_needed(ticker_stats):
    """
    שולח סיכום יומי פעם אחת ביום, בהרצה הראשונה אחרי סגירת שוק ארה"ב.
    משתמש בזמן מקומי של ניו יורק (לא שעה קבועה ב-UTC) כדי שההתחשבנות תהיה
    נכונה גם בשעון קיץ וגם בשעון חורף אמריקאי (ZoneInfo מטפל ב-DST אוטומטית).
    נשען על קובץ סמן (LAST_SUMMARY_FILE) כדי לא לשלוח פעמיים באותו יום,
    כי הסקריפט רץ כל 15 דקות.
    """
    now_et = datetime.now(ZoneInfo("America/New_York"))
    if now_et.hour < MARKET_CLOSE_HOUR_ET:
        return False

    today_str = now_et.strftime("%Y-%m-%d")
    last_sent = None
    if os.path.isfile(LAST_SUMMARY_FILE):
        with open(LAST_SUMMARY_FILE, encoding="utf-8") as f:
            last_sent = f.read().strip()
    if last_sent == today_str:
        return False

    title = f"סיכום רווח/הפסד ליום {today_str}"
    body = f"{title}:\n\n" + build_daily_summary(ticker_stats)
    html = build_daily_summary_html(ticker_stats, title)
    send_email("שי פיננס - סיכום יומי", body, html=html)

    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(LAST_SUMMARY_FILE, "w", encoding="utf-8") as f:
        f.write(today_str)
    return True
