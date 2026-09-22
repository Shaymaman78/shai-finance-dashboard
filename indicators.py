"""
חישוב אינדיקטורים טכניים בסיסיים - ממוצע נע (SMA) ו-RSI.
חשוב: אלה נתונים טכניים אינפורמטיביים בלבד, לא המלצות השקעה.
"""


def sma(values, period):
    """ממוצע נע פשוט על הערך האחרון. מחזיר None אם אין מספיק נתונים."""
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def rsi(values, period=14):
    """RSI (Relative Strength Index) על הערך האחרון. מחזיר None אם אין מספיק נתונים."""
    if len(values) < period + 1:
        return None
    deltas = [values[i] - values[i - 1] for i in range(1, len(values))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def trend_label_i18n(sma20, sma50):
    """
    תיאור מגמה טכני רב-לשוני על סמך יחס בין שני ממוצעים נעים -
    לא המלצת השקעה, רק תיאור נתון. מחזיר dict {lang: text}.
    """
    if sma20 is None or sma50 is None:
        return {
            "he": "אין מספיק נתונים", "en": "Not enough data",
            "es": "Datos insuficientes", "fr": "Données insuffisantes",
            "ar": "بيانات غير كافية",
        }
    if sma20 > sma50:
        return {
            "he": "מגמה טכנית חיובית (ממוצע קצר מעל ממוצע ארוך)",
            "en": "Positive technical trend (short MA above long MA)",
            "es": "Tendencia técnica positiva (media corta sobre media larga)",
            "fr": "Tendance technique positive (MM courte au-dessus de MM longue)",
            "ar": "اتجاه فني إيجابي (المتوسط القصير فوق المتوسط الطويل)",
        }
    if sma20 < sma50:
        return {
            "he": "מגמה טכנית שלילית (ממוצע קצר מתחת לממוצע ארוך)",
            "en": "Negative technical trend (short MA below long MA)",
            "es": "Tendencia técnica negativa (media corta bajo media larga)",
            "fr": "Tendance technique négative (MM courte sous MM longue)",
            "ar": "اتجاه فني سلبي (المتوسط القصير تحت المتوسط الطويل)",
        }
    return {
        "he": "מגמה טכנית ניטרלית", "en": "Neutral technical trend",
        "es": "Tendencia técnica neutral", "fr": "Tendance technique neutre",
        "ar": "اتجاه فني محايد",
    }


def rsi_label_i18n(rsi_value):
    """תיאור מצב RSI רב-לשוני - לא המלצת השקעה, רק תיאור נתון טכני מקובל. מחזיר dict {lang: text}."""
    if rsi_value is None:
        return {
            "he": "אין מספיק נתונים", "en": "Not enough data",
            "es": "Datos insuficientes", "fr": "Données insuffisantes",
            "ar": "بيانات غير كافية",
        }
    if rsi_value >= 70:
        return {
            "he": f"RSI גבוה ({rsi_value:.0f}) - אזור שנחשב טכנית 'קניית יתר'",
            "en": f"High RSI ({rsi_value:.0f}) - technically considered 'overbought'",
            "es": f"RSI alto ({rsi_value:.0f}) - zona técnicamente considerada 'sobrecompra'",
            "fr": f"RSI élevé ({rsi_value:.0f}) - zone techniquement considérée en 'surachat'",
            "ar": f"مؤشر RSI مرتفع ({rsi_value:.0f}) - منطقة تعتبر فنياً 'تشبع شرائي'",
        }
    if rsi_value <= 30:
        return {
            "he": f"RSI נמוך ({rsi_value:.0f}) - אזור שנחשב טכנית 'מכירת יתר'",
            "en": f"Low RSI ({rsi_value:.0f}) - technically considered 'oversold'",
            "es": f"RSI bajo ({rsi_value:.0f}) - zona técnicamente considerada 'sobreventa'",
            "fr": f"RSI faible ({rsi_value:.0f}) - zone techniquement considérée en 'survente'",
            "ar": f"مؤشر RSI منخفض ({rsi_value:.0f}) - منطقة تعتبر فنياً 'تشبع بيعي'",
        }
    return {
        "he": f"RSI ניטרלי ({rsi_value:.0f})", "en": f"Neutral RSI ({rsi_value:.0f})",
        "es": f"RSI neutral ({rsi_value:.0f})", "fr": f"RSI neutre ({rsi_value:.0f})",
        "ar": f"مؤشر RSI محايد ({rsi_value:.0f})",
    }
