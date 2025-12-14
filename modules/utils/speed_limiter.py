# modules/utils/speed_limiter.py
import asyncio
import time
from typing import Optional, Callable

class SpeedLimiter:
    """محدود کننده سرعت دانلود/آپلود"""
    
    def __init__(self, max_speed: Optional[int] = None):
        self.max_speed = max_speed  # بایت بر ثانیه
        self.start_time = None
        self.total_bytes = 0
        
    async def limit_speed(self, chunk_size: int) -> int:
        """محدود کردن سرعت"""
        if not self.max_speed:
            return chunk_size
        
        if self.start_time is None:
            self.start_time = time.time()
        
        elapsed = time.time() - self.start_time
        expected_bytes = self.max_speed * elapsed
        
        if self.total_bytes + chunk_size > expected_bytes:
            # محاسبه زمان انتظار
            bytes_over = (self.total_bytes + chunk_size) - expected_bytes
            wait_time = bytes_over / self.max_speed
            
            await asyncio.sleep(wait_time)
        
        self.total_bytes += chunk_size
        return chunk_size
    
    def get_current_speed(self) -> float:
        """دریافت سرعت فعلی"""
        if self.start_time is None:
            return 0
        
        elapsed = time.time() - self.start_time
        if elapsed == 0:
            return 0
        
        return self.total_bytes / elapsed
    
    def reset(self):
        """بازنشانی"""
        self.start_time = None
        self.total_bytes = 0

class RateLimiter:
    """محدود کننده Rate برای API"""
    
    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period  # ثانیه
        self.calls = []
    
    async def acquire(self):
        """دریافت اجازه اجرا"""
        now = time.time()
        
        # حذف callهای قدیمی
        self.calls = [call for call in self.calls if now - call < self.period]
        
        if len(self.calls) >= self.max_calls:
            # محاسبه زمان انتظار
            oldest_call = self.calls[0]
            wait_time = self.period - (now - oldest_call)
            
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            
            # حذف قدیمی‌ترین
            self.calls.pop(0)
        
        self.calls.append(time.time())
    
    def get_remaining_calls(self) -> int:
        """دریافت تعداد callهای باقی‌مانده"""
        now = time.time()
        self.calls = [call for call in self.calls if now - call < self.period]
        return self.max_calls - len(self.calls)
