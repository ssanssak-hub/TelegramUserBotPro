# src/modules/downloader/advanced_downloader.py
import asyncio
import aiohttp
import aiofiles
from typing import List, Dict
import math
from concurrent.futures import ThreadPoolExecutor

class MultiPartDownloader:
    """دانلود چند بخشی برای افزایش سرعت"""
    
    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers
        self.chunk_size = 1024 * 1024 * 2  # 2MB chunks
        
    async def download_file(self, url: str, file_path: str, 
                           progress_callback=None) -> Dict:
        """دانلود فایل با تقسیم به بخش‌های موازی"""
        
        async with aiohttp.ClientSession() as session:
            # دریافت اطلاعات فایل
            async with session.head(url) as response:
                total_size = int(response.headers.get('content-length', 0))
                
                if total_size == 0:
                    # اگر سایز مشخص نبود، دانلود عادی
                    return await self._simple_download(session, url, file_path, progress_callback)
                
                # محاسبه تعداد بخش‌ها
                num_parts = min(self.max_workers, math.ceil(total_size / self.chunk_size))
                chunk_size = math.ceil(total_size / num_parts)
                
                # ایجاد لیست وظایف
                tasks = []
                for i in range(num_parts):
                    start = i * chunk_size
                    end = start + chunk_size - 1 if i < num_parts - 1 else total_size - 1
                    
                    task = self._download_chunk(
                        session, url, file_path, start, end, i, 
                        progress_callback, total_size
                    )
                    tasks.append(task)
                
                # اجرای موازی
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # ترکیب بخش‌ها
                await self._merge_chunks(file_path, num_parts)
                
                return {
                    'success': True,
                    'file_path': file_path,
                    'total_size': total_size,
                    'num_parts': num_parts,
                    'chunk_size': chunk_size
                }
    
    async def _download_chunk(self, session, url, file_path, 
                             start, end, part_num, progress_callback, total_size):
        """دانلود یک بخش از فایل"""
        
        chunk_path = f"{file_path}.part{part_num}"
        headers = {'Range': f'bytes={start}-{end}'}
        
        async with session.get(url, headers=headers) as response:
            async with aiofiles.open(chunk_path, 'wb') as f:
                downloaded = 0
                async for chunk in response.content.iter_chunked(8192):
                    await f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback:
                        global_progress = start + downloaded
                        percentage = (global_progress / total_size) * 100
                        await progress_callback({
                            'percentage': percentage,
                            'downloaded': global_progress,
                            'total': total_size,
                            'part': part_num,
                            'speed': 0  # محاسبه سرعت جداگانه
                        })
        
        return chunk_path
