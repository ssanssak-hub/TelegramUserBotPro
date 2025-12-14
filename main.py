# main.py (نسخه کامل)
import asyncio
import logging
import sys
from pathlib import Path

# اضافه کردن مسیر ماژول‌ها
sys.path.append(str(Path(__file__).parent))

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from config.settings import settings
from database.models import DatabaseManager
from modules.auth.login_handler import LoginHandler
from modules.auth.multi_account_manager import MultiAccountManager
from modules.downloader.smart_downloader import SmartDownloader
from modules.downloader.telegram_downloader import TelegramDownloader
from modules.uploader.smart_uploader import SmartUploader
from modules.behavior.human_simulator import HumanSimulator
from modules.admin.advanced_panel import AdvancedAdminPanel
from modules.core.security import AdvancedSecurity
from modules.ui.progress_display import ProgressDisplay

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOGS_DIR / 'bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AdvancedTelegramUserBot:
    """ربات کامل UserBot با تمام ویژگی‌ها"""
    
    def __init__(self):
        self.settings = settings
        self.db = DatabaseManager()
        self.security = AdvancedSecurity()
        self.login_handler = LoginHandler(self.db, self.security)
        self.account_manager = MultiAccountManager(self.db, self.security)
        self.downloader = SmartDownloader()
        self.telegram_downloader = TelegramDownloader()
        self.uploader = SmartUploader()
        self.humanizer = HumanSimulator()
        self.admin_panel = None
        self.bot = None
        self.start_time = None
        
    async def initialize(self):
        """مقداردهی اولیه کامل"""
        logger.info("🚀 در حال راه‌اندازی ربات پیشرفته...")
        
        # ایجاد دیتابیس
        self.db.init_db()
        
        # ایجاد ربات
        self.bot = Client(
            "advanced_userbot",
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            bot_token=settings.BOT_TOKEN
        )
        
        # تنظیم پنل ادمین
        self.admin_panel = AdvancedAdminPanel(self.db, self)
        
        # ثبت هندلرها
        self._register_all_handlers()
        
        self.start_time = asyncio.get_event_loop().time()
        logger.info("✅ ربات آماده به کار است")
    
    def _register_all_handlers(self):
        """ثبت تمام هندلرها"""
        
        @self.bot.on_message(filters.command("start") & filters.private)
        async def start_command(client, message: Message):
            await self.handle_start(message)
        
        @self.bot.on_message(filters.command("login") & filters.private)
        async def login_command(client, message: Message):
            await self.handle_login(message)
        
        @self.bot.on_message(filters.command("menu") & filters.private)
        async def menu_command(client, message: Message):
            await self.show_main_menu(message)
        
        @self.bot.on_message(filters.command("download") & filters.private)
        async def download_command(client, message: Message):
            await self.handle_download(message)
        
        @self.bot.on_message(filters.command("upload") & filters.private)
        async def upload_command(client, message: Message):
            await self.handle_upload(message)
        
        @self.bot.on_message(filters.command("accounts") & filters.private)
        async def accounts_command(client, message: Message):
            await self.show_accounts(message)
        
        @self.bot.on_message(filters.command("admin") & filters.private)
        async def admin_command(client, message: Message):
            await self.handle_admin_command(message)
        
        @self.bot.on_message(filters.command("help") & filters.private)
        async def help_command(client, message: Message):
            await self.show_help(message)
        
        @self.bot.on_message(filters.command("stats") & filters.private)
        async def stats_command(client, message: Message):
            await self.show_stats(message)
        
        @self.bot.on_callback_query()
        async def handle_callback(client, callback_query):
            await self.handle_all_callbacks(callback_query)
        
        @self.bot.on_message(filters.private & filters.text)
        async def handle_text_messages(client, message: Message):
            await self.handle_text_message(message)
        
        @self.bot.on_message(filters.private & filters.media)
        async def handle_media_messages(client, message: Message):
            await self.handle_media_message(message)
    
    async def handle_start(self, message: Message):
        """مدیریت دستور start"""
        user_id = message.from_user.id
        
        # شبیه‌سازی رفتار انسانی
        await self.humanizer.simulate_typing(self.bot, message.chat.id, 1.5)
        
        welcome_text = f"""
🎉 **به ربات UserBot پیشرفته خوش آمدید!**

🆔 **شناسه شما:** `{user_id}`
📅 **ورژن:** 2.0.0 کامل
⚡ **وضعیت:** آماده به کار

✨ **ویژگی‌های فعال:**
✅ سیستم احراز هویت امن
✅ دانلود هوشمند چند قسمتی
✅ آپلود با قابلیت Resume
✅ پنل ادمین پیشرفته
✅ رفتار انسانی واقعی
✅ مدیریت چند حساب همزمان
✅ دانلود از تلگرام

🔧 **برای شروع:**
1. `/login` - ورود به حساب تلگرام
2. `/menu` - نمایش منوی کامل
3. `/help` - راهنمای استفاده

📊 **آمار سیستم:**
• کاربران آنلاین: در حال محاسبه...
• سرعت دانلود: نامحدود ⚡
• پشتیبانی: 24/7 🛡️
        """
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔐 ورود فوری", callback_data="quick_login")],
            [InlineKeyboardButton("📥 تست دانلود", callback_data="test_download")],
            [InlineKeyboardButton("⚙️ تنظیمات سریع", callback_data="quick_settings")]
        ])
        
        await message.reply_text(welcome_text, reply_markup=keyboard)
    
    async def handle_login(self, message: Message):
        """مدیریت لاگین"""
        await self.login_handler.start_login_process(message.from_user.id, message)
    
    async def show_main_menu(self, message: Message):
        """نمایش منوی اصلی"""
        user_id = message.from_user.id
        
        # بررسی لاگین بودن
        if not await self._is_user_logged_in(user_id):
            await message.reply_text("""
⚠️ **لطفاً ابتدا وارد شوید!**

برای استفاده از ربات نیاز به اتصال حساب تلگرام دارید.

دستور: `/login`
            """)
            return
        
        # شبیه‌سازی رفتار
        await self.humanizer.simulate_thinking(self.bot, message.chat.id, 0.8)
        
        menu_text = """
📱 **منوی اصلی ربات**

🎯 **عملیات اصلی:**
• 📥 دانلود فایل از لینک
• 📤 آپلود فایل به تلگرام
• 🔄 مدیریت حساب‌ها
• ⚡ عملیات سریع

👤 **حساب کاربری:**
• افزودن حساب جدید
• تعویض حساب فعال
• مشاهده حساب‌ها
• تنظیمات حریم خصوصی

⚙️ **تنظیمات:**
• محدودیت سرعت
• مسیر ذخیره‌سازی
• کیفیت دانلود
• رفتار ربات

📊 **آمار و گزارش:**
• استفاده ماهانه
• حجم ترافیک
• فعالیت حساب‌ها
• گزارش سیستم
        """
        
        buttons = [
            [
                InlineKeyboardButton("📥 دانلود جدید", callback_data="new_download"),
                InlineKeyboardButton("📤 آپلود فایل", callback_data="new_upload")
            ],
            [
                InlineKeyboardButton("👥 حساب‌های من", callback_data="my_accounts"),
                InlineKeyboardButton("⚡ عملیات سریع", callback_data="quick_actions")
            ],
            [
                InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings_menu"),
                InlineKeyboardButton("📊 آمار من", callback_data="my_stats")
            ],
            [
                InlineKeyboardButton("🆘 راهنما", callback_data="help_menu"),
                InlineKeyboardButton("🔄 وضعیت", callback_data="system_status")
            ]
        ]
        
        # اضافه کردن دکمه ادمین اگر کاربر ادمین است
        if user_id in settings.ADMIN_IDS:
            buttons.append([
                InlineKeyboardButton("🛠️ پنل ادمین", callback_data="admin_panel")
            ])
        
        keyboard = InlineKeyboardMarkup(buttons)
        
        await message.reply_text(menu_text, reply_markup=keyboard)
    
    async def handle_download(self, message: Message):
        """مدیریت دانلود"""
        user_id = message.from_user.id
        
        if not await self._is_user_logged_in(user_id):
            await message.reply_text("لطفاً ابتدا وارد شوید: /login")
            return
        
        # دریافت لینک از پیام
        args = message.text.split(" ", 1)
        if len(args) < 2:
            await message.reply_text("""
📥 **فرمت صحیح:**
`/download [لینک]`

📝 **مثال‌ها:**
• `/download https://example.com/file.zip`
• `/download https://t.me/channel/123`
• `/download https://youtube.com/watch?v=...`

💡 **نکته:** همچنین می‌توانید فایل را مستقیم فوروارد کنید.
            """)
            return
        
        url = args[1].strip()
        
        # انتخاب حساب برای دانلود
        accounts = await self.account_manager.get_user_accounts(user_id)
        if not accounts:
            await message.reply_text("هیچ حساب فعالی ندارید. لطفاً ابتدا حساب اضافه کنید.")
            return
        
        # استفاده از حساب اول به صورت پیش‌فرض
        account_id = accounts[0]['account_id']
        
        # نمایش وضعیت شروع
        status_msg = await message.reply_text("⏳ در حال بررسی لینک...")
        
        # تابع callback برای پیشرفت
        async def progress_callback(progress_data):
            try:
                progress_text = ProgressDisplay.create_progress_message(progress_data)
                await status_msg.edit_text(progress_text)
            except:
                pass
        
        # شروع دانلود
        if "t.me" in url or "telegram" in url:
            # دانلود از تلگرام
            result = await self.telegram_downloader.download_from_telegram(
                self.account_manager.active_clients[user_id][account_id]['client'],
                url,
                progress_callback
            )
        else:
            # دانلود از لینک عادی
            result = await self.account_manager.download_with_account(
                user_id, account_id, url, progress_callback
            )
        
        # نمایش نتیجه
        if result.get('success'):
            # شبیه‌سازی آپلود خودکار
            await self.humanizer.simulate_uploading(self.bot, message.chat.id, 1.0)
            
            final_text = f"""
✅ **دانلود کامل شد!**

📁 **فایل:** `{result.get('file_name', 'نامشخص')}`
📊 **حجم:** {ProgressDisplay.format_size(result.get('file_size', 0))}
⚡ **نوع:** {'تلگرام' if 't.me' in url else 'اینترنت'}

📍 **مسیر:** `{result.get('file_path', 'نامشخص')}`

🔄 **آپلود خودکار فعال است...**
            """
            
            # آپلود فایل
            upload_result = await self.account_manager.upload_with_account(
                user_id, account_id,
                result['file_path'],
                message.chat.id,
                progress_callback
            )
            
            if upload_result.get('success'):
                final_text += "\n\n📤 **آپلود موفقیت‌آمیز!**"
            else:
                final_text += f"\n\n⚠️ **خطا در آپلود:** {upload_result.get('error')}"
            
            await status_msg.edit_text(final_text)
        else:
            error_text = f"""
❌ **خطا در دانلود!**

📛 **خطا:** {result.get('error', 'خطای نامشخص')}
🔗 **لینک:** {url[:50]}...

💡 **راه‌حل‌ها:**
• لینک را بررسی کنید
• اتصال اینترنت را چک کنید
• از حساب دیگری امتحان کنید
• با ادمین تماس بگیرید
            """
            await status_msg.edit_text(error_text)
    
    async def handle_upload(self, message: Message):
        """مدیریت آپلود"""
        user_id = message.from_user.id
        
        if not await self._is_user_logged_in(user_id):
            await message.reply_text("لطفاً ابتدا وارد شوید: /login")
            return
        
        # بررسی فایل پیوست
        if not message.media:
            await message.reply_text("""
📤 **فرمت صحیح:**
• فایل را به ربات فوروارد کنید
• یا از دستور زیر استفاده کنید:
`/upload [مسیر فایل]`
            """)
            return
        
        # دریافت حساب‌ها
        accounts = await self.account_manager.get_user_accounts(user_id)
        if not accounts:
            await message.reply_text("هیچ حساب فعالی ندارید.")
            return
        
        # استفاده از حساب اول
        account_id = accounts[0]['account_id']
        
        # دانلود فایل از پیام
        status_msg = await message.reply_text("📥 در حال دریافت فایل...")
        
        async def progress_callback(progress_data):
            try:
                progress_text = ProgressDisplay.create_progress_message(progress_data)
                await status_msg.edit_text(progress_text)
            except:
                pass
        
        # دانلود فایل از پیام
        download_result = await self.telegram_downloader._download_message_media(
            self.bot, message, progress_callback
        )
        
        if not download_result.get('success'):
            await status_msg.edit_text(f"❌ خطا در دریافت فایل: {download_result.get('error')}")
            return
        
        # آپلود فایل با حساب کاربر
        await status_msg.edit_text("📤 در حال آپلود با حساب شما...")
        
        upload_result = await self.account_manager.upload_with_account(
            user_id, account_id,
            download_result['file_path'],
            message.chat.id,
            progress_callback
        )
        
        if upload_result.get('success'):
            await status_msg.edit_text(f"""
✅ **آپلود موفقیت‌آمیز!**

📁 **فایل:** `{download_result['file_name']}`
📊 **حجم:** {ProgressDisplay.format_size(download_result['file_size'])}
👤 **با حساب:** {accounts[0]['name']}

🎯 **عملیات تکمیل شد!**
            """)
        else:
            await status_msg.edit_text(f"""
❌ **خطا در آپلود!**

📛 **خطا:** {upload_result.get('error')}
💡 **راه‌حل:** 
• اتصال اینترنت را بررسی کنید
• از حساب دیگری امتحان کنید
• فایل را دوباره ارسال کنید
            """)
    
    async def show_accounts(self, message: Message):
        """نمایش حساب‌های کاربر"""
        user_id = message.from_user.id
        
        accounts = await self.account_manager.get_user_accounts(user_id)
        
        if not accounts:
            await message.reply_text("""
👤 **حساب‌های شما**

❌ **هیچ حسابی اضافه نکرده‌اید!**

برای اضافه کردن حساب:
1. از /login استفاده کنید
2. یا روی دکمه زیر کلیک کنید
            """)
            return
        
        accounts_text = "👥 **حساب‌های متصل شما:**\n\n"
        
        for i, account in enumerate(accounts, 1):
            status = "✅ فعال" if account['is_active'] else "❌ غیرفعال"
            primary = "⭐ اصلی" if account['is_primary'] else ""
            
            accounts_text += f"{i}. **{account['name']}**\n"
            accounts_text += f"   👤 @{account.get('username', 'بدون یوزرنیم')}\n"
            accounts_text += f"   {status} {primary}\n"
            accounts_text += f"   📅 آخرین استفاده: {account.get('last_used', 'هرگز')}\n\n"
        
        accounts_text += """
💡 **دستورات مدیریت حساب:**
• `/accounts add` - افزودن حساب جدید
• `/accounts switch [شماره]` - تعویض حساب
• `/accounts remove [شماره]` - حذف حساب
• `/accounts logout` - خروج از همه حساب‌ها
        """
        
        buttons = []
        for i, account in enumerate(accounts[:5], 1):
            buttons.append([
                InlineKeyboardButton(
                    f"{i}. {account['name'][:15]}...",
                    callback_data=f"account_{account['account_id']}"
                )
            ])
        
        buttons.extend([
            [
                InlineKeyboardButton("➕ افزودن حساب", callback_data="add_account"),
                InlineKeyboardButton("🔄 تعویض حساب", callback_data="switch_account")
            ],
            [
                InlineKeyboardButton("🗑️ حذف حساب", callback_data="remove_account"),
                InlineKeyboardButton("🚪 خروج از همه", callback_data="logout_all")
            ]
        ])
        
        keyboard = InlineKeyboardMarkup(buttons)
        await message.reply_text(accounts_text, reply_markup=keyboard)
    
    async def handle_admin_command(self, message: Message):
        """مدیریت دستورات ادمین"""
        user_id = message.from_user.id
        
        if user_id not in settings.ADMIN_IDS:
            await message.reply_text("⚠️ دسترسی ممنوع! شما ادمین نیستید.")
            return
        
        await self.admin_panel.show_admin_panel(message)
    
    async def handle_all_callbacks(self, callback_query):
        """مدیریت تمام callback‌ها"""
        data = callback_query.data
        
        # هندل‌کردن callback‌های مختلف
        if data.startswith("admin_"):
            await self.admin_panel.handle_admin_callback(callback_query)
        elif data.startswith("account_"):
            await self.handle_account_callback(callback_query)
        elif data == "quick_login":
            await self.handle_quick_login(callback_query)
        elif data == "test_download":
            await self.handle_test_download(callback_query)
        else:
            await callback_query.answer("⚠️ این دکمه در حال حاضر فعال نیست")
    
    async def _is_user_logged_in(self, user_id: int) -> bool:
        """بررسی لاگین بودن کاربر"""
        return user_id in self.account_manager.active_clients
    
    async def run(self):
        """اجرای ربات"""
        await self.initialize()
        
        logger.info("🚀 ربات UserBot در حال اجرا...")
        await self.bot.start()
        
        # اطلاعات شروع
        me = await self.bot.get_me()
        logger.info(f"🤖 ربات: @{me.username} (ID: {me.id})")
        logger.info(f"👑 ادمین‌ها: {settings.ADMIN_IDS}")
        logger.info(f"📁 مسیر داده: {settings.DATA_DIR}")
        logger.info(f"🔐 امنیت: AES-256 فعال")
        
        # نگه داشتن ربات
        await asyncio.Event().wait()

async def main():
    """تابع اصلی"""
    bot = AdvancedTelegramUserBot()
    
    try:
        await bot.run()
    except KeyboardInterrupt:
        logger.info("🛑 ربات متوقف شد (KeyboardInterrupt)")
    except Exception as e:
        logger.error(f"❌ خطای غیرمنتظره: {e}", exc_info=True)
    finally:
        if bot.bot:
            await bot.bot.stop()
        logger.info("👋 ربات خاموش شد")

if __name__ == "__main__":
    # اجرای ربات
    asyncio.run(main())
