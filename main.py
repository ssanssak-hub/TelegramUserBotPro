# main.py
import asyncio
import logging
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config.settings import settings
from database.models import DatabaseManager
from modules.auth.login_handler import LoginHandler
from modules.downloader.smart_downloader import SmartDownloader
from modules.ui.progress_display import ProgressDisplay
from modules.core.security import AdvancedSecurity

# تنظیمات لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOGS_DIR / 'bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TelegramUserBot:
    """کلاس اصلی ربات"""
    
    def __init__(self):
        self.settings = settings
        self.db = DatabaseManager()
        self.security = AdvancedSecurity()
        self.login_handler = LoginHandler(self.db, self.security)
        self.downloader = SmartDownloader()
        self.bot = None
        self.start_time = datetime.now()
        
    async def initialize(self):
        """مقداردهی اولیه"""
        logger.info("📦 در حال مقداردهی ربات...")
        
        # ایجاد دیتابیس
        self.db.init_db()
        
        # ایجاد ربات
        self.bot = Client(
            "userbot_manager",
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            bot_token=settings.BOT_TOKEN
        )
        
        # ثبت هندلرها
        self._register_handlers()
        
        logger.info("✅ مقداردهی کامل شد")
    
    def _register_handlers(self):
        """ثبت هندلرهای ربات"""
        
        @self.bot.on_message(filters.command("start") & filters.private)
        async def start_command(client, message: Message):
            """دستور شروع"""
            user_id = message.from_user.id
            
            welcome_text = f"""
🎊 **به ربات UserBot حرفه‌ای خوش آمدید!**

🆔 **شناسه شما:** `{user_id}`
📅 **تاریخ:** {datetime.now().strftime('%Y/%m/%d %H:%M')}

📋 **قابلیت‌های اصلی:**
• 🔐 مدیریت چند حساب کاربری
• 📥 دانلود فوق‌سریع از تلگرام
• 📤 آپلود فایل با سرعت بالا
• 📊 نمایش پیشرفت گرافیکی
• ⚙️ پنل مدیریت پیشرفته

💡 **برای شروع:**
1. ابتدا با حساب تلگرام خود وارد شوید
2. از منو یا دستورات استفاده کنید

⚠️ **توجه:** این ربات کاملاً ایمن است و کد آن قابل بررسی می‌باشد.
            """
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔐 ورود به حساب", callback_data="start_login")],
                [InlineKeyboardButton("📖 راهنمای کامل", callback_data="show_guide")],
                [InlineKeyboardButton("🔒 امنیت و حریم خصوصی", callback_data="show_privacy")]
            ])
            
            await message.reply_text(welcome_text, reply_markup=keyboard)
        
        @self.bot.on_message(filters.command("login") & filters.private)
        async def login_command(client, message: Message):
            """دستور ورود"""
            await self.login_handler.start_login_process(
                message.from_user.id, 
                message
            )
        
        @self.bot.on_message(filters.command("download") & filters.private)
        async def download_command(client, message: Message):
            """دستور دانلود"""
            user_id = message.from_user.id
            
            # بررسی لاگین بودن کاربر
            if not await self._check_user_login(user_id):
                await message.reply_text(
                    "⚠️ لطفاً ابتدا وارد حساب کاربری خود شوید.\n"
                    "از دستور /login استفاده کنید."
                )
                return
            
            # دریافت لینک
            args = message.text.split(" ", 1)
            if len(args) < 2:
                await message.reply_text("""
📥 **فرمت دستور دانلود:**

`/download [لینک]`

🔗 **مثال:**
• `/download https://example.com/file.zip`
• `/download https://t.me/channel/123`

💡 **نکته:** همچنین می‌توانید پیام حاوی فایل را فوروارد کنید.
                """)
                return
            
            url = args[1].strip()
            
            # نمایش پیام شروع
            status_msg = await message.reply_text("⏳ در حال بررسی لینک...")
            
            # تابع callback برای نمایش پیشرفت
            async def progress_callback(progress_data):
                try:
                    progress_text = ProgressDisplay.create_progress_message(progress_data)
                    await status_msg.edit_text(progress_text)
                except:
                    pass
            
            # شروع دانلود
            result = await self.downloader.download_from_url(
                url, user_id, progress_callback
            )
            
            if result['success']:
                await status_msg.edit_text(f"""
✅ **دانلود کامل شد!**

📁 **فایل:** `{result['file_name']}`
📊 **حجم:** {ProgressDisplay.format_size(result['file_size'])}
🎯 **نوع:** {result.get('download_type', 'ناشناخته')}

📍 **مسیر:** `{result['file_path']}`

📤 **برای آپلود فایل از دستور زیر استفاده کنید:**
`/upload {result['file_path']}`
                """)
                
                # آپلود خودکار
                await self._auto_upload_file(
                    message.chat.id, 
                    result['file_path'],
                    status_msg
                )
            else:
                await status_msg.edit_text(f"""
❌ **خطا در دانلود**

📛 **خطا:** {result.get('error', 'خطای نامشخص')}
🆔 **کد کار:** {result.get('task_id', 'نامشخص')}

💡 **راه‌حل:**
• لینک را بررسی کنید
• اتصال اینترنت خود را چک کنید
• دوباره تلاش کنید
                """)
        
        @self.bot.on_message(filters.command("menu") & filters.private)
        async def menu_command(client, message: Message):
            """نمایش منوی اصلی"""
            user_id = message.from_user.id
            is_admin = user_id in settings.ADMIN_IDS
            
            menu_text = """
📋 **منوی اصلی ربات**

📥 **دانلود:**
• لینک مستقیم
• فایل‌های تلگرام
• کانال‌های خصوصی

👤 **حساب کاربری:**
• مشاهده حساب‌های متصل
• افزودن حساب جدید
• حذف حساب
• تنظیمات حریم خصوصی

⚙️ **تنظیمات:**
• محدودیت سرعت
• کیفیت دانلود
• مسیر ذخیره‌سازی

📊 **آمار:**
• استفاده ماهانه
• حجم دانلود/آپلود
• حساب‌های فعال
            """
            
            buttons = []
            
            # دکمه‌های عمومی
            buttons.append([
                InlineKeyboardButton("📥 دانلود جدید", callback_data="new_download"),
                InlineKeyboardButton("👤 حساب‌های من", callback_data="my_accounts")
            ])
            
            buttons.append([
                InlineKeyboardButton("📊 آمار استفاده", callback_data="usage_stats"),
                InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings")
            ])
            
            # دکمه‌های ادمین
            if is_admin:
                buttons.append([
                    InlineKeyboardButton("🛠️ پنل ادمین", callback_data="admin_panel"),
                    InlineKeyboardButton("📈 آمار سیستم", callback_data="system_stats")
                ])
            
            buttons.append([
                InlineKeyboardButton("📖 راهنما", callback_data="help"),
                InlineKeyboardButton("🔄 وضعیت ربات", callback_data="bot_status")
            ])
            
            keyboard = InlineKeyboardMarkup(buttons)
            await message.reply_text(menu_text, reply_markup=keyboard)
        
        @self.bot.on_message(filters.private & filters.text)
        async def handle_text_messages(client, message: Message):
            """مدیریت پیام‌های متنی"""
            user_id = message.from_user.id
            
            # بررسی حالت‌های ورود
            if user_id in self.login_handler.login_states:
                login_data = self.login_handler.login_states[user_id]
                
                if login_data['step'] == 'awaiting_phone':
                    await self.login_handler.handle_phone_number(user_id, message)
                elif login_data['step'] == 'awaiting_code':
                    await self.login_handler.handle_verification_code(user_id, message)
                elif login_data['step'] == 'awaiting_password':
                    await self.login_handler.handle_two_factor_password(user_id, message)
                return
            
            # اگر شماره تلفن وارد شده
            if message.text.startswith('+') and len(message.text) > 5:
                await self.login_handler.handle_phone_number(user_id, message)
                return
    
    async def _check_user_login(self, user_id: int) -> bool:
        """بررسی لاگین بودن کاربر"""
        # بررسی در دیتابیس
        with self.db.get_session() as session:
            user = session.query(User).filter_by(user_id=user_id).first()
            return user is not None and user.is_active
    
    async def _auto_upload_file(self, chat_id: int, file_path: str, 
                               original_message: Message):
        """آپلود خودکار فایل دانلود شده"""
        try:
            # این بخش نیاز به پیاده‌سازی آپلودر دارد
            # فعلاً یک پیام نمایش می‌دهیم
            await original_message.reply_text("""
📤 **آپلود خودکار فعال است!**

فایل دانلود شده آماده آپلود است.
این قابلیت در نسخه کامل پیاده‌سازی خواهد شد.

💡 **برای آپلود دستی:**
فایل را به چت فوروارد کنید یا از ربات آپلودر استفاده نمایید.
            """)
        except Exception as e:
            logger.error(f"خطا در آپلود خودکار: {e}")
    
    async def run(self):
        """اجرای ربات"""
        await self.initialize()
        
        logger.info("🚀 شروع ربات UserBot...")
        await self.bot.start()
        
        # نمایش اطلاعات شروع
        me = await self.bot.get_me()
        logger.info(f"🤖 ربات با موفقیت شروع شد: @{me.username}")
        logger.info(f"🆔 شناسه ربات: {me.id}")
        logger.info(f"👑 ادمین‌ها: {settings.ADMIN_IDS}")
        
        # نگه داشتن ربات فعال
        await asyncio.Event().wait()

async def main():
    """تابع اصلی"""
    bot = TelegramUserBot()
    
    try:
        await bot.run()
    except KeyboardInterrupt:
        logger.info("🛑 ربات متوقف شد")
    except Exception as e:
        logger.error(f"❌ خطای غیرمنتظره: {e}")
    finally:
        if bot.bot:
            await bot.bot.stop()

if __name__ == "__main__":
    # اجرای ربات
    asyncio.run(main())
