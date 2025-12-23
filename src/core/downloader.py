"""
Download Manager with automatic method selection
"""
import os
import uuid
import tempfile
import asyncio
from pathlib import Path
from typing import Dict, Optional
from PyQt6.QtCore import QObject, pyqtSignal, QThread
import yt_dlp

from core.segment_downloader import SegmentDownloader

class DownloadWorker(QThread):
    """Worker thread for downloading videos"""
    
    progress_updated = pyqtSignal(int, float, int)  # progress%, speed, eta
    status_changed = pyqtSignal(str)  # status message
    download_completed = pyqtSignal(str)  # output_path
    download_error = pyqtSignal(str)  # error_message
    
    def __init__(
        self, 
        url: str, 
        output_path: str, 
        cookies: str = "",
        use_manual_download: bool = False,
        video_id: Optional[str] = None,
        quality: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ):
        super().__init__()
        self.url = url
        self.output_path = output_path
        self.cookies = cookies
        self.use_manual_download = use_manual_download
        self.video_id = video_id
        self.quality = quality
        self.start_time = start_time
        self.end_time = end_time
        self.should_stop = False
        self.cookie_file = None
    
    def run(self):
        """Run the download"""
        try:
            if self.use_manual_download:
                self._run_manual_download()
            else:
                self._run_ytdlp_download()
        except Exception as e:
            self.download_error.emit(str(e))
    
    def _run_manual_download(self):
        """Run manual segment download"""
        try:
            self.status_changed.emit("수동 다운로드 시작 중...")
            
            # Create event loop for async operations
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Fetch fresh m3u8 URL (signatures expire quickly)
            from core.chzzk_api import ChzzkAPI
            api = ChzzkAPI()
            
            try:
                # Get fresh metadata with valid m3u8 URL
                fresh_metadata = loop.run_until_complete(
                    api.fetch_vod_metadata(self.video_id, self.cookies)
                )
                
                # Extract Master Playlist URL first
                m3u8_url = api.get_master_playlist_url(fresh_metadata)
                
                # Fallback to direct media URL if master not available
                if not m3u8_url:
                    m3u8_url = api.get_m3u8_url(fresh_metadata, self.quality)
                
                if not m3u8_url:
                    raise Exception("Failed to extract m3u8 URL from metadata")
                    
            except Exception as e:
                raise Exception(f"Failed to fetch fresh m3u8 URL: {str(e)}")
            
            downloader = SegmentDownloader()
            
            def progress_callback(current, total):
                if self.should_stop:
                    raise Exception("Download cancelled by user")
                
                progress = int((current / total) * 100) if total > 0 else 0
                self.progress_updated.emit(progress, 0, 0)
                self.status_changed.emit(f"다운로드 중... ({current}/{total} 세그먼트)")
            
            # Parse cookies
            cookies_dict = {}
            if self.cookies:
                for cookie in self.cookies.split(';'):
                    if '=' in cookie:
                        key, value = cookie.strip().split('=', 1)
                        cookies_dict[key] = value
            
            # Use same headers as yt-dlp
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://chzzk.naver.com/',
                'Origin': 'https://chzzk.naver.com'
            }
            
            # Run async download
            output_path = loop.run_until_complete(
                downloader.download_video(
                    m3u8_url,
                    self.output_path,
                    progress_callback,
                    headers=headers,
                    cookies=cookies_dict,
                    target_quality=self.quality,
                    start_time=self.start_time,
                    end_time=self.end_time
                )
            )
            
            loop.close()
            
            self.status_changed.emit("완료")
            self.download_completed.emit(output_path)
            
        except Exception as e:
            self.download_error.emit(f"수동 다운로드 실패: {str(e)}")
    
    def _run_ytdlp_download(self):
        """Run yt-dlp download"""
        actual_output_path = None
        
        try:
            # Create cookie file if cookies provided
            if self.cookies:
                self.cookie_file = tempfile.NamedTemporaryFile(
                    mode='w', 
                    suffix='.txt', 
                    delete=False
                )
                self.cookie_file.write(self.cookies)
                self.cookie_file.close()
            
            # Configure yt-dlp options
            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'outtmpl': self.output_path + '.%(ext)s',  # Let yt-dlp add extension
                'merge_output_format': 'mp4',
                'progress_hooks': [self._progress_hook],
                'quiet': True,
                'no_warnings': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                }
            }
            
            # Add range download support
            if self.start_time is not None or self.end_time is not None:
                def download_ranges_callback(info_dict, ydl):
                    return [{
                        'start_time': self.start_time if self.start_time is not None else 0,
                        'end_time': self.end_time if self.end_time is not None else float('inf')
                    }]
                ydl_opts['download_ranges'] = download_ranges_callback
                # Force keyframes at cuts for precision (optional, might re-encode)
                # ydl_opts['force_keyframes_at_cuts'] = True 
            
            if self.cookie_file:
                ydl_opts['cookiefile'] = self.cookie_file.name
            
            # Start download
            self.status_changed.emit("다운로드 시작 중...")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if self.should_stop:
                    return
                
                # Download and get info
                info = ydl.extract_info(self.url, download=True)
                
                # Get the actual output filename
                if info:
                    actual_output_path = ydl.prepare_filename(info)
            
            self.status_changed.emit("완료")
            
            # Use actual path if available, otherwise fallback to expected path
            final_path = actual_output_path if actual_output_path else (self.output_path + '.mp4')
            self.download_completed.emit(final_path)
            
        except Exception as e:
            self.download_error.emit(str(e))
        
        finally:
            # Cleanup cookie file
            if self.cookie_file and os.path.exists(self.cookie_file.name):
                try:
                    os.remove(self.cookie_file.name)
                except:
                    pass
    
    def _progress_hook(self, d):
        """Progress hook for yt-dlp"""
        if self.should_stop:
            raise Exception("Download cancelled by user")
        
        if d['status'] == 'downloading':
            try:
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded_bytes = d.get('downloaded_bytes', 0)
                
                progress = 0
                if total_bytes > 0:
                    progress = int((downloaded_bytes / total_bytes) * 100)
                
                speed = d.get('speed', 0) or 0
                eta = d.get('eta', 0) or 0
                
                self.progress_updated.emit(progress, speed, eta)
                
                # Update status with fragment info if available
                fragment_index = d.get('fragment_index', 0)
                fragment_count = d.get('fragment_count', 0)
                if fragment_count > 0:
                    self.status_changed.emit(
                        f"다운로드 중... ({fragment_index}/{fragment_count} 조각)"
                    )
                else:
                    self.status_changed.emit("다운로드 중...")
                    
            except Exception:
                pass
        
        elif d['status'] == 'finished':
            self.status_changed.emit("병합 중...")
            self.progress_updated.emit(100, 0, 0)
    
    def stop(self):
        """Stop the download"""
        self.should_stop = True


