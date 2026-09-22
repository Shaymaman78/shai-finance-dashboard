"""
בניית עמוד HTML (dashboard.html) מתוך היסטוריית מזג האוויר והמניות.
"""

import csv
import html
import json
import os
from datetime import datetime

import config

# תיאורי weathercode לפי הסטנדרט של Open-Meteo (WMO) - הקודים הנפוצים בלבד, רב-לשוני
WEATHER_DESCRIPTIONS = {
    0: {"he": "בהיר", "en": "Clear", "es": "Despejado", "fr": "Dégagé", "ar": "صافٍ"},
    1: {"he": "בהיר בעיקר", "en": "Mostly clear", "es": "Mayormente despejado", "fr": "Généralement dégagé", "ar": "صافٍ في الغالب"},
    2: {"he": "מעונן חלקית", "en": "Partly cloudy", "es": "Parcialmente nublado", "fr": "Partiellement nuageux", "ar": "غائم جزئياً"},
    3: {"he": "מעונן", "en": "Cloudy", "es": "Nublado", "fr": "Nuageux", "ar": "غائم"},
    45: {"he": "ערפל", "en": "Fog", "es": "Niebla", "fr": "Brouillard", "ar": "ضباب"},
    48: {"he": "ערפל קרח", "en": "Icy fog", "es": "Niebla helada", "fr": "Brouillard givrant", "ar": "ضباب جليدي"},
    51: {"he": "טפטוף קל", "en": "Light drizzle", "es": "Llovizna ligera", "fr": "Bruine légère", "ar": "رذاذ خفيف"},
    53: {"he": "טפטוף", "en": "Drizzle", "es": "Llovizna", "fr": "Bruine", "ar": "رذاذ"},
    55: {"he": "טפטוף חזק", "en": "Heavy drizzle", "es": "Llovizna intensa", "fr": "Bruine forte", "ar": "رذاذ غزير"},
    61: {"he": "גשם קל", "en": "Light rain", "es": "Lluvia ligera", "fr": "Pluie légère", "ar": "مطر خفيف"},
    63: {"he": "גשם", "en": "Rain", "es": "Lluvia", "fr": "Pluie", "ar": "مطر"},
    65: {"he": "גשם חזק", "en": "Heavy rain", "es": "Lluvia intensa", "fr": "Pluie forte", "ar": "مطر غزير"},
    71: {"he": "שלג קל", "en": "Light snow", "es": "Nieve ligera", "fr": "Neige légère", "ar": "ثلج خفيف"},
    73: {"he": "שלג", "en": "Snow", "es": "Nieve", "fr": "Neige", "ar": "ثلج"},
    75: {"he": "שלג חזק", "en": "Heavy snow", "es": "Nieve intensa", "fr": "Neige forte", "ar": "ثلج غزير"},
    80: {"he": "ממטרים קלים", "en": "Light showers", "es": "Chubascos ligeros", "fr": "Averses légères", "ar": "زخات خفيفة"},
    81: {"he": "ממטרים", "en": "Showers", "es": "Chubascos", "fr": "Averses", "ar": "زخات مطرية"},
    82: {"he": "ממטרים חזקים", "en": "Heavy showers", "es": "Chubascos intensos", "fr": "Averses fortes", "ar": "زخات غزيرة"},
    95: {"he": "סופת רעמים", "en": "Thunderstorm", "es": "Tormenta eléctrica", "fr": "Orage", "ar": "عاصفة رعدية"},
}


