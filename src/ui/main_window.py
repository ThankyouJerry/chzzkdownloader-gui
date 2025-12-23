"""
Main Window for Chzzk Downloader
"""
import asyncio
import sys
import subprocess
import platform
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QListWidget, QListWidgetItem, QMessageBox, QMenuBar,
    QGroupBox, QSizePolicy, QFileDialog
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QPixmap
from qasync import asyncSlot

from ui.download_item import DownloadItemWidget
from ui.settings_dialog import SettingsDialog
from core.chzzk_api import ChzzkAPI
from core.downloader import DownloadManager
from core.config import Config


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.api = ChzzkAPI()
        self.download_manager = DownloadManager()
        self.current_metadata = None
        self.download_widgets = {}  # download_id -> widget
        
        # Load download path from config or default
        default_path = os.path.join(os.getcwd(), "downloads")
        self.download_path = self.config.get("download_path", default_path)
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path, exist_ok=True)
        
        self.setWindowTitle("Chzzk Downloader")
        self.setMinimumSize(900, 700)
        
        self._init_ui()
        self._create_menu_bar()
    
    def _init_ui(self):
        """Initialize the user interface"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_label = QLabel("🎥 Chzzk Downloader")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: 700;
                color: #00FFA3;
                padding: 10px 0;
            }
        """)
        main_layout.addWidget(header_label)
        
        # URL Input Section
        url_group = self._create_url_input_section()
        main_layout.addWidget(url_group)
        
        # Video Info Section
        self.info_group = self._create_video_info_section()
        self.info_group.setVisible(False)
        main_layout.addWidget(self.info_group)
        
        # Download Queue Section
        queue_group = self._create_download_queue_section()
        main_layout.addWidget(queue_group)
        
        central_widget.setLayout(main_layout)
    
    def _create_url_input_section(self) -> QGroupBox:
        """Create URL input section"""
        group = QGroupBox("URL 입력")
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # URL input
        input_layout = QHBoxLayout()
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("치지직 VOD 또는 클립 URL을 입력하세요 (예: https://chzzk.naver.com/video/12345)")
        self.url_input.returnPressed.connect(self._fetch_metadata)
        input_layout.addWidget(self.url_input)
        
        # Status indicator
        self.status_indicator = QLabel("⚪")
        self.status_indicator.setStyleSheet("""
            QLabel {
                font-size: 24px;
                padding: 0 8px;
            }
        """)
        self.status_indicator.setToolTip("URL 입력 후 정보를 가져오면 다운로드 가능 여부가 표시됩니다")
        input_layout.addWidget(self.status_indicator)
        
        self.fetch_button = QPushButton("정보 가져오기")
        self.fetch_button.clicked.connect(self._fetch_metadata)
        input_layout.addWidget(self.fetch_button)
        
        layout.addLayout(input_layout)
        
        # Status message label (hidden by default)
        self.status_message_label = QLabel()
        self.status_message_label.setWordWrap(True)
        self.status_message_label.setVisible(False)
        layout.addWidget(self.status_message_label)
        
        group.setLayout(layout)
        return group
    
    def _create_video_info_section(self) -> QGroupBox:
        """Create video info display section"""
        group = QGroupBox("영상 정보")
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Title
        self.title_label = QLabel()
        self.title_label.setObjectName("titleLabel")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)
        
        # Channel and duration
        self.meta_label = QLabel()
        self.meta_label.setObjectName("subtitleLabel")
        layout.addWidget(self.meta_label)
        
        # Quality selection
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("화질 선택:"))
        
        self.quality_combo = QComboBox()
        self.quality_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        quality_layout.addWidget(self.quality_combo)
        
        self.download_button = QPushButton("다운로드")
        self.download_button.clicked.connect(self._start_download)
        quality_layout.addWidget(self.download_button)
        
        layout.addLayout(quality_layout)
        group.setLayout(layout)
        return group
    
    def _create_download_queue_section(self) -> QGroupBox:
        """Create download queue section"""
        group = QGroupBox("다운로드 목록")
        layout = QVBoxLayout()
        
        self.download_list = QListWidget()
        self.download_list.setSpacing(8)
        layout.addWidget(self.download_list)
        
        group.setLayout(layout)
        return group
    
    def _create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("파일")
        
        settings_action = QAction("설정", self)
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("종료", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("도움말")
        
        about_action = QAction("정보", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    @asyncSlot()
    async def _fetch_metadata(self):
        """Fetch video metadata from URL"""
        url = self.url_input.text().strip()
        
        # Reset status indicator
        self.status_indicator.setText("⚪")
        self.status_indicator.setToolTip("확인 중...")
        self.status_message_label.setVisible(False)
        
        # Hide info sections
        self.info_container.setVisible(False)
        self.part_selector.setVisible(False)
        self.quality_frame.setVisible(False)
        self.download_btn.setEnabled(False)
        
        if not url:
            self.status_indicator.setText("🔴")
            self.status_indicator.setToolTip("URL을 입력해주세요")
            QMessageBox.warning(self, "오류", "URL을 입력해주세요.")
            return
        
        # Parse URL
        parsed = self.api.parse_url(url)
        if not parsed:
            self.status_indicator.setText("🔴")
            self.status_indicator.setToolTip("올바른 치지직 URL이 아닙니다")
            QMessageBox.warning(self, "오류", "올바른 치지직 URL이 아닙니다.")
            return
        
        # Disable button
        self.fetch_button.setEnabled(False)
        self.fetch_button.setText("가져오는 중...")
        self.status_indicator.setText("🟡")
        self.status_indicator.setToolTip("정보를 가져오는 중...")
        
        try:
            # Get cookies
            cookies_dict = self.config.get("cookies", {})
            cookie_str = ""
            if cookies_dict.get("NID_AUT") and cookies_dict.get("NID_SES"):
                cookie_str = f"NID_AUT={cookies_dict['NID_AUT']}; NID_SES={cookies_dict['NID_SES']}"
            
            # Fetch metadata
            if parsed['type'] == 'vod':
                metadata = await self.api.fetch_vod_metadata(parsed['id'], cookie_str)
            else:
                metadata = await self.api.fetch_clip_metadata(parsed['id'], cookie_str)
            
            self.current_metadata = metadata
            self._display_metadata(metadata)
            
        except Exception as e:
            self.status_indicator.setText("🔴")
            self.status_indicator.setToolTip(f"오류: {str(e)}")
            QMessageBox.critical(self, "오류", f"메타데이터를 가져오는데 실패했습니다:\n{str(e)}")
        
        finally:
            self.fetch_button.setEnabled(True)
            self.fetch_button.setText("정보 가져오기")
    
    def _display_metadata(self, metadata: dict):
        """Display fetched metadata"""
        self.current_metadata = metadata
        
        # Show info sections
        self.info_container.setVisible(True)
        self.part_selector.setVisible(True)
        self.quality_frame.setVisible(True)
        
        # Update text info
        self.video_title.setText(metadata['title'])
        self.channel_name.setText(metadata['channel_name'])
        
        # Format publish date if available, otherwise use empty string
        publish_date = metadata.get('publish_date', '')
        self.video_date.setText(publish_date)
        
        # Update Part Selector with duration
        duration = metadata.get('duration', 0)
        self.part_selector.set_duration(duration)
        
        # Update status indicator
        is_downloadable = metadata.get('is_downloadable', False)
        vod_status = metadata.get('vod_status', 'UNKNOWN')
        
        if is_downloadable:
            self.status_indicator.setText("🟢")
            self.status_indicator.setToolTip("다운로드 가능")
            self.status_message_label.setVisible(False)
            self.download_btn.setEnabled(True)
            self.download_btn.setText("다운로드")
        else:
            # Fast replay / upload state - Manual download available
            self.status_indicator.setText("🟠")
            self.status_indicator.setToolTip("수동 다운로드 (느릴 수 있음)")
            self.status_message_label.setVisible(True)
            self.status_message_label.setStyleSheet("""
                QLabel {
                    color: #FF9F43;
                    background-color: rgba(255, 159, 67, 0.1);
                    padding: 10px;
                    border-radius: 8px;
                    font-size: 13px;
                }
            """)
            self.status_message_label.setText(
                f"⚠️ 빠른 다시보기 상태 (vodStatus: {vod_status})\n"
                f"수동 다운로드 모드로 진행됩니다.\n"
                f"속도가 느릴 수 있으며, 완료까지 시간이 걸립니다."
            )
            self.download_btn.setEnabled(True)
            self.download_btn.setText("수동 다운로드 시작")
        
        # Load thumbnail async (assuming _load_thumbnail exists or will be added)
        # For now, just set a placeholder or handle it if it's not critical
        # self._load_thumbnail(metadata['thumbnail']) 
        # Placeholder for thumbnail loading
        pixmap = QPixmap()
        if pixmap.loadFromData(self.api.get_thumbnail_data(metadata.get('thumbnail', ''))):
            self.thumbnail_label.setPixmap(pixmap.scaled(self.thumbnail_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.thumbnail_label.setText("No Thumbnail")
        
        # Update quality combo
        self.quality_combo.clear()
        for res in metadata['resolutions']:
            self.quality_combo.addItem(
                f"{res['label']} ({res.get('bitrate', 0) // 1000} kbps)",
                res # Store the full resolution dict as data
            )
    
    def _start_download(self):
        """Start the download process"""
        if not self.current_metadata:
            return
            
        # Get selected quality
        selected_res = self.quality_combo.currentData()
        if not selected_res:
            QMessageBox.warning(self, "오류", "화질을 선택해주세요.")
            return
        
        url = selected_res['url'] # Use the URL from the selected resolution
        quality_label = selected_res['label'] # Use the label for display
        title = self.current_metadata['title']
        video_id = self.current_metadata['id']
        
        # Check if manual download is needed
        # VOD_ON_AIR (live rewind) or manual flag overrides yt-dlp
        use_manual_download = (
            self.current_metadata.get('vod_status') != 'ABR_HLS' and self.current_metadata.get('type') == 'vod'
        )
        
        # Check split download
        selected_parts = self.part_selector.get_selected_ranges()
        
        if not selected_parts:
            # Download full video
            self._initiate_download(video_id, url, title, quality_label, use_manual_download)
        else:
            # Download selected parts
            for i, part in enumerate(selected_parts):
                part_title = f"{title} (Part {i+1})" # Use i+1 for part number
                self._initiate_download(
                    video_id, 
                    url, 
                    part_title, 
                    quality_label, 
                    use_manual_download,
                    start_time=part['start'],
                    end_time=part['end']
                )
        
        # Show confirmation
        QMessageBox.information(
            self,
            "다운로드 시작",
            f"다운로드가 시작되었습니다!\n저장 위치: {self.download_path}"
        )
        
    def _initiate_download(
        self, 
        video_id, 
        url, 
        title, 
        quality, 
        use_manual, 
        start_time=None, 
        end_time=None
    ):
        """Helper to start a single download task"""
        # Create output directory if not exists
        output_dir = Path(self.download_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get cookies
        cookies = self.config.get_cookies()
        
        # Start download
        download_id = self.download_manager.start_download(
            video_id=video_id,
            url=url,
            title=title,
            quality=quality,
            output_dir=str(output_dir), # Pass as string
            cookies=cookies,
            use_manual_download=use_manual,
            start_time=start_time,
            end_time=end_time
        )
        
        # Create UI item
        widget = DownloadItemWidget(
            download_id=download_id,
            title=title,
            thumbnail_url=self.current_metadata.get('thumbnail', '') # Use current metadata thumbnail
        )
        
        # Connect signals
        worker = self.download_manager.get_worker(download_id)
        if worker:
            worker.progress_updated.connect(widget.update_progress)
            worker.status_changed.connect(widget.update_status)
            worker.download_completed.connect(widget.set_completed)
            worker.download_error.connect(widget.set_error)
            
            # Start download
            worker.start()
        
        widget.cancel_requested.connect(self._cancel_download)
        widget.open_file_requested.connect(self._open_file)
        
        # Add to list
        item = QListWidgetItem(self.download_list)
        item.setSizeHint(widget.sizeHint())
        self.download_list.addItem(item)
        self.download_list.setItemWidget(item, widget)
        
        self.download_widgets[download_id] = (item, widget)
        
    def _cancel_download(self, download_id: str):
        """Cancel a download"""
        self.download_manager.cancel_download(download_id)
        
        # Remove from list
        if download_id in self.download_widgets:
            item, widget = self.download_widgets[download_id]
            row = self.download_list.row(item)
            self.download_list.takeItem(row)
            del self.download_widgets[download_id]
    
    def _open_file(self, file_path: str):
        """Open downloaded file"""
        try:
            if platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', file_path])
            elif platform.system() == 'Windows':
                os.startfile(file_path)
            else:  # Linux
                subprocess.run(['xdg-open', file_path])
        except Exception as e:
            QMessageBox.warning(self, "오류", f"파일을 열 수 없습니다:\n{str(e)}")
    
    def _open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self.config, self)
        dialog.exec()
    
    def _show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "Chzzk Downloader 정보",
            "<h3>Chzzk Downloader</h3>"
            "<p>네이버 치지직 VOD 및 클립 다운로더</p>"
            "<p>Version 1.0.0</p>"
            "<p>PyQt6 기반 데스크톱 애플리케이션</p>"
        )
