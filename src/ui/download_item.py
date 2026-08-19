"""
Download Item Widget
Custom widget for displaying download progress
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QProgressBar, QPushButton, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QPixmap
import os
import urllib.request
from urllib.parse import urlsplit

class ThumbnailLoader(QThread):
    """Thread for loading thumbnail images"""
    thumbnail_loaded = pyqtSignal(str, bytes)

    MAX_THUMBNAIL_BYTES = 10 * 1024 * 1024
    
    def __init__(self, url: str):
        super().__init__()
        self.url = url
    
    def run(self):
        """Download and load thumbnail"""
        try:
            if self.url:
                request = urllib.request.Request(
                    self.url,
                    headers={"User-Agent": "ClipCatcher thumbnail loader"},
                )
                with urllib.request.urlopen(request, timeout=8) as response:
                    final_parts = urlsplit(response.geturl())
                    if final_parts.scheme != "https" or not final_parts.hostname:
                        raise RuntimeError("unsafe thumbnail redirect")
                    data = response.read(self.MAX_THUMBNAIL_BYTES + 1)
                if len(data) > self.MAX_THUMBNAIL_BYTES:
                    raise RuntimeError("thumbnail is too large")
                self.thumbnail_loaded.emit(self.url, data)
        except Exception as e:
            print(f"Failed to load thumbnail: {e}")

class DownloadItemWidget(QWidget):
    """Widget for a single download item"""
    
    cancel_requested = pyqtSignal(str)  # download_id
    open_file_requested = pyqtSignal(str)  # file_path
    
    def __init__(self, download_id: str, title: str, thumbnail_url: str = ""):
        super().__init__()
        self.download_id = download_id
        self.title = title
        self.thumbnail_url = thumbnail_url
        self.output_path = ""
        self._compact = False
        
        self._init_ui()
        
        # Load thumbnail if URL provided
        if thumbnail_url:
            self._load_thumbnail()
    
    def _init_ui(self):
        """Initialize the UI"""
        # Main layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        
        # Thumbnail (placeholder for now)
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(160, 90)
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                background-color: #363650;
                border-radius: 6px;
                font-size: 32px;
            }
        """)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setText("📹")
        main_layout.addWidget(self.thumbnail_label)
        
        # Info section
        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)
        
        # Title
        self.title_label = QLabel(self.title)
        self.title_label.setObjectName("titleLabel")
        self.title_label.setWordWrap(True)
        self.title_label.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred,
        )
        info_layout.addWidget(self.title_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        info_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("대기 중...")
        self.status_label.setObjectName("subtitleLabel")
        info_layout.addWidget(self.status_label)
        
        main_layout.addLayout(info_layout, 1)
        
        # Buttons
        button_layout = QVBoxLayout()
        button_layout.setSpacing(6)
        
        self.cancel_button = QPushButton("취소")
        self.cancel_button.setObjectName("dangerButton")
        self.cancel_button.setFixedWidth(92)
        self.cancel_button.clicked.connect(self._on_cancel)
        button_layout.addWidget(self.cancel_button)
        
        self.open_button = QPushButton("파일 열기")
        self.open_button.setObjectName("secondaryButton")
        self.open_button.setFixedWidth(92)
        self.open_button.setVisible(False)
        self.open_button.clicked.connect(self._on_open_file)
        button_layout.addWidget(self.open_button)
        
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # Container frame
        container = QFrame()
        container.setLayout(main_layout)
        container.setStyleSheet("""
            QFrame {
                background-color: #2a2a3e;
                border-radius: 8px;
            }
        """)
        
        # Main widget layout
        widget_layout = QVBoxLayout()
        widget_layout.setContentsMargins(0, 0, 0, 0)
        widget_layout.addWidget(container)
        
        self.setLayout(widget_layout)

    def resizeEvent(self, event):
        """Keep the primary action visible when the download center is narrow."""
        super().resizeEvent(event)
        compact = event.size().width() < 560
        if compact == self._compact:
            return
        self._compact = compact
        self.thumbnail_label.setVisible(not compact)
        button_width = 72 if compact else 92
        self.cancel_button.setFixedWidth(button_width)
        self.open_button.setFixedWidth(button_width)
        self.open_button.setText("열기" if compact else "파일 열기")
    
    def update_progress(self, progress: int, speed: float, eta: int):
        """Update download progress"""
        self.progress_bar.setValue(progress)
        
        # Format speed
        if speed > 0:
            speed_mb = speed / (1024 * 1024)
            speed_text = f"{speed_mb:.1f} MB/s"
        else:
            speed_text = "계산 중..."
        
        # Format ETA
        if eta > 0:
            eta_min = eta // 60
            eta_sec = eta % 60
            eta_text = f"{eta_min}분 {eta_sec}초"
        else:
            eta_text = "계산 중..."
        
        self.status_label.setText(f"다운로드 중... | 속도: {speed_text} | 남은 시간: {eta_text}")
    
    def update_status(self, status: str):
        """Update status message"""
        self.status_label.setText(status)
    
    def set_completed(self, output_path: str):
        """Mark download as completed"""
        self.output_path = output_path
        self.progress_bar.setValue(100)
        self.status_label.setText("✅ 다운로드 완료!")
        self.status_label.setStyleSheet("color: #10b981; font-weight: 600;")
        
        self.cancel_button.setVisible(False)
        self.open_button.setVisible(True)
    
    def set_error(self, error_message: str):
        """Mark download as failed"""
        self.status_label.setText(f"❌ 오류: {error_message}")
        self.status_label.setStyleSheet("color: #ef4444; font-weight: 600;")
        self.cancel_button.setText("제거")
    
    def _on_cancel(self):
        """Handle cancel button click"""
        self.cancel_requested.emit(self.download_id)
    
    def _on_open_file(self):
        """Handle open file button click"""
        if self.output_path and os.path.exists(self.output_path):
            self.open_file_requested.emit(self.output_path)
    
    def _load_thumbnail(self):
        """Load thumbnail image from URL"""
        self.thumbnail_loader = ThumbnailLoader(self.thumbnail_url)
        self.thumbnail_loader.thumbnail_loaded.connect(self._set_thumbnail)
        self.thumbnail_loader.start()
    
    def _set_thumbnail(self, url: str, data: bytes):
        """Set the loaded thumbnail image"""
        if url != self.thumbnail_url:
            return
        pixmap = QPixmap()
        if not pixmap.loadFromData(data):
            return
        scaled = pixmap.scaled(
            self.thumbnail_label.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.thumbnail_label.setPixmap(scaled)
        self.thumbnail_label.setText("")  # Clear emoji text