def read_weather_history():
    dates, temp_min, temp_max = [], [], []
    if not os.path.isfile(config.WEATHER_HISTORY_FILE):
        return dates, temp_min, temp_max
    with open(config.WEATHER_HISTORY_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dates.append(row["date"])
            temp_min.append(float(row["temp_min"]))
            temp_max.append(float(row["temp_max"]))
    return dates, temp_min, temp_max


import indicators

RECOMMENDATION_LABELS = {
    "strong_buy": {"he": "קנייה חזקה", "en": "Strong Buy", "es": "Compra fuerte", "fr": "Achat fort", "ar": "شراء قوي"},
    "buy": {"he": "קנייה", "en": "Buy", "es": "Comprar", "fr": "Acheter", "ar": "شراء"},
    "hold": {"he": "החזקה", "en": "Hold", "es": "Mantener", "fr": "Conserver", "ar": "احتفاظ"},
    "sell": {"he": "מכירה", "en": "Sell", "es": "Vender", "fr": "Vendre", "ar": "بيع"},
    "strong_sell": {"he": "מכירה חזקה", "en": "Strong Sell", "es": "Venta fuerte", "fr": "Vente forte", "ar": "بيع قوي"},
    "underperform": {"he": "תת-ביצוע", "en": "Underperform", "es": "Rendimiento inferior", "fr": "Sous-performance", "ar": "أداء ضعيف"},
    "outperform": {"he": "עודף-ביצוע", "en": "Outperform", "es": "Rendimiento superior", "fr": "Surperformance", "ar": "أداء متفوق"},
    "none": {"he": "אין דירוג", "en": "No rating", "es": "Sin calificación", "fr": "Pas de notation", "ar": "بدون تصنيف"},
}


# רשימת ערים עולמיות מובנית (שם, מדינה, קו רוחב, קו אורך, אזור זמן) - לחיפוש מיקום
# בלי תלות ברשת (חיפוש חי היה עלול להיחסם על ידי מדיניות CORS בקבצים מקומיים).
WORLD_CITIES = [
    ("חיפה", "ישראל", 32.7940, 34.9896, "Asia/Jerusalem"),
    ("תל אביב", "ישראל", 32.0853, 34.7818, "Asia/Jerusalem"),
    ("ירושלים", "ישראל", 31.7683, 35.2137, "Asia/Jerusalem"),
    ("אילת", "ישראל", 29.5581, 34.9482, "Asia/Jerusalem"),
    ("באר שבע", "ישראל", 31.2518, 34.7913, "Asia/Jerusalem"),
    ("New York", "USA", 40.7128, -74.0060, "America/New_York"),
    ("Los Angeles", "USA", 34.0522, -118.2437, "America/Los_Angeles"),
    ("Chicago", "USA", 41.8781, -87.6298, "America/Chicago"),
    ("Miami", "USA", 25.7617, -80.1918, "America/New_York"),
    ("San Francisco", "USA", 37.7749, -122.4194, "America/Los_Angeles"),
    ("Las Vegas", "USA", 36.1699, -115.1398, "America/Los_Angeles"),
    ("Boston", "USA", 42.3601, -71.0589, "America/New_York"),
    ("Seattle", "USA", 47.6062, -122.3321, "America/Los_Angeles"),
    ("Toronto", "Canada", 43.6532, -79.3832, "America/Toronto"),
    ("Vancouver", "Canada", 49.2827, -123.1207, "America/Vancouver"),
    ("Montreal", "Canada", 45.5019, -73.5674, "America/Toronto"),
    ("Mexico City", "Mexico", 19.4326, -99.1332, "America/Mexico_City"),
    ("Sao Paulo", "Brazil", -23.5505, -46.6333, "America/Sao_Paulo"),
    ("Rio de Janeiro", "Brazil", -22.9068, -43.1729, "America/Sao_Paulo"),
    ("Buenos Aires", "Argentina", -34.6037, -58.3816, "America/Argentina/Buenos_Aires"),
    ("London", "UK", 51.5074, -0.1278, "Europe/London"),
    ("Manchester", "UK", 53.4808, -2.2426, "Europe/London"),
    ("Paris", "France", 48.8566, 2.3522, "Europe/Paris"),
    ("Marseille", "France", 43.2965, 5.3698, "Europe/Paris"),
    ("Berlin", "Germany", 52.5200, 13.4050, "Europe/Berlin"),
    ("Munich", "Germany", 48.1351, 11.5820, "Europe/Berlin"),
    ("Frankfurt", "Germany", 50.1109, 8.6821, "Europe/Berlin"),
    ("Madrid", "Spain", 40.4168, -3.7038, "Europe/Madrid"),
    ("Barcelona", "Spain", 41.3851, 2.1734, "Europe/Madrid"),
    ("Rome", "Italy", 41.9028, 12.4964, "Europe/Rome"),
    ("Milan", "Italy", 45.4642, 9.1900, "Europe/Rome"),
    ("Amsterdam", "Netherlands", 52.3676, 4.9041, "Europe/Amsterdam"),
    ("Brussels", "Belgium", 50.8503, 4.3517, "Europe/Brussels"),
    ("Vienna", "Austria", 48.2082, 16.3738, "Europe/Vienna"),
    ("Zurich", "Switzerland", 47.3769, 8.5417, "Europe/Zurich"),
    ("Geneva", "Switzerland", 46.2044, 6.1432, "Europe/Zurich"),
    ("Lisbon", "Portugal", 38.7223, -9.1393, "Europe/Lisbon"),
    ("Dublin", "Ireland", 53.3498, -6.2603, "Europe/Dublin"),
    ("Stockholm", "Sweden", 59.3293, 18.0686, "Europe/Stockholm"),
    ("Oslo", "Norway", 59.9139, 10.7522, "Europe/Oslo"),
    ("Copenhagen", "Denmark", 55.6761, 12.5683, "Europe/Copenhagen"),
    ("Helsinki", "Finland", 60.1699, 24.9384, "Europe/Helsinki"),
    ("Warsaw", "Poland", 52.2297, 21.0122, "Europe/Warsaw"),
    ("Prague", "Czechia", 50.0755, 14.4378, "Europe/Prague"),
    ("Budapest", "Hungary", 47.4979, 19.0402, "Europe/Budapest"),
    ("Athens", "Greece", 37.9838, 23.7275, "Europe/Athens"),
    ("Istanbul", "Turkey", 41.0082, 28.9784, "Europe/Istanbul"),
    ("Moscow", "Russia", 55.7558, 37.6173, "Europe/Moscow"),
    ("Kyiv", "Ukraine", 50.4501, 30.5234, "Europe/Kyiv"),
    ("Cairo", "Egypt", 30.0444, 31.2357, "Africa/Cairo"),
    ("Dubai", "UAE", 25.2048, 55.2708, "Asia/Dubai"),
    ("Abu Dhabi", "UAE", 24.4539, 54.3773, "Asia/Dubai"),
    ("Doha", "Qatar", 25.2854, 51.5310, "Asia/Qatar"),
    ("Riyadh", "Saudi Arabia", 24.7136, 46.6753, "Asia/Riyadh"),
    ("Amman", "Jordan", 31.9454, 35.9284, "Asia/Amman"),
    ("Beirut", "Lebanon", 33.8938, 35.5018, "Asia/Beirut"),
    ("Nairobi", "Kenya", -1.2921, 36.8219, "Africa/Nairobi"),
    ("Lagos", "Nigeria", 6.5244, 3.3792, "Africa/Lagos"),
    ("Johannesburg", "South Africa", -26.2041, 28.0473, "Africa/Johannesburg"),
    ("Cape Town", "South Africa", -33.9249, 18.4241, "Africa/Johannesburg"),
    ("Mumbai", "India", 19.0760, 72.8777, "Asia/Kolkata"),
    ("New Delhi", "India", 28.6139, 77.2090, "Asia/Kolkata"),
    ("Bangalore", "India", 12.9716, 77.5946, "Asia/Kolkata"),
    ("Karachi", "Pakistan", 24.8607, 67.0011, "Asia/Karachi"),
    ("Dhaka", "Bangladesh", 23.8103, 90.4125, "Asia/Dhaka"),
    ("Bangkok", "Thailand", 13.7563, 100.5018, "Asia/Bangkok"),
    ("Singapore", "Singapore", 1.3521, 103.8198, "Asia/Singapore"),
    ("Kuala Lumpur", "Malaysia", 3.1390, 101.6869, "Asia/Kuala_Lumpur"),
    ("Jakarta", "Indonesia", -6.2088, 106.8456, "Asia/Jakarta"),
    ("Manila", "Philippines", 14.5995, 120.9842, "Asia/Manila"),
    ("Hong Kong", "China", 22.3193, 114.1694, "Asia/Hong_Kong"),
    ("Shanghai", "China", 31.2304, 121.4737, "Asia/Shanghai"),
    ("Beijing", "China", 39.9042, 116.4074, "Asia/Shanghai"),
    ("Taipei", "Taiwan", 25.0330, 121.5654, "Asia/Taipei"),
    ("Seoul", "South Korea", 37.5665, 126.9780, "Asia/Seoul"),
    ("Tokyo", "Japan", 35.6762, 139.6503, "Asia/Tokyo"),
    ("Osaka", "Japan", 34.6937, 135.5023, "Asia/Tokyo"),
    ("Sydney", "Australia", -33.8688, 151.2093, "Australia/Sydney"),
    ("Melbourne", "Australia", -37.8136, 144.9631, "Australia/Melbourne"),
    ("Perth", "Australia", -31.9505, 115.8605, "Australia/Perth"),
    ("Auckland", "New Zealand", -36.8485, 174.7633, "Pacific/Auckland"),
    ("Honolulu", "USA", 21.3069, -157.8583, "Pacific/Honolulu"),
]


def tr(he, en, es=None, fr=None, ar=None):
    """
    מייצר span שמכיל תרגומים למספר שפות (לא מוגבל ל-2) - ה-JS מחליף בין הטקסטים
    לפי השפה שנבחרה מהתפריט. שפות שלא סופקו נופלות חזרה לאנגלית.
    """
    translations = {
        "he": he,
        "en": en,
        "es": es or en,
        "fr": fr or en,
        "ar": ar or en,
    }
    raw_json = json.dumps(translations, ensure_ascii=False)
    escaped = raw_json.replace("&", "&amp;").replace('"', "&quot;")
    return f'<span data-i18n="{escaped}">{he}</span>'


def tr_d(translations):
    """כמו tr(), אבל מקבל dict מוכן {lang: text} ישירות (למשל מ-WEATHER_DESCRIPTIONS)."""
    he = translations.get("he", "")
    raw_json = json.dumps(translations, ensure_ascii=False)
    escaped = raw_json.replace("&", "&amp;").replace('"', "&quot;")
    return f'<span data-i18n="{escaped}">{he}</span>'


def bi(he_text, en_text):
    """תאימות לאחור לקריאות ישנות - עוטף tr() עם עברית/אנגלית בלבד."""
    return tr(he_text, en_text)


def tr_attr(he, en, es=None, fr=None, ar=None):
    """
    כמו tr(), אבל לשימוש בתוך attribute (placeholder/title) ולא כתוכן אלמנט -
    אי אפשר לשים שם <span> (זה שובר את ה-HTML), אז מחזירים רק את הטקסט העברי
    הרגיל (escaped לשימוש ב-attribute), בתוספת JSON נפרד שה-JS יכול לקרוא כדי
    להחליף שפה. משתמשים בזה עם attr_i18n(), ראו שם.
    """
    translations = {"he": he, "en": en, "es": es or en, "fr": fr or en, "ar": ar or en}
    raw_json = json.dumps(translations, ensure_ascii=False)
    escaped_json = raw_json.replace("&", "&amp;").replace('"', "&quot;")
    escaped_he = he.replace("&", "&amp;").replace('"', "&quot;")
    return escaped_he, escaped_json


def attr_i18n(attr_name, he, en, es=None, fr=None, ar=None):
    """
    בונה זוג attributes לשימוש בתוך תג HTML: הערך ההתחלתי (בעברית) + data-i18n-<attr>
    עם JSON לכל השפות, כדי שסקריפט החלפת השפה יוכל לעדכן גם placeholder/title
    ולא רק תוכן טקסט רגיל. שימוש: <input {attr_i18n('placeholder', 'חפש...', 'Search...')}>
    """
    escaped_he, escaped_json = tr_attr(he, en, es, fr, ar)
    return f'{attr_name}="{escaped_he}" data-i18n-{attr_name}="{escaped_json}"'


def format_market_cap(value):
    if value is None:
        return "אין נתון"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    return f"${value:,.0f}"


def build_market_summary(ticker_stats, news):
    """
    בונה פאנל סיכום שוק יומי מנתונים אמיתיים בלבד:
    - סטטיסטיקות מצטברות על 10 המניות שאתה עוקב אחריהן (עולות/יורדות, ממוצע שינוי, המובילה/הכי חלשה)
    - סקירה טכנית מצטברת (כמה במגמה חיובית/שלילית, כמה ב-RSI קיצוני)
    - כותרות חדשות אמיתיות מ-Yahoo Finance (לא סנטימנט רשתות חברתיות - זה דורש API בתשלום שאין לנו)
    """
    valid = [s for s in ticker_stats if s["pct"] is not None]
    advancers = [s for s in valid if s["pct"] > 0]
    decliners = [s for s in valid if s["pct"] < 0]
    avg_pct = sum(s["pct"] for s in valid) / len(valid) if valid else 0
    best = max(valid, key=lambda s: s["pct"]) if valid else None
    worst = min(valid, key=lambda s: s["pct"]) if valid else None
    total_volume = sum(s["volume"] for s in ticker_stats if s["volume"])

    trend_up_count = sum(1 for s in ticker_stats if s["trend_up"])
    trend_down_count = sum(1 for s in ticker_stats if s["trend_down"])
    overbought_count = sum(1 for s in ticker_stats if s["rsi_overbought"])
    oversold_count = sum(1 for s in ticker_stats if s["rsi_oversold"])

    def stat_card(label_tr, value_html):
        return f'<div class="summary-stat"><div class="summary-stat-label">{label_tr}</div><div class="summary-stat-value">{value_html}</div></div>'

    avg_color = "#2e7d32" if avg_pct >= 0 else "#c62828"
    avg_sign = "+" if avg_pct >= 0 else ""

    stats_html = ""
    stats_html += stat_card(
        tr("עולות היום", "Advancing today", "En alza hoy", "En hausse aujourd'hui", "صاعدة اليوم"),
        f'<span style="color:#2e7d32">{len(advancers)}</span> / {len(valid)}',
    )
    stats_html += stat_card(
        tr("יורדות היום", "Declining today", "En baja hoy", "En baisse aujourd'hui", "هابطة اليوم"),
        f'<span style="color:#c62828">{len(decliners)}</span> / {len(valid)}',
    )
    stats_html += stat_card(
        tr("שינוי ממוצע", "Average change", "Cambio promedio", "Variation moyenne", "متوسط التغير"),
        f'<span style="color:{avg_color}">{avg_sign}{avg_pct:.2f}%</span>',
    )
    if best:
        stats_html += stat_card(
            tr("המובילה היום", "Top performer", "Mejor desempeño", "Meilleure performance", "الأفضل أداءً اليوم"),
            f'{best["ticker"]} <span style="color:#2e7d32">+{best["pct"]:.2f}%</span>',
        )
    if worst:
        stats_html += stat_card(
            tr("החלשה היום", "Worst performer", "Peor desempeño", "Pire performance", "الأضعف أداءً اليوم"),
            f'{worst["ticker"]} <span style="color:#c62828">{worst["pct"]:.2f}%</span>',
        )
    stats_html += stat_card(
        tr("נפח מסחר כולל", "Total volume", "Volumen total", "Volume total", "إجمالي حجم التداول"),
        f"{total_volume:,}" if total_volume else na_placeholder(),
    )

    technical_html = f"""
    <div class="summary-technical">
      <div>📈 {tr("מגמה חיובית", "Positive trend", "Tendencia positiva", "Tendance positive", "اتجاه إيجابي")}: {trend_up_count}/{len(ticker_stats)}</div>
      <div>📉 {tr("מגמה שלילית", "Negative trend", "Tendencia negativa", "Tendance négative", "اتجاه سلبي")}: {trend_down_count}/{len(ticker_stats)}</div>
      <div>🔴 {tr("קניית יתר (RSI)", "Overbought (RSI)", "Sobrecompra (RSI)", "Surachat (RSI)", "تشبع شرائي (RSI)")}: {overbought_count}</div>
      <div>🟢 {tr("מכירת יתר (RSI)", "Oversold (RSI)", "Sobreventa (RSI)", "Survente (RSI)", "تشبع بيعي (RSI)")}: {oversold_count}</div>
    </div>
    """

    news_items_html = ""
    if news:
        for item in news[:12]:
            link_attr = f' href="{html.escape(item["link"])}" target="_blank" rel="noopener"' if item.get("link") else ""
            tag = "a" if item.get("link") else "span"
            date_html = f'<span class="news-date">{html.escape(item["date"])}</span>' if item.get("date") else ""
            news_items_html += f"""
            <div class="news-item">
              <span class="news-ticker">{html.escape(item['ticker'])}</span>
              <{tag} class="news-title"{link_attr}>{html.escape(item['title'])}</{tag}>
              <span class="news-publisher">{html.escape(item.get('publisher', ''))}</span>
              {date_html}
            </div>
            """
        news_section_html = f"""
        <div class="summary-news">
          <h3>📰 {tr("כותרות חדשות אחרונות", "Recent news headlines", "Titulares de noticias recientes", "Dernières actualités", "أحدث عناوين الأخبار")}</h3>
          {news_items_html}
        </div>
        """
    else:
        news_section_html = f"""
        <div class="summary-news">
          <p class="summary-news-empty">{tr(
              "לא נמצאו כותרות חדשות בהרצה הזו.",
              "No news headlines found in this run.",
              "No se encontraron titulares de noticias en esta ejecución.",
              "Aucun titre d'actualité trouvé lors de cette exécution.",
              "لم يتم العثور على عناوين أخبار في هذا التشغيل.",
          )}</p>
        </div>
        """

    return f"""
    <div class="market-summary">
      <h2>📊 {tr("סיכום שוק יומי", "Daily Market Summary", "Resumen diario del mercado", "Résumé quotidien du marché", "ملخص السوق اليومي")}</h2>
      <div class="summary-stats-grid">
        {stats_html}
      </div>
      {technical_html}
      {news_section_html}
      <div class="summary-note">
        ℹ️ {tr(
            "הסיכום מבוסס על 10 המניות שבמעקב שלך בלבד, ועל כותרות חדשות אמיתיות מ-Yahoo Finance. "
            "אין כאן ניתוח סנטימנט מרשתות חברתיות (זה דורש גישת API בתשלום שלא זמינה כאן).",
            "This summary is based only on the 10 stocks you track, and real news headlines from "
            "Yahoo Finance. There is no social media sentiment analysis here (that requires paid "
            "API access not available in this tool).",
            "Este resumen se basa únicamente en las 10 acciones que sigues, y en titulares de "
            "noticias reales de Yahoo Finance. No hay análisis de sentimiento de redes sociales "
            "aquí (eso requiere acceso a una API de pago no disponible en esta herramienta).",
            "Ce résumé est basé uniquement sur les 10 actions que vous suivez, et sur de vraies "
            "actualités de Yahoo Finance. Il n'y a pas d'analyse de sentiment des réseaux sociaux "
            "ici (cela nécessite un accès API payant non disponible dans cet outil).",
            "يعتمد هذا الملخص فقط على الأسهم العشرة التي تتابعها، وعلى عناوين أخبار حقيقية من "
            "Yahoo Finance. لا يوجد هنا تحليل مشاعر من وسائل التواصل الاجتماعي (يتطلب ذلك "
            "الوصول إلى واجهة برمجة تطبيقات مدفوعة غير متوفرة في هذه الأداة).",
        )}
      </div>
    </div>
    """


def na_placeholder():
    return tr("אין נתון", "N/A", "N/D", "N/D", "غير متوفر")


# תרגומי תוויות עמוד "הכסף שלי" - dict יחיד שגם בונה את row_labels (HTML) וגם
# מיוצא כ-JSON ל-JS (MONEY_LABELS), כדי שמקרא גרף העוגה יתעדכן בהחלפת שפה
# ולא יישאר קבוע בעברית כמו שהיה לפני התיקון.
MONEY_LABEL_TRANSLATIONS = {
    "general_savings": {"he": "כללי / חיסכון", "en": "General / Savings", "es": "General / Ahorros", "fr": "Général / Épargne", "ar": "عام / مدخرات"},
    "ibi": {"he": "IBI (ברוקר)", "en": "IBI (broker)", "es": "IBI (bróker)", "fr": "IBI (courtier)", "ar": "IBI (وسيط)"},
    "checking": {"he": "עובר ושב", "en": "Checking account", "es": "Cuenta corriente", "fr": "Compte courant", "ar": "حساب جاري"},
    "sp500": {"he": "S&P 500", "en": "S&P 500", "es": "S&P 500", "fr": "S&P 500", "ar": "S&P 500"},
    "cash": {"he": "מזומן", "en": "Cash", "es": "Efectivo", "fr": "Espèces", "ar": "نقد"},
    "forex": {"he": 'חשבון מט"ח', "en": "Forex account", "es": "Cuenta forex", "fr": "Compte forex", "ar": "حساب فوركس"},
    "bitcoin": {"he": "ביטקוין", "en": "Bitcoin", "es": "Bitcoin", "fr": "Bitcoin", "ar": "بيتكوين"},
}


def build_money_page(exchange_rates):
    """
    בונה עמוד "הכסף שלי" - נכסים כלליים (לא רק מניות) עם שדות עריכה ישירים בדף.
    הסכומים ניתנים לעריכה ישירות בדפדפן, כדי שלא נצטרך לנחש מספרים מטקסט -
    אתה מקליד את הסכום הנכון, השמש מתעדכנת מיד.
    """
    # שורות ברירת מחדל - חלק מהסכומים מולאו כניחוש ראשוני לפי מה שכתבת, אבל הכל ניתן לעריכה.
    # שדות עם אי-ודאות (שהמספרים התחלפו בין ההודעות) מולאו באפס בכוונה - תמלא את המספר הנכון.
    default_rows = [
        {"label_key": "general_savings", "amount": 150000, "currency": "ILS"},
        {"label_key": "ibi", "amount": 32978, "currency": "ILS"},
        {"label_key": "checking", "amount": 35000, "currency": "ILS"},
        {"label_key": "sp500", "amount": 2704, "currency": "USD"},
        {"label_key": "cash", "amount": 9000, "currency": "ILS"},
        {"label_key": "forex", "amount": 0, "currency": "USD"},
        {"label_key": "bitcoin", "amount": 0, "currency": "USD"},
    ]

    row_labels = {key: tr_d(translations) for key, translations in MONEY_LABEL_TRANSLATIONS.items()}

    rates = exchange_rates or {}
    fallback_rates = {"USD": 3.7, "EUR": 4.0, "GBP": 4.7, "JPY": 0.025}
    currency_symbols = {"ILS": "₪", "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥"}

    rows_html = ""
    for row in default_rows:
        currency_options = ""
        for code, symbol in currency_symbols.items():
            selected = "selected" if row["currency"] == code else ""
            currency_options += f'<option value="{code}" {selected}>{symbol}</option>'
        rows_html += f"""
        <tr>
          <td class="money-label">{row_labels[row['label_key']]}</td>
          <td>
            <input type="number" class="money-input" id="money-amount-{row['label_key']}"
                   value="{row['amount']}" step="any" oninput="updateMoneyTotal()">
          </td>
          <td>
            <select class="money-currency" id="money-currency-{row['label_key']}" onchange="updateMoneyTotal()">
              {currency_options}
            </select>
          </td>
        </tr>
        """

    rate_rows_html = ""
    for code in ["USD", "EUR", "GBP", "JPY"]:
        fetched = rates.get(code)
        value = fetched if fetched else fallback_rates[code]
        note = (
            tr("שער אמיתי", "Live rate", "Tasa real", "Taux réel", "سعر حقيقي")
            if fetched
            else tr("משוער - כדאי לתקן", "Estimated - worth correcting", "Estimado - conviene corregir", "Estimé - à corriger", "تقديري - يُستحسن تصحيحه")
        )
        rate_rows_html += f"""
        <div class="exchange-rate-row">
          <label>{currency_symbols[code]} {code}-{tr("שקל", "ILS", "ILS", "ILS", "شيكل")}:</label>
          <input type="number" id="rate-{code}" class="money-input" value="{value}" step="any" oninput="updateMoneyTotal()" style="width:80px">
          <span class="rate-source-note">({note})</span>
        </div>
        """

    piggy_html = build_piggy_visual(
        tr("הכסף של שי", "Shai's Money", "Dinero de Shai", "Argent de Shai", "أموال شاي"),
        "₪ 0",
        "money-total-display",
        tr("מתעדכן אוטומטית כשמשנים בטבלה", "Updates automatically as you edit the table", "Se actualiza automáticamente al editar la tabla", "Se met à jour automatiquement en modifiant le tableau", "يتم التحديث تلقائياً عند تعديل الجدول"),
    )

    return f"""
    <div class="sun-page">
      {piggy_html}

      <div class="portfolio-table-wrap">
        <h2>💰 {tr("פיזור הכסף", "Money Distribution", "Distribución del Dinero", "Répartition de l'Argent", "توزيع الأموال")}</h2>
        <p class="portfolio-note">
          {tr(
              "כל הסכומים ניתנים לעריכה - פשוט תקליד את המספר הנכון בכל שדה, החזרזיר למעלה יתעדכן מיד. "
              "שדות עם 0 הם כאלה שלא הייתי בטוח לגביהם.",
              "All amounts are editable - just type the correct number in each field, the piggy above "
              "updates immediately. Fields showing 0 are ones I wasn't confident about.",
              "Todos los montos son editables - simplemente escribe el número correcto en cada campo, "
              "el cerdito de arriba se actualiza de inmediato. Los campos con 0 son aquellos de los que no estaba seguro.",
              "Tous les montants sont modifiables - il suffit de saisir le bon nombre dans chaque champ, "
              "le cochon ci-dessus se met à jour immédiatement. Les champs à 0 sont ceux dont je n'étais pas sûr.",
              "جميع المبالغ قابلة للتعديل - فقط اكتب الرقم الصحيح في كل حقل، وسيتحدث الخنزير أعلاه فوراً. "
              "الحقول التي تظهر 0 هي تلك التي لم أكن متأكداً منها.",
          )}
        </p>
        <table class="portfolio-table">
          <thead>
            <tr>
              <th>{tr("נכס", "Asset", "Activo", "Actif", "الأصل")}</th>
              <th>{tr("סכום", "Amount", "Monto", "Montant", "المبلغ")}</th>
              <th>{tr("מטבע", "Currency", "Moneda", "Devise", "العملة")}</th>
            </tr>
          </thead>
          <tbody>
            {rows_html}
          </tbody>
        </table>
        <div class="exchange-rates-section">
          <div class="exchange-rates-title">{tr("שערי חליפין", "Exchange rates", "Tipos de cambio", "Taux de change", "أسعار الصرف")}</div>
          {rate_rows_html}
        </div>
        <button class="save-money-btn" onclick="manualSaveMoneyData()">
          {tr("שמור", "Save", "Guardar", "Enregistrer", "حفظ")} 💾
        </button>
        <button class="save-money-btn export-btn" onclick="exportMoneyData()">
          {tr("ייצוא לקובץ", "Export to file", "Exportar a archivo", "Exporter vers un fichier", "تصدير إلى ملف")} ⬇️
        </button>
        <span class="save-confirm" id="save-confirm-msg"></span>
      </div>

      <div class="portfolio-table-wrap goal-section">
        <h2>🎯 {tr("יעד חיסכון", "Savings Goal", "Meta de Ahorro", "Objectif d'Épargne", "هدف الادخار")}</h2>
        <div class="goal-input-row">
          <label>{tr("היעד שלי", "My goal", "Mi meta", "Mon objectif", "هدفي")}: ₪</label>
          <input type="number" id="savings-goal-input" class="money-input" value="0" step="any" oninput="updateMoneyTotal()">
        </div>
        <div class="goal-progress-bar-bg">
          <div class="goal-progress-bar-fill" id="goal-progress-fill" style="width:0%"></div>
        </div>
        <div class="goal-progress-text" id="goal-progress-text">₪0 / ₪0 (0%)</div>
      </div>

      <div class="portfolio-table-wrap">
        <h2>🥧 {tr("פיזור לפי נכס", "Allocation by Asset", "Distribución por Activo", "Répartition par Actif", "التوزيع حسب الأصل")}</h2>
        <div class="pie-chart-row">
          <canvas id="allocation-pie-canvas" width="220" height="220"></canvas>
          <div id="allocation-legend" class="allocation-legend"></div>
        </div>
      </div>

      <div class="portfolio-table-wrap">
        <h2>📈 {tr("היסטוריית שווי נטו", "Net Worth History", "Historial de Patrimonio Neto", "Historique du Patrimoine Net", "سجل صافي الثروة")}</h2>
        <p class="portfolio-note">
          {tr(
              "כל פעם שאתה שומר, נוסף רישום עם התאריך והסכום. ככה רואים איך ההון גדל (או קטן) עם הזמן.",
              "Every time you save, a record with the date and amount is added. This way you can see how your net worth grows (or shrinks) over time.",
              "Cada vez que guardas, se agrega un registro con la fecha y el monto. Así puedes ver cómo crece (o disminuye) tu patrimonio con el tiempo.",
              "Chaque fois que vous enregistrez, un relevé avec la date et le montant est ajouté. Vous pouvez ainsi voir comment votre patrimoine évolue dans le temps.",
              "في كل مرة تحفظ فيها، تتم إضافة سجل بالتاريخ والمبلغ. بهذه الطريقة يمكنك رؤية كيف تنمو (أو تتقلص) ثروتك بمرور الوقت.",
          )}
        </p>
        <canvas id="net-worth-history-canvas" style="width:100%; height:200px; display:block;"></canvas>
        <div class="history-table-wrap">
          <table class="history-table">
            <thead>
              <tr>
                <th>{tr("תאריך", "Date", "Fecha", "Date", "التاريخ")}</th>
                <th>{tr("שווי נטו", "Net worth", "Patrimonio neto", "Patrimoine net", "صافي الثروة")}</th>
                <th>{tr("שינוי", "Change", "Cambio", "Variation", "التغير")}</th>
              </tr>
            </thead>
            <tbody id="net-worth-history-tbody"></tbody>
          </table>
          <p class="history-empty-note" id="net-worth-history-empty" style="display:none">
            {tr("עדיין אין מספיק היסטוריה - שמור כמה פעמים בימים שונים כדי לראות כאן טבלה.", "Not enough history yet - save a few times on different days to see a table here.", "Aún no hay suficiente historial - guarda varias veces en días distintos para ver una tabla aquí.", "Pas encore assez d'historique - enregistrez plusieurs fois à des jours différents pour voir un tableau ici.", "لا يوجد سجل كافٍ بعد - احفظ عدة مرات في أيام مختلفة لرؤية جدول هنا.")}
          </p>
        </div>
      </div>
    </div>
    """


def build_briefcase_visual(label_html, amount_html, amount_id, hint_html):
    """
    בונה ויזואל של תיק עסקים פתוח עם הסכום כתוב בפנים - לעמוד "תיק של שי".
    """
    id_attr = f' id="{amount_id}"' if amount_id else ""
    return f"""
    <div class="briefcase-container">
      <div class="briefcase-glow"></div>
      <div class="briefcase-emoji">💼</div>
      <div class="briefcase-amount-overlay"{id_attr}>{amount_html}</div>
    </div>
    <div class="piggy-info-card">
      <div class="piggy-label">{label_html}</div>
      <div class="piggy-hint">{hint_html}</div>
    </div>
    """


def build_piggy_visual(label_html, amount_html, amount_id, hint_html):
    """
    בונה את הוויזואל של "חזרזיר החיסכון" עם מטבעות מרחפים - משותף לעמוד התיק ולעמוד הכסף.
    amount_id: אם ניתן (לא None), ה-div של הסכום מקבל את ה-id הזה (לעדכון חי ב-JS).
    """
    id_attr = f' id="{amount_id}"' if amount_id else ""
    return f"""
    <div class="piggy-container" id="money-piggy-container">
      <div class="piggy-glow"></div>
      <div class="floating-coin coin-1">🪙</div>
      <div class="floating-coin coin-2">🪙</div>
      <div class="floating-coin coin-3">🪙</div>
      <div class="floating-coin coin-4">🪙</div>
      <div class="floating-coin coin-5">🪙</div>
      <div class="floating-coin coin-6">🪙</div>
      <div class="piggy-emoji">🐷</div>
    </div>
    <div class="piggy-info-card">
      <div class="piggy-label">{label_html}</div>
      <div class="piggy-amount"{id_attr}>{amount_html}</div>
      <div class="piggy-hint">{hint_html}</div>
    </div>
    """


def build_portfolio_view(ticker_stats):
    """
    בונה טבלת רווח/הפסד למניה, עם עמודת כמות מניות שניתנת לעריכה -
    ברגע שתמלא כמות, מחושב שווי אמיתי בדולרים ורווח/הפסד אמיתי (נשמר בדפדפן).
    """
    rows_html = ""
    valid_pcts = []
    for stat in ticker_stats:
        ticker = stat["ticker"]
        entry = config.ENTRY_PRICES.get(ticker)
        current = stat.get("latest_price")
        if entry is None or current is None:
            continue
        diff = current - entry
        pct = (diff / entry) * 100 if entry else 0
        valid_pcts.append(pct)
        color = "#2e7d32" if diff >= 0 else "#c62828"
        sign = "+" if diff >= 0 else ""
        rows_html += f"""
        <tr>
          <td class="port-ticker">{ticker}</td>
          <td>${entry:.2f}</td>
          <td>${current:.2f}</td>
          <td style="color:{color}">{sign}{diff:.2f}</td>
          <td style="color:{color}">{sign}{pct:.2f}%</td>
          <td>
            <input type="number" class="money-input qty-input" id="qty-{ticker}"
                   value="0" min="0" step="any" oninput="updatePortfolioTotal()" style="width:90px">
          </td>
          <td class="qty-value" id="qty-value-{ticker}">$0.00</td>
        </tr>
        """

    avg_pct = sum(valid_pcts) / len(valid_pcts) if valid_pcts else 0
    avg_color = "#2e7d32" if avg_pct >= 0 else "#c62828"
    avg_sign = "+" if avg_pct >= 0 else ""

    portfolio_table_html = f"""
    <div class="portfolio-table-wrap">
      <h2>💰 {tr("רווח/הפסד לפי מחיר", "Gain/Loss by price", "Ganancia/Pérdida por precio", "Gain/Perte par prix", "الربح/الخسارة حسب السعر")}</h2>
      <p class="portfolio-note">
        {tr(
            "השורות מציגות שינוי מחיר למניה בודדת. כדי לראות שווי אמיתי בדולרים, תמלא כמה מניות יש לך "
            "בעמודה 'כמות' - הכל נשמר אוטומטית בדפדפן. השורה התחתונה היא ממוצע פשוט (לא משוקלל).",
            "The rows show per-share price change. To see a real dollar value, fill in how many shares "
            "you hold in the 'Quantity' column - everything saves automatically in your browser. The "
            "bottom row is a simple average (not weighted).",
            "Las filas muestran el cambio de precio por acción. Para ver un valor real en dólares, "
            "completa cuántas acciones tienes en la columna 'Cantidad' - todo se guarda automáticamente "
            "en tu navegador. La fila inferior es un promedio simple (no ponderado).",
            "Les lignes montrent la variation de prix par action. Pour voir une valeur réelle en dollars, "
            "renseignez le nombre d'actions que vous détenez dans la colonne 'Quantité' - tout est "
            "enregistré automatiquement dans votre navigateur. La ligne du bas est une moyenne simple.",
            "تعرض الصفوف تغير السعر لكل سهم. لرؤية قيمة حقيقية بالدولار، املأ عدد الأسهم التي تملكها في "
            "عمود 'الكمية' - يتم الحفظ تلقائياً في متصفحك. الصف السفلي هو متوسط بسيط (غير مرجح).",
        )}
      </p>
      <table class="portfolio-table">
        <thead>
          <tr>
            <th>{tr("מניה", "Ticker", "Ticker", "Titre", "السهم")}</th>
            <th>{tr("מחיר כניסה", "Entry price", "Precio de entrada", "Prix d'entrée", "سعر الدخول")}</th>
            <th>{tr("מחיר נוכחי", "Current price", "Precio actual", "Prix actuel", "السعر الحالي")}</th>
            <th>{tr("שינוי ($)", "Change ($)", "Cambio ($)", "Variation ($)", "التغير ($)")}</th>
            <th>{tr("שינוי (%)", "Change (%)", "Cambio (%)", "Variation (%)", "التغير (%)")}</th>
            <th>{tr("כמות", "Quantity", "Cantidad", "Quantité", "الكمية")}</th>
            <th>{tr("שווי כולל", "Total value", "Valor total", "Valeur totale", "القيمة الإجمالية")}</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
        <tfoot>
          <tr>
            <td colspan="4">{tr("ממוצע פשוט", "Simple average", "Promedio simple", "Moyenne simple", "المتوسط البسيط")}</td>
            <td style="color:{avg_color}">{avg_sign}{avg_pct:.2f}%</td>
            <td></td>
            <td id="portfolio-total-value" style="font-weight:bold">$0.00</td>
          </tr>
        </tfoot>
      </table>
    </div>
    """

    piggy_html = build_briefcase_visual(
        tr("תיק של שי", "Shai's Portfolio", "Cartera de Shai", "Portefeuille de Shai", "محفظة شاي"),
        "$0.00",
        "portfolio-briefcase-total",
        tr(
            "מתעדכן אוטומטית לפי הכמות שתמלא בטבלה למטה",
            "Updates automatically based on the quantity you fill in the table below",
            "Se actualiza automáticamente según la cantidad que completes en la tabla de abajo",
            "Se met à jour automatiquement selon la quantité que vous renseignez dans le tableau ci-dessous",
            "يتم التحديث تلقائياً حسب الكمية التي تُدخلها في الجدول أدناه",
        ),
    )

    sun_view_html = f"""
    <div class="sun-page">
      {piggy_html}
      {portfolio_table_html}
    </div>
    """
    return sun_view_html


def build(weather_today, prices_today, stock_ranges, fundamentals=None, news=None, exchange_rates=None):
    """
    stock_ranges: תוצאה של fetch_data.fetch_stock_ranges() -
    dict בצורה {ticker: {"1D"/"1W"/"1M"/"3M"/"6M"/"1Y": {"dates","open","high","low","close","volume"}}}
    news: תוצאה של fetch_data.fetch_market_news() - רשימת כותרות חדשות אמיתיות מ-Yahoo Finance
    """
    weather_dates, weather_min, weather_max = read_weather_history()

    weather_desc_dict = WEATHER_DESCRIPTIONS.get(
        weather_today["weathercode"],
        {"he": "לא ידוע", "en": "Unknown", "es": "Desconocido", "fr": "Inconnu", "ar": "غير معروف"},
    )
    updated_at = datetime.now().strftime("%d/%m/%Y %H:%M")

    empty_range = {"dates": [], "open": [], "high": [], "low": [], "close": [], "volume": []}

    stock_cards_html = ""
    stock_charts_js = ""
    ticker_stats = []  # לסיכום השוק היומי - נאסף תוך כדי הלולאה
    for ticker in config.TICKERS:
        ranges = stock_ranges.get(ticker, {})
        data = ranges.get("3M", empty_range)
        closes = data["close"]
        latest = closes[-1] if closes else prices_today.get(ticker)
        prev = closes[-2] if len(closes) >= 2 else None

        change_html = ""
        pct = None
        if latest is not None and prev is not None:
            diff = latest - prev
            pct = (diff / prev) * 100 if prev else 0
            color = "#2e7d32" if diff >= 0 else "#c62828"
            sign = "+" if diff >= 0 else ""
            change_html = f'<span style="color:{color}">{sign}{diff:.2f} ({sign}{pct:.1f}%)</span>'

        # סיכום יומי - מה קרה היום
        if data["dates"]:
            day_open = data["open"][-1]
            day_high = data["high"][-1]
            day_low = data["low"][-1]
            day_volume = data["volume"][-1]
            daily_summary_html = f"""
            <div class="daily-summary">
              <span>{tr("פתיחה", "Open", "Apertura", "Ouverture", "افتتاح")}: ${day_open:.2f}</span>
              <span>{tr("גבוה", "High", "Máximo", "Haut", "أعلى")}: ${day_high:.2f}</span>
              <span>{tr("נמוך", "Low", "Mínimo", "Bas", "أدنى")}: ${day_low:.2f}</span>
              <span>{tr("נפח", "Volume", "Volumen", "Volume", "الحجم")}: {day_volume:,}</span>
            </div>
            """
        else:
            daily_summary_html = ""
            day_volume = None

        # אינדיקטורים טכניים - נתון אינפורמטיבי בלבד, לא המלצת השקעה
        sma20 = indicators.sma(closes, 20)
        sma50 = indicators.sma(closes, 50)
        rsi_val = indicators.rsi(closes, 14)
        trend_text = tr_d(indicators.trend_label_i18n(sma20, sma50))
        rsi_text = tr_d(indicators.rsi_label_i18n(rsi_val))

        # ייצוג ויזואלי קטן לאינדיקטורים - נקודת מגמה צבעונית + מד RSI, כדי שיהיה
        # אפשר לסרוק במבט חטוף בלי לקרוא את כל המשפט. הטקסט המלא נשאר לצד זה.
        if sma20 is not None and sma50 is not None and sma20 > sma50:
            trend_dot_class = "trend-up"
        elif sma20 is not None and sma50 is not None and sma20 < sma50:
            trend_dot_class = "trend-down"
        else:
            trend_dot_class = "trend-flat"

        if rsi_val is not None:
            rsi_pct = max(0.0, min(100.0, rsi_val))
            rsi_gauge_html = (
                '<div class="rsi-gauge" title="RSI">'
                '<div class="rsi-gauge-track"></div>'
                f'<div class="rsi-gauge-marker" style="left:{rsi_pct:.1f}%"></div>'
                "</div>"
            )
        else:
            rsi_gauge_html = ""

        # תג RSI קטן בפינת הכרטיס - כדי לראות קניית/מכירת יתר במבט חטוף בלי לפתוח כרטיס
        if rsi_val is not None and rsi_val >= 70:
            rsi_badge_html = f'<span class="rsi-badge overbought">🔴 {tr("קניית יתר", "Overbought", "Sobrecompra", "Surachat", "تشبع شرائي")}</span>'
        elif rsi_val is not None and rsi_val <= 30:
            rsi_badge_html = f'<span class="rsi-badge oversold">🟢 {tr("מכירת יתר", "Oversold", "Sobreventa", "Survente", "تشبع بيعي")}</span>'
        else:
            rsi_badge_html = ""

        # מסגרת עליונה שמגיבה לביצועי היום - ירוק/אדום עדין, כדי שסריקה של כל הרשת
        # תראה מיד מי עולה ומי יורד (הזהב עדיין מופיע ב-hover)
        if pct is not None and pct > 0:
            perf_class = "perf-up"
        elif pct is not None and pct < 0:
            perf_class = "perf-down"
        else:
            perf_class = "perf-flat"
        pct_attr = f"{pct:.4f}" if pct is not None else ""

        ticker_stats.append(
            {
                "ticker": ticker,
                "pct": pct,
                "latest_price": latest,
                "volume": day_volume,
                "trend_up": (sma20 is not None and sma50 is not None and sma20 > sma50),
                "trend_down": (sma20 is not None and sma50 is not None and sma20 < sma50),
                "rsi_overbought": (rsi_val is not None and rsi_val >= 70),
                "rsi_oversold": (rsi_val is not None and rsi_val <= 30),
            }
        )

        # נתוני יסוד ודירוג אנליסטים חיצוניים (לא דעה של הכלי)
        fund = (fundamentals or {}).get(ticker, {})
        na_text = tr("אין נתון", "N/A", "N/D", "N/D", "غير متوفر")
        pe = fund.get("pe_ratio")
        pe_text = f"{pe:.1f}" if pe else na_text
        market_cap_text = format_market_cap(fund.get("market_cap"))
        rec_key = fund.get("analyst_recommendation")
        rec_dict = RECOMMENDATION_LABELS.get(rec_key)
        rec_text = tr_d(rec_dict) if rec_dict else na_text
        analyst_count = fund.get("analyst_count")
        target_price = fund.get("target_mean_price")
        target_text = f"${target_price:.2f}" if target_price else na_text
        analysts_word = tr("אנליסטים", "analysts", "analistas", "analystes", "محللين")
        analysts_suffix = f" ({analyst_count} {analysts_word})" if analyst_count else ""

        fundamentals_html = f"""
        <div class="fundamentals">
          <div>P/E: {pe_text}</div>
          <div>{tr("שווי שוק", "Market cap", "Capitalización de mercado", "Capitalisation boursière", "القيمة السوقية")}: {market_cap_text}</div>
          <div>{tr("יעד מחיר ממוצע (אנליסטים)", "Avg. analyst price target", "Precio objetivo promedio (analistas)", "Objectif de cours moyen (analystes)", "متوسط السعر المستهدف (المحللين)")}: {target_text}</div>
          <div>{tr("דירוג אנליסטים ממוצע", "Avg. analyst rating", "Calificación promedio de analistas", "Note moyenne des analystes", "متوسط تقييم المحللين")}: {rec_text}{analysts_suffix}</div>
        </div>
        """

        price_display = f"${latest:.2f}" if latest is not None else na_text
        stock_cards_html += f"""
        <div class="card {perf_class}" onclick="openStockModal('{ticker}')" data-ticker="{ticker}" data-pct="{pct_attr}" data-rsi="{rsi_val if rsi_val is not None else ''}">
          <div class="card-header">
            {rsi_badge_html}
            <h3>{ticker}</h3>
            <div class="price-block">
              <canvas class="sparkline" id="spark-{ticker}"></canvas>
              <span class="price" id="price-{ticker}">{price_display}</span>
              <span class="change" id="change-{ticker}">{change_html}</span>
            </div>
          </div>
          {daily_summary_html}
          <canvas id="chart-{ticker}" height="220"></canvas>
          <div class="indicators">
            <div class="indicator-row"><span class="trend-dot {trend_dot_class}"></span>{trend_text}</div>
            <div class="indicator-row indicator-row-rsi">
              <span>📊 {rsi_text}</span>
              {rsi_gauge_html}
            </div>
          </div>
          {fundamentals_html}
          <div class="zoom-hint">🔍 {tr("לחץ להגדלה ולבחירת טווח זמן", "Click to expand and choose a time range", "Haz clic para expandir y elegir un rango de tiempo", "Cliquez pour agrandir et choisir une période", "انقر للتكبير واختيار نطاق زمني")}</div>
        </div>
        """

        # נתוני נרות - מצייר אותם בעצמנו ב-canvas, בלי תלות בספריית חוץ
        candles = [
            {
                "o": data["open"][i],
                "h": data["high"][i],
                "l": data["low"][i],
                "c": data["close"][i],
            }
            for i in range(len(data["dates"]))
        ]
        stock_charts_js += f"CARD_CANDLES['{ticker}'] = {json.dumps(candles)};\ndrawCandlestick('chart-{ticker}', CARD_CANDLES['{ticker}']);\ndrawSparkline('spark-{ticker}', CARD_CANDLES['{ticker}']);\n"

    market_summary_html = build_market_summary(ticker_stats, news)
    portfolio_view_html = build_portfolio_view(ticker_stats)
    money_page_html = build_money_page(exchange_rates)

    # מכינים גרסה קומפקטית של כל הטווחים (רק המערכים הדרושים לציור, כדי לא לכפול נתונים בכל טיקר)
    all_ranges_compact = {}
    for ticker in config.TICKERS:
        ranges = stock_ranges.get(ticker, {})
        all_ranges_compact[ticker] = {}
        for range_key, range_data in ranges.items():
            n = len(range_data.get("dates", []))
            all_ranges_compact[ticker][range_key] = {
                "dates": range_data["dates"],
                "candles": [
                    {
                        "o": range_data["open"][i],
                        "h": range_data["high"][i],
                        "l": range_data["low"][i],
                        "c": range_data["close"][i],
                        "v": range_data["volume"][i],
                    }
                    for i in range(n)
                ],
            }
    all_ranges_json = json.dumps(all_ranges_compact)

    portfolio_data = {}
    for stat in ticker_stats:
        ticker = stat["ticker"]
        entry = config.ENTRY_PRICES.get(ticker)
        current = stat.get("latest_price")
        if entry is not None and current is not None:
            portfolio_data[ticker] = {"entry": entry, "current": current}
    portfolio_data_json = json.dumps(portfolio_data)

    ticker_stats_json = json.dumps(
        [
            {
                "ticker": s["ticker"],
                "pct": s["pct"],
                "rsi_overbought": s["rsi_overbought"],
                "rsi_oversold": s["rsi_oversold"],
            }
            for s in ticker_stats
        ]
    )

    valid_stats_glance = [s for s in ticker_stats if s["pct"] is not None]
    valid_pcts_glance = [s["pct"] for s in valid_stats_glance]
    glance_avg_pct = sum(valid_pcts_glance) / len(valid_pcts_glance) if valid_pcts_glance else None
    glance_best = max(valid_stats_glance, key=lambda s: s["pct"]) if valid_stats_glance else None
    glance_worst = min(valid_stats_glance, key=lambda s: s["pct"]) if valid_stats_glance else None

    def glance_pct_html(pct):
        if pct is None:
            return na_placeholder()
        color = "#2e7d32" if pct >= 0 else "#c62828"
        sign = "+" if pct >= 0 else ""
        return f'<b style="color:{color}">{sign}{pct:.2f}%</b>'

    glance_strip_html = f"""
    <div class="glance-strip">
      <div class="glance-pill">📊 {tr("שינוי ממוצע היום", "Avg change today", "Cambio promedio hoy", "Variation moyenne", "متوسط التغير اليوم")}: {glance_pct_html(glance_avg_pct)}</div>
      <div class="glance-pill">🏆 {tr("המובילה", "Top", "Mejor", "Meilleure", "الأفضل")}: <b>{glance_best["ticker"] if glance_best else na_placeholder()}</b> {glance_pct_html(glance_best["pct"]) if glance_best else ""}</div>
      <div class="glance-pill">⚠️ {tr("החלשה", "Worst", "Peor", "Pire", "الأضعف")}: <b>{glance_worst["ticker"] if glance_worst else na_placeholder()}</b> {glance_pct_html(glance_worst["pct"]) if glance_worst else ""}</div>
    </div>
    """

    html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>שי פיננס</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #000000;
    --text: #e8e8e8;
    --text-dim: #999;
    --text-dimmer: #777;
    --heading: #ffffff;
    --card-bg: #121212;
    --card-border: #262626;
    --card-hover-border: #3a3a3a;
    --input-bg: #1a1a1a;
    --input-hover-bg: #262626;
    --input-border: #333333;
    --weather-bg: #14202e;
    --weather-text: #a9c6e8;
    --modal-bg: #0d0d0d;
    --summary-bg: #0f1420;
    --summary-border: #26314a;
    --summary-stat-bg: #161d2e;
    --news-border: #1c2536;
    --disclaimer-bg: #2a2410;
    --disclaimer-border: #4a3f10;
    --disclaimer-text: #e0c96b;
    --overlay: rgba(0,0,0,0.85);
    /* פלטת "בורסה" - כחול מוסדי עמוק לפעולות עיקריות, זהב לאקסנטים ולהדגשות */
    --accent: #1e4d8c;
    --accent-hover: #163c6e;
    --accent-text: #7fb2ff;
    --gold: #c9a227;
    --gold-dim: rgba(201,162,39,0.14);
    --masthead-bg: linear-gradient(180deg, #0c1626 0%, #0a1220 100%);
    --masthead-border: #1e4d8c;
  }}
  body.light-theme {{
    --bg: #f4f6f8;
    --text: #1a1a1a;
    --text-dim: #666666;
    --text-dimmer: #888888;
    --heading: #111111;
    --card-bg: #ffffff;
    --card-border: #e2e2e2;
    --card-hover-border: #c8c8c8;
    --input-bg: #f0f0f0;
    --input-hover-bg: #e4e4e4;
    --input-border: #cccccc;
    --weather-bg: #eaf1f8;
    --weather-text: #2c4a6b;
    --modal-bg: #ffffff;
    --summary-bg: #eef2f8;
    --summary-border: #d0dae8;
    --summary-stat-bg: #ffffff;
    --news-border: #e4e9f2;
    --disclaimer-bg: #fff8e1;
    --disclaimer-border: #f0e0a0;
    --disclaimer-text: #7a5c00;
    --overlay: rgba(0,0,0,0.5);
    --accent: #1a4a8a;
    --accent-hover: #123a70;
    --accent-text: #1a4a8a;
    --gold: #a3800c;
    --gold-dim: rgba(163,128,12,0.10);
    --masthead-bg: linear-gradient(180deg, #0f2947 0%, #0c223c 100%);
    --masthead-border: #a3800c;
  }}
  body {{
    font-family: "Rubik", -apple-system, "Segoe UI", Arial, sans-serif;
    background: var(--bg);
    margin: 0;
    padding: 24px;
    color: var(--text);
    font-variant-numeric: tabular-nums;
  }}
  h1 {{
    margin: 0 0 2px 0;
    font-size: 19px;
    font-weight: 700;
    letter-spacing: 0.03em;
    text-transform: uppercase;
    color: #ffffff;
  }}
  .updated {{ color: rgba(255,255,255,0.55); font-size: 12px; margin-bottom: 0; }}
  .top-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 22px;
    flex-wrap: wrap;
    gap: 12px;
    background: var(--masthead-bg);
    border-bottom: 2px solid var(--masthead-border);
    border-radius: 10px 10px 0 0;
    padding: 16px 20px;
  }}
  .top-bar .weather-strip, .top-bar .clock-strip {{
    background: rgba(255,255,255,0.08);
    color: #cfe0f5;
  }}
  .top-bar .lang-toggle, .top-bar select.lang-toggle, .top-bar button.lang-toggle {{
    background: rgba(255,255,255,0.10);
    color: #eaf1fb;
    border: 1px solid rgba(255,255,255,0.2);
  }}
  .top-bar .lang-toggle:hover {{ background: rgba(255,255,255,0.2); }}
  .top-bar .location-search-btn {{ filter: brightness(1.4); }}
  .lang-toggle {{
    background: var(--input-bg);
    color: var(--text);
    border: 1px solid var(--input-border);
    border-radius: 6px;
    padding: 6px 14px;
    cursor: pointer;
    font-size: 13px;
  }}
  .lang-toggle:hover {{ background: var(--input-hover-bg); }}
  .weather-strip {{
    background: var(--weather-bg);
    color: var(--weather-text);
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 14px;
    display: flex;
    align-items: center;
    gap: 10px;
    white-space: nowrap;
  }}
  .weather-strip .temp {{ font-weight: bold; font-size: 16px; }}
  .location-search-btn {{
    background: none;
    border: none;
    cursor: pointer;
    font-size: 14px;
    margin-right: 4px;
    opacity: 0.8;
  }}
  .location-search-btn:hover {{ opacity: 1; }}
  .clock-strip {{
    background: var(--weather-bg);
    color: var(--weather-text);
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 14px;
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .clock-tz-name {{ font-size: 11px; opacity: 0.75; }}
  .location-clickable {{ cursor: pointer; text-decoration: underline dotted; }}
  .location-clickable:hover {{ opacity: 0.8; }}
  .location-search-box {{
    position: absolute;
    top: 100%;
    right: 0;
    margin-top: 6px;
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 8px;
    padding: 10px;
    width: 240px;
    z-index: 100;
    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
  }}
  .location-search-box input {{
    width: 100%;
    padding: 8px 10px;
    border-radius: 6px;
    border: 1px solid var(--input-border);
    background: var(--input-bg);
    color: var(--text);
    font-size: 14px;
    box-sizing: border-box;
  }}
  .location-result {{
    padding: 8px 6px;
    cursor: pointer;
    font-size: 13px;
    color: var(--text);
    border-bottom: 1px solid var(--card-border);
  }}
  .location-result:hover {{ background: var(--input-hover-bg); }}
  .location-result:last-child {{ border-bottom: none; }}
  .location-result-empty {{ padding: 8px 6px; font-size: 12px; color: var(--text-dimmer); }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
    gap: 20px;
  }}
  .live-update-row {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
  }}
  .live-update-status {{ font-size: 12px; color: var(--text-dimmer); }}
  .card {{
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-top: 3px solid var(--accent);
    border-radius: 8px;
    padding: 24px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.15);
    cursor: pointer;
    transition: box-shadow 0.15s, border-color 0.15s;
  }}
  .card.perf-up {{ border-top-color: #2e7d32; }}
  .card.perf-down {{ border-top-color: #c62828; }}
  .card.perf-flat {{ border-top-color: var(--accent); }}
  .card:hover {{
    box-shadow: 0 4px 16px rgba(0,0,0,0.25);
    border-color: var(--card-hover-border);
    border-top-color: var(--gold);
  }}
  .card-header {{ position: relative; }}
  .rsi-badge {{
    position: absolute;
    top: -10px;
    left: 0;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.03em;
    padding: 2px 8px;
    border-radius: 10px;
    white-space: nowrap;
  }}
  .rsi-badge.overbought {{ background: rgba(198,40,40,0.16); color: #e05252; }}
  .rsi-badge.oversold {{ background: rgba(46,125,50,0.16); color: #4caf50; }}
  .sparkline {{ width: 72px; height: 26px; display: block; margin-bottom: 4px; }}
  .price.price-flash-up {{ animation: price-flash-up 0.9s ease; }}
  .price.price-flash-down {{ animation: price-flash-down 0.9s ease; }}
  @keyframes price-flash-up {{
    0% {{ color: #2e7d32; }} 100% {{ color: var(--heading); }}
  }}
  @keyframes price-flash-down {{
    0% {{ color: #c62828; }} 100% {{ color: var(--heading); }}
  }}
  .zoom-hint {{
    margin-top: 10px;
    font-size: 12px;
    color: var(--text-dimmer);
    text-align: center;
  }}
  .card-header {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 14px;
  }}
  .card h3 {{ margin: 0; font-size: 21px; font-weight: 700; letter-spacing: 0.04em; color: var(--heading); }}
  .price-block {{ text-align: left; }}
  .price {{ font-size: 26px; font-weight: 700; display: block; color: var(--heading); }}
  .change {{ font-size: 15px; font-weight: 600; }}
  .card canvas {{ width: 100%; height: 220px; display: block; }}
  .daily-summary {{
    display: flex;
    gap: 14px;
    flex-wrap: wrap;
    font-size: 13px;
    color: var(--text-dim);
    margin-bottom: 10px;
    border-bottom: 1px solid var(--card-border);
    padding-bottom: 10px;
  }}
  .indicators {{
    margin-top: 12px;
    font-size: 13px;
    color: var(--text-dim);
    display: flex;
    flex-direction: column;
    gap: 4px;
  }}
  .indicator-row {{ display: flex; align-items: center; gap: 6px; }}
  .indicator-row-rsi {{ justify-content: space-between; }}
  .trend-dot {{
    display: inline-block; width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
  }}
  .trend-dot.trend-up {{ background: #2e7d32; }}
  .trend-dot.trend-down {{ background: #c62828; }}
  .trend-dot.trend-flat {{ background: var(--text-dimmer); }}
  .rsi-gauge {{ position: relative; width: 64px; height: 6px; flex-shrink: 0; }}
  .rsi-gauge-track {{
    position: absolute; inset: 0; border-radius: 3px;
    background: linear-gradient(90deg, #2e7d32 0%, #2e7d32 30%, var(--input-border) 30%, var(--input-border) 70%, #c62828 70%, #c62828 100%);
    opacity: 0.55;
  }}
  .rsi-gauge-marker {{
    position: absolute; top: -2px; width: 2px; height: 10px;
    background: var(--heading); border-radius: 1px; transform: translateX(-1px);
  }}
  .fundamentals {{
    margin-top: 12px;
    padding-top: 10px;
    border-top: 1px solid var(--card-border);
    font-size: 13px;
    color: var(--text-dim);
    display: flex;
    flex-direction: column;
    gap: 4px;
  }}
  .disclaimer {{
    margin-top: 32px;
    padding: 16px;
    background: var(--disclaimer-bg);
    border: 1px solid var(--disclaimer-border);
    border-radius: 8px;
    font-size: 13px;
    color: var(--disclaimer-text);
    text-align: center;
  }}
  .market-summary {{
    background: var(--summary-bg);
    border: 1px solid var(--summary-border);
    border-top: 3px solid var(--gold);
    border-radius: 8px;
    padding: 24px;
    margin-bottom: 24px;
  }}
  .market-summary h2 {{
    margin: 0 0 16px 0;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--heading);
  }}
  .summary-stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 12px;
    margin-bottom: 16px;
  }}
  .summary-stat {{
    background: var(--summary-stat-bg);
    border-radius: 8px;
    padding: 12px 14px;
  }}
  .summary-stat-label {{ font-size: 12px; color: var(--text-dim); margin-bottom: 4px; }}
  .summary-stat-value {{ font-size: 18px; font-weight: bold; color: var(--text); }}
  .summary-technical {{
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
    font-size: 13px;
    color: var(--text-dim);
    padding: 12px 0;
    border-top: 1px solid var(--summary-border);
    border-bottom: 1px solid var(--summary-border);
    margin-bottom: 16px;
  }}
  .summary-news h3 {{ font-size: 15px; color: var(--heading); margin: 0 0 10px 0; }}
  .news-item {{
    display: flex;
    align-items: baseline;
    gap: 10px;
    padding: 8px 0;
    border-bottom: 1px solid var(--news-border);
    font-size: 13px;
    flex-wrap: wrap;
  }}
  .news-item:last-child {{ border-bottom: none; }}
  .news-ticker {{
    background: var(--summary-border);
    color: var(--weather-text);
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: bold;
    flex-shrink: 0;
  }}
  .news-title {{ color: var(--text); text-decoration: none; flex: 1; min-width: 200px; }}
  .news-title:hover {{ color: var(--weather-text); text-decoration: underline; }}
  .news-publisher {{ color: var(--text-dimmer); font-size: 11px; flex-shrink: 0; }}
  .news-date {{ color: var(--text-dimmer); font-size: 11px; flex-shrink: 0; }}
  .summary-news-empty {{ color: var(--text-dimmer); font-size: 13px; }}
  .summary-note {{
    margin-top: 16px;
    padding-top: 12px;
    border-top: 1px solid var(--summary-border);
    font-size: 11px;
    color: var(--text-dimmer);
  }}
  .modal-overlay {{
    display: none;
    position: fixed;
    top: 0; right: 0; bottom: 0; left: 0;
    background: var(--overlay);
    z-index: 1000;
    align-items: center;
    justify-content: center;
  }}
  .modal-overlay.open {{ display: flex; }}
  .modal-box {{
    background: var(--modal-bg);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    padding: 24px;
    width: 95vw;
    height: 92vh;
    max-width: none;
    max-height: 92vh;
    overflow-y: auto;
    cursor: default;
    display: flex;
    flex-direction: column;
  }}
  .modal-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }}
  .modal-header h2 {{ margin: 0; font-size: 26px; color: var(--heading); }}
  .modal-close {{
    background: none;
    border: none;
    font-size: 22px;
    cursor: pointer;
    color: var(--text-dim);
  }}
  .modal-close:hover {{ color: var(--heading); }}
  .range-buttons {{
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
    flex-wrap: wrap;
  }}
  .range-buttons button {{
    padding: 6px 16px;
    border-radius: 6px;
    border: 1px solid var(--input-border);
    background: var(--input-bg);
    color: var(--text);
    cursor: pointer;
    font-size: 14px;
  }}
  .range-buttons button:hover {{ background: var(--input-hover-bg); }}
  .range-buttons button.active {{
    background: var(--accent);
    color: white;
    border-color: var(--accent);
  }}
  .modal-range-label {{
    font-size: 12px;
    color: var(--text-dim);
    margin-bottom: 8px;
  }}
  .zoom-instructions {{
    font-size: 12px;
    color: var(--weather-text);
    margin-bottom: 8px;
  }}
  #drawing-info-panel {{
    margin-top: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 140px;
    overflow-y: auto;
  }}
  .drawing-info-card {{
    background: var(--input-bg);
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 13px;
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
    align-items: center;
    border-right: 3px solid #b968e0;
    color: var(--text);
  }}
  .drawing-info-card.fibonacci {{ border-right-color: #ff9800; }}
  .drawing-info-card .di-label {{ font-weight: bold; min-width: 70px; color: var(--heading); }}
  .delete-drawing-btn {{
    margin-right: auto;
    background: none;
    border: 1px solid var(--input-border);
    color: var(--text-dim);
    border-radius: 4px;
    width: 22px;
    height: 22px;
    cursor: pointer;
    font-size: 12px;
    flex-shrink: 0;
  }}
  .delete-drawing-btn:hover {{ background: #c62828; color: white; border-color: #c62828; }}
  #modal-canvas {{ width: 100%; flex: 1 1 auto; min-height: 400px; display: block; }}
  .nav-tabs {{
    display: flex;
    gap: 8px;
    margin-bottom: 20px;
    border-bottom: 1px solid var(--card-border);
  }}
  .nav-tab {{
    background: none;
    border: none;
    border-bottom: 3px solid transparent;
    color: var(--text-dim);
    padding: 10px 18px;
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.02em;
    cursor: pointer;
  }}
  .nav-tab:hover {{ color: var(--text); }}
  .nav-tab.active {{ color: var(--heading); border-bottom-color: var(--gold); font-weight: 700; }}
  .sun-page {{ display: flex; flex-direction: column; align-items: center; gap: 16px; }}
  .piggy-container {{
    position: relative;
    width: 280px;
    height: 240px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-top: 24px;
  }}
  .piggy-glow {{
    position: absolute;
    width: 200px;
    height: 200px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255,182,193,0.45), transparent 70%);
    filter: blur(12px);
    animation: piggy-pulse 3s ease-in-out infinite;
  }}
  @keyframes piggy-pulse {{
    0%, 100% {{ transform: scale(1); opacity: 0.7; }}
    50% {{ transform: scale(1.1); opacity: 1; }}
  }}
  .piggy-emoji {{
    position: relative;
    font-size: 120px;
    z-index: 2;
    filter: drop-shadow(0 8px 14px rgba(0,0,0,0.25));
    animation: piggy-bob 4s ease-in-out infinite;
  }}
  @keyframes piggy-bob {{
    0%, 100% {{ transform: translateY(0) rotate(-2deg); }}
    50% {{ transform: translateY(-10px) rotate(2deg); }}
  }}
  .floating-coin {{
    position: absolute;
    font-size: 26px;
    animation: coin-float 6s ease-in-out infinite;
    filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
  }}
  @keyframes coin-float {{
    0%, 100% {{ transform: translateY(0) rotate(0deg); opacity: 0.85; }}
    50% {{ transform: translateY(-18px) rotate(15deg); opacity: 1; }}
  }}
  .coin-1 {{ top: 8%; left: 12%; animation-delay: 0s; }}
  .coin-2 {{ top: 18%; right: 8%; animation-delay: 0.8s; }}
  .coin-3 {{ top: 55%; left: 2%; animation-delay: 1.6s; }}
  .coin-4 {{ top: 58%; right: 2%; animation-delay: 2.4s; }}
  .coin-5 {{ top: 2%; left: 48%; animation-delay: 3.2s; }}
  .coin-6 {{ bottom: 4%; left: 42%; animation-delay: 4s; }}
  .piggy-info-card {{
    text-align: center;
    background: var(--summary-stat-bg);
    border: 1px solid var(--summary-border);
    border-radius: 12px;
    padding: 14px 24px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.15);
  }}
  .piggy-label {{ font-size: 16px; font-weight: bold; margin-bottom: 6px; color: var(--heading); }}
  .piggy-amount {{ font-size: 28px; font-weight: bold; margin-bottom: 6px; color: var(--heading); }}
  .piggy-hint {{ font-size: 11px; opacity: 0.75; max-width: 260px; color: var(--text-dim); }}
  .briefcase-container {{
    position: relative;
    width: 280px;
    height: 220px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-top: 24px;
  }}
  .briefcase-glow {{
    position: absolute;
    width: 200px;
    height: 170px;
    border-radius: 24px;
    background: radial-gradient(circle, rgba(180,140,90,0.4), transparent 70%);
    filter: blur(12px);
    animation: piggy-pulse 3s ease-in-out infinite;
  }}
  .briefcase-emoji {{
    position: relative;
    font-size: 150px;
    z-index: 1;
    filter: drop-shadow(0 8px 14px rgba(0,0,0,0.3));
    animation: piggy-bob 4s ease-in-out infinite;
  }}
  .briefcase-amount-overlay {{
    position: absolute;
    z-index: 2;
    top: 60%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(255,255,255,0.94);
    color: #3a2a10;
    font-weight: bold;
    font-size: 17px;
    padding: 4px 14px;
    border-radius: 8px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.3);
    white-space: nowrap;
  }}
  .portfolio-table-wrap {{ width: 100%; max-width: 900px; }}
  .portfolio-table-wrap h2 {{ color: var(--heading); font-size: 20px; }}
  .portfolio-note {{
    font-size: 12px;
    color: var(--text-dim);
    background: var(--summary-bg);
    border: 1px solid var(--summary-border);
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 16px;
  }}
  .portfolio-table {{
    width: 100%;
    border-collapse: collapse;
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 10px;
    overflow: hidden;
  }}
  .portfolio-table th, .portfolio-table td {{
    padding: 10px 14px;
    text-align: right;
    font-size: 14px;
    border-bottom: 1px solid var(--card-border);
  }}
  .portfolio-table th {{ color: var(--text-dim); font-size: 12px; }}
  .portfolio-table td {{ color: var(--text); }}
  .portfolio-table .port-ticker {{ font-weight: bold; color: var(--heading); }}
  .qty-value {{ font-weight: bold; color: var(--heading); }}
  .portfolio-table tfoot td {{ font-weight: bold; border-top: 2px solid var(--card-border); border-bottom: none; }}
  .money-label {{ font-weight: bold; color: var(--heading); }}
  .money-input {{
    width: 120px;
    padding: 6px 10px;
    border-radius: 6px;
    border: 1px solid var(--input-border);
    background: var(--input-bg);
    color: var(--text);
    font-size: 14px;
  }}
  .money-currency {{
    padding: 6px 8px;
    border-radius: 6px;
    border: 1px solid var(--input-border);
    background: var(--input-bg);
    color: var(--text);
    font-size: 14px;
  }}
  .exchange-rate-row {{
    margin-top: 6px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: var(--text-dim);
  }}
  .exchange-rates-section {{
    margin-top: 16px;
    padding-top: 12px;
    border-top: 1px solid var(--card-border);
  }}
  .exchange-rates-title {{ font-size: 14px; font-weight: bold; color: var(--heading); margin-bottom: 8px; }}
  .save-money-btn {{
    margin-top: 16px;
    padding: 8px 20px;
    border-radius: 6px;
    border: 1px solid var(--input-border);
    background: var(--accent);
    color: white;
    cursor: pointer;
    font-size: 14px;
    font-weight: bold;
  }}
  .save-money-btn:hover {{ background: var(--accent-hover); }}
  .save-confirm {{
    margin-right: 10px;
    font-size: 13px;
    color: #2e7d32;
    font-weight: bold;
  }}
  .export-btn {{ background: #6b4423; margin-right: 8px; }}
  .export-btn:hover {{ background: #57371c; }}
  .goal-section {{ margin-top: 24px; }}
  .goal-input-row {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    font-size: 14px;
    color: var(--text-dim);
  }}
  .goal-progress-bar-bg {{
    width: 100%;
    height: 20px;
    border-radius: 10px;
    background: var(--input-bg);
    border: 1px solid var(--input-border);
    overflow: hidden;
  }}
  .goal-progress-bar-fill {{
    height: 100%;
    background: linear-gradient(90deg, var(--accent), var(--gold));
    transition: width 0.4s ease;
  }}
  .goal-progress-text {{
    margin-top: 8px;
    font-size: 13px;
    color: var(--text-dim);
    text-align: center;
  }}
  .pie-chart-row {{
    display: flex;
    align-items: center;
    gap: 24px;
    flex-wrap: wrap;
  }}
  .allocation-legend {{
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-size: 13px;
    color: var(--text);
  }}
  .legend-item {{ display: flex; align-items: center; gap: 8px; }}
  .legend-swatch {{ width: 12px; height: 12px; border-radius: 3px; flex-shrink: 0; }}
  .rate-source-note {{ font-size: 11px; color: var(--text-dimmer); }}

  /* --- שורת תמונת מצב ("במבט חטוף") --- */
  .glance-strip {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 16px;
  }}
  .glance-pill {{
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--summary-stat-bg);
    border: 1px solid var(--summary-border);
    border-radius: 999px;
    padding: 8px 16px;
    font-size: 13px;
    color: var(--text-dim);
  }}
  .glance-pill b {{ color: var(--heading); font-size: 14px; }}

  /* --- בקרות מיון ותצוגת חום --- */
  .stock-controls-row {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
  select.stock-sort-select {{
    background: var(--input-bg);
    color: var(--text);
    border: 1px solid var(--input-border);
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 13px;
    cursor: pointer;
  }}
  .heatmap-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
    gap: 8px;
    margin-bottom: 20px;
  }}
  .heatmap-tile {{
    border-radius: 8px;
    padding: 16px 10px;
    text-align: center;
    color: #ffffff;
    cursor: pointer;
    transition: transform 0.12s;
  }}
  .heatmap-tile:hover {{ transform: scale(1.05); }}
  .heatmap-tile .ht-ticker {{ font-weight: 800; font-size: 15px; letter-spacing: 0.03em; }}
  .heatmap-tile .ht-pct {{ font-size: 13px; margin-top: 4px; font-weight: 600; }}

  /* --- טבלת היסטוריית שווי נטו --- */
  .history-table-wrap {{ margin-top: 14px; }}
  .history-table {{
    width: 100%;
    border-collapse: collapse;
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 10px;
    overflow: hidden;
  }}
  .history-table th, .history-table td {{
    padding: 8px 14px;
    text-align: right;
    font-size: 13px;
    border-bottom: 1px solid var(--card-border);
  }}
  .history-table th {{ color: var(--text-dim); font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; }}
  .history-table tr:last-child td {{ border-bottom: none; }}
  .history-table tbody tr:nth-child(even) td {{ background: var(--summary-bg); }}
  .history-empty-note {{ font-size: 12px; color: var(--text-dimmer); padding: 10px 2px; }}

  /* --- חזרזיר גדל + קונפטי ביעד --- */
  #money-piggy-container {{ transition: transform 0.6s cubic-bezier(.34,1.56,.64,1); transform-origin: center bottom; }}
  .confetti-piece {{
    position: absolute;
    width: 8px;
    height: 8px;
    top: 30%;
    left: 50%;
    opacity: 0.95;
    border-radius: 2px;
    animation: confetti-fall 1.3s ease-out forwards;
    z-index: 3;
  }}
  @keyframes confetti-fall {{
    0% {{ transform: translate(0, 0) rotate(0deg); opacity: 1; }}
    100% {{ transform: translate(var(--dx), 200px) rotate(720deg); opacity: 0; }}
  }}

  /* --- הערות אישיות למניה (במודל) --- */
  .stock-notes-wrap {{ margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--card-border); }}
  .stock-notes-label {{ font-size: 12px; color: var(--text-dim); margin-bottom: 6px; display: block; }}
  .stock-notes-textarea {{
    width: 100%;
    min-height: 64px;
    resize: vertical;
    box-sizing: border-box;
    background: var(--input-bg);
    color: var(--text);
    border: 1px solid var(--input-border);
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 13px;
    font-family: inherit;
  }}
  .stock-notes-saved {{ font-size: 11px; color: #2e7d32; margin-top: 4px; height: 14px; }}

  /* --- מובייל --- */
  @media (max-width: 640px) {{
    body {{ padding: 12px; }}
    .top-bar {{ padding: 12px 14px; flex-direction: column; align-items: stretch; }}
    .top-bar > div:last-child {{ justify-content: flex-start; flex-wrap: wrap; }}
    h1 {{ font-size: 16px; }}
    .grid {{ grid-template-columns: 1fr; }}
    .nav-tab {{ padding: 8px 10px; font-size: 13px; }}
    .modal-box {{ width: 100vw; height: 100vh; max-height: 100vh; border-radius: 0; padding: 14px; }}
    .portfolio-table-wrap {{ max-width: 100%; }}
    .portfolio-table, .history-table {{ display: block; overflow-x: auto; white-space: nowrap; }}
    .summary-stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
    .heatmap-grid {{ grid-template-columns: repeat(3, 1fr); }}
  }}
</style>
</head>
<body>
  <div class="top-bar">
    <div>
      <h1>{tr("שי פיננס", "Shai Finance", "Shai Finanzas", "Shai Finance", "شاي المالية")} 💼</h1>
      <p class="updated">{tr("עודכן לאחרונה", "Last updated", "Última actualización", "Dernière mise à jour", "آخر تحديث")}: {updated_at}</p>
    </div>
    <div style="display:flex; align-items:center; gap:12px; position:relative;">
      <div class="weather-strip">
        <span>🌤️ <span id="weather-location-name">{config.LOCATION_NAME}</span>:</span>
        <span class="temp" id="weather-temp">{weather_today['temp_min']:.0f}°-{weather_today['temp_max']:.0f}°</span>
        <span id="weather-desc-display">{tr_d(weather_desc_dict)}</span>
        <button class="location-search-btn" onclick="toggleLocationSearch()" {attr_i18n('title', 'שנה מיקום', 'Change location', 'Cambiar ubicación', 'Changer de lieu', 'تغيير الموقع')}>📍</button>
      </div>
      <div class="clock-strip">
        🕐 <span id="clock-display">--:--:--</span>
        <span class="clock-tz-name" id="clock-tz-name">{config.LOCATION_NAME}</span>
      </div>
      <div class="location-search-box" id="location-search-box" style="display:none">
        <input type="text" id="location-search-input" {attr_i18n('placeholder', 'חפש עיר...', 'Search city...', 'Buscar ciudad...', 'Rechercher une ville...', 'ابحث عن مدينة...')} oninput="searchLocation()">
        <div id="location-search-results"></div>
      </div>
      <select class="lang-toggle" id="lang-select" onchange="selectLanguage(this.value)">
        <option value="he">🌐 עברית</option>
        <option value="en">🌐 English</option>
        <option value="es">🌐 Español</option>
        <option value="fr">🌐 Français</option>
        <option value="ar">🌐 العربية</option>
      </select>
      <button class="lang-toggle" id="theme-toggle-btn" onclick="toggleTheme()">🌙</button>
      <button class="lang-toggle" onclick="location.reload()">{tr("רענון", "Refresh", "Actualizar", "Actualiser", "تحديث")} 🔄</button>
    </div>
  </div>

  <div class="nav-tabs">
    <button class="nav-tab active" id="nav-tab-stocks" onclick="showPage('stocks')">{tr("מניות", "Stocks", "Acciones", "Actions", "الأسهم")} 📊</button>
    <button class="nav-tab" id="nav-tab-portfolio" onclick="showPage('portfolio')">{tr("תיק של שי", "Shai's Portfolio", "Cartera de Shai", "Portefeuille de Shai", "محفظة شاي")} 💼</button>
    <button class="nav-tab" id="nav-tab-money" onclick="showPage('money')">{tr("הכסף של שי", "Shai's Money", "Dinero de Shai", "Argent de Shai", "أموال شاي")} 🐷</button>
  </div>

  <div id="page-stocks" class="page-view">
    {glance_strip_html}
    <div class="live-update-row">
      <button class="lang-toggle" id="live-update-btn" onclick="toggleLiveUpdates()">🔴 {tr("עדכון חי (נסיוני)", "Live update (experimental)", "Actualización en vivo (experimental)", "Mise à jour en direct (expérimental)", "تحديث مباشر (تجريبي)")}</button>
      <span class="live-update-status" id="live-update-status"></span>
    </div>
    <div class="stock-controls-row">
      <select class="stock-sort-select" id="stock-sort-select" onchange="applySortStocks(this.value)">
        <option value="default">{tr("מיון: ברירת מחדל", "Sort: default", "Orden: predeterminado", "Tri: par défaut", "الترتيب: افتراضي")}</option>
        <option value="pct-desc">{tr("מיון: % שינוי (גבוה→נמוך)", "Sort: % change (high→low)", "Orden: % cambio (alto→bajo)", "Tri: % variation (haut→bas)", "الترتيب: % التغير (الأعلى→الأدنى)")}</option>
        <option value="pct-asc">{tr("מיון: % שינוי (נמוך→גבוה)", "Sort: % change (low→high)", "Orden: % cambio (bajo→alto)", "Tri: % variation (bas→haut)", "الترتيب: % التغير (الأدنى→الأعلى)")}</option>
        <option value="alpha">{tr("מיון: א-ב", "Sort: A-Z", "Orden: A-Z", "Tri: A-Z", "الترتيب: أبجدي")}</option>
        <option value="rsi">{tr("מיון: RSI", "Sort: RSI", "Orden: RSI", "Tri: RSI", "الترتيب: RSI")}</option>
      </select>
      <button class="lang-toggle" id="heatmap-toggle-btn" onclick="toggleHeatmapView()">🗺️ {tr("תצוגת חום", "Heatmap view", "Vista de mapa de calor", "Vue carte thermique", "عرض الخريطة الحرارية")}</button>
      <a class="lang-toggle" href="https://github.com/{config.GITHUB_REPO}/issues/new?template=price-alert.yml" target="_blank" rel="noopener" style="text-decoration:none;display:inline-flex;align-items:center">🔔 {tr("הוסף התראת מחיר", "Add price alert", "Agregar alerta de precio", "Ajouter une alerte de prix", "إضافة تنبيه سعر")}</a>
    </div>
    <div class="heatmap-grid" id="heatmap-grid" style="display:none"></div>
    <div class="grid" id="stock-grid">
      {stock_cards_html}
    </div>

    {market_summary_html}
  </div>

  <div id="page-portfolio" class="page-view" style="display:none">
    {portfolio_view_html}
  </div>

  <div id="page-money" class="page-view" style="display:none">
    {money_page_html}
  </div>

  <div class="disclaimer">
    ⚠️ {tr(
        "האינדיקטורים הטכניים (מגמה, RSI), נתוני היסוד, ודירוגי האנליסטים מוצגים כפי שהם "
        "מ-Yahoo Finance - הם אינפורמציה ציבורית אינפורמטיבית בלבד, לא המלצת השקעה או ייעוץ "
        "פיננסי מטעם הכלי הזה. ההחלטה כיצד לפעול היא שלך בלבד.",
        "Technical indicators (trend, RSI), fundamental data, and analyst ratings are shown "
        "as-is from Yahoo Finance - they are public informational data only, not investment "
        "advice or financial guidance from this tool. The decision on how to act is yours alone.",
        "Los indicadores técnicos (tendencia, RSI), datos fundamentales y calificaciones de "
        "analistas se muestran tal cual desde Yahoo Finance - son información pública "
        "meramente informativa, no un consejo de inversión de esta herramienta. La decisión "
        "de cómo actuar es únicamente tuya.",
        "Les indicateurs techniques (tendance, RSI), les données fondamentales et les notes "
        "des analystes sont affichés tels quels depuis Yahoo Finance - il s'agit d'informations "
        "publiques uniquement, pas d'un conseil d'investissement de cet outil. La décision "
        "vous appartient entièrement.",
        "المؤشرات الفنية (الاتجاه، RSI)، البيانات الأساسية، وتقييمات المحللين معروضة كما هي من "
        "Yahoo Finance - وهي معلومات عامة فقط، وليست نصيحة استثمارية من هذه الأداة. القرار "
        "بشأن كيفية التصرف يعود إليك وحدك.",
    )}
  </div>

  <div class="modal-overlay" id="stock-modal" onclick="if(event.target===this) closeStockModal()">
    <div class="modal-box">
      <div class="modal-header">
        <h2 id="modal-title">-</h2>
        <div>
          <button class="modal-close" id="reset-zoom-btn" onclick="resetZoom()" style="font-size:14px; margin-left:8px;">↺ {tr("איפוס זום", "Reset zoom", "Restablecer zoom", "Réinitialiser le zoom", "إعادة ضبط التكبير")}</button>
          <button class="modal-close" onclick="closeStockModal()">✕</button>
        </div>
      </div>
      <div class="range-buttons" id="range-buttons"></div>
      <div class="range-buttons" id="draw-tools">
        <button id="draw-tool-pan" class="active" onclick="setDrawMode('pan')">🖐 {tr("הזזה", "Pan", "Desplazar", "Déplacer", "تحريك")}</button>
        <button id="draw-tool-trendline" onclick="setDrawMode('trendline')">／ {tr("קו מגמה", "Trendline", "Línea de tendencia", "Ligne de tendance", "خط الاتجاه")}</button>
        <button id="draw-tool-fibonacci" onclick="setDrawMode('fibonacci')">📐 {tr("פיבונאצ'י", "Fibonacci", "Fibonacci", "Fibonacci", "فيبوناتشي")}</button>
        <button onclick="clearDrawings()">🗑 {tr("נקה ציורים", "Clear drawings", "Borrar dibujos", "Effacer les dessins", "مسح الرسومات")}</button>
      </div>
      <div class="modal-range-label" id="modal-range-label"></div>
      <div class="zoom-instructions">🖱️ {tr(
          "במצב הזזה: גרור לזוז (אנכית ואופקית), ריחוף מציג קו הצלבה, גלגלת לזום | בכלי ציור: גרור לצייר קו/פיבונאצ'י | דאבל-קליק לאיפוס זום",
          "In pan mode: drag to move (vertically and horizontally), hover shows crosshair, wheel to zoom | In drawing tools: drag to draw a line/Fibonacci | double-click to reset zoom",
          "En modo desplazar: arrastra para mover (vertical y horizontalmente), al pasar el cursor se muestra una mira, rueda del ratón para zoom | En herramientas de dibujo: arrastra para dibujar una línea/Fibonacci | doble clic para restablecer el zoom",
          "En mode déplacer : glissez pour déplacer (verticalement et horizontalement), le survol affiche un réticule, molette pour zoomer | Avec les outils de dessin : glissez pour tracer une ligne/Fibonacci | double-clic pour réinitialiser le zoom",
          "في وضع التحريك: اسحب للتحريك (عمودياً وأفقياً)، التمرير يعرض خط تقاطع، عجلة الماوس للتكبير | في أدوات الرسم: اسحب لرسم خط/فيبوناتشي | انقر نقراً مزدوجاً لإعادة ضبط التكبير",
      )}</div>
      <canvas id="modal-canvas"></canvas>
      <div id="drawing-info-panel"></div>
      <div class="stock-notes-wrap">
        <label class="stock-notes-label" for="stock-notes-textarea">📝 {tr("הערה אישית", "Personal note", "Nota personal", "Note personnelle", "ملاحظة شخصية")} <span style="opacity:0.7">({tr("למה קניתי, מה המחשבה...", "why I bought, what I was thinking...", "por qué compré, qué pensaba...", "pourquoi j'ai acheté, ce que je pensais...", "لماذا اشتريت، ما كان تفكيري...")})</span></label>
        <textarea class="stock-notes-textarea" id="stock-notes-textarea" oninput="saveStockNote()"></textarea>
        <div class="stock-notes-saved" id="stock-notes-saved"></div>
      </div>
    </div>
  </div>

<script>
let currentLanguage = 'he';
const WEATHER_DESCRIPTIONS_JS = {json.dumps(WEATHER_DESCRIPTIONS)};
const WEATHER_UNKNOWN = {{"he": "לא ידוע", "en": "Unknown", "es": "Desconocido", "fr": "Inconnu", "ar": "غير معروف"}};

function weatherCodeToText(code) {{
  const entry = WEATHER_DESCRIPTIONS_JS[code] || WEATHER_UNKNOWN;
  return entry[currentLanguage] || entry.he;
}}

// --- מיקום (מזג אוויר + שעון) - חיפוש מתוך רשימת ערים מובנית (בלי תלות ברשת
// לחיפוש עצמו, כדי לא להיתקע על חסימות CORS), נשמר בדפדפן ---
const WORLD_CITIES_JS = {json.dumps(WORLD_CITIES)};
const MONEY_LABELS = {json.dumps(MONEY_LABEL_TRANSLATIONS, ensure_ascii=False)};
const LOCATION_STORAGE_KEY = 'shai_finance_location_v1';
let currentTimezone = 'Asia/Jerusalem';
let clockInterval = null;

function worldCitiesAsObjects() {{
  return WORLD_CITIES_JS.map(c => ({{ name: c[0], country: c[1], latitude: c[2], longitude: c[3], timezone: c[4] }}));
}}

function toggleLocationSearch() {{
  const box = document.getElementById('location-search-box');
  if (!box) return;
  const isOpen = box.style.display !== 'none';
  box.style.display = isOpen ? 'none' : 'block';
  if (!isOpen) {{
    const input = document.getElementById('location-search-input');
    if (input) {{
      input.value = '';
      input.focus();
      renderLocationResults(worldCitiesAsObjects().slice(0, 8));
    }}
  }}
}}

let locationSearchDebounce = null;
let locationSearchToken = 0;

// חיפוש חי מול Open-Meteo Geocoding API (אותו ספק שכבר משמש למזג האוויר) - מכסה כמעט
// כל עיר בעולם, לא מוגבל לרשימת הערים המובנית. יש debounce כדי לא לירות בקשה על כל תו.
function searchLocation() {{
  const inputEl = document.getElementById('location-search-input');
  if (!inputEl) return;
  const query = inputEl.value.trim();
  if (locationSearchDebounce) clearTimeout(locationSearchDebounce);
  if (query.length === 0) {{
    locationSearchToken++; // מבטל כל חיפוש חי שעדיין ממתין, כדי שתוצאה מאוחרת לא תדרוס את רשימת ברירת המחדל
    renderLocationResults(worldCitiesAsObjects().slice(0, 8));
    return;
  }}
  const resultsEl = document.getElementById('location-search-results');
  if (resultsEl) resultsEl.innerHTML = `<div class="location-result-empty">${{tr_searching_text()}}</div>`;
  locationSearchDebounce = setTimeout(() => doLiveLocationSearch(query), 300);
}}

async function doLiveLocationSearch(query) {{
  const myToken = ++locationSearchToken;
  try {{
    const url = 'https://geocoding-api.open-meteo.com/v1/search?name=' + encodeURIComponent(query) +
      '&count=10&language=' + currentLanguage + '&format=json';
    const resp = await fetch(url);
    const data = await resp.json();
    if (myToken !== locationSearchToken) return; // תוצאה מאוחרת של חיפוש קודם - מתעלמים
    const results = (data.results || []).map(r => ({{
      name: r.name,
      country: r.country || '',
      latitude: r.latitude,
      longitude: r.longitude,
      timezone: r.timezone || 'UTC',
    }}));
    renderLocationResults(results);
  }} catch (e) {{
    console.error('שגיאה בחיפוש מיקום חי - נופל לרשימה המובנית', e);
    if (myToken !== locationSearchToken) return;
    const q = query.toLowerCase();
    const fallback = worldCitiesAsObjects().filter(c =>
      c.name.toLowerCase().includes(q) || c.country.toLowerCase().includes(q)
    ).slice(0, 10);
    renderLocationResults(fallback);
  }}
}}

function renderLocationResults(cities) {{
  const resultsEl = document.getElementById('location-search-results');
  if (!resultsEl) return;
  if (cities.length === 0) {{
    resultsEl.innerHTML = `<div class="location-result-empty">${{tr_no_results_text()}}</div>`;
    return;
  }}
  resultsEl.innerHTML = cities.map((c, i) => `<div class="location-result" data-idx="${{i}}">${{c.name}}${{c.country ? ', ' + c.country : ''}}</div>`).join('');
  resultsEl.querySelectorAll('.location-result').forEach((el, i) => {{
    el.addEventListener('click', () => {{
      const c = cities[i];
      selectLocation(c.latitude, c.longitude, c.timezone, c.name + (c.country ? ', ' + c.country : ''));
    }});
  }});
}}

function tr_no_results_text() {{
  const map = {{ he: 'אין תוצאות - נסה שם עיר אחר', en: 'No results - try another city name', es: 'Sin resultados - prueba otro nombre', fr: 'Aucun résultat - essayez un autre nom', ar: 'لا توجد نتائج - جرّب اسماً آخر' }};
  return map[currentLanguage] || map.he;
}}

function tr_searching_text() {{
  const map = {{ he: 'מחפש...', en: 'Searching...', es: 'Buscando...', fr: 'Recherche...', ar: 'جارٍ البحث...' }};
  return map[currentLanguage] || map.he;
}}

async function selectLocation(lat, lon, timezone, name) {{
  try {{
    localStorage.setItem(LOCATION_STORAGE_KEY, JSON.stringify({{ lat, lon, timezone, name }}));
  }} catch (e) {{ /* localStorage לא זמין - לא קריטי */ }}
  const box = document.getElementById('location-search-box');
  if (box) box.style.display = 'none';
  await applyLocation(lat, lon, timezone, name);
}}

let applyLocationToken = 0;

async function applyLocation(lat, lon, timezone, name) {{
  const myToken = ++applyLocationToken;
  const nameEl = document.getElementById('weather-location-name');
  if (nameEl) nameEl.textContent = name;
  currentTimezone = timezone || 'Asia/Jerusalem';
  const tzNameEl = document.getElementById('clock-tz-name');
  if (tzNameEl) tzNameEl.textContent = name;
  startClock();

  try {{
    const url = 'https://api.open-meteo.com/v1/forecast?latitude=' + lat + '&longitude=' + lon +
      '&daily=temperature_2m_max,temperature_2m_min,weathercode&timezone=' + encodeURIComponent(currentTimezone);
    const resp = await fetch(url);
    const data = await resp.json();
    if (myToken !== applyLocationToken) return; // בחירת מיקום מאוחרת יותר כבר החליפה את זו - מתעלמים
    const daily = data.daily;
    if (daily && daily.temperature_2m_max && daily.temperature_2m_max.length) {{
      const tempMax = Math.round(daily.temperature_2m_max[0]);
      const tempMin = Math.round(daily.temperature_2m_min[0]);
      const code = daily.weathercode[0];
      const tempEl = document.getElementById('weather-temp');
      const descEl = document.getElementById('weather-desc-display');
      if (tempEl) tempEl.textContent = tempMin + '°-' + tempMax + '°';
      if (descEl) descEl.textContent = weatherCodeToText(code);
    }}
  }} catch (e) {{
    // אם קריאת הרשת נכשלת (למשל חסימת CORS בדפדפן), שם המיקום והשעון עדיין מתעדכנים - רק הטמפרטורה לא
    console.error('שגיאה בשליפת מזג אוויר עבור המיקום החדש - השם והשעון עדיין עודכנו', e);
  }}
}}

function startClock() {{
  if (clockInterval) clearInterval(clockInterval);
  updateClockDisplay();
  clockInterval = setInterval(updateClockDisplay, 1000);
}}

function updateClockDisplay() {{
  const el = document.getElementById('clock-display');
  if (!el) return;
  try {{
    const formatter = new Intl.DateTimeFormat(undefined, {{
      timeZone: currentTimezone, hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
    }});
    el.textContent = formatter.format(new Date());
  }} catch (e) {{
    el.textContent = '--:--:--';
  }}
}}

function initLocationFromStorage() {{
  try {{
    const raw = localStorage.getItem(LOCATION_STORAGE_KEY);
    if (raw) {{
      const loc = JSON.parse(raw);
      applyLocation(loc.lat, loc.lon, loc.timezone, loc.name);
      return;
    }}
  }} catch (e) {{ /* מתעלמים, נופלים לברירת המחדל */ }}
  const tzNameEl = document.getElementById('clock-tz-name');
  if (tzNameEl) tzNameEl.textContent = {json.dumps(config.LOCATION_NAME)};
  startClock();
}}
const RTL_LANGUAGES = ['he', 'ar'];
const TRANSLATIONS = {{
  he: {{
    volume: 'נפח', no_data: 'אין נתונים להצגה', no_data_range: 'אין נתונים לטווח הזה',
    data_points: 'נקודות נתון', zoomed: ' (מוגדל)', to: 'עד', bars: 'נרות',
    trendline: 'קו מגמה', fibonacci: "פיבונאצ'י", up: 'עולה 📈', down: 'יורדת 📉',
    flat: 'אופקית ➡️', high: 'גבוה', low: 'נמוך', range: 'טווח',
  }},
  en: {{
    volume: 'Volume', no_data: 'No data to display', no_data_range: 'No data for this range',
    data_points: 'data points', zoomed: ' (zoomed)', to: 'to', bars: 'bars',
    trendline: 'Trendline', fibonacci: 'Fibonacci', up: 'Up 📈', down: 'Down 📉',
    flat: 'Flat ➡️', high: 'High', low: 'Low', range: 'Range',
  }},
  es: {{
    volume: 'Volumen', no_data: 'Sin datos para mostrar', no_data_range: 'No hay datos para este rango',
    data_points: 'puntos de datos', zoomed: ' (ampliado)', to: 'a', bars: 'velas',
    trendline: 'Línea de tendencia', fibonacci: 'Fibonacci', up: 'Al alza 📈', down: 'A la baja 📉',
    flat: 'Plano ➡️', high: 'Máximo', low: 'Mínimo', range: 'Rango',
  }},
  fr: {{
    volume: 'Volume', no_data: 'Aucune donnée à afficher', no_data_range: 'Aucune donnée pour cette période',
    data_points: 'points de données', zoomed: ' (zoomé)', to: 'à', bars: 'bougies',
    trendline: 'Ligne de tendance', fibonacci: 'Fibonacci', up: 'Hausse 📈', down: 'Baisse 📉',
    flat: 'Plat ➡️', high: 'Haut', low: 'Bas', range: 'Plage',
  }},
  ar: {{
    volume: 'الحجم', no_data: 'لا توجد بيانات للعرض', no_data_range: 'لا توجد بيانات لهذا النطاق',
    data_points: 'نقاط بيانات', zoomed: ' (مكبّر)', to: 'إلى', bars: 'شموع',
    trendline: 'خط الاتجاه', fibonacci: 'فيبوناتشي', up: 'صاعد 📈', down: 'هابط 📉',
    flat: 'أفقي ➡️', high: 'أعلى', low: 'أدنى', range: 'النطاق',
  }},
}};

function selectLanguage(lang) {{
  if (!TRANSLATIONS[lang]) return;
  currentLanguage = lang;
  document.documentElement.dir = RTL_LANGUAGES.includes(lang) ? 'rtl' : 'ltr';
  document.documentElement.lang = lang;
  document.querySelectorAll('[data-i18n]').forEach(el => {{
    try {{
      const map = JSON.parse(el.getAttribute('data-i18n'));
      el.textContent = map[lang] || map.he || map.en || '';
    }} catch (e) {{ /* אלמנט בלי תרגום תקין - משאירים כמו שהוא */ }}
  }});
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {{
    try {{
      const map = JSON.parse(el.getAttribute('data-i18n-placeholder'));
      el.placeholder = map[lang] || map.he || map.en || '';
    }} catch (e) {{ /* אלמנט בלי תרגום תקין - משאירים כמו שהוא */ }}
  }});
  document.querySelectorAll('[data-i18n-title]').forEach(el => {{
    try {{
      const map = JSON.parse(el.getAttribute('data-i18n-title'));
      el.title = map[lang] || map.he || map.en || '';
    }} catch (e) {{ /* אלמנט בלי תרגום תקין - משאירים כמו שהוא */ }}
  }});
  const select = document.getElementById('lang-select');
  if (select) select.value = lang;
  updateDrawingInfo();
  if (currentModalTicker) renderModalChart();
  // מרענן את מקרא גרף העוגה בעמוד "הכסף שלי" לשפה החדשה, בלי לקרוא ל-updateMoneyTotal()
  // המלא (זה היה שומר וגם מוסיף רשומת היסטוריית שווי נטו חדשה - תופעת לוואי לא רצויה)
  if (typeof computeMoneyBreakdown === 'function' && typeof drawAllocationPie === 'function') {{
    const {{ totalILS, byAsset }} = computeMoneyBreakdown();
    drawAllocationPie(byAsset, totalILS);
  }}
}}

const CHART_PADDING = {{ top: 10, bottom: 10, left: 48, right: 8 }};

// עוזר ל"מספרים עגולים" בציר המחיר (אלגוריתם Heckbert הקלאסי) - הופך שברי
// חלוקה שרירותיים למספרים כמו 10/20/50/100 שקל יותר לקרוא בגרף
function niceNumber(range, round) {{
  const exponent = Math.floor(Math.log10(range));
  const fraction = range / Math.pow(10, exponent);
  let niceFraction;
  if (round) {{
    niceFraction = fraction < 1.5 ? 1 : fraction < 3 ? 2 : fraction < 7 ? 5 : 10;
  }} else {{
    niceFraction = fraction <= 1 ? 1 : fraction <= 2 ? 2 : fraction <= 5 ? 5 : 10;
  }}
  return niceFraction * Math.pow(10, exponent);
}}

let lastGeometry = null;
let currentDrawings = [];
let currentRangeKey = '3M';
const DRAWINGS_STORAGE_KEY = 'shai_finance_drawings_v1';

function drawingsStorageKey() {{
  return currentModalTicker + '_' + currentRangeKey;
}}

function saveDrawings() {{
  try {{
    const raw = localStorage.getItem(DRAWINGS_STORAGE_KEY);
    const all = raw ? JSON.parse(raw) : {{}};
    const key = drawingsStorageKey();
    if (currentDrawings.length > 0) {{
      all[key] = currentDrawings;
    }} else {{
      delete all[key];
    }}
    localStorage.setItem(DRAWINGS_STORAGE_KEY, JSON.stringify(all));
  }} catch (e) {{ /* localStorage לא זמין - לא קריטי */ }}
}}

function loadDrawings() {{
  currentDrawings = [];
  try {{
    const raw = localStorage.getItem(DRAWINGS_STORAGE_KEY);
    if (!raw) return;
    const all = JSON.parse(raw);
    const saved = all[drawingsStorageKey()];
    if (Array.isArray(saved)) currentDrawings = saved;
  }} catch (e) {{ /* מתעלמים, נשארים עם רשימה ריקה */ }}
}}

function deleteDrawing(index) {{
  currentDrawings.splice(index, 1);
  saveDrawings();
  updateDrawingInfo();
  renderModalChart();
}}
let activeDraw = null;
let drawMode = 'pan';
let manualPriceMin = null;
let manualPriceMax = null;
const CARD_CANDLES = {{}};

// --- עדכון חי (נסיוני) - מנסה לשלוף מחירים בזמן אמת מ-Yahoo Finance ישירות
// מהדפדפן. זה לא מובטח לעבוד: אנדפוינט זה לא רשמי ועלול להיחסם על ידי
// מדיניות CORS, בניגוד לשליפה דרך yfinance בפייתון שעובדת תמיד. אם זה נכשל,
// המערכת עוצרת בעדינות ומודיעה, בלי לקרוס.
let liveUpdateInterval = null;
let liveUpdateFailed = false;

function toggleLiveUpdates() {{
  if (liveUpdateInterval) {{
    stopLiveUpdates();
  }} else {{
    startLiveUpdates();
  }}
}}

function startLiveUpdates() {{
  liveUpdateFailed = false;
  const btn = document.getElementById('live-update-btn');
  const status = document.getElementById('live-update-status');
  if (btn) btn.textContent = '🟢 ' + LIVE_UPDATE_LABELS[currentLanguage].stop;
  if (status) status.textContent = LIVE_UPDATE_LABELS[currentLanguage].connecting;
  fetchLivePrices();
  liveUpdateInterval = setInterval(fetchLivePrices, 30000);
}}

function stopLiveUpdates() {{
  if (liveUpdateInterval) clearInterval(liveUpdateInterval);
  liveUpdateInterval = null;
  const btn = document.getElementById('live-update-btn');
  const status = document.getElementById('live-update-status');
  if (btn) btn.textContent = '🔴 ' + LIVE_UPDATE_LABELS[currentLanguage].start;
  if (status) status.textContent = '';
}}

const LIVE_UPDATE_LABELS = {{
  he: {{ start: 'עדכון חי (נסיוני)', stop: 'עצור עדכון חי', connecting: 'מתחבר...', ok: 'מעודכן', failed: 'לא הצלחתי להתחבר - ייתכן שהדפדפן חוסם את זה' }},
  en: {{ start: 'Live update (experimental)', stop: 'Stop live update', connecting: 'Connecting...', ok: 'Updated', failed: "Couldn't connect - your browser may be blocking this" }},
  es: {{ start: 'Actualización en vivo (experimental)', stop: 'Detener actualización', connecting: 'Conectando...', ok: 'Actualizado', failed: 'No se pudo conectar - tu navegador podría estar bloqueando esto' }},
  fr: {{ start: 'Mise à jour en direct (expérimental)', stop: "Arrêter la mise à jour", connecting: 'Connexion...', ok: 'Mis à jour', failed: "Échec de connexion - votre navigateur bloque peut-être cela" }},
  ar: {{ start: 'تحديث مباشر (تجريبي)', stop: 'إيقاف التحديث المباشر', connecting: 'جارٍ الاتصال...', ok: 'محدّث', failed: 'تعذر الاتصال - قد يحظر متصفحك هذا' }},
}};

async function fetchLivePrices() {{
  const tickers = Object.keys(CARD_CANDLES);
  if (tickers.length === 0 || liveUpdateFailed) return;
  const status = document.getElementById('live-update-status');
  let anySuccess = false;

  for (const ticker of tickers) {{
    try {{
      const url = 'https://query1.finance.yahoo.com/v8/finance/chart/' + encodeURIComponent(ticker);
      const resp = await fetch(url);
      const data = await resp.json();
      const result = data && data.chart && data.chart.result && data.chart.result[0];
      const meta = result && result.meta;
      if (!meta || meta.regularMarketPrice === undefined) continue;

      const price = meta.regularMarketPrice;
      const prevClose = meta.previousClose || meta.chartPreviousClose;
      const priceEl = document.getElementById('price-' + ticker);
      const changeEl = document.getElementById('change-' + ticker);
      if (priceEl) {{
        const prevShown = parseFloat((priceEl.textContent || '').replace('$', ''));
        priceEl.textContent = '$' + price.toFixed(2);
        if (!isNaN(prevShown) && prevShown !== price) {{
          const flashClass = price > prevShown ? 'price-flash-up' : 'price-flash-down';
          priceEl.classList.remove('price-flash-up', 'price-flash-down');
          void priceEl.offsetWidth;
          priceEl.classList.add(flashClass);
        }}
      }}
      if (changeEl && prevClose) {{
        const diff = price - prevClose;
        const pct = (diff / prevClose) * 100;
        const color = diff >= 0 ? '#2e7d32' : '#c62828';
        const sign = diff >= 0 ? '+' : '';
        changeEl.innerHTML = `<span style="color:${{color}}">${{sign}}${{diff.toFixed(2)}} (${{sign}}${{pct.toFixed(1)}}%)</span>`;
      }}
      anySuccess = true;
    }} catch (e) {{
      // ממשיכים לטיקר הבא - כשל בודד לא עוצר את כל התהליך
    }}
  }}

  if (anySuccess) {{
    if (status) status.textContent = '🟢 ' + LIVE_UPDATE_LABELS[currentLanguage].ok + ' ' + new Date().toLocaleTimeString();
  }} else {{
    liveUpdateFailed = true;
    stopLiveUpdates();
    if (status) status.textContent = '⚠️ ' + LIVE_UPDATE_LABELS[currentLanguage].failed;
  }}
}}
let isDarkTheme = true;

function getChartColors() {{
  return isDarkTheme
    ? {{
        grid: '#2a2a2a', label: '#999', crosshair: '#888',
        crosshairLabelBg: '#e8e8e8', crosshairLabelText: '#000',
        infoBoxBg: 'rgba(20,20,20,0.95)', infoBoxBorder: '#444', infoBoxText: '#e8e8e8',
        noDataText: '#999', candleHollowFill: '#101010',
      }}
    : {{
        grid: '#ddd', label: '#666', crosshair: '#555',
        crosshairLabelBg: '#222', crosshairLabelText: '#fff',
        infoBoxBg: 'rgba(255,255,255,0.95)', infoBoxBorder: '#ccc', infoBoxText: '#222',
        noDataText: '#888', candleHollowFill: '#ffffff',
      }};
}}

function toggleTheme() {{
  setTheme(isDarkTheme ? 'light' : 'dark');
}}

function showPage(page) {{
  document.getElementById('page-stocks').style.display = (page === 'stocks') ? 'block' : 'none';
  document.getElementById('page-portfolio').style.display = (page === 'portfolio') ? 'block' : 'none';
  document.getElementById('page-money').style.display = (page === 'money') ? 'block' : 'none';
  document.getElementById('nav-tab-stocks').classList.toggle('active', page === 'stocks');
  document.getElementById('nav-tab-portfolio').classList.toggle('active', page === 'portfolio');
  document.getElementById('nav-tab-money').classList.toggle('active', page === 'money');

  // ברגע שהכרטיסייה נהיית גלויה בפועל, מציירים מחדש - עכשיו ה-canvas מדווח
  // מידות אמיתיות (clientWidth/Height) ולא 0, כך שהגרף לא "נמתח"
  if (page === 'money') {{
    requestAnimationFrame(() => {{
      const {{ totalILS, byAsset }} = computeMoneyBreakdown();
      drawAllocationPie(byAsset, totalILS);
      drawNetWorthHistory();
      renderNetWorthHistoryTable();
    }});
  }}
}}

const MONEY_ROW_KEYS = ['general_savings', 'ibi', 'checking', 'sp500', 'cash', 'forex', 'bitcoin'];
const MONEY_STORAGE_KEY = 'shai_finance_money_v1';

function saveMoneyData() {{
  try {{
    const data = {{ rates: {{}}, assets: {{}} }};
    ['USD', 'EUR', 'GBP', 'JPY'].forEach(code => {{
      const el = document.getElementById('rate-' + code);
      if (el) data.rates[code] = el.value;
    }});
    MONEY_ROW_KEYS.forEach(key => {{
      const amountEl = document.getElementById('money-amount-' + key);
      const currencyEl = document.getElementById('money-currency-' + key);
      if (amountEl && currencyEl) {{
        data.assets[key] = {{ amount: amountEl.value, currency: currencyEl.value }};
      }}
    }});
    localStorage.setItem(MONEY_STORAGE_KEY, JSON.stringify(data));
  }} catch (e) {{
    // localStorage לא זמין (למשל מצב פרטי בדפדפן) - לא קריטי, פשוט לא נשמר
  }}
}}

function loadMoneyData() {{
  try {{
    const raw = localStorage.getItem(MONEY_STORAGE_KEY);
    if (!raw) return;
    const data = JSON.parse(raw);
    if (data.rates) {{
      Object.keys(data.rates).forEach(code => {{
        const el = document.getElementById('rate-' + code);
        if (el) el.value = data.rates[code];
      }});
    }}
    if (data.assets) {{
      Object.keys(data.assets).forEach(key => {{
        const amountEl = document.getElementById('money-amount-' + key);
        const currencyEl = document.getElementById('money-currency-' + key);
        const saved = data.assets[key];
        if (amountEl && saved && saved.amount !== undefined) amountEl.value = saved.amount;
        if (currencyEl && saved && saved.currency !== undefined) currencyEl.value = saved.currency;
      }});
    }}
  }} catch (e) {{
    // נתונים פגומים או localStorage חסום - פשוט משתמשים בברירת המחדל
  }}
}}

function manualSaveMoneyData() {{
  saveMoneyData();
  const t = TRANSLATIONS[currentLanguage];
  const msg = document.getElementById('save-confirm-msg');
  if (msg) {{
    msg.textContent = '✓ ' + tr_saved_text();
    setTimeout(() => {{ msg.textContent = ''; }}, 2000);
  }}
}}

function tr_saved_text() {{
  const map = {{ he: 'נשמר', en: 'Saved', es: 'Guardado', fr: 'Enregistré', ar: 'تم الحفظ' }};
  return map[currentLanguage] || map.he;
}}

const PORTFOLIO_QTY_STORAGE_KEY = 'shai_finance_portfolio_qty_v1';

function savePortfolioQty() {{
  try {{
    const data = {{}};
    Object.keys(PORTFOLIO_DATA).forEach(ticker => {{
      const el = document.getElementById('qty-' + ticker);
      if (el) data[ticker] = el.value;
    }});
    localStorage.setItem(PORTFOLIO_QTY_STORAGE_KEY, JSON.stringify(data));
  }} catch (e) {{ /* localStorage לא זמין - לא קריטי */ }}
}}

function loadPortfolioQty() {{
  try {{
    const raw = localStorage.getItem(PORTFOLIO_QTY_STORAGE_KEY);
    if (!raw) return;
    const data = JSON.parse(raw);
    Object.keys(data).forEach(ticker => {{
      const el = document.getElementById('qty-' + ticker);
      if (el && data[ticker] !== undefined) el.value = data[ticker];
    }});
  }} catch (e) {{ /* מתעלמים, נשארים עם ברירת המחדל (0) */ }}
}}

function updatePortfolioTotal() {{
  let totalValue = 0;
  Object.keys(PORTFOLIO_DATA).forEach(ticker => {{
    const qtyEl = document.getElementById('qty-' + ticker);
    const valueEl = document.getElementById('qty-value-' + ticker);
    if (!qtyEl) return;
    const qty = parseFloat(qtyEl.value) || 0;
    const current = PORTFOLIO_DATA[ticker].current;
    const value = qty * current;
    totalValue += value;
    if (valueEl) valueEl.textContent = '$' + value.toLocaleString(undefined, {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
  }});

  const totalEl = document.getElementById('portfolio-total-value');
  if (totalEl) totalEl.textContent = '$' + totalValue.toLocaleString(undefined, {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});

  const briefcaseEl = document.getElementById('portfolio-briefcase-total');
  if (briefcaseEl) briefcaseEl.textContent = '$' + totalValue.toLocaleString(undefined, {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});

  savePortfolioQty();
}}

function moneyLabelFor(key) {{
  const entry = MONEY_LABELS[key];
  if (!entry) return key;
  return entry[currentLanguage] || entry.he || key;
}}
// פלטה עברה בדיקת נגישות (validate_palette.py): רצועת בהירות, רוויה מינימלית,
// הפרדה לעיוורי צבעים וניגודיות - עוברת PASS מלא במצב כהה ובהיר
const ASSET_COLORS = ['#a3800c', '#3b6fc9', '#2e7d32', '#0097a7', '#b968e0', '#c62828', '#d97706'];

function computeMoneyBreakdown() {{
  const rates = {{ ILS: 1 }};
  ['USD', 'EUR', 'GBP', 'JPY'].forEach(code => {{
    const el = document.getElementById('rate-' + code);
    rates[code] = el ? (parseFloat(el.value) || 0) : 0;
  }});

  let totalILS = 0;
  const byAsset = {{}};
  MONEY_ROW_KEYS.forEach(key => {{
    const amountEl = document.getElementById('money-amount-' + key);
    const currencyEl = document.getElementById('money-currency-' + key);
    if (!amountEl || !currencyEl) return;
    const amount = parseFloat(amountEl.value) || 0;
    const currency = currencyEl.value;
    const rate = (rates[currency] !== undefined) ? rates[currency] : 1;
    const valueILS = amount * rate;
    byAsset[key] = valueILS;
    totalILS += valueILS;
  }});

  return {{ totalILS, byAsset }};
}}

function updateMoneyTotal() {{
  const {{ totalILS, byAsset }} = computeMoneyBreakdown();

  const display = document.getElementById('money-total-display');
  if (display) {{
    display.textContent = '₪ ' + totalILS.toLocaleString(undefined, {{ maximumFractionDigits: 0 }});
  }}

  updateGoalProgress(totalILS);
  drawAllocationPie(byAsset, totalILS);
  saveMoneyData();
  recordNetWorthHistory(totalILS);
  drawNetWorthHistory();
  renderNetWorthHistoryTable();
}}

// --- יעד חיסכון ---
const GOAL_STORAGE_KEY = 'shai_finance_goal_v1';

function saveGoal() {{
  try {{
    const el = document.getElementById('savings-goal-input');
    if (el) localStorage.setItem(GOAL_STORAGE_KEY, el.value);
  }} catch (e) {{}}
}}

function loadGoal() {{
  try {{
    const saved = localStorage.getItem(GOAL_STORAGE_KEY);
    const el = document.getElementById('savings-goal-input');
    if (el && saved !== null) el.value = saved;
  }} catch (e) {{}}
}}

let goalReachedCelebrated = false;

function updateGoalProgress(totalILS) {{
  const goalEl = document.getElementById('savings-goal-input');
  const fillEl = document.getElementById('goal-progress-fill');
  const textEl = document.getElementById('goal-progress-text');
  if (!goalEl || !fillEl || !textEl) return;

  totalILS = totalILS || 0;
  const goal = parseFloat(goalEl.value) || 0;
  const pct = goal > 0 ? Math.min(100, (totalILS / goal) * 100) : 0;
  const remaining = Math.max(0, goal - totalILS);
  fillEl.style.width = pct + '%';

  // החזרזיר "גדל" בהדרגה עם ההתקדמות ליעד (1.0x בהתחלה, עד 1.35x ב-100%)
  const piggyContainer = document.getElementById('money-piggy-container');
  if (piggyContainer) {{
    const scale = 1 + (pct / 100) * 0.35;
    piggyContainer.style.transform = 'scale(' + scale.toFixed(3) + ')';
  }}

  const t = TRANSLATIONS[currentLanguage];
  let statusText = '₪' + Math.round(totalILS).toLocaleString() + ' / ₪' + Math.round(goal).toLocaleString() + ' (' + pct.toFixed(1) + '%)';
  if (goal > 0) {{
    if (totalILS >= goal) {{
      statusText += ' — ' + GOAL_REACHED_TEXT[currentLanguage];
      if (!goalReachedCelebrated) {{
        goalReachedCelebrated = true;
        fireConfetti();
      }}
    }} else {{
      statusText += ' — ' + GOAL_REMAINING_TEXT[currentLanguage] + ': ₪' + Math.round(remaining).toLocaleString();
      goalReachedCelebrated = false;
    }}
  }} else {{
    goalReachedCelebrated = false;
  }}
  textEl.textContent = statusText;
  saveGoal();
}}

const GOAL_REACHED_TEXT = {{ he: '🎉 הגעת ליעד!', en: '🎉 Goal reached!', es: '🎉 ¡Meta alcanzada!', fr: '🎉 Objectif atteint!', ar: '🎉 تم الوصول للهدف!' }};
const GOAL_REMAINING_TEXT = {{ he: 'חסר', en: 'Remaining', es: 'Falta', fr: 'Restant', ar: 'المتبقي' }};

// --- קונפטי כשמגיעים ליעד החיסכון ---
function fireConfetti() {{
  const container = document.getElementById('money-piggy-container');
  if (!container) return;
  const colors = ['#c9a227', '#1e4d8c', '#2e7d32', '#c62828', '#b968e0'];
  for (let i = 0; i < 24; i++) {{
    const piece = document.createElement('div');
    piece.className = 'confetti-piece';
    piece.style.background = colors[i % colors.length];
    piece.style.setProperty('--dx', (Math.random() * 160 - 80) + 'px');
    piece.style.left = (35 + Math.random() * 30) + '%';
    piece.style.animationDelay = (Math.random() * 0.3) + 's';
    container.appendChild(piece);
    setTimeout(() => piece.remove(), 1700);
  }}
}}

// --- גרף עוגה של פיזור נכסים ---
function drawAllocationPie(byAsset, totalILS) {{
  const canvas = document.getElementById('allocation-pie-canvas');
  const legend = document.getElementById('allocation-legend');
  if (!canvas || !legend) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width, h = canvas.height;
  ctx.clearRect(0, 0, w, h);

  const entries = MONEY_ROW_KEYS.filter(k => (byAsset[k] || 0) > 0);
  if (entries.length === 0 || totalILS <= 0) {{
    ctx.fillStyle = isDarkTheme ? '#999' : '#888';
    ctx.font = '13px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(TRANSLATIONS[currentLanguage].no_data, w / 2, h / 2);
    legend.innerHTML = '';
    return;
  }}

  const cx = w / 2, cy = h / 2, radius = Math.min(w, h) / 2 - 6;
  let startAngle = -Math.PI / 2;
  legend.innerHTML = '';

  entries.forEach((key, i) => {{
    const value = byAsset[key] || 0;
    const sliceAngle = (value / totalILS) * Math.PI * 2;
    const color = ASSET_COLORS[i % ASSET_COLORS.length];

    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, radius, startAngle, startAngle + sliceAngle);
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();

    startAngle += sliceAngle;

    const pct = (value / totalILS) * 100;
    const label = moneyLabelFor(key);
    const legendItem = document.createElement('div');
    legendItem.className = 'legend-item';
    legendItem.innerHTML = '<span class="legend-swatch" style="background:' + color + '"></span>' +
      '<span>' + label + ': ' + pct.toFixed(1) + '%</span>';
    legend.appendChild(legendItem);
  }});
}}

// --- היסטוריית שווי נטו ---
const NET_WORTH_HISTORY_KEY = 'shai_finance_networth_history_v1';

function localDateString(d) {{
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${{yyyy}}-${{mm}}-${{dd}}`;
}}

function recordNetWorthHistory(totalILS) {{
  try {{
    // תאריך מקומי של הדפדפן, לא UTC (toISOString) - אחרת עדכון בערב מאוחר יכול להירשם בטעות בתאריך של מחר
    const today = localDateString(new Date());
    const raw = localStorage.getItem(NET_WORTH_HISTORY_KEY);
    let history = raw ? JSON.parse(raw) : [];
    const existingIdx = history.findIndex(h => h.date === today);
    if (existingIdx >= 0) {{
      history[existingIdx].total = totalILS;
    }} else {{
      history.push({{ date: today, total: totalILS }});
    }}
    if (history.length > 365) history = history.slice(history.length - 365);
    localStorage.setItem(NET_WORTH_HISTORY_KEY, JSON.stringify(history));
  }} catch (e) {{}}
}}

function drawNetWorthHistory() {{
  const canvas = document.getElementById('net-worth-history-canvas');
  if (!canvas) return;

  // אם הכרטיסייה "הכסף של שי" עדיין display:none (למשל בטעינה ראשונית של
  // הדף), ה-canvas מדווח clientWidth/clientHeight 0 - וזו בדיוק הסיבה
  // שהגרף נראה "מתוח": הוא ננעל על רזולוציה זעירה ואז ה-CSS מותח אותו על פני
  // כל רוחב הכרטיסייה. במקום לצייר עם מידות שגויות, מחכים לפריים הבא ומנסים
  // שוב (בדיוק כמו drawCandlestick) - וגם showPage קורא לפונקציה הזו מחדש
  // ברגע שהכרטיסייה נהיית גלויה, כדי לוודא רזולוציה נכונה.
  const cssWidth = canvas.clientWidth;
  const cssHeight = canvas.clientHeight;
  if (!cssWidth || !cssHeight) {{
    requestAnimationFrame(() => {{ if (canvas.clientWidth && canvas.clientHeight) drawNetWorthHistory(); }});
    return;
  }}

  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  canvas.width = cssWidth * dpr;
  canvas.height = cssHeight * dpr;
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, cssWidth, cssHeight);

  let history = [];
  try {{
    const raw = localStorage.getItem(NET_WORTH_HISTORY_KEY);
    history = raw ? JSON.parse(raw) : [];
  }} catch (e) {{}}

  if (history.length < 2) {{
    ctx.fillStyle = isDarkTheme ? '#999' : '#888';
    ctx.font = '13px sans-serif';
    ctx.fillText(TRANSLATIONS[currentLanguage].no_data, 10, cssHeight / 2);
    return;
  }}

  const padding = {{ top: 10, bottom: 24, left: 60, right: 10 }};
  const plotWidth = cssWidth - padding.left - padding.right;
  const plotHeight = cssHeight - padding.top - padding.bottom;

  const totals = history.map(h => h.total);
  const maxVal = Math.max(...totals) || 1;
  const minVal = Math.min(0, ...totals);
  const range = (maxVal - minVal) || 1;

  function xFor(i) {{ return padding.left + (i / (history.length - 1)) * plotWidth; }}
  function yFor(val) {{ return padding.top + (1 - (val - minVal) / range) * plotHeight; }}

  ctx.strokeStyle = isDarkTheme ? '#2a2a2a' : '#ddd';
  ctx.fillStyle = isDarkTheme ? '#999' : '#666';
  ctx.font = '10px sans-serif';
  ctx.textAlign = 'left';
  for (let i = 0; i <= 4; i++) {{
    const val = minVal + (range * i / 4);
    const y = yFor(val);
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(cssWidth - padding.right, y);
    ctx.stroke();
    ctx.fillText('₪' + Math.round(val).toLocaleString(), 2, y + 3);
  }}

  ctx.strokeStyle = isDarkTheme ? '#1e4d8c' : '#1a4a8a';
  ctx.lineWidth = 2;
  ctx.beginPath();
  history.forEach((h, i) => {{
    const x = xFor(i), y = yFor(h.total);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }});
  ctx.stroke();
  ctx.lineWidth = 1;

  ctx.fillStyle = isDarkTheme ? '#1e4d8c' : '#1a4a8a';
  history.forEach((h, i) => {{
    const x = xFor(i), y = yFor(h.total);
    ctx.beginPath();
    ctx.arc(x, y, 3, 0, Math.PI * 2);
    ctx.fill();
  }});

  ctx.fillStyle = isDarkTheme ? '#999' : '#666';
  ctx.textAlign = 'center';
  ctx.fillText(history[0].date, xFor(0), cssHeight - 6);
  ctx.fillText(history[history.length - 1].date, xFor(history.length - 1), cssHeight - 6);
}}

// --- טבלת היסטוריית שווי נטו (סדורה, החדש ביותר למעלה) ---
function renderNetWorthHistoryTable() {{
  const tbody = document.getElementById('net-worth-history-tbody');
  const emptyNote = document.getElementById('net-worth-history-empty');
  if (!tbody) return;

  let history = [];
  try {{
    const raw = localStorage.getItem(NET_WORTH_HISTORY_KEY);
    history = raw ? JSON.parse(raw) : [];
  }} catch (e) {{}}

  if (history.length === 0) {{
    tbody.innerHTML = '';
    if (emptyNote) emptyNote.style.display = 'block';
    return;
  }}
  if (emptyNote) emptyNote.style.display = 'none';

  const newestFirst = history.slice().reverse();
  tbody.innerHTML = newestFirst.map((h, i) => {{
    const prev = newestFirst[i + 1];
    let changeHtml = '—';
    if (prev) {{
      const diff = h.total - prev.total;
      const pct = prev.total ? (diff / prev.total) * 100 : 0;
      const color = diff >= 0 ? '#2e7d32' : '#c62828';
      const sign = diff >= 0 ? '+' : '';
      changeHtml = `<span style="color:${{color}}">${{sign}}₪${{Math.round(diff).toLocaleString()}} (${{sign}}${{pct.toFixed(1)}}%)</span>`;
    }}
    return `<tr>
      <td>${{h.date}}</td>
      <td>₪${{Math.round(h.total).toLocaleString()}}</td>
      <td>${{changeHtml}}</td>
    </tr>`;
  }}).join('');
}}

// --- ייצוא לקובץ ---
function exportMoneyData() {{
  try {{
    const data = {{
      money: JSON.parse(localStorage.getItem(MONEY_STORAGE_KEY) || '{{}}'),
      goal: localStorage.getItem(GOAL_STORAGE_KEY),
      history: JSON.parse(localStorage.getItem(NET_WORTH_HISTORY_KEY) || '[]'),
      portfolioQty: JSON.parse(localStorage.getItem(PORTFOLIO_QTY_STORAGE_KEY) || '{{}}'),
      exportedAt: new Date().toISOString(),
    }};
    const blob = new Blob([JSON.stringify(data, null, 2)], {{ type: 'application/json' }});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'shai-finance-backup-' + new Date().toISOString().slice(0, 10) + '.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }} catch (e) {{
    console.error('שגיאה בייצוא הנתונים', e);
  }}
}}

function setTheme(theme) {{
  isDarkTheme = (theme !== 'light');
  document.body.classList.toggle('light-theme', theme === 'light');
  const btn = document.getElementById('theme-toggle-btn');
  if (btn) btn.textContent = isDarkTheme ? '🌙' : '☀️';
  Object.keys(CARD_CANDLES).forEach(t => drawCandlestick('chart-' + t, CARD_CANDLES[t]));
  if (currentModalTicker) renderModalChart();
}}

function drawCandlestick(canvasId, candles, crosshair) {{
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const cssWidth = canvas.clientWidth;
  const cssHeight = canvas.clientHeight;

  // אם ה-canvas עדיין לא נראה בפועל (0 רוחב/גובה - למשל המודל עדיין לא נפתח
  // לגמרי), לא מציירים עם מידות שגויות. מנסים שוב בפריים הבא.
  if (!cssWidth || !cssHeight) {{
    requestAnimationFrame(() => drawCandlestick(canvasId, candles, crosshair));
    return;
  }}

  canvas.width = cssWidth * dpr;
  canvas.height = cssHeight * dpr;
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, cssWidth, cssHeight);

  const colors = getChartColors();
  const validCandles = candles ? candles.filter(c => c) : [];

  if (validCandles.length === 0) {{
    ctx.fillStyle = colors.noDataText;
    ctx.font = '13px sans-serif';
    ctx.fillText(TRANSLATIONS[currentLanguage].no_data, 10, cssHeight / 2);
    return;
  }}

  const highs = validCandles.map(c => c.h);
  const lows = validCandles.map(c => c.l);
  const volumes = validCandles.map(c => c.v || 0);
  const autoMaxPrice = Math.max(...highs);
  const autoMinPrice = Math.min(...lows);
  const usingManualPrice = canvasId === 'modal-canvas' && manualPriceMin !== null && manualPriceMax !== null;
  const maxPrice = usingManualPrice ? manualPriceMax : autoMaxPrice;
  const minPrice = usingManualPrice ? manualPriceMin : autoMinPrice;
  const priceRange = (maxPrice - minPrice) || 1;
  const maxVolume = Math.max(...volumes) || 1;

  // בגרף המודל מוסיפים מקום בתחתית לציר תאריכים (הכרטיסים הקטנים נשארים בלי
  // שינוי, כדי לא לצופף אותם)
  const padding = canvasId === 'modal-canvas'
    ? {{ ...CHART_PADDING, bottom: CHART_PADDING.bottom + 16 }}
    : CHART_PADDING;
  const plotWidth = cssWidth - padding.left - padding.right;
  const plotHeight = cssHeight - padding.top - padding.bottom;

  const volumeHeight = Math.min(60, plotHeight * 0.25);
  const gap = 6;
  const priceAreaTop = padding.top;
  const priceAreaHeight = plotHeight - volumeHeight - gap;
  const volumeAreaTop = priceAreaTop + priceAreaHeight + gap;

  function priceToY(price) {{
    return priceAreaTop + (1 - (price - minPrice) / priceRange) * priceAreaHeight;
  }}
  function yToPrice(y) {{
    return minPrice + (1 - (y - priceAreaTop) / priceAreaHeight) * priceRange;
  }}

  // קווי רשת + תוויות מחיר (אזור המחיר בלבד) - במספרים "עגולים" (10/20/50 וכו')
  // במקום חלוקה גסה ל-4 שברים שווים, כדי שיהיה קל יותר לקרוא במבט חטוף
  ctx.strokeStyle = colors.grid;
  ctx.fillStyle = colors.label;
  ctx.font = '10px sans-serif';
  ctx.textAlign = 'left';
  const desiredTicks = 5;
  const tickSpacing = priceRange > 0 ? niceNumber(priceRange / (desiredTicks - 1), true) : 1;
  const tickDecimals = tickSpacing < 1 ? 2 : 0;
  const firstTick = Math.ceil(minPrice / tickSpacing) * tickSpacing;
  const tickCount = tickSpacing > 0 ? Math.floor((maxPrice - firstTick) / tickSpacing) + 1 : 0;
  for (let i = 0; i < tickCount; i++) {{
    const price = firstTick + i * tickSpacing;
    const y = priceToY(price);
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(cssWidth - padding.right, y);
    ctx.stroke();
    ctx.fillText('$' + price.toFixed(tickDecimals), 2, y + 3);
  }}

  const n = candles.length;
  const slotWidth = plotWidth / n;
  const bodyWidth = Math.max(2, slotWidth * 0.6);

  candles.forEach((candle, i) => {{
    if (!candle) return;
    const xCenter = padding.left + slotWidth * i + slotWidth / 2;
    const isUp = candle.c >= candle.o;
    const color = isUp ? '#2e7d32' : '#c62828';
    ctx.strokeStyle = color;
    ctx.fillStyle = color;

    // פתיל (high-low)
    ctx.beginPath();
    ctx.moveTo(xCenter, priceToY(candle.h));
    ctx.lineTo(xCenter, priceToY(candle.l));
    ctx.stroke();

    // גוף הנר (open-close). עלייה = גוף חלול (מתאר בלבד, מוסכמת הנרות היפניים
    // הקלאסית), ירידה = גוף מלא - כך שכיוון הנר ניכר גם בלי הבחנת צבע (נגישות
    // לעיוורי צבעים), ובכל צפיפות נרות (לא רק כשיש מקום פנוי לסימון נפרד).
    const yOpen = priceToY(candle.o);
    const yClose = priceToY(candle.c);
    const bodyTop = Math.min(yOpen, yClose);
    const bodyHeight = Math.max(1, Math.abs(yOpen - yClose));
    if (isUp) {{
      ctx.fillStyle = colors.candleHollowFill;
      ctx.fillRect(xCenter - bodyWidth / 2, bodyTop, bodyWidth, bodyHeight);
      ctx.strokeStyle = color;
      ctx.lineWidth = Math.min(1.5, bodyWidth / 2);
      ctx.strokeRect(xCenter - bodyWidth / 2, bodyTop, bodyWidth, bodyHeight);
      ctx.lineWidth = 1;
    }} else {{
      ctx.fillStyle = color;
      ctx.fillRect(xCenter - bodyWidth / 2, bodyTop, bodyWidth, bodyHeight);
    }}

    // עמודת נפח
    const volHeight = (candle.v / maxVolume) * volumeHeight;
    ctx.fillStyle = isUp ? 'rgba(46,125,50,0.4)' : 'rgba(198,40,40,0.4)';
    ctx.fillRect(xCenter - bodyWidth / 2, volumeAreaTop + volumeHeight - volHeight, bodyWidth, volHeight);
  }});

  // ציר תאריכים לאורך תחתית הגרף - רק במודל המוגדל (בכרטיסים הקטנים אין מקום
  // ואין dateLabel לכל נר). מתעדכן אוטומטית עם הזזה/זום כי מחשב מהנרות הנראים.
  if (canvasId === 'modal-canvas' && n > 0) {{
    const desiredLabels = Math.max(2, Math.min(6, Math.floor(plotWidth / 90)));
    const labelStep = Math.max(1, Math.round(n / desiredLabels));
    const axisY = volumeAreaTop + volumeHeight;
    ctx.strokeStyle = colors.grid;
    ctx.fillStyle = colors.label;
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';
    for (let i = 0; i < n; i += labelStep) {{
      const tickCandle = candles[i];
      if (!tickCandle || !tickCandle.dateLabel) continue;
      const xTick = padding.left + slotWidth * i + slotWidth / 2;
      let label = tickCandle.dateLabel;
      if (label.includes(' ')) label = label.split(' ')[1] || label;
      ctx.beginPath();
      ctx.moveTo(xTick, axisY);
      ctx.lineTo(xTick, axisY + 4);
      ctx.stroke();
      ctx.fillText(label, xTick, axisY + 14);
    }}
    ctx.textAlign = 'left';
  }}

  // ציורים (קווי מגמה / פיבונאצ'י) - רק על גרף המודל
  if (canvasId === 'modal-canvas') {{
    const geometry = {{ padding, slotWidth, minPrice, maxPrice, priceAreaTop, priceAreaHeight }};
    currentDrawings.forEach(d => renderDrawing(ctx, d, geometry));
    if (activeDraw) renderDrawing(ctx, activeDraw, geometry);
    lastGeometry = {{ ...geometry, visibleCount: n }};
  }}

  // קו הצלבה (crosshair) + תיבת מידע - רק אם מרחפים מעל נר אמיתי, לא שטח ריק
  if (crosshair) {{
    let index = Math.floor((crosshair.x - padding.left) / slotWidth);
    index = Math.max(0, Math.min(n - 1, index));
    const candle = candles[index];
    if (candle) {{
    const xCenter = padding.left + slotWidth * index + slotWidth / 2;

    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = colors.crosshair;

    // קו אנכי
    ctx.beginPath();
    ctx.moveTo(xCenter, padding.top);
    ctx.lineTo(xCenter, volumeAreaTop + volumeHeight);
    ctx.stroke();

    // קו אופקי (במחיר שבו נמצא העכבר בפועל)
    const clampedY = Math.max(priceAreaTop, Math.min(priceAreaTop + priceAreaHeight, crosshair.y));
    ctx.beginPath();
    ctx.moveTo(padding.left, clampedY);
    ctx.lineTo(cssWidth - padding.right, clampedY);
    ctx.stroke();
    ctx.setLineDash([]);

    // תווית מחיר על הקו האופקי
    const hoveredPrice = yToPrice(clampedY);
    ctx.fillStyle = colors.crosshairLabelBg;
    ctx.fillRect(2, clampedY - 8, 46, 14);
    ctx.fillStyle = colors.crosshairLabelText;
    ctx.font = '10px sans-serif';
    ctx.fillText('$' + hoveredPrice.toFixed(2), 4, clampedY + 3);

    // תיבת מידע (OHLCV) בפינה השמאלית-עליונה
    const boxLines = [
      candle.dateLabel || '',
      `O: $${{candle.o.toFixed(2)}}  H: $${{candle.h.toFixed(2)}}`,
      `L: $${{candle.l.toFixed(2)}}  C: $${{candle.c.toFixed(2)}}`,
      `${{TRANSLATIONS[currentLanguage].volume}}: ${{(candle.v || 0).toLocaleString()}}`,
    ];
    ctx.font = '11px sans-serif';
    const boxWidth = 190;
    const boxHeight = boxLines.length * 14 + 10;
    ctx.fillStyle = colors.infoBoxBg;
    ctx.strokeStyle = colors.infoBoxBorder;
    ctx.fillRect(padding.left + 4, padding.top + 4, boxWidth, boxHeight);
    ctx.strokeRect(padding.left + 4, padding.top + 4, boxWidth, boxHeight);
    ctx.fillStyle = colors.infoBoxText;
    boxLines.forEach((line, i) => {{
      ctx.fillText(line, padding.left + 10, padding.top + 20 + i * 14);
    }});
    }}
  }}
}}

// --- ספארקליין זעיר בכותרת הכרטיס - מגמת המחיר האחרונה במבט חטוף ---
function drawSparkline(canvasId, candles) {{
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const dpr = window.devicePixelRatio || 1;
  const cssWidth = canvas.clientWidth || 72;
  const cssHeight = canvas.clientHeight || 26;
  canvas.width = cssWidth * dpr;
  canvas.height = cssHeight * dpr;
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, cssWidth, cssHeight);

  const valid = (candles || []).filter(c => c);
  const closes = valid.slice(-14).map(c => c.c);
  if (closes.length < 2) return;

  const maxVal = Math.max(...closes);
  const minVal = Math.min(...closes);
  const range = (maxVal - minVal) || 1;
  const pad = 2;
  const isUp = closes[closes.length - 1] >= closes[0];
  ctx.strokeStyle = isUp ? '#2e7d32' : '#c62828';
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  closes.forEach((val, i) => {{
    const x = pad + (i / (closes.length - 1)) * (cssWidth - pad * 2);
    const y = pad + (1 - (val - minVal) / range) * (cssHeight - pad * 2);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }});
  ctx.stroke();
}}

{stock_charts_js}

// --- מיון וטבלת חום למניות ---
function applySortStocks(mode) {{
  const grid = document.getElementById('stock-grid');
  if (!grid) return;
  const cards = Array.from(grid.querySelectorAll('.card'));
  const parsePct = (el) => {{
    const v = el.getAttribute('data-pct');
    return v === '' ? null : parseFloat(v);
  }};
  const parseRsi = (el) => {{
    const v = el.getAttribute('data-rsi');
    return v === '' ? null : parseFloat(v);
  }};
  let sorted;
  if (mode === 'pct-desc') {{
    sorted = cards.sort((a, b) => (parsePct(b) ?? -Infinity) - (parsePct(a) ?? -Infinity));
  }} else if (mode === 'pct-asc') {{
    sorted = cards.sort((a, b) => (parsePct(a) ?? Infinity) - (parsePct(b) ?? Infinity));
  }} else if (mode === 'alpha') {{
    sorted = cards.sort((a, b) => a.getAttribute('data-ticker').localeCompare(b.getAttribute('data-ticker')));
  }} else if (mode === 'rsi') {{
    sorted = cards.sort((a, b) => (parseRsi(b) ?? -Infinity) - (parseRsi(a) ?? -Infinity));
  }} else {{
    sorted = cards.sort((a, b) => {{
      const ta = a.getAttribute('data-ticker'), tb = b.getAttribute('data-ticker');
      return TICKER_STATS.findIndex(s => s.ticker === ta) - TICKER_STATS.findIndex(s => s.ticker === tb);
    }});
  }}
  sorted.forEach(card => grid.appendChild(card));
}}

let heatmapVisible = false;
function toggleHeatmapView() {{
  heatmapVisible = !heatmapVisible;
  const grid = document.getElementById('stock-grid');
  const heatmap = document.getElementById('heatmap-grid');
  if (grid) grid.style.display = heatmapVisible ? 'none' : 'grid';
  if (heatmap) heatmap.style.display = heatmapVisible ? 'grid' : 'none';
  if (heatmapVisible) renderHeatmap();
}}

function renderHeatmap() {{
  const container = document.getElementById('heatmap-grid');
  if (!container) return;
  const pcts = TICKER_STATS.map(s => s.pct).filter(p => p !== null && p !== undefined);
  const maxAbs = Math.max(1, ...pcts.map(p => Math.abs(p)));
  container.innerHTML = TICKER_STATS.map(s => {{
    const pct = s.pct;
    let bg = '#555';
    let pctText = TRANSLATIONS[currentLanguage].no_data;
    if (pct !== null && pct !== undefined) {{
      const intensity = Math.min(1, Math.abs(pct) / maxAbs);
      const lightness = 46 - intensity * 20;
      bg = pct >= 0 ? `hsl(122, 45%, ${{lightness}}%)` : `hsl(0, 55%, ${{lightness}}%)`;
      const sign = pct >= 0 ? '+' : '';
      pctText = sign + pct.toFixed(2) + '%';
    }}
    return `<div class="heatmap-tile" style="background:${{bg}}" onclick="openStockModal('${{s.ticker}}')">
      <div class="ht-ticker">${{s.ticker}}</div>
      <div class="ht-pct">${{pctText}}</div>
    </div>`;
  }}).join('');
}}

// --- נתונים לחלון הזום (מודל) ---
const ALL_RANGES = {all_ranges_json};
const PORTFOLIO_DATA = {portfolio_data_json};
const TICKER_STATS = {ticker_stats_json};
const RANGE_ORDER = ['1D', '1W', '1M', '3M', '6M', '1Y'];
let currentModalTicker = null;
let fullCandles = [];
let fullDates = [];
let viewStart = 0;
let viewEnd = 0;

const STOCK_NOTES_KEY = 'shai_finance_stock_notes_v1';

function loadStockNote() {{
  const el = document.getElementById('stock-notes-textarea');
  if (!el) return;
  try {{
    const all = JSON.parse(localStorage.getItem(STOCK_NOTES_KEY) || '{{}}');
    el.value = all[currentModalTicker] || '';
  }} catch (e) {{ el.value = ''; }}
}}

function saveStockNote() {{
  const el = document.getElementById('stock-notes-textarea');
  const savedEl = document.getElementById('stock-notes-saved');
  if (!el || !currentModalTicker) return;
  try {{
    const all = JSON.parse(localStorage.getItem(STOCK_NOTES_KEY) || '{{}}');
    if (el.value.trim()) {{
      all[currentModalTicker] = el.value;
    }} else {{
      delete all[currentModalTicker];
    }}
    localStorage.setItem(STOCK_NOTES_KEY, JSON.stringify(all));
    if (savedEl) {{
      savedEl.textContent = '✓ ' + tr_saved_text();
      clearTimeout(saveStockNote._t);
      saveStockNote._t = setTimeout(() => {{ savedEl.textContent = ''; }}, 1500);
    }}
  }} catch (e) {{ /* localStorage לא זמין - לא קריטי */ }}
}}

function openStockModal(ticker) {{
  currentModalTicker = ticker;
  document.getElementById('modal-title').innerText = ticker;
  loadStockNote();

  const buttonsContainer = document.getElementById('range-buttons');
  buttonsContainer.innerHTML = '';
  RANGE_ORDER.forEach(rangeKey => {{
    const btn = document.createElement('button');
    btn.innerText = rangeKey;
    btn.onclick = () => showModalRange(rangeKey);
    btn.id = 'range-btn-' + rangeKey;
    buttonsContainer.appendChild(btn);
  }});

  // חשוב: מציגים את המודל *לפני* שמציירים עליו. אם מציירים בזמן שהוא עדיין
  // display:none, ה-canvas מדווח clientWidth/clientHeight של 0, והציור ננעל
  // על גודל שגוי (ואז חישובי מיקום העכבר לא תואמים למה שמצויר בפועל).
  document.getElementById('stock-modal').classList.add('open');

  // requestAnimationFrame מוודא שהדפדפן כבר סיים לעדכן את הפריסה (layout)
  // לפני שאנחנו קוראים את המידות ומציירים.
  requestAnimationFrame(() => {{
    showModalRange('3M');
  }});
}}

function closeStockModal() {{
  document.getElementById('stock-modal').classList.remove('open');
  currentModalTicker = null;
}}

function showModalRange(rangeKey) {{
  RANGE_ORDER.forEach(k => {{
    const btn = document.getElementById('range-btn-' + k);
    if (btn) btn.classList.toggle('active', k === rangeKey);
  }});

  currentRangeKey = rangeKey;
  activeDraw = null;
  manualPriceMin = null;
  manualPriceMax = null;
  setDrawMode('pan');
  loadDrawings();
  updateDrawingInfo();

  const rangeData = (ALL_RANGES[currentModalTicker] || {{}})[rangeKey];
  fullDates = rangeData ? rangeData.dates : [];
  fullCandles = rangeData ? rangeData.candles : [];
  viewStart = 0;
  viewEnd = fullCandles.length;

  renderModalChart();
}}

function resetZoom() {{
  viewStart = 0;
  viewEnd = fullCandles.length;
  manualPriceMin = null;
  manualPriceMax = null;
  renderModalChart();
}}

function updateDrawingInfo() {{
  const panel = document.getElementById('drawing-info-panel');
  if (!currentDrawings.length) {{
    panel.innerHTML = '';
    return;
  }}

  panel.innerHTML = currentDrawings.map((d, i) => {{
    const t = TRANSLATIONS[currentLanguage];
    const dateOf = (idx) => (fullDates[idx] !== undefined ? fullDates[idx] : '?');
    const p1 = d.p1, p2 = d.p2;
    const startIdx = Math.min(p1.index, p2.index);
    const endIdx = Math.max(p1.index, p2.index);
    const startPrice = (p1.index <= p2.index) ? p1.price : p2.price;
    const endPrice = (p1.index <= p2.index) ? p2.price : p1.price;
    const change = endPrice - startPrice;
    const pct = startPrice ? (change / startPrice) * 100 : 0;
    const bars = endIdx - startIdx;
    const direction = change > 0 ? t.up : (change < 0 ? t.down : t.flat);
    const changeColor = change >= 0 ? '#2e7d32' : '#c62828';
    const sign = change >= 0 ? '+' : '';

    if (d.type === 'trendline') {{
      return `
        <div class="drawing-info-card">
          <span class="di-label">／ ${{t.trendline}} #${{i + 1}}</span>
          <span>${{dateOf(startIdx)}} ($${{startPrice.toFixed(2)}}) ← ${{dateOf(endIdx)}} ($${{endPrice.toFixed(2)}})</span>
          <span>${{bars}} ${{t.bars}}</span>
          <span style="color:${{changeColor}}">${{sign}}${{change.toFixed(2)}} (${{sign}}${{pct.toFixed(2)}}%)</span>
          <span>${{direction}}</span>
          <button class="delete-drawing-btn" onclick="deleteDrawing(${{i}})" title="מחק">✕</button>
        </div>
      `;
    }} else {{
      const high = Math.max(p1.price, p2.price);
      const low = Math.min(p1.price, p2.price);
      return `
        <div class="drawing-info-card fibonacci">
          <span class="di-label">📐 ${{t.fibonacci}} #${{i + 1}}</span>
          <span>${{t.high}}: $${{high.toFixed(2)}} | ${{t.low}}: $${{low.toFixed(2)}}</span>
          <span>${{t.range}}: $${{(high - low).toFixed(2)}}</span>
          <span>${{dateOf(startIdx)}} עד ${{dateOf(endIdx)}}</span>
          <button class="delete-drawing-btn" onclick="deleteDrawing(${{i}})" title="מחק">✕</button>
        </div>
      `;
    }}
  }}).join('');
}}

function renderDrawing(ctx, drawing, geometry) {{
  if (!drawing || !drawing.p1 || !drawing.p2) return;
  const g = geometry;
  const localIndex1 = drawing.p1.index - viewStart;
  const localIndex2 = drawing.p2.index - viewStart;
  const x1 = g.padding.left + g.slotWidth * localIndex1 + g.slotWidth / 2;
  const x2 = g.padding.left + g.slotWidth * localIndex2 + g.slotWidth / 2;

  function priceToYLocal(price) {{
    return g.priceAreaTop + (1 - (price - g.minPrice) / (g.maxPrice - g.minPrice)) * g.priceAreaHeight;
  }}

  const y1 = priceToYLocal(drawing.p1.price);
  const y2 = priceToYLocal(drawing.p2.price);

  if (drawing.type === 'trendline') {{
    ctx.strokeStyle = '#9c27b0';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
    ctx.lineWidth = 1;
  }} else if (drawing.type === 'fibonacci') {{
    const levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1];
    const priceHigh = Math.max(drawing.p1.price, drawing.p2.price);
    const priceLow = Math.min(drawing.p1.price, drawing.p2.price);
    const range = priceHigh - priceLow;
    const xLeft = Math.min(x1, x2);
    const xRight = Math.max(x1, x2, xLeft + 40);

    levels.forEach(level => {{
      const price = priceHigh - level * range;
      const y = priceToYLocal(price);
      ctx.strokeStyle = 'rgba(255,152,0,0.8)';
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(xLeft, y);
      ctx.lineTo(xRight, y);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = '#e65100';
      ctx.font = '9px sans-serif';
      ctx.fillText(`${{(level * 100).toFixed(1)}}% ($${{price.toFixed(2)}})`, xRight + 2, y + 3);
    }});
  }}
}}

function pixelToDataCoord(pixelX, pixelY) {{
  if (!lastGeometry) return null;
  const g = lastGeometry;
  let localIndex = Math.floor((pixelX - g.padding.left) / g.slotWidth);
  localIndex = Math.max(0, Math.min(g.visibleCount - 1, localIndex));
  const absoluteIndex = viewStart + localIndex;
  const price = g.minPrice + (1 - (pixelY - g.priceAreaTop) / g.priceAreaHeight) * (g.maxPrice - g.minPrice);
  return {{ index: absoluteIndex, price }};
}}

function setDrawMode(mode) {{
  drawMode = mode;
  activeDraw = null;
  ['pan', 'trendline', 'fibonacci'].forEach(m => {{
    const btn = document.getElementById('draw-tool-' + m);
    if (btn) btn.classList.toggle('active', m === mode);
  }});
}}

function clearDrawings() {{
  currentDrawings = [];
  activeDraw = null;
  saveDrawings();
  updateDrawingInfo();
  renderModalChart();
}}

function renderModalChart(crosshair) {{
  // בונים חלון עם "מקומות ריקים" (null) בקצוות אם גררו מעבר לנתונים האמיתיים -
  // ככה רואים את הנרות האמיתיים נדחקים לצד אחד עם שטח ריק, לא נמתחים על כל הרוחב.
  const totalSlots = viewEnd - viewStart;
  const visibleCandles = [];
  const visibleDates = [];
  for (let i = 0; i < totalSlots; i++) {{
    const idx = viewStart + i;
    if (idx >= 0 && idx < fullCandles.length) {{
      visibleCandles.push({{ ...fullCandles[idx], dateLabel: fullDates[idx] }});
      visibleDates.push(fullDates[idx]);
    }} else {{
      visibleCandles.push(null);
      visibleDates.push(null);
    }}
  }}

  const realDates = visibleDates.filter(d => d !== null);
  const t = TRANSLATIONS[currentLanguage];
  const label = document.getElementById('modal-range-label');
  const zoomedNote = (viewStart > 0 || viewEnd < fullCandles.length) ? t.zoomed : '';
  label.innerText = realDates.length
    ? `${{realDates[0]}} ${{t.to}} ${{realDates[realDates.length - 1]}} (${{realDates.length}} ${{t.data_points}})${{zoomedNote}}`
    : t.no_data_range;

  drawCandlestick('modal-canvas', visibleCandles, crosshair);
}}

// --- אינטראקציה: גרירה = הזזה (pan), ריחוף = קו הצלבה, גלגלת = זום, דאבל-קליק = איפוס ---
let isDragging = false;
let dragStartX = 0;
let dragStartY = 0;
let dragStartViewStart = 0;
let dragStartViewEnd = 0;
let dragStartPriceMin = 0;
let dragStartPriceMax = 0;

const modalCanvasEl = document.getElementById('modal-canvas');
if (modalCanvasEl) {{
  const canvas = modalCanvasEl;

  canvas.addEventListener('mousedown', (e) => {{
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    if (drawMode === 'trendline' || drawMode === 'fibonacci') {{
      const coord = pixelToDataCoord(mouseX, mouseY);
      if (coord) {{
        activeDraw = {{ type: drawMode, p1: coord, p2: coord }};
      }}
    }} else {{
      isDragging = true;
      dragStartX = mouseX;
      dragStartY = mouseY;
      dragStartViewStart = viewStart;
      dragStartViewEnd = viewEnd;
      dragStartPriceMin = (manualPriceMin !== null) ? manualPriceMin : (lastGeometry ? lastGeometry.minPrice : 0);
      dragStartPriceMax = (manualPriceMax !== null) ? manualPriceMax : (lastGeometry ? lastGeometry.maxPrice : 1);
    }}
  }});

  canvas.addEventListener('mousemove', (e) => {{
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    if (activeDraw) {{
      const coord = pixelToDataCoord(mouseX, mouseY);
      if (coord) activeDraw.p2 = coord;
      renderModalChart({{ x: mouseX, y: mouseY }});
      return;
    }}

    if (isDragging) {{
      const plotWidth = rect.width - CHART_PADDING.left - CHART_PADDING.right;
      const currentLength = dragStartViewEnd - dragStartViewStart;
      const deltaPixels = mouseX - dragStartX;
      const deltaIndex = Math.round(-(deltaPixels / plotWidth) * currentLength);

      // מאפשרים לגרור קצת מעבר לקצוות הנתונים (שטח ריק) כדי שהגרירה תמיד תזיז
      // משהו, בדיוק כמו בהזזה האנכית - לא רק כשכבר בזום פנימה.
      const maxOverscroll = Math.max(5, Math.round(currentLength * 0.5));
      let newStart = dragStartViewStart + deltaIndex;
      newStart = Math.max(-maxOverscroll, Math.min(newStart, fullCandles.length + maxOverscroll - currentLength));
      let newEnd = newStart + currentLength;

      viewStart = newStart;
      viewEnd = newEnd;

      // הזזה אנכית (מחיר) - גוררים למעלה כדי לראות מחירים גבוהים יותר
      const priceAreaHeight = lastGeometry ? lastGeometry.priceAreaHeight : (rect.height - CHART_PADDING.top - CHART_PADDING.bottom);
      const currentPriceRange = dragStartPriceMax - dragStartPriceMin;
      const deltaYPixels = mouseY - dragStartY;
      const priceDelta = (deltaYPixels / priceAreaHeight) * currentPriceRange;
      manualPriceMin = dragStartPriceMin + priceDelta;
      manualPriceMax = dragStartPriceMax + priceDelta;

      renderModalChart();
    }} else {{
      renderModalChart({{ x: mouseX, y: mouseY }});
    }}
  }});

  canvas.addEventListener('mouseleave', () => {{
    isDragging = false;
    renderModalChart();
  }});

  window.addEventListener('mouseup', () => {{
    if (activeDraw) {{
      if (activeDraw.p1.index !== activeDraw.p2.index || activeDraw.p1.price !== activeDraw.p2.price) {{
        currentDrawings.push(activeDraw);
        saveDrawings();
        updateDrawingInfo();
      }}
      activeDraw = null;
      renderModalChart();
    }}
    isDragging = false;
  }});

  canvas.addEventListener('wheel', (e) => {{
    if (!fullCandles.length) return;
    e.preventDefault();
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const currentLength = viewEnd - viewStart;
    const fraction = (mouseX - CHART_PADDING.left) / (rect.width - CHART_PADDING.left - CHART_PADDING.right);
    const zoomFactor = e.deltaY < 0 ? 0.8 : 1.25;

    let newLength = Math.round(currentLength * zoomFactor);
    newLength = Math.max(5, Math.min(newLength, fullCandles.length));

    const centerIndex = viewStart + fraction * currentLength;
    let newStart = Math.round(centerIndex - fraction * newLength);
    let newEnd = newStart + newLength;

    if (newStart < 0) {{ newEnd -= newStart; newStart = 0; }}
    if (newEnd > fullCandles.length) {{ newStart -= (newEnd - fullCandles.length); newEnd = fullCandles.length; }}
    newStart = Math.max(0, newStart);

    viewStart = newStart;
    viewEnd = newEnd;
    renderModalChart();
  }}, {{ passive: false }});

  canvas.addEventListener('dblclick', () => {{
    resetZoom();
  }});
}}

// סוגר את החלון גם עם מקש Escape
document.addEventListener('keydown', (e) => {{
  if (e.key === 'Escape') closeStockModal();
}});

initLocationFromStorage();
loadPortfolioQty();
updatePortfolioTotal();
loadMoneyData();
loadGoal();
updateMoneyTotal();
</script>
</body>
</html>
"""

    with open(config.DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    return ticker_stats
