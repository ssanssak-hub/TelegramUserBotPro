# modules/auth/login_handler.py
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid
import asyncio
import re
from datetime import datetime
from typing import Optional, Dict, Any
import json

class LoginHandler:
    """مدیریت ورود کاربران"""
    
    def __init__(self, db_manager, security_manager):
        self.db = db_manager
        self.security = security_manager
        self.login_states = {}  # user_id -> login_data
        
    async def start_login_process(self, user_id: int, message: Message) -> bool:
        """شروع فرآیند ورود"""
        
        welcome_text = """
🔐 **ورود به حساب کاربری**

برای استفاده از ربات، نیاز به دسترسی به حساب تلگرام شما داریم.

✅ **دسترسی‌های مورد نیاز:**
• خواندن پیام‌ها و مدیا
• دسترسی به فایل‌ها
• مشاهده گروه‌ها و کانال‌ها

⚠️ **تضمین امنیت:**
• اطلاعات شما رمزنگاری می‌شود
• کد منبع قابل بررسی است
• امکان خروج در هر زمان

📱 لطفاً شماره تلفن خود را با فرمت بین‌المللی ارسال کنید:
مثال: `+989123456789`
        """
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📖 جزئیات دسترسی‌ها", callback_data="auth_permissions_detail")],
            [InlineKeyboardButton("🔒 حریم خصوصی", callback_data="auth_privacy_detail")],
            [InlineKeyboardButton("❌ لغو", callback_data="auth_cancel")]
        ])
        
        await message.reply_text(welcome_text, reply_markup=keyboard)
        
        # ذخیره حالت کاربر
        self.login_states[user_id] = {
            'step': 'awaiting_phone',
            'created_at': datetime.now()
        }
        
        return True
    
    async def handle_phone_number(self, user_id: int, message: Message) -> bool:
        """دریافت و اعتبارسنجی شماره تلفن"""
        
        phone_number = message.text.strip()
        
        # اعتبارسنجی شماره تلفن
        if not self._validate_phone_number(phone_number):
            await message.reply_text("""
❌ شماره تفرن نامعتبر است!

لطفاً شماره را با فرمت بین‌المللی وارد کنید:
• `+989123456789` (ایران)
• `+12345678901` (سایر کشورها)

⚠️ شماره باید با + شروع شود.
            """)
            return False
        
        # ایجاد کلاینت موقت
        try:
            client = Client(
                f"user_{user_id}_temp",
                api_id=settings.API_ID,
                api_hash=settings.API_HASH,
                device_model="UserBot Premium",
                system_version="Android 10",
                app_version="8.7.3",
                lang_code="fa"
            )
            
            await client.connect()
            
            # ارسال کد
            sent_code = await client.send_code(phone_number)
            
            # ذخیره اطلاعات
            self.login_states[user_id] = {
                'step': 'awaiting_code',
                'phone_number': phone_number,
                'phone_code_hash': sent_code.phone_code_hash,
                'client': client,
                'created_at': datetime.now()
            }
            
            await message.reply_text("""
✅ کد تأیید ارسال شد!

🔢 لطفاً کد ۵ رقمی ارسال شده به تلگرام را وارد کنید:

📝 **نحوه ارسال:**
• به صورت عدد ساده: `12345`
• یا با اسلش: `/code 12345`

⏱️ کد تا ۲ دقیقه معتبر است.
            """)
            
            return True
            
        except Exception as e:
            await message.reply_text(f"❌ خطا در ارسال کد: {str(e)}")
            return False
    
    async def handle_verification_code(self, user_id: int, message: Message) -> bool:
        """دریافت و بررسی کد تأیید"""
        
        if user_id not in self.login_states:
            await message.reply_text("❌ فرآیند ورود منقضی شده است. لطفاً مجدداً تلاش کنید.")
            return False
        
        code = message.text.strip()
        
        # حذف /code اگر وجود دارد
        if code.startswith('/code '):
            code = code[6:]
        
        # اعتبارسنجی کد
        if not re.match(r'^\d{5}$', code):
            await message.reply_text("❌ کد نامعتبر است! لطفاً کد ۵ رقمی را وارد کنید.")
            return False
        
        login_data = self.login_states[user_id]
        client = login_data['client']
        
        try:
            # ورود با کد
            await client.sign_in(
                phone_number=login_data['phone_number'],
                phone_code_hash=login_data['phone_code_hash'],
                phone_code=code
            )
            
            # اگر نیاز به رمز عبور دو مرحله‌ای باشد
            if await client.is_user_authorized():
                # دریافت اطلاعات کاربر
                me = await client.get_me()
                
                # دریافت session string
                session_string = await client.export_session_string()
                
                # رمزنگاری session
                encrypted_session = self.security.encrypt_session(
                    session_string, 
                    user_id
                )
                
                # ذخیره در دیتابیس
                await self._save_user_session(
                    user_id=user_id,
                    telegram_user=me,
                    phone_number=login_data['phone_number'],
                    session_data=encrypted_session
                )
                
                # قطع اتصال
                await client.disconnect()
                
                # حذف حالت
                del self.login_states[user_id]
                
                # ارسال پیام موفقیت
                await self._send_login_success(message, me)
                
                return True
                
        except SessionPasswordNeeded:
            # نیاز به رمز عبور دو مرحله‌ای
            login_data['step'] = 'awaiting_password'
            await message.reply_text("""
🔐 **رمز عبور دو مرحله‌ای نیاز است**

لطفاً رمز عبور دو مرحله‌ای حساب خود را وارد کنید.

⚠️ **توجه:** این رمز همان رمزی است که هنگام فعال‌سازی 2FA تنظیم کردید.
            """)
            return False
            
        except PhoneCodeInvalid:
            await message.reply_text("❌ کد تأیید نامعتبر یا منقضی شده است.")
            return False
            
        except Exception as e:
            await message.reply_text(f"❌ خطا در ورود: {str(e)}")
            return False
    
    async def handle_two_factor_password(self, user_id: int, message: Message) -> bool:
        """دریافت رمز عبور دو مرحله‌ای"""
        
        if user_id not in self.login_states:
            return False
        
        password = message.text.strip()
        login_data = self.login_states[user_id]
        client = login_data['client']
        
        try:
            # ورود با رمز عبور
            await client.check_password(password)
            
            # دریافت اطلاعات
            me = await client.get_me()
            session_string = await client.export_session_string()
            
            # رمزنگاری و ذخیره
            encrypted_session = self.security.encrypt_session(session_string, user_id)
            
            await self._save_user_session(
                user_id=user_id,
                telegram_user=me,
                phone_number=login_data['phone_number'],
                session_data=encrypted_session
            )
            
            await client.disconnect()
            del self.login_states[user_id]
            
            await self._send_login_success(message, me)
            
            return True
            
        except Exception as e:
            await message.reply_text(f"❌ رمز عبور اشتباه است: {str(e)}")
            return False
    
    async def _save_user_session(self, user_id: int, telegram_user, 
                                phone_number: str, session_data: dict):
        """ذخیره نشست کاربر در دیتابیس"""
        
        with self.db.get_session() as session:
            # بررسی وجود کاربر
            user = session.query(User).filter_by(user_id=user_id).first()
            
            if not user:
                user = User(
                    user_id=user_id,
                    username=telegram_user.username,
                    first_name=telegram_user.first_name,
                    last_name=telegram_user.last_name,
                    phone_number=phone_number,
                    session_string=json.dumps(session_data),
                    last_login=datetime.now(),
                    is_active=True
                )
                session.add(user)
            else:
                user.session_string = json.dumps(session_data)
                user.last_login = datetime.now()
                user.is_active = True
            
            session.commit()
    
    async def _send_login_success(self, message: Message, telegram_user):
        """ارسال پیام موفقیت آمیز بودن ورود"""
        
        success_text = f"""
✅ **ورود موفقیت‌آمیز!**

👤 **حساب کاربری:**
• نام: {telegram_user.first_name or ''} {telegram_user.last_name or ''}
• یوزرنیم: @{telegram_user.username or 'ندارد'}
• شناسه: `{telegram_user.id}`

🔐 **وضعیت امنیت:**
• حساب شما با موفقیت متصل شد
• اطلاعات به صورت رمزنگاری شده ذخیره شد
• امکان خروج از همه دستگاه‌ها وجود دارد

📋 **برای شروع از دستورات زیر استفاده کنید:**
• `/menu` - نمایش منوی اصلی
• `/download [لینک]` - دانلود فایل
• `/accounts` - مدیریت حساب‌ها
• `/help` - راهنمای استفاده

⚠️ **نکته:** شما می‌توانید از طریق منو از حساب خود خارج شوید.
        """
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 منوی اصلی", callback_data="main_menu")],
            [InlineKeyboardButton("📥 شروع دانلود", callback_data="start_download")],
            [InlineKeyboardButton("⚙️ تنظیمات حساب", callback_data="account_settings")]
        ])
        
        await message.reply_text(success_text, reply_markup=keyboard)
    
    def _validate_phone_number(self, phone: str) -> bool:
        """اعتبارسنجی شماره تلفن"""
        pattern = r'^\+\d{10,15}$'
        return bool(re.match(pattern, phone))
