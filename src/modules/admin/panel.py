# src/modules/admin/panel.py
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import json

class AdminPanel:
    """پنل مدیریت پیشرفته برای ادمین اصلی"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        
    async def get_main_admin_menu(self, admin_id: int) -> InlineKeyboardMarkup:
        """منوی اصلی ادمین"""
        
        # دریافت آمار
        stats = await self.db.get_system_stats()
        
        buttons = [
            [InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_users")],
            [InlineKeyboardButton("📊 آمار سیستم", callback_data="admin_stats")],
            [InlineKeyboardButton("⚙️ تنظیمات ربات", callback_data="admin_settings")],
            [InlineKeyboardButton("🔒 امنیت و لاگ", callback_data="admin_security")],
            [InlineKeyboardButton("🚀 بهینه‌سازی", callback_data="admin_optimize")],
            [InlineKeyboardButton("📦 Backup/Restore", callback_data="admin_backup")],
            [
                InlineKeyboardButton("📈 گزارش روزانه", callback_data="admin_daily_report"),
                InlineKeyboardButton("⚠️ هشدارها", callback_data="admin_alerts")
            ]
        ]
        
        return InlineKeyboardMarkup(buttons)
    
    async def get_system_stats_message(self) -> str:
        """پیام آمار سیستم"""
        
        stats = await self.db.get_system_stats()
        
        message = f"""
🏢 **پنل مدیریت - آمار سیستم**

👥 **کاربران:**
• کل کاربران: {stats['total_users']}
• کاربران فعال: {stats['active_users']}
• کاربران امروز: {stats['today_users']}

📊 **استفاده:**
• کل دانلود: {self._format_size(stats['total_download'])}
• کل آپلود: {self._format_size(stats['total_upload'])}
• میانگین سرعت: {stats['avg_speed']} MB/s

⚙️ **سیستم:**
• Uptime: {stats['uptime']}
• حافظه استفاده شده: {stats['memory_usage']}%
• CPU استفاده شده: {stats['cpu_usage']}%

🚨 **وضعیت:**
• خطاهای امروز: {stats['today_errors']}
• اتصالات فعال: {stats['active_connections']}
• وضعیت: {'✅ عالی' if stats['health_score'] > 80 else '⚠️ نیاز به توجه'}
        """
        
        return message
