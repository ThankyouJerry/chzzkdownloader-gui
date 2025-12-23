from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QPushButton, QLabel, QCheckBox, QScrollArea, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPalette

class PartSelectionWidget(QWidget):
    """Widget for selecting video parts (30-minute segments)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.checkboxes = []
        self.duration = 0
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        
        # Header section
        header_layout = QHBoxLayout()
        
        title_label = QLabel("다운로드할 부분 선택")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(title_label)
        
        self.count_label = QLabel("0 개 선택됨")
        self.count_label.setStyleSheet("color: #888; margin-left: 10px;")
        header_layout.addWidget(self.count_label)
        
        header_layout.addStretch()
        
        # Action buttons
        btn_style = """
            QPushButton {
                background-color: #333;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 4px 12px;
                color: #ddd;
            }
            QPushButton:hover {
                background-color: #444;
            }
        """
        
        self.all_btn = QPushButton("All")
        self.all_btn.setStyleSheet(btn_style)
        self.all_btn.clicked.connect(self.select_all)
        header_layout.addWidget(self.all_btn)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setStyleSheet(btn_style)
        self.clear_btn.clicked.connect(self.clear_selection)
        header_layout.addWidget(self.clear_btn)
        
        layout.addLayout(header_layout)
        
        # Grid area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("background-color: transparent;")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        self.grid_layout = QGridLayout(scroll_content)
        self.grid_layout.setSpacing(10)
        
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        # Hide by default
        self.setVisible(False)
        
    def set_duration(self, duration_sec: float):
        """Set video duration and generate checkboxes"""
        self.duration = duration_sec
        self.checkboxes = []
        
        # Clear existing items
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        if duration_sec <= 0:
            self.setVisible(False)
            return
            
        self.setVisible(True)
        
        # Calculate parts (30 mins = 1800 sec)
        part_duration = 1800
        num_parts = int(duration_sec // part_duration) + (1 if duration_sec % part_duration > 0 else 0)
        
        # Reset count label
        self.count_label.setText("0 개 선택됨")
        
        # Create checkboxes
        columns = 3
        for i in range(num_parts):
            start = i * part_duration
            end = min((i + 1) * part_duration, duration_sec)
            
            # Format times (HH:MM:SS)
            start_str = self._format_time(start)
            end_str = self._format_time(end)
            duration_str = self._format_duration(end - start)
            
            # Create container widget for styling
            container = QFrame()
            container.setStyleSheet("""
                QFrame {
                    background-color: #2a2a2a;
                    border: 1px solid #3d3d3d;
                    border-radius: 6px;
                }
                QFrame:hover {
                    border-color: #555;
                }
            """)
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(10, 8, 10, 8)
            
            # Top row: Checkbox and duration badge
            top_row = QHBoxLayout()
            
            cb = QCheckBox(f"Part {i+1}")
            cb.setStyleSheet("font-weight: bold; color: #eee;")
            cb.part_index = i
            cb.start_time = start
            cb.end_time = end
            cb.stateChanged.connect(self._update_count)
            self.checkboxes.append(cb)
            top_row.addWidget(cb)
            
            top_row.addStretch()
            
            badge = QLabel(duration_str)
            badge.setStyleSheet("""
                background-color: #00C73C;
                color: white;
                border-radius: 3px;
                padding: 2px 4px;
                font-size: 11px;
            """)
            top_row.addWidget(badge)
            
            container_layout.addLayout(top_row)
            
            # Bottom row: Time range
            range_label = QLabel(f"{start_str} - {end_str}")
            range_label.setStyleSheet("color: #888; font-size: 12px; margin-top: 2px;")
            container_layout.addWidget(range_label)
            
            # Add to grid
            row = i // columns
            col = i % columns
            self.grid_layout.addWidget(container, row, col)
            
    def _format_time(self, seconds: float) -> str:
        """Format seconds to H:MM:SS"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"
        
    def _format_duration(self, seconds: float) -> str:
        """Format duration (e.g. 30m, 24m)"""
        m = int(seconds // 60)
        return f"{m}m"
        
    def select_all(self):
        for cb in self.checkboxes:
            cb.setChecked(True)
            
    def clear_selection(self):
        for cb in self.checkboxes:
            cb.setChecked(False)
            
    def _update_count(self):
        count = sum(1 for cb in self.checkboxes if cb.isChecked())
        self.count_label.setText(f"{count} 개 선택됨")
        
    def get_selected_ranges(self):
        """Return list of (start, end, part_index) for selected parts"""
        selected = []
        for cb in self.checkboxes:
            if cb.isChecked():
                selected.append({
                    'start': cb.start_time,
                    'end': cb.end_time,
                    'part': cb.part_index + 1
                })
        return selected
