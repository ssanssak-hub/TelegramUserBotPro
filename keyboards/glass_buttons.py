#glass_buttons.py
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_permission_buttons() -> InlineKeyboardMarkup:
    """ایجاد دکمه‌های شیشه‌ای برای انتخاب دسترسی‌ها"""
    
    buttons = [
        [
            InlineKeyboardButton("👁️ مشاهده پیام‌ها", callback_data="permission_view"),
            InlineKeyboardButton("📤 ارسال پیام", callback_data="permission_send")
        ],
        [
            InlineKeyboardButton("🗑️ حذف پیام‌ها", callback_data="permission_delete"),
            InlineKeyboardButton("👥 مدیریت گروه", callback_data="permission_manage")
        ],
        [
            InlineKeyboardButton("📁 دسترسی به فایل‌ها", callback_data="permission_files"),
            InlineKeyboardButton("👤 اطلاعات حساب", callback_data="permission_account")
        ],
        [
            InlineKeyboardButton("✅ تایید همه", callback_data="permission_all"),
            InlineKeyboardButton("⚙️ انتخاب دستی", callback_data="permission_custom")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data="start"),
            InlineKeyboardButton("➡️ ادامه", callback_data="confirm_login")
        ]
    ]
    
    return InlineKeyboardMarkup(buttons)

def get_glass_style_button(text: str, callback_data: str) -> InlineKeyboardButton:
    """ایجاد دکمه با استایل شیشه‌ای"""
    return InlineKeyboardButton(f"🔮 {text}", callback_data=callback_data)
