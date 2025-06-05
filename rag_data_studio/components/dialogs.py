# rag_data_studio/components/dialogs.py
"""
Custom dialog boxes used in the Data Extractor Studio.
"""
import json
import csv
from typing import List, Dict, Any

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


class ScrapedDataViewerDialog(QDialog):
    def __init__(self, scraped_data: List[Dict[str, Any]], parent=None, list_name="Scraped Items"):
        super().__init__(parent)
        self.scraped_data = scraped_data
        self.list_name = list_name
        self.setWindowTitle(f"Scraped Data: {list_name}")
        self.setModal(True)
        self.resize(900, 700)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.table_widget = QTableWidget()
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        if not self.scraped_data:
            self.table_widget.setRowCount(1)
            self.table_widget.setColumnCount(1)
            self.table_widget.setItem(0, 0, QTableWidgetItem("No data items found."))
            self.table_widget.horizontalHeader().setStretchLastSection(True)
        else:
            headers = list(self.scraped_data[0].keys())
            self.table_widget.setColumnCount(len(headers))
            self.table_widget.setHorizontalHeaderLabels(headers)
            self.table_widget.setRowCount(len(self.scraped_data))
            for row_idx, item_dict in enumerate(self.scraped_data):
                for col_idx, header in enumerate(headers):
                    value = item_dict.get(header)
                    cell_value = json.dumps(value, indent=2) if isinstance(value, (list, dict)) else str(
                        value) if value is not None else ""
                    self.table_widget.setItem(row_idx, col_idx,
                                              QTableWidgetItem(cell_value[:500]))  # Truncate long values
            self.table_widget.resizeColumnsToContents()
            self.table_widget.horizontalHeader().setStretchLastSection(True)

        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 Save List as...")
        self.save_btn.clicked.connect(self.save_data)
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(QLabel(f"Displaying {len(self.scraped_data)} items from list: '{self.list_name}'"))
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.close_button)
        layout.addWidget(self.table_widget)
        layout.addLayout(button_layout)

    def save_data(self):
        if not self.scraped_data: QMessageBox.warning(self, "No Data", "There is no data to save."); return
        filename, selected_filter = QFileDialog.getSaveFileName(self, "Save Scraped Data", f"{self.list_name}.json",
                                                                "JSON files (*.json);;CSV files (*.csv)")
        if not filename: return
        try:
            if selected_filter.startswith("JSON"):
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.scraped_data, f, indent=2)
            elif selected_filter.startswith("CSV"):
                with open(filename, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=self.scraped_data[0].keys())
                    writer.writeheader()
                    writer.writerows(self.scraped_data)
            QMessageBox.information(self, "Save Complete", f"Data successfully saved to\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Could not save data: {e}")


# TestResultsDialog (moved from backend_bridge)
class TestResultsDialog(QDialog):
    def __init__(self, results: Dict[str, Any], parent=None, test_url="N/A"):
        super().__init__(parent)
        self.setWindowTitle(f"Selector Test Results: {test_url[:80]}")
        self.setModal(True)
        self.resize(800, 600)
        layout = QVBoxLayout(self)
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Rule Name", "Status", "Found", "Sample Values"])
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setWordWrap(True)
        if "error" in results:
            self.results_table.setRowCount(1)
            self.results_table.setItem(0, 0, QTableWidgetItem("Error"))
            error_item = QTableWidgetItem(results["error"])
            self.results_table.setItem(0, 1, error_item)
            self.results_table.setSpan(0, 1, 1, 3)
        else:
            self.results_table.setRowCount(len(results))
            for row, (name, result_data) in enumerate(results.items()):
                self.results_table.setItem(row, 0, QTableWidgetItem(name))
                status_text = "✅ Success" if result_data.get('success') else "❌ Failed"
                status_item = QTableWidgetItem(status_text)
                if result_data.get('success'):
                    status_item.setBackground(QColor(200, 255, 200))
                else:
                    status_item.setBackground(QColor(255, 200, 200)); status_item.setToolTip(
                        result_data.get('error', ''))
                self.results_table.setItem(row, 1, status_item)
                self.results_table.setItem(row, 2, QTableWidgetItem(str(result_data.get('found_count', 0))))
                sample_text = "\n---\n".join(result_data.get('sample_values', []))
                self.results_table.setItem(row, 3, QTableWidgetItem(sample_text))
        self.results_table.resizeColumnsToContents()
        self.results_table.resizeRowsToContents()
        self.results_table.horizontalHeader().setStretchLastSection(True)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(QLabel(f"Test URL: {test_url}"))
        layout.addWidget(self.results_table)
        layout.addWidget(close_btn)