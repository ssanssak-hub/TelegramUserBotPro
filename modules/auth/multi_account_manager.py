# modules/auth/multi_account_manager.py
import asyncio
from typing import Dict, List, Optional, Any
from pyrogram import Client
import json
from datetime import datetime
import hashlib

class MultiAccountManager:
    """مدیریت چند حساب کاربری همزمان"""
    
    def __init__(self, db_manager, security_manager):
        self.db = db_manager
        self.security = security_manager
        self.active_clients: Dict[int, Dict[str, Any]] = {}  # user_id -> {account_id: client}
        self.account_sessions = {}
        
    async def add_account(self, user_id: int, session_data: dict, 
                         account_name: Optional[str] = None) -> Dict[str, Any]:
        """افزودن حساب جدید"""
        
        try:
            # رمزگشایی session
            session_string = self.security.decrypt_session(session_data)
            
            # تولید شناسه حساب
            account_id = self._generate_account_id(user_id, session_string)
            
            # ایجاد کلاینت
            client = Client(
                f"user_{user_id}_account_{account_id[:8]}",
                session_string=session_string,
                api_id=settings.API_ID,
                api_hash=settings.API_HASH
            )
            
            await client.connect()
            
            # بررسی اعتبار session
            if not await client.is_user_authorized():
                await client.disconnect()
                return {
                    'success': False,
                    'error': 'Session نامعتبر است'
                }
            
            # دریافت اطلاعات حساب
            me = await client.get_me()
            
            # ذخیره حساب در دیتابیس
            account_info = {
                'account_id': account_id,
                'user_id': user_id,
                'telegram_id': me.id,
                'username': me.username,
                'first_name': me.first_name,
                'last_name': me.last_name,
                'phone_number': None,  # در صورت نیاز از دیتابیس بخوانید
                'session_data': session_data,
                'account_name': account_name or f"اکانت {me.id}",
                'is_active': True,
                'is_primary': False,
                'added_at': datetime.now(),
                'last_used': datetime.now()
            }
            
            await self._save_account_to_db(account_info)
            
            # ذخیره در حافظه
            if user_id not in self.active_clients:
                self.active_clients[user_id] = {}
            
            self.active_clients[user_id][account_id] = {
                'client': client,
                'info': account_info,
                'stats': {
                    'downloads': 0,
                    'uploads': 0,
                    'last_activity': datetime.now()
                }
            }
            
            return {
                'success': True,
                'account_id': account_id,
                'account_info': {
                    'name': account_info['account_name'],
                    'username': me.username,
                    'user_id': me.id,
                    'is_primary': account_info['is_primary']
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def switch_account(self, user_id: int, account_id: str) -> bool:
        """تعویض حساب فعال"""
        
        if user_id not in self.active_clients:
            return False
        
        if account_id not in self.active_clients[user_id]:
            return False
        
        # علامت‌گذاری حساب به عنوان فعال
        for acc_id in self.active_clients[user_id]:
            self.active_clients[user_id][acc_id]['info']['is_active'] = (acc_id == account_id)
        
        return True
    
    async def get_user_accounts(self, user_id: int) -> List[Dict[str, Any]]:
        """دریافت لیست حساب‌های کاربر"""
        
        accounts = []
        
        # از دیتابیس بخوان
        with self.db.get_session() as session:
            from database.models import UserAccount  # نیاز به مدل جدید داریم
            
            # این بخش نیاز به مدل UserAccount دارد
            # فعلاً از active_clients برمی‌گردانیم
        
        # از حافظه برگردان
        if user_id in self.active_clients:
            for account_id, account_data in self.active_clients[user_id].items():
                accounts.append({
                    'account_id': account_id,
                    'name': account_data['info']['account_name'],
                    'username': account_data['info']['username'],
                    'is_active': account_data['info']['is_active'],
                    'is_primary': account_data['info']['is_primary'],
                    'last_used': account_data['info']['last_used']
                })
        
        return accounts
    
    async def download_with_account(self, user_id: int, account_id: str,
                                   url: str, progress_callback=None) -> Dict[str, Any]:
        """دانلود با حساب مشخص"""
        
        if user_id not in self.active_clients:
            return {'success': False, 'error': 'کاربر لاگین نکرده است'}
        
        if account_id not in self.active_clients[user_id]:
            return {'success': False, 'error': 'حساب یافت نشد'}
        
        account_data = self.active_clients[user_id][account_id]
        client = account_data['client']
        
        # شبیه‌سازی رفتار انسانی
        humanizer = HumanSimulator()
        await humanizer.simulate_human_interaction(
            client, user_id, 'process_request'
        )
        
        # دانلود فایل
        from modules.downloader.smart_downloader import SmartDownloader
        downloader = SmartDownloader()
        
        result = await downloader.download_from_url(
            url, user_id, progress_callback
        )
        
        if result['success']:
            # به‌روزرسانی آمار حساب
            account_data['stats']['downloads'] += 1
            account_data['stats']['last_activity'] = datetime.now()
        
        return result
    
    async def upload_with_account(self, user_id: int, account_id: str,
                                 file_path: str, chat_id: int,
                                 progress_callback=None) -> Dict[str, Any]:
        """آپلود با حساب مشخص"""
        
        if user_id not in self.active_clients:
            return {'success': False, 'error': 'کاربر لاگین نکرده است'}
        
        if account_id not in self.active_clients[user_id]:
            return {'success': False, 'error': 'حساب یافت نشد'}
        
        account_data = self.active_clients[user_id][account_id]
        client = account_data['client']
        
        from modules.uploader.smart_uploader import SmartUploader
        uploader = SmartUploader()
        
        result = await uploader.upload_file(
            client, file_path, chat_id, progress_callback
        )
        
        if result['success']:
            # به‌روزرسانی آمار حساب
            account_data['stats']['uploads'] += 1
            account_data['stats']['last_activity'] = datetime.now()
        
        return result
    
    async def remove_account(self, user_id: int, account_id: str) -> bool:
        """حذف حساب"""
        
        if user_id not in self.active_clients:
            return False
        
        if account_id not in self.active_clients[user_id]:
            return False
        
        try:
            # قطع اتصال
            client = self.active_clients[user_id][account_id]['client']
            await client.disconnect()
            
            # حذف از حافظه
            del self.active_clients[user_id][account_id]
            
            # حذف از دیتابیس
            await self._remove_account_from_db(user_id, account_id)
            
            return True
            
        except Exception:
            return False
    
    async def logout_all_accounts(self, user_id: int) -> bool:
        """خروج از همه حساب‌ها"""
        
        if user_id not in self.active_clients:
            return False
        
        try:
            for account_id in list(self.active_clients[user_id].keys()):
                await self.remove_account(user_id, account_id)
            
            del self.active_clients[user_id]
            return True
            
        except Exception:
            return False
    
    def _generate_account_id(self, user_id: int, session_string: str) -> str:
        """تولید شناسه منحصر به فرد برای حساب"""
        unique_string = f"{user_id}_{session_string}_{datetime.now().timestamp()}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:16]
    
    async def _save_account_to_db(self, account_info: Dict[str, Any]):
        """ذخیره حساب در دیتابیس"""
        # پیاده‌سازی ذخیره در دیتابیس
        pass
    
    async def _remove_account_from_db(self, user_id: int, account_id: str):
        """حذف حساب از دیتابیس"""
        pass
