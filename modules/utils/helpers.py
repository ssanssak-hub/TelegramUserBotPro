# modules/utils/helpers.py
import os
import hashlib
import re
from typing import Optional, Tuple, List
from urllib.parse import urlparse
from pathlib import Path
import mimetypes

class Helpers:
    """توابع کمکی"""
    
    @staticmethod
    def validate_url(url: str) -> Tuple[bool, Optional[str]]:
        """اعتبارسنجی URL"""
        try:
            result = urlparse(url)
            if all([result.scheme, result.netloc]):
                if result.scheme in ['http', 'https', 'ftp']:
                    return True, None
                else:
                    return False, "پروتکل پشتیبانی نمی‌شود"
            else:
                return False, "URL نامعتبر است"
        except:
            return False, "URL نامعتبر است"
    
    @staticmethod
    def validate_telegram_link(url: str) -> Tuple[bool, Optional[str]]:
        """اعتبارسنجی لینک تلگرام"""
        patterns = [
            r'^https?://t\.me/([a-zA-Z0-9_]+)/(\d+)$',
            r'^https?://telegram\.me/([a-zA-Z0-9_]+)/(\d+)$',
            r'^https?://telegram\.dog/([a-zA-Z0-9_]+)/(\d+)$',
            r'^https?://t\.me/joinchat/([a-zA-Z0-9_-]+)$',
            r'^https?://t\.me/c/(\d+)/(\d+)$'
        ]
        
        for pattern in patterns:
            if re.match(pattern, url):
                return True, None
        
        return False, "لینک تلگرام نامعتبر است"
    
    @staticmethod
    def get_file_hash(file_path: str, algorithm: str = 'md5') -> str:
        """محاسبه هش فایل"""
        hash_func = getattr(hashlib, algorithm)()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict:
        """دریافت اطلاعات فایل"""
        path = Path(file_path)
        
        if not path.exists():
            return {'error': 'فایل وجود ندارد'}
        
        stat = path.stat()
        
        return {
            'name': path.name,
            'size': stat.st_size,
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'extension': path.suffix.lower(),
            'mime_type': mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
        }
    
    @staticmethod
    def format_time_delta(seconds: float) -> str:
        """فرمت‌بندی زمان"""
        if seconds < 60:
            return f"{int(seconds)} ثانیه"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes} دقیقه و {secs} ثانیه"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours} ساعت و {minutes} دقیقه"
        else:
            days = int(seconds // 86400)
            hours = int((seconds % 86400) // 3600)
            return f"{days} روز و {hours} ساعت"
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """پاک‌سازی نام فایل"""
        # حذف کاراکترهای خطرناک
        dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # محدود کردن طول
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200 - len(ext)] + ext
        
        return filename
    
    @staticmethod
    def split_list(lst: List, chunk_size: int) -> List[List]:
        """تقسیم لیست به بخش‌های کوچک"""
        return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
    
    @staticmethod
    def is_admin(user_id: int, admin_ids: List[int]) -> bool:
        """بررسی ادمین بودن کاربر"""
        return user_id in admin_ids
    
    @staticmethod
    def create_progress_text(downloaded: int, total: int, 
                            speed: float, elapsed: float) -> str:
        """ایجاد متن پیشرفت"""
        if total == 0:
            return "در حال محاسبه..."
        
        percentage = (downloaded / total) * 100
        
        # نوار پیشرفت
        bar_length = 20
        filled_length = int(bar_length * downloaded // total)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        # فرمت‌بندی
        downloaded_fmt = Helpers._format_size(downloaded)
        total_fmt = Helpers._format_size(total)
        speed_fmt = Helpers._format_size(speed) + "/s"
        
        # محاسبه زمان باقی‌مانده
        if speed > 0:
            eta = (total - downloaded) / speed
            eta_fmt = Helpers.format_time_delta(eta)
        else:
            eta_fmt = "نامحدود"
        
        return f"""
{bar} {percentage:.1f}%

📊 {downloaded_fmt} / {total_fmt}
⚡ سرعت: {speed_fmt}
⏱️ زمان باقی‌مانده: {eta_fmt}
        """
    
    @staticmethod
    def _format_size(size: float) -> str:
        """فرمت‌بندی حجم"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
