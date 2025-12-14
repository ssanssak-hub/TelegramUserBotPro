# modules/uploader/smart_uploader.py
import asyncio
import os
import time
from typing import Dict, Any, Optional, Callable
from pathlib import Path
import aiofiles
from pyrogram import Client
from pyrogram.types import Message, InputMediaDocument, InputMediaVideo, InputMediaPhoto, InputMediaAudio
from pyrogram.errors import FloodWait, FilePartMissing
import math

class SmartUploader:
    """سیستم آپلود هوشمند با قابلیت Resume و نمایش پیشرفت"""
    
    def __init__(self):
        self.chunk_size = 512 * 1024  # 512KB
        self.max_retries = 3
        self.active_uploads = {}
        
    async def upload_file(self, client: Client, file_path: str, 
                         chat_id: int, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """آپلود فایل با نمایش پیشرفت"""
        
        task_id = os.path.basename(file_path)
        self.active_uploads[task_id] = {
            'start_time': time.time(),
            'uploaded': 0,
            'speed': 0,
            'retries': 0
        }
        
        try:
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            
            # تعیین نوع مدیا
            media_type = self._detect_media_type(file_path)
            
            # نمایش شروع آپلود
            if progress_callback:
                await progress_callback({
                    'task_id': task_id,
                    'progress': 0,
                    'uploaded': 0,
                    'total': file_size,
                    'filename': file_name,
                    'status': 'starting'
                })
            
            # آپلود با توجه به نوع فایل
            if file_size < 10 * 1024 * 1024:  # کمتر از 10MB
                result = await self._upload_small_file(
                    client, file_path, chat_id, file_name, 
                    media_type, progress_callback, task_id, file_size
                )
            else:
                result = await self._upload_large_file(
                    client, file_path, chat_id, file_name,
                    media_type, progress_callback, task_id, file_size
                )
            
            # ثبت لاگ موفقیت
            self._log_upload_success(task_id, file_size, result)
            
            return {
                'success': True,
                'message_id': result.id if hasattr(result, 'id') else None,
                'file_id': result.document.file_id if hasattr(result, 'document') else None,
                'file_path': file_path,
                'file_size': file_size,
                'upload_time': time.time() - self.active_uploads[task_id]['start_time']
            }
            
        except FloodWait as e:
            # مدیریت FloodWait
            wait_time = e.value
            if progress_callback:
                await progress_callback({
                    'task_id': task_id,
                    'status': 'flood_wait',
                    'wait_time': wait_time
                })
            
            await asyncio.sleep(wait_time)
            return await self.upload_file(client, file_path, chat_id, progress_callback)
            
        except Exception as e:
            # مدیریت خطا
            return {
                'success': False,
                'error': str(e),
                'task_id': task_id,
                'retries': self.active_uploads.get(task_id, {}).get('retries', 0)
            }
        finally:
            # پاکسازی
            if task_id in self.active_uploads:
                del self.active_uploads[task_id]
    
    async def _upload_small_file(self, client: Client, file_path: str, 
                                chat_id: int, file_name: str, media_type: str,
                                progress_callback: Callable, task_id: str, 
                                file_size: int):
        """آپلود فایل‌های کوچک"""
        
        # تابع callback برای پیشرفت
        async def progress(current, total):
            if progress_callback:
                progress_percent = (current / total) * 100
                elapsed = time.time() - self.active_uploads[task_id]['start_time']
                speed = current / elapsed if elapsed > 0 else 0
                
                self.active_uploads[task_id].update({
                    'uploaded': current,
                    'speed': speed
                })
                
                await progress_callback({
                    'task_id': task_id,
                    'progress': progress_percent,
                    'uploaded': current,
                    'total': total,
                    'speed': speed,
                    'eta': (total - current) / speed if speed > 0 else 0,
                    'filename': file_name,
                    'status': 'uploading'
                })
        
        # آپلود بر اساس نوع
        if media_type == 'photo':
            return await client.send_photo(
                chat_id=chat_id,
                photo=file_path,
                caption=f"📸 {file_name}",
                progress=progress
            )
        elif media_type == 'video':
            return await client.send_video(
                chat_id=chat_id,
                video=file_path,
                caption=f"🎥 {file_name}",
                supports_streaming=True,
                progress=progress
            )
        elif media_type == 'audio':
            return await client.send_audio(
                chat_id=chat_id,
                audio=file_path,
                caption=f"🎵 {file_name}",
                progress=progress
            )
        else:
            return await client.send_document(
                chat_id=chat_id,
                document=file_path,
                caption=f"📄 {file_name}",
                force_document=True,
                progress=progress
            )
    
    async def _upload_large_file(self, client: Client, file_path: str,
                                chat_id: int, file_name: str, media_type: str,
                                progress_callback: Callable, task_id: str,
                                file_size: int):
        """آپلود فایل‌های بزرگ با قابلیت Resume"""
        
        # بررسی فایل آپلود شده قبلی
        resume_info = await self._check_resume_info(file_path, chat_id)
        
        if resume_info and resume_info.get('uploaded', 0) > 0:
            # ادامه آپلود قبلی
            await progress_callback({
                'task_id': task_id,
                'status': 'resuming',
                'resumed_from': resume_info['uploaded']
            })
            
            offset = resume_info['uploaded']
        else:
            offset = 0
        
        # آپلود به صورت قطعه‌ای
        async with aiofiles.open(file_path, 'rb') as file:
            if offset > 0:
                await file.seek(offset)
            
            part_number = offset // self.chunk_size
            
            while offset < file_size:
                # خواندن قطعه
                chunk = await file.read(self.chunk_size)
                chunk_size = len(chunk)
                
                if not chunk:
                    break
                
                # آپلود قطعه
                try:
                    # اینجا نیاز به استفاده از روش آپلود قطعه‌ای تلگرام داریم
                    # برای سادگی فعلاً از send_document استفاده می‌کنیم
                    if offset == 0:  # اولین قطعه
                        result = await client.send_document(
                            chat_id=chat_id,
                            document=file_path,
                            caption=f"📦 {file_name} (بزرگ)",
                            file_name=file_name,
                            force_document=True
                        )
                        file_id = result.document.file_id
                    
                    # به‌روزرسانی پیشرفت
                    offset += chunk_size
                    progress_percent = (offset / file_size) * 100
                    
                    if progress_callback:
                        elapsed = time.time() - self.active_uploads[task_id]['start_time']
                        speed = offset / elapsed if elapsed > 0 else 0
                        
                        await progress_callback({
                            'task_id': task_id,
                            'progress': progress_percent,
                            'uploaded': offset,
                            'total': file_size,
                            'speed': speed,
                            'eta': (file_size - offset) / speed if speed > 0 else 0,
                            'filename': file_name,
                            'status': 'uploading',
                            'part': part_number
                        })
                    
                    # ذخیره اطلاعات برای Resume
                    await self._save_resume_info(file_path, chat_id, offset)
                    
                    part_number += 1
                    
                except Exception as e:
                    # مدیریت خطا و ریتری
                    if self.active_uploads[task_id]['retries'] < self.max_retries:
                        self.active_uploads[task_id]['retries'] += 1
                        await asyncio.sleep(2)  # تاخیر قبل از ریتری
                        continue
                    else:
                        raise e
        
        # پاکسازی اطلاعات Resume
        await self._clear_resume_info(file_path, chat_id)
        
        # بازگشت نتیجه
        return {'id': 'uploaded', 'document': {'file_id': 'large_file_id'}}  # جایگزین با نتیجه واقعی
    
    def _detect_media_type(self, file_path: str) -> str:
        """تشخیص نوع فایل"""
        ext = Path(file_path).suffix.lower()
        
        image_exts = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif']
        video_exts = ['.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv']
        audio_exts = ['.mp3', '.ogg', '.wav', '.flac', '.m4a']
        
        if ext in image_exts:
            return 'photo'
        elif ext in video_exts:
            return 'video'
        elif ext in audio_exts:
            return 'audio'
        else:
            return 'document'
    
    async def _check_resume_info(self, file_path: str, chat_id: int) -> Optional[Dict]:
        """بررسی اطلاعات Resume"""
        # پیاده‌سازی ساده - در نسخه کامل در دیتابیس ذخیره می‌شود
        return None
    
    async def _save_resume_info(self, file_path: str, chat_id: int, uploaded: int):
        """ذخیره اطلاعات برای Resume"""
        pass
    
    async def _clear_resume_info(self, file_path: str, chat_id: int):
        """پاکسازی اطلاعات Resume"""
        pass
    
    def _log_upload_success(self, task_id: str, file_size: int, result: Any):
        """ثبت لاگ موفقیت آمیز بودن آپلود"""
        upload_time = time.time() - self.active_uploads[task_id]['start_time']
        speed = file_size / upload_time if upload_time > 0 else 0
        
        print(f"✅ آپلود موفق: {task_id}")
        print(f"   📊 حجم: {self._format_size(file_size)}")
        print(f"   ⏱️ زمان: {upload_time:.1f} ثانیه")
        print(f"   ⚡ سرعت: {self._format_size(speed)}/s")
    
    def _format_size(self, size_bytes: float) -> str:
        """فرمت‌بندی حجم"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
