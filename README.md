# Coffee Scrapper

اسکرپر اخبار قهوه از [World Coffee Portal](https://www.worldcoffeeportal.com/latest). پیش‌نمایش عمومی مقاله با Gemini رایگان به فارسی ترجمه می‌شود و هر روز یک پست به کانال تلگرام ارسال می‌گردد.

## نصب

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

در `.env` این‌ها را بگذار (این فایل commit نمی‌شود):

```
GEMINI_API_KEY=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHANNEL_ID=-100...
```

کلید رایگان Gemini: [Google AI Studio](https://aistudio.google.com/apikey)

ربات تلگرام باید **ادمین کانال** باشد و اجازه ارسال پیام داشته باشد.

## اجرا

```bash
# فقط فهرست آخرین تیترها
python main.py --list --max=8

# اسکرپ و ترجمه بدون ارسال
python main.py --max=1

# ترجمه و ارسال به کانال
python main.py --max=1 --send
```

قبل از اجرای محلی با `--send` یک `git pull` بزن تا `output/seen.json` به‌روز باشد و خبری که Action قبلاً فرستاده دوباره ارسال نشود.

## ارسال خودکار

`.github/workflows/daily-telegram.yml` هر روز `04:30 UTC` (ساعت ۸ صبح ایران) یک مقاله تازه می‌فرستد و `output/seen.json` را commit می‌کند.

Secrets لازم در تنظیمات ریپو:

- `GEMINI_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHANNEL_ID`

اجرای دستی: تب **Actions** → «Daily coffee article» → **Run workflow**

## خروجی محلی

- `output/telegram-board.html` — پیش‌نمایش راست‌چین پست‌ها
- `output/articles.json` و `output/posts/*.json` — متن آماده کپی
- `output/seen.json` — لینک‌های ارسال‌شده (برای جلوگیری از تکرار)

## قالب پست

1. تصویر + تیتر فارسی + تاریخ شمسی + منبع «ورلد کافی پورتال» + دکمه مطالعه اصل مقاله
2. ادامه ترجمه شماره‌دار (`📝 1- ...`)
