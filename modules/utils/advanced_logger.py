# modules/utils/advanced_logger.py
import logging
import logging.handlers
import json
from datetime import datetime
from pathlib import Path
import sys

class AdvancedLogger:
    """سیستم لاگ‌گیری پیشرفته"""
    
    def __init__(self, name: str, log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # جلوگیری از لاگ‌های تکراری
        self.logger.propagate = False
        
        # تنظیم فرمت
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler کنسول
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Handler فایل برای همه لاگ‌ها
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'bot.log',
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Handler فایل برای خطاها
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'errors.log',
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)
        
        # Handler فایل برای فعالیت کاربران
        user_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'users.log',
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        user_handler.setLevel(logging.INFO)
        user_formatter = logging.Formatter(
            '%(asctime)s - USER:%(user_id)s - ACTION:%(action)s - %(message)s'
        )
        user_handler.setFormatter(user_formatter)
        self.logger.addHandler(user_handler)
    
    def log_user_action(self, user_id: int, action: str, details: str = "", 
                       extra_data: dict = None):
        """ثبت فعالیت کاربر"""
        extra = {
            'user_id': user_id,
            'action': action
        }
        
        if extra_data:
            extra.update(extra_data)
        
        self.logger.info(details, extra=extra)
    
    def log_download_start(self, user_id: int, url: str, file_name: str):
        """ثبت شروع دانلود"""
        self.log_user_action(
            user_id,
            'download_start',
            f"شروع دانلود: {file_name} از {url}"
        )
    
    def log_download_complete(self, user_id: int, file_name: str, 
                            file_size: int, download_time: float):
        """ثبت اتمام دانلود"""
        speed = file_size / download_time if download_time > 0 else 0
        
        self.log_user_action(
            user_id,
            'download_complete',
            f"اتمام دانلود: {file_name} ({file_size} بایت, {speed:.2f} بایت/ثانیه)",
            {
                'file_size': file_size,
                'download_time': download_time,
                'speed': speed
            }
        )
    
    def log_login(self, user_id: int, success: bool, method: str = ""):
        """ثبت ورود"""
        status = "موفق" if success else "ناموفق"
        self.log_user_action(
            user_id,
            'login',
            f"ورود {status} با روش {method}"
        )
    
    def log_security_event(self, event_type: str, user_id: int = None, 
                          details: str = "", severity: str = "MEDIUM"):
        """ثبت رویداد امنیتی"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'severity': severity,
            'details': details
        }
        
        # ذخیره در فایل JSON
        security_log = self.log_dir / 'security.json'
        with open(security_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
        
        # همچنین در لاگ معمولی
        self.logger.warning(
            f"رویداد امنیتی: {event_type} - کاربر: {user_id} - جزئیات: {details}",
            extra={'user_id': user_id or 'system', 'action': 'security_event'}
        )
    
    def get_recent_logs(self, lines: int = 100, log_type: str = "bot") -> list:
        """دریافت لاگ‌های اخیر"""
        log_file = self.log_dir / f"{log_type}.log"
        
        if not log_file.exists():
            return []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return all_lines[-lines:]
        except:
            return []
