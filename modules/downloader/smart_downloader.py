# modules/downloader/smart_downloader.py
import asyncio
import aiohttp
import aiofiles
from typing import Optional, Callable, Dict, Any
import os
import time
from pathlib import Path
import hashlib
from urllib.parse import urlparse, unquote

class SmartDownloader:
    """سیستم دانلود هوشمند با قابلیت‌های پیشرفته"""
    
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_downloads = {}
        
    async def download_from_url(self, url: str, user_id: int, 
                               progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """دانلود از لینک با قابلیت‌های پیشرفته"""
        
        # بررسی نوع لینک
        if self._is_telegram_link(url):
            return await self._download_telegram_content(url, user_id, progress_callback)
        else:
            return await self._download_http_content(url, user_id, progress_callback)
    
    async def _download_http_content(self, url: str, user_id: int, 
                                    progress_callback: Optional[Callable]) -> Dict[str, Any]:
        """دانلود محتوای HTTP/HTTPS"""
        
        task_id = hashlib.md5(f"{url}_{user_id}".encode()).hexdigest()[:10]
        self.active_downloads[task_id] = {
            'start_time': time.time(),
            'last_update': time.time(),
            'downloaded': 0,
            'speed': 0
        }
        
        try:
            async with self.semaphore:
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=3600)
                ) as session:
                    
                    # دریافت هدرها
                    async with session.head(url, allow_redirects=True) as head_resp:
                        total_size = int(head_resp.headers.get('content-length', 0))
                        
                        if total_size > settings.MAX_FILE_SIZE:
                            return {
                                'success': False,
                                'error': f'حجم فایل ({total_size/1024/1024:.1f}MB) بیشتر از حد مجاز است',
                                'task_id': task_id
                            }
                        
                        # تعیین نام فایل
                        filename = self._extract_filename(url, head_resp)
                        
                        # ایجاد مسیر دانلود
                        download_path = self._get_download_path(user_id, filename)
                        
                        # دانلود فایل
                        await self._download_with_progress(
                            session, url, download_path, total_size,
                            task_id, progress_callback
                        )
                        
                        # بررسی یکپارچگی فایل
                        if await self._verify_file_integrity(download_path, total_size):
                            return {
                                'success': True,
                                'file_path': str(download_path),
                                'file_name': filename,
                                'file_size': total_size,
                                'task_id': task_id,
                                'download_type': 'http'
                            }
                        else:
                            return {
                                'success': False,
                                'error': 'خطا در یکپارچگی فایل دانلود شده',
                                'task_id': task_id
                            }
                            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'task_id': task_id
            }
        finally:
            if task_id in self.active_downloads:
                del self.active_downloads[task_id]
    
    async def _download_with_progress(self, session, url, file_path, 
                                     total_size, task_id, progress_callback):
        """دانلود با نمایش پیشرفت"""
        
        downloaded = 0
        start_time = time.time()
        
        async with session.get(url) as response:
            async with aiofiles.open(file_path, 'wb') as f:
                async for chunk in response.content.iter_chunked(8192 * 8):  # 64KB chunks
                    if chunk:
                        await f.write(chunk)
                        downloaded += len(chunk)
                        
                        # محاسبه سرعت
                        elapsed = time.time() - start_time
                        speed = downloaded / elapsed if elapsed > 0 else 0
                        
                        # به‌روزرسانی آمار
                        self.active_downloads[task_id].update({
                            'downloaded': downloaded,
                            'speed': speed,
                            'last_update': time.time()
                        })
                        
                        # فراخوانی callback پیشرفت
                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            eta = (total_size - downloaded) / speed if speed > 0 else 0
                            
                            await progress_callback({
                                'task_id': task_id,
                                'progress': progress,
                                'downloaded': downloaded,
                                'total': total_size,
                                'speed': speed,
                                'eta': eta,
                                'filename': file_path.name
                            })
    
    def _extract_filename(self, url: str, response) -> str:
        """استخراج نام فایل از URL و هدرها"""
        
        # بررسی content-disposition
        cd = response.headers.get('content-disposition', '')
        if 'filename=' in cd:
            filename = cd.split('filename=')[1].strip('"\'').strip()
            return unquote(filename)
        
        # استخراج از URL
        parsed = urlparse(url)
        if parsed.path:
            filename = parsed.path.split('/')[-1]
            if filename:
                return unquote(filename)
        
        # نام پیش‌فرض
        return f"download_{int(time.time())}.bin"
    
    def _get_download_path(self, user_id: int, filename: str) -> Path:
        """ایجاد مسیر دانلود"""
        
        user_dir = settings.DOWNLOADS_DIR / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # جلوگیری از تداخل نام فایل
        base_name = Path(filename).stem
        extension = Path(filename).suffix
        
        counter = 1
        final_path = user_dir / filename
        
        while final_path.exists():
            final_path = user_dir / f"{base_name}_{counter}{extension}"
            counter += 1
        
        return final_path
    
    async def _verify_file_integrity(self, file_path: Path, expected_size: int) -> bool:
        """بررسی یکپارچگی فایل دانلود شده"""
        
        if not file_path.exists():
            return False
        
        actual_size = file_path.stat().st_size
        
        if expected_size > 0 and actual_size != expected_size:
            return False
        
        return True
    
    def _is_telegram_link(self, url: str) -> bool:
        """بررسی اینکه آیا لینک تلگرام است"""
        telegram_domains = ['t.me', 'telegram.me', 'telegram.dog']
        parsed = urlparse(url)
        return any(domain in parsed.netloc for domain in telegram_domains)
    
    async def _download_telegram_content(self, url: str, user_id: int, 
                                        progress_callback: Optional[Callable]) -> Dict[str, Any]:
        """دانلود محتوای تلگرام"""
        # این بخش نیاز به اتصال به کلاینت کاربر دارد
        # فعلاً یک پیام بازگشتی می‌دهیم
        return {
            'success': False,
            'error': 'دانلود از لینک تلگرام نیاز به اتصال به حساب کاربری دارد. لطفاً ابتدا وارد شوید.',
            'task_id': 'telegram_dl'
        }
