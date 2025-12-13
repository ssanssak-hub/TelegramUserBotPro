#config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # تنظیمات API از my.telegram.org
    API_ID = int(os.getenv('API_ID', 0))
    API_HASH = os.getenv('API_HASH', '')
    
    # توکن ربات از @BotFather
    BOT_TOKEN = os.getenv('BOT_TOKEN', '')
    
    # تنظیمات دیتابیس (اختیاری - برای ذخیره کاربران)
    DB_PATH = os.getenv('DB_PATH', 'users.db')
    
    # محدودیت‌ها
    MAX_FILE_SIZE = 2000 * 1024 * 1024  # 2GB
    MAX_SESSIONS_PER_USER = 3
    SESSION_TIMEOUT = 24 * 60 * 60  # 24 ساعت
    
    # تنظیمات امنیتی
    ALLOWED_USER_IDS = [int(x) for x in os.getenv('ALLOWED_USER_IDS', '').split(',') if x]
    ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x]