class DownloadManager(QObject):
    """Manages multiple downloads"""
    
    def __init__(self):
        super().__init__()
        self.active_downloads: Dict[str, DownloadWorker] = {}
    
    def start_download(
        self, 
        video_id: str,
        url: str,
        title: str,
        quality: str,
        output_dir: Path,
        cookies: str = "",
        use_manual_download: bool = False,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> str:
        """
        Start a new download
        
        Args:
            video_id: Video ID
            url: Video URL
            title: Video title
            quality: Quality label (e.g., "1080p", "720p")
            output_dir: Output directory
            cookies: Cookie string
            use_manual_download: Whether to use manual segment download
            start_time: Start time in seconds
            end_time: End time in seconds
        
        Returns:
            download_id
        """
        download_id = str(uuid.uuid4())
        
        # Sanitize filename and add quality
        safe_title = self._sanitize_filename(title)
        
        # Add part info to filename if range download
        filename_suffix = quality
        if start_time is not None:
             # Just a simple check to differentiate, exact part name is handled by caller in title usually,
             # but we can append range info or rely on title passed being unique.
             # Ideally title passed to this function should already distinguish the part.
             pass
             
        filename = f"{safe_title}_{filename_suffix}"
        output_path = str(output_dir / filename)
        
        # Create worker
        worker = DownloadWorker(
            url, 
            output_path, 
            cookies, 
            use_manual_download=use_manual_download,
            video_id=video_id,
            quality=quality,
            start_time=start_time,
            end_time=end_time
        )
        self.active_downloads[download_id] = worker
        
        # NOTE: Worker is NOT started here anymore. 
        # Caller must connect signals first and then call worker.start()
        
        return download_id
    
    def cancel_download(self, download_id: str):
        """Cancel a download"""
        if download_id in self.active_downloads:
            worker = self.active_downloads[download_id]
            worker.stop()
            worker.wait()  # Wait for thread to finish
            del self.active_downloads[download_id]
    
    def get_worker(self, download_id: str) -> Optional[DownloadWorker]:
        """Get download worker by ID"""
        return self.active_downloads.get(download_id)
    
    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Sanitize filename to remove invalid characters"""
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 200:
            filename = filename[:200]
        
        return filename
