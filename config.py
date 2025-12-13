import os
from dotenv import load_dotenv

load_dotenv()

# اطلاعات API تلگرام
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# ادمین‌های ربات
ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]

# تنظیمات دیتابیس
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///database.db")

# محدودیت‌ها
MAX_DOWNLOAD_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
MAX_CONCURRENT_DOWNLOADS = 3
DOWNLOAD_SPEED_LIMIT = 50 * 1024 * 1024  # 50 MB/s

# تنظیمات سرور (اختیاری)
PROXY = None  # یا {'scheme': 'socks5', 'hostname': 'localhost', 'port': 9050}
