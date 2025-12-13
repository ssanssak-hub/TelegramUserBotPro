#downloader.py
import asyncio
import os
import time
from typing import Dict, Any, Callable
from pyrogram import Client
from pyrogram.types import Message
import aiohttp
from urllib.parse import urlparse

class DownloadManager:
    def __init__(self):
        self.downloads: Dict[int, Dict] = {}
        self.chunk_size = 65536  # 64KB
        
    async def download_message(self, client: Client, message: Message, 
                              user_id: int, progress_callback: Callable = None) -> Dict[str, Any]:
        """دانلود محتوا از یک پیام"""
        try:
            if message.media:
                # تعیین نوع مدیا و نام فایل
                if message.document:
                    file_name = message.document.file_name
                    file_size = message.document.file_size
                    media_type = "document"
                elif message.video:
                    file_name = f"{message.video.file_name or 'video'}.mp4"
                    file_size = message.video.file_size
                    media_type = "video"
                elif message.audio:
                    file_name = f"{message.audio.file_name or 'audio'}.mp3"
                    file_size = message.audio.file_size
                    media_type = "audio"
                elif message.photo:
                    file_name = f"photo_{message.id}.jpg"
                    file_size = 0  # عکس‌ها سایز مشخصی ندارند
                    media_type = "photo"
                else:
                    return {"success": False, "error": "نوع مدیا پشتیبانی نمی‌شود"}
                
                # ایجاد پوشه دانلود
                download_dir = f"downloads/{user_id}"
                os.makedirs(download_dir, exist_ok=True)
                file_path = os.path.join(download_dir, file_name)
                
                # تابع callback برای نمایش پیشرفت
                async def progress(current, total):
                    if progress_callback:
                        percentage = (current / total) * 100
                        speed = self._calculate_speed(user_id, current)
                        eta = self._calculate_eta(current, total, speed)
                        
                        progress_data = {
                            'percentage': percentage,
                            'downloaded': current,
                            'total': total,
                            'speed': speed,
                            'eta': eta,
                            'filename': file_name
                        }
                        
                        await progress_callback(progress_data)
                
                # دانلود فایل
                await client.download_media(
                    message,
                    file_name=file_path,
                    progress=progress
                )
                
                return {
                    "success": True,
                    "file_path": file_path,
                    "file_name": file_name,
                    "file_size": file_size,
                    "media_type": media_type
                }
            else:
                return {"success": False, "error": "پیام حاوی مدیا نیست"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def download_from_url(self, client: Client, url: str, 
                               user_id: int, progress_callback: Callable = None) -> Dict[str, Any]:
        """دانلود از لینک مستقیم"""
        try:
            parsed_url = urlparse(url)
            
            # اگر لینک تلگرام باشد
            if "t.me" in parsed_url.netloc:
                return await self._download_telegram_link(client, url, user_id, progress_callback)
            else:
                return await self._download_direct_link(url, user_id, progress_callback)
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _download_telegram_link(self, client: Client, url: str, 
                                     user_id: int, progress_callback: Callable) -> Dict[str, Any]:
        """دانلود لینک تلگرام"""
        # تجزیه لینک تلگرام
        # این بخش نیاز به پردازش پیچیده دارد
        # فعلاً پیام دهید که این قابلیت در حال توسعه است
        return {"success": False, "error": "دانلود از لینک تلگرام در حال توسعه است"}
    
    async def _download_direct_link(self, url: str, user_id: int, 
                                   progress_callback: Callable) -> Dict[str, Any]:
        """دانلود لینک مستقیم"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=3600) as response:
                if response.status == 200:
                    # دریافت نام فایل
                    content_disposition = response.headers.get('content-disposition', '')
                    if 'filename=' in content_disposition:
                        file_name = content_disposition.split('filename=')[1].strip('"\'')
                    else:
                        file_name = url.split('/')[-1] or f"download_{int(time.time())}"
                    
                    # ایجاد پوشه دانلود
                    download_dir = f"downloads/{user_id}"
                    os.makedirs(download_dir, exist_ok=True)
                    file_path = os.path.join(download_dir, file_name)
                    
                    # دریافت حجم فایل
                    total_size = int(response.headers.get('content-length', 0))
                    
                    # دانلود با نمایش پیشرفت
                    downloaded = 0
                    start_time = time.time()
                    
                    with open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(self.chunk_size):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                
                                if progress_callback and total_size > 0:
                                    elapsed = time.time() - start_time
                                    speed = downloaded / elapsed if elapsed > 0 else 0
                                    percentage = (downloaded / total_size) * 100
                                    eta = (total_size - downloaded) / speed if speed > 0 else 0
                                    
                                    progress_data = {
                                        'percentage': percentage,
                                        'downloaded': downloaded,
                                        'total': total_size,
                                        'speed': speed,
                                        'eta': int(eta),
                                        'filename': file_name
                                    }
                                    
                                    await progress_callback(progress_data)
                    
                    return {
                        "success": True,
                        "file_path": file_path,
                        "file_name": file_name,
                        "file_size": total_size
                    }
                else:
                    return {"success": False, "error": f"خطای HTTP: {response.status}"}
    
    def _calculate_speed(self, user_id: int, downloaded: int) -> float:
        """محاسبه سرعت دانلود"""
        if user_id not in self.downloads:
            self.downloads[user_id] = {'start_time': time.time(), 'last_downloaded': 0}
        
        download_info = self.downloads[user_id]
        elapsed = time.time() - download_info['start_time']
        
        if elapsed > 0:
            speed = (downloaded - download_info['last_downloaded']) / elapsed
            download_info['last_downloaded'] = downloaded
            download_info['start_time'] = time.time()
            return speed
        return 0
    
    def _calculate_eta(self, downloaded: int, total: int, speed: float) -> int:
        """محاسبه زمان باقی‌مانده"""
        if speed > 0:
            return int((total - downloaded) / speed)
        return 0
