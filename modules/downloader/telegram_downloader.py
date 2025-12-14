# modules/downloader/telegram_downloader.py
import asyncio
from typing import Dict, Any, Optional, Callable
from pyrogram.types import Message
from pyrogram.errors import ChannelPrivate, FloodWait
import re
from urllib.parse import urlparse, parse_qs

class TelegramDownloader:
    """دانلود از تلگرام با استفاده از Session کاربر"""
    
    def __init__(self):
        self.message_patterns = {
            'channel_post': r't\.me/(c/)?(\w+)/(\d+)',
            'private_channel': r't\.me/\+(\w+)',
            'group_message': r't\.me/(\w+)/(\d+)',
            'bot_file': r't\.me/(\w+)\?start=(\w+)'
        }
        
    async def download_from_telegram(self, client, url: str, 
                                    progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """دانلود از لینک تلگرام"""
        
        # شناسایی نوع لینک
        link_type, params = self._parse_telegram_link(url)
        
        if not link_type:
            return {
                'success': False,
                'error': 'لینک تلگرام نامعتبر است'
            }
        
        try:
            if link_type == 'channel_post':
                return await self._download_channel_post(
                    client, params['chat'], params['message_id'], progress_callback
                )
            elif link_type == 'private_channel':
                return await self._download_private_content(
                    client, params['invite_hash'], progress_callback
                )
            elif link_type == 'group_message':
                return await self._download_group_message(
                    client, params['chat'], params['message_id'], progress_callback
                )
            elif link_type == 'bot_file':
                return await self._download_bot_file(
                    client, params['bot'], params['file_id'], progress_callback
                )
            else:
                return {
                    'success': False,
                    'error': 'نوع لینک پشتیبانی نمی‌شود'
                }
                
        except ChannelPrivate:
            return {
                'success': False,
                'error': 'کانال خصوصی است و نیاز به عضویت دارید'
            }
        except FloodWait as e:
            return {
                'success': False,
                'error': f'محدودیت تلگرام، لطفاً {e.value} ثانیه صبر کنید'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'خطا در دانلود: {str(e)}'
            }
    
    async def _download_channel_post(self, client, chat: str, 
                                    message_id: int, 
                                    progress_callback: Optional[Callable]) -> Dict[str, Any]:
        """دانلود پست کانال"""
        
        try:
            # دریافت پیام
            message = await client.get_messages(chat, message_id)
            
            if not message or not message.media:
                return {
                    'success': False,
                    'error': 'پیام یا مدیا یافت نشد'
                }
            
            # دانلود فایل
            return await self._download_message_media(
                client, message, progress_callback
            )
            
        except Exception as e:
            return {
                'success': False,
                'error': f'خطا در دریافت پیام: {str(e)}'
            }
    
    async def _download_private_content(self, client, invite_hash: str,
                                       progress_callback: Optional[Callable]) -> Dict[str, Any]:
        """دانلود از کانال/گروه خصوصی"""
        
        try:
            # جوین شدن به چت
            chat = await client.join_chat(invite_hash)
            
            # دریافت آخرین پیام‌ها
            messages = await client.get_chat_history(chat.id, limit=10)
            
            if not messages:
                return {
                    'success': False,
                    'error': 'هیچ محتوایی در این چت یافت نشد'
                }
            
            # پیدا کردن اولین پیام با مدیا
            for message in messages:
                if message.media:
                    result = await self._download_message_media(
                        client, message, progress_callback
                    )
                    
                    # لفت دادن از چت
                    try:
                        await client.leave_chat(chat.id)
                    except:
                        pass
                    
                    return result
            
            # لفت دادن اگر مدیا پیدا نشد
            try:
                await client.leave_chat(chat.id)
            except:
                pass
            
            return {
                'success': False,
                'error': 'هیچ مدیایی در این چت یافت نشد'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'خطا در دسترسی به محتوای خصوصی: {str(e)}'
            }
    
    async def _download_group_message(self, client, chat: str, 
                                     message_id: int,
                                     progress_callback: Optional[Callable]) -> Dict[str, Any]:
        """دانلود از گروه"""
        
        try:
            # بررسی عضویت در گروه
            try:
                chat_obj = await client.get_chat(chat)
            except:
                return {
                    'success': False,
                    'error': 'نیاز به عضویت در گروه دارید'
                }
            
            # دریافت پیام
            message = await client.get_messages(chat_obj.id, message_id)
            
            if not message or not message.media:
                return {
                    'success': False,
                    'error': 'پیام یا مدیا یافت نشد'
                }
            
            # دانلود فایل
            return await self._download_message_media(
                client, message, progress_callback
            )
            
        except Exception as e:
            return {
                'success': False,
                'error': f'خطا در دانلود از گروه: {str(e)}'
            }
    
    async def _download_bot_file(self, client, bot_username: str,
                                file_id: str,
                                progress_callback: Optional[Callable]) -> Dict[str, Any]:
        """دانلود فایل از ربات"""
        
        try:
            # شروع مکالمه با ربات
            await client.send_message(bot_username, "/start")
            
            # درخواست فایل
            message = await client.send_message(bot_username, file_id)
            
            if not message or not message.media:
                return {
                    'success': False,
                    'error': 'ربات فایلی ارسال نکرد'
                }
            
            # دانلود فایل
            return await self._download_message_media(
                client, message, progress_callback
            )
            
        except Exception as e:
            return {
                'success': False,
                'error': f'خطا در دریافت فایل از ربات: {str(e)}'
            }
    
    async def _download_message_media(self, client, message: Message,
                                     progress_callback: Optional[Callable]) -> Dict[str, Any]:
        """دانلود مدیا از یک پیام"""
        
        # تعیین نام فایل
        file_name = self._get_media_filename(message)
        
        # ایجاد پوشه دانلود
        import os
        download_dir = "downloads/telegram"
        os.makedirs(download_dir, exist_ok=True)
        
        file_path = os.path.join(download_dir, file_name)
        
        # تابع callback برای پیشرفت
        async def download_progress(current, total):
            if progress_callback:
                progress_data = {
                    'progress': (current / total) * 100,
                    'downloaded': current,
                    'total': total,
                    'filename': file_name,
                    'speed': 0,  # محاسبه جداگانه نیاز دارد
                    'eta': 0     # محاسبه جداگانه نیاز دارد
                }
                await progress_callback(progress_data)
        
        # دانلود فایل
        try:
            await client.download_media(
                message,
                file_name=file_path,
                progress=download_progress
            )
            
            file_size = os.path.getsize(file_path)
            
            return {
                'success': True,
                'file_path': file_path,
                'file_name': file_name,
                'file_size': file_size,
                'message_id': message.id,
                'chat_id': message.chat.id
            }
            
        except Exception as e:
            # حذف فایل ناقص
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return {
                'success': False,
                'error': f'خطا در دانلود: {str(e)}'
            }
    
    def _parse_telegram_link(self, url: str) -> tuple:
        """تجزیه و تحلیل لینک تلگرام"""
        
        parsed = urlparse(url)
        
        # بررسی لینک‌های معمولی
        for pattern_name, pattern in self.message_patterns.items():
            match = re.match(pattern, parsed.path.lstrip('/'))
            if match:
                if pattern_name == 'channel_post':
                    return 'channel_post', {
                        'chat': match.group(2),
                        'message_id': int(match.group(3))
                    }
                elif pattern_name == 'private_channel':
                    return 'private_channel', {
                        'invite_hash': match.group(1)
                    }
                elif pattern_name == 'group_message':
                    return 'group_message', {
                        'chat': match.group(1),
                        'message_id': int(match.group(2))
                    }
        
        # بررسی لینک‌های ربات
        if parsed.netloc == 't.me' and parsed.query:
            query_params = parse_qs(parsed.query)
            if 'start' in query_params:
                return 'bot_file', {
                    'bot': parsed.path.lstrip('/'),
                    'file_id': query_params['start'][0]
                }
        
        return None, None
    
    def _get_media_filename(self, message: Message) -> str:
        """تعیین نام فایل برای مدیا"""
        
        import time
        
        if message.document:
            return message.document.file_name or f"document_{message.id}.bin"
        elif message.video:
            return message.video.file_name or f"video_{message.id}.mp4"
        elif message.audio:
            return message.audio.file_name or f"audio_{message.id}.mp3"
        elif message.photo:
            return f"photo_{message.id}.jpg"
        elif message.voice:
            return f"voice_{message.id}.ogg"
        elif message.sticker:
            return f"sticker_{message.id}.webp"
        else:
            return f"file_{int(time.time())}.bin"
    
    async def download_forwarded_content(self, client, chat_id: int,
                                        from_chat_id: int, message_id: int,
                                        progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """دانلود محتوای فوروارد شده"""
        
        try:
            # دریافت پیام فوروارد شده
            message = await client.get_messages(from_chat_id, message_id)
            
            if not message:
                return {
                    'success': False,
                    'error': 'پیام یافت نشد'
                }
            
            # فوروارد به خود
            forwarded = await client.forward_messages(chat_id, from_chat_id, message_id)
            
            # دانلود مدیا
            if forwarded.media:
                return await self._download_message_media(
                    client, forwarded, progress_callback
                )
            else:
                return {
                    'success': False,
                    'error': 'پیام فوروارد شده مدیا ندارد'
                }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'خطا در دانلود محتوای فوروارد شده: {str(e)}'
            }
