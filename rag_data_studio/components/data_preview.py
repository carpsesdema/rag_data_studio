from typing import Dict, List, Any

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *


class DataPreviewWidget(QWidget):
    """Preview scraped data in real-time"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Controls
        controls_layout = QHBoxLayout()
        self.auto_refresh_check = QCheckBox("Auto-refresh")
        self.refresh_button = QPushButton("Refresh Preview")
        self.export_sample_button = QPushButton("Export Sample")

        controls_layout.addWidget(self.auto_refresh_check)
        controls_layout.addWidget(self.refresh_button)
        controls_layout.addWidget(self.export_sample_button)
        controls_layout.addStretch()

        # Preview table
        self.preview_table = QTableWidget()
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        # Statistics
        self.stats_label = QLabel("No data previewed yet")

        layout.addLayout(controls_layout)
        layout.addWidget(QLabel("Data Preview"))
        layout.addWidget(self.preview_table)
        layout.addWidget(self.stats_label)

    def update_preview(self, data: List[Dict[str, Any]]):
        """Update the preview with new data"""
        if not data:
            self.preview_table.setRowCount(0)
            self.stats_label.setText("No data found")
            return

        # Set up table
        first_item = data[0]
        columns = list(first_item.keys())

        self.preview_table.setColumnCount(len(columns))
        self.preview_table.setHorizontalHeaderLabels(columns)
        self.preview_table.setRowCount(min(len(data), 100))  # Limit to 100 rows for performance

        # Populate data
        for row, item in enumerate(data[:100]):
            for col, key in enumerate(columns):
                value = str(item.get(key, ""))
                if len(value) > 100:
                    value = value[:97] + "..."
                self.preview_table.setItem(row, col, QTableWidgetItem(value))

        # Resize columns
        self.preview_table.resizeColumnsToContents()

        # Update statistics
        total_items = len(data)
        populated_fields = sum(1 for item in data for value in item.values() if value)
        avg_fields_per_item = populated_fields / len(data) if data else 0

        self.stats_label.setText(
            f"Total items: {total_items} | "
            f"Avg fields per item: {avg_fields_per_item:.1f} | "
            f"Showing: {min(total_items, 100)} rows"
        )
