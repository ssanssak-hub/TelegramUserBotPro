# database/crud.py
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from .models import User, DownloadTask, SystemLog

class CRUDOperations:
    """عملیات CRUD برای دیتابیس"""
    
    @staticmethod
    async def create_user(session: Session, user_data: Dict[str, Any]) -> User:
        """ایجاد کاربر جدید"""
        user = User(**user_data)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    
    @staticmethod
    async def get_user_by_id(session: Session, user_id: int) -> Optional[User]:
        """دریافت کاربر با شناسه"""
        return session.query(User).filter(User.user_id == user_id).first()
    
    @staticmethod
    async def update_user(session: Session, user_id: int, 
                         update_data: Dict[str, Any]) -> Optional[User]:
        """به‌روزرسانی کاربر"""
        user = session.query(User).filter(User.user_id == user_id).first()
        if user:
            for key, value in update_data.items():
                setattr(user, key, value)
            user.last_activity = datetime.utcnow()
            session.commit()
            session.refresh(user)
        return user
    
    @staticmethod
    async def create_download_task(session: Session, task_data: Dict[str, Any]) -> DownloadTask:
        """ایجاد کار دانلود جدید"""
        task = DownloadTask(**task_data)
        session.add(task)
        session.commit()
        session.refresh(task)
        return task
    
    @staticmethod
    async def get_active_downloads(session: Session, user_id: int) -> List[DownloadTask]:
        """دریافت دانلودهای فعال کاربر"""
        return session.query(DownloadTask).filter(
            DownloadTask.user_id == user_id,
            DownloadTask.status.in_(['pending', 'downloading'])
        ).order_by(DownloadTask.created_at.desc()).all()
    
    @staticmethod
    async def log_system_event(session: Session, log_data: Dict[str, Any]):
        """ثبت رویداد سیستم"""
        log = SystemLog(**log_data)
        session.add(log)
        session.commit()
    
    @staticmethod
    async def get_daily_stats(session: Session) -> Dict[str, Any]:
        """دریافت آمار روزانه"""
        today = datetime.utcnow().date()
        
        total_users = session.query(User).count()
        new_users_today = session.query(User).filter(
            User.created_at >= today
        ).count()
        
        total_downloads = session.query(DownloadTask).count()
        downloads_today = session.query(DownloadTask).filter(
            DownloadTask.created_at >= today
        ).count()
        
        total_size_today = session.query(
            func.sum(DownloadTask.file_size)
        ).filter(
            DownloadTask.created_at >= today
        ).scalar() or 0
        
        return {
            'total_users': total_users,
            'new_users_today': new_users_today,
            'total_downloads': total_downloads,
            'downloads_today': downloads_today,
            'total_size_today': total_size_today
        }
