# הדשבורד האישי שלי

עוקב אחרי מזג האוויר בחיפה ואחרי המניות: AMZN, BE, GOOG, IBM, MRVL, MU, NASA (Tema Space
Innovators ETF), NOK, PLPC, TSLA. כל הרצה שומרת את הנתונים להיסטוריה ובונה מחדש עמוד
`dashboard.html` עם גרפים.

## התקנה (פעם אחת)

1. ודא שיש לך Python 3.9+ מותקן (`python3 --version`).
2. בתוך תיקיית הפרויקט, התקן את הספריות הדרושות:

```bash
pip install -r requirements.txt --break-system-packages
```

(אם אתה עובד בסביבה וירטואלית - `python3 -m venv venv && source venv/bin/activate` לפני זה -
אז בלי `--break-system-packages`.)

## הרצה ידנית

```bash
python3 main.py
```

זה ייצור/יעדכן:
- `data/stock_history.csv` - היסטוריית מחירים
- `data/weather_history.csv` - היסטוריית מזג אוויר
- `dashboard.html` - העמוד שאתה פותח בדפדפן

## הרצה אוטומטית כל יום בשעה קבועה

### macOS / Linux (cron)

1. פתח את עורך ה-cron:
```bash
crontab -e
```
2. הוסף שורה (הדוגמה מריצה כל יום ב-08:00 - שנה לפי הצורך):
```
0 8 * * * cd /נתיב/מלא/לתיקיית/dashboard && /usr/bin/python3 main.py >> run.log 2>&1
```

### Windows (Task Scheduler)

1. פתח את "Task Scheduler" -> "Create Basic Task"
2. בחר טריגר יומי בשעה הרצויה
3. תחת Action, בחר "Start a program":
   - Program: `python`
   - Arguments: `main.py`
   - Start in: הנתיב המלא לתיקיית `dashboard`

## הערות

- מקור נתוני מזג האוויר: Open-Meteo (חינמי, ללא מפתח API).
- מקור מחירי המניות: ספריית `yfinance` (נתונים מ-Yahoo Finance).
- הדשבורד מיועד למעקב אישי בלבד ולא מהווה ייעוץ השקעות.
