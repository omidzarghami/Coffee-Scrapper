# Coffee Scrapper

اسکرپر اخبار قهوه از [World Coffee Portal](https://www.worldcoffeeportal.com/latest). پیش‌نمایش عمومی مقاله با Gemini رایگان به فارسی ترجمه می‌شود و هر روز یک پست به کانال تلگرام ارسال می‌گردد.

## نصب

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

در `.env` این‌ها را بگذار (این فایل را commit نکن):

```
GEMINI_API_KEY=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHANNEL_ID=-100...
```

کلید رایگان Gemini: [Google AI Studio](https://aistudio.google.com/apikey)

ربات تلگرام باید **ادمین کانال** باشد و اجازه ارسال پیام داشته باشد.

## اجرا

```bash
python main.py --list --max=8
python main.py --max=1 --send
```

GitHub Action هر روز ساعت `۰۸:۰۰` به وقت ایران (`04:30 UTC`) یک مقاله تازه می‌فرستد. Secrets لازم:

- `GEMINI_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHANNEL_ID`

## خروجی محلی

- `output/telegram-board.html` — پیش‌نمایش راست‌چین
- `output/seen.json` — لینک‌های ارسال‌شده (برای جلوگیری از تکرار)
