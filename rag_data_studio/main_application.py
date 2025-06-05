# rag_data_studio/main_application.py
"""
Data Extractor Studio - Main Application Window and Entry Point
Orchestrates the UI components and backend bridge.
"""
import sys
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import asdict
from datetime import datetime  # <--- THE BUG FIX IS HERE!

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

# Local imports from the new modular structure
import config
from .core.models import ProjectConfig, ScrapingRule
from .components.browser import InteractiveBrowser
from .components.project_panel import ProjectManager, ProjectDialog
from .components.rule_editor import VisualElementTargeter, RulesManager
from .components.dialogs import ScrapedDataViewerDialog, TestResultsDialog
from .integration.backend_bridge import RAGStudioBridge

DARK_THEME = """
QMainWindow, QWidget { background-color: #1e1e1e; color: #ffffff; font-family: 'Segoe UI', Arial, sans-serif; font-size: 11px; }
QGroupBox { font-weight: bold; border: 2px solid #404040; border-radius: 8px; margin-top: 10px; padding-top: 10px; background-color: #2d2d2d; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; color: #4CAF50; }
QPushButton { background-color: #404040; border: 1px solid #606060; border-radius: 6px; padding: 8px 16px; color: white; font-weight: bold; }
QPushButton:hover { background-color: #505050; border-color: #4CAF50; }
QPushButton:pressed { background-color: #303030; }
QPushButton[class="success"] { background-color: #4CAF50; border-color: #45a049; }
QPushButton[class="success"]:hover { background-color: #45a049; }
QLineEdit, QTextEdit, QPlainTextEdit { background-color: #3a3a3a; border: 2px solid #555555; border-radius: 6px; padding: 6px; color: white; selection-background-color: #4CAF50; }
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus { border-color: #4CAF50; }
QComboBox { background-color: #3a3a3a; border: 2px solid #555555; border-radius: 6px; padding: 6px; color: white; min-width: 100px; }
QComboBox:hover { border-color: #4CAF50; }
QComboBox::drop-down { border: none; background-color: #505050; border-radius: 3px; }
QComboBox QAbstractItemView { background-color: #3a3a3a; border: 1px solid #555555; selection-background-color: #4CAF50; color: white; }
QTableWidget, QTreeWidget { background-color: #2a2a2a; alternate-background-color: #343434; gridline-color: #555555; border: 1px solid #555555; border-radius: 6px; }
QTableWidget::item:selected, QTreeWidget::item:selected { background-color: #4CAF50; color: white; }
QHeaderView::section { background-color: #404040; color: white; padding: 8px; border: 1px solid #555555; font-weight: bold; }
QListWidget { background-color: #2a2a2a; border: 1px solid #555555; border-radius: 6px; padding: 4px; }
QListWidget::item:selected { background-color: #4CAF50; color: white; }
QCheckBox::indicator { width: 16px; height: 16px; border: 2px solid #555555; border-radius: 3px; background-color: #3a3a3a; }
QCheckBox::indicator:checked { background-color: #4CAF50; border-color: #4CAF50; }
QStatusBar { background-color: #2a2a2a; border-top: 1px solid #555555; color: #ffffff; }
QSplitter::handle { background-color: #404040; }
"""


class DataExtractorStudio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_project: Optional[ProjectConfig] = None
        self.backend_bridge = RAGStudioBridge()
        self.selection_poll_timer = QTimer(self)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Data Extractor Studio")
        self.setGeometry(100, 100, 1600, 1000)
        self.setStyleSheet(DARK_THEME)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_splitter = QSplitter(Qt.Horizontal)
        self.project_manager = ProjectManager()
        self.browser = InteractiveBrowser()
        self.element_targeter = VisualElementTargeter()
        self.rules_manager = RulesManager()
        self.project_manager.setMaximumWidth(320)
        main_splitter.addWidget(self.project_manager)
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        toolbar_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter URL to analyze...")
        self.load_btn = QPushButton("🌐 Load Page")
        self.selector_btn = QPushButton("🎯 Target Elements")
        self.selector_btn.setCheckable(True)
        self.selector_btn.setProperty("class", "success")
        toolbar_layout.addWidget(QLabel("URL:"))
        toolbar_layout.addWidget(self.url_input)
        toolbar_layout.addWidget(self.load_btn)
        toolbar_layout.addWidget(self.selector_btn)
        center_layout.addLayout(toolbar_layout)
        center_layout.addWidget(self.browser)
        main_splitter.addWidget(center_widget)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.addWidget(self.element_targeter)
        right_splitter.addWidget(self.rules_manager)
        right_splitter.setSizes([self.height() // 2, self.height() // 2])
        right_layout.addWidget(right_splitter)
        right_widget.setMinimumWidth(400)
        right_widget.setMaximumWidth(500)
        main_splitter.addWidget(right_widget)
        main_splitter.setSizes([300, self.width() - 750, 450])
        main_layout.addWidget(main_splitter)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Create or load a project to begin.")
        self.create_menu_bar()
        self.connect_signals()

    def connect_signals(self):
        self.load_btn.clicked.connect(self.load_page)
        self.url_input.returnPressed.connect(self.load_page)
        self.selector_btn.toggled.connect(self.toggle_selector_mode_handler)
        self.project_manager.project_selected.connect(self.load_project_into_ui)
        self.project_manager.new_project_requested.connect(self.show_new_project_dialog)
        self.element_targeter.rule_created.connect(self.add_rule_to_current_project)
        self.element_targeter.test_selector_requested.connect(self.handle_test_selector_request)
        self.browser.element_selected.connect(self.element_targeter.update_selection)
        self.rules_manager.delete_rule_requested.connect(self.delete_rule_from_project)
        self.rules_manager.add_sub_rule_requested.connect(self.handle_add_sub_rule)
        self.selection_poll_timer.timeout.connect(self.browser.check_for_selection)

    def create_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        new_action = QAction('New Project...', self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self.show_new_project_dialog)
        file_menu.addAction(new_action)
        file_menu.addSeparator()
        export_selectors_action = QAction('Export Project Config...', self)
        export_selectors_action.triggered.connect(self.export_project_configuration)
        file_menu.addAction(export_selectors_action)
        file_menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        tools_menu = menubar.addMenu('Tools')
        test_all_rules_action = QAction('Test All Rules', self)
        test_all_rules_action.triggered.connect(self.handle_test_all_rules_request)
        tools_menu.addAction(test_all_rules_action)
        run_pipeline_action = QAction('Run Extraction Pipeline...', self)
        run_pipeline_action.triggered.connect(self.run_extraction_pipeline)
        tools_menu.addAction(run_pipeline_action)
        help_menu = menubar.addMenu('Help')
        about_action = QAction('About...', self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def show_new_project_dialog(self):
        dialog = ProjectDialog(self)
        if dialog.exec() == QDialog.Accepted:
            project = dialog.get_project_config()
            self.project_manager.add_or_update_project(project)
            self.load_project_into_ui(project)
            self.status_bar.showMessage(f"Created and loaded new project: {project.name}")

    def load_page(self):
        url = self.url_input.text().strip()
        if not url: self.status_bar.showMessage("Please enter a URL.", 3000); return
        if not (url.startswith('http://') or url.startswith('https://')):
            if Path(url).is_file() and Path(url).suffix.lower() in ['.html', '.htm']:
                url_qurl = QUrl.fromLocalFile(str(Path(url).resolve()))
            else:
                url_qurl = QUrl('https://' + url)
        else:
            url_qurl = QUrl(url)
        if url_qurl.isValid():
            self.browser.load(url_qurl)
            self.status_bar.showMessage(f"Loading: {url_qurl.toString()}")
            try:
                self.browser.page().loadFinished.disconnect(self._on_load_finished)
            except (TypeError, RuntimeError):
                pass
            self.browser.page().loadFinished.connect(self._on_load_finished)
        else:
            QMessageBox.warning(self, "Invalid URL", f"The URL '{url}' is not valid.")

    def _on_load_finished(self, ok):
        self.status_bar.showMessage(f"Page loaded: {self.browser.url().toString()}" if ok else f"Failed to load page.",
                                    3000)
        if ok and self.selector_btn.isChecked():
            self.browser.enable_selector_mode()
            if not self.selection_poll_timer.isActive(): self.selection_poll_timer.start(250)

    def toggle_selector_mode_handler(self, checked):
        if checked:
            if self.browser.url().isValid() and not self.browser.url().isEmpty():
                self.browser.enable_selector_mode()
                self.selector_btn.setText("❌ Stop Targeting")
                self.selector_btn.setProperty("class", "")
                self.status_bar.showMessage("🎯 Targeting mode ON. Click elements to define selectors.")
                if not self.selection_poll_timer.isActive(): self.selection_poll_timer.start(250)
                self.element_targeter.reset_mode()
            else:
                self.status_bar.showMessage("Load a page first to enable targeting.",
                                            3000); self.selector_btn.setChecked(False)
        else:
            self.browser.disable_selector_mode()
            self.selector_btn.setText("🎯 Target Elements")
            self.selector_btn.setProperty("class", "success")
            self.status_bar.showMessage("Targeting mode OFF.")
            self.selection_poll_timer.stop()
            self.element_targeter.reset_mode()
        self.selector_btn.style().unpolish(self.selector_btn)
        self.selector_btn.style().polish(self.selector_btn)

    def load_project_into_ui(self, project: ProjectConfig):
        self.current_project = project
        self.rules_manager.set_rules(project.scraping_rules)
        if project.target_websites:
            self.url_input.setText(project.target_websites[0]); self.load_page()
        else:
            self.url_input.clear()
        self.setWindowTitle(f"Data Extractor Studio - {project.name}")
        self.status_bar.showMessage(f"Project loaded: {project.name} ({len(project.scraping_rules)} rules)")
        self.element_targeter.reset_mode()

    def add_rule_to_current_project(self, rule: ScrapingRule, parent_id: Optional[str]):
        if not self.current_project: QMessageBox.warning(self, "No Project Loaded",
                                                         "Load or create a project first."); return
        if any(r.name == rule.name for r in self.current_project.scraping_rules):
            QMessageBox.warning(self, "Duplicate Rule Name", f"Rule '{rule.name}' already exists.")
            return
        if parent_id:
            parent_rule = next((r for r in self.current_project.scraping_rules if r.id == parent_id), None)
            if parent_rule:
                parent_rule.sub_selectors.append(rule)
            else:
                self.current_project.scraping_rules.append(rule)
        else:
            self.current_project.scraping_rules.append(rule)
        self.current_project.updated_at = datetime.now().isoformat()
        self.project_manager.add_or_update_project(self.current_project)
        self.rules_manager.set_rules(self.current_project.scraping_rules)
        self.status_bar.showMessage(f"Added rule '{rule.name}' to '{self.current_project.name}'.")
        if self.selector_btn.isChecked():
            self.browser.enable_selector_mode()
            if not self.selection_poll_timer.isActive(): self.selection_poll_timer.start(250)

    def delete_rule_from_project(self, rule_id_to_delete: str):
        if not self.current_project: return
        rule_found = False
        for i, rule in enumerate(self.current_project.scraping_rules):
            if rule.id == rule_id_to_delete:
                del self.current_project.scraping_rules[i]
                rule_found = True
                break
            else:
                for j, sub_rule in enumerate(rule.sub_selectors):
                    if sub_rule.id == rule_id_to_delete:
                        del rule.sub_selectors[j]
                        rule_found = True
                        break
            if rule_found: break
        if rule_found:
            self.current_project.updated_at = datetime.now().isoformat()
            self.project_manager.add_or_update_project(self.current_project)
            self.rules_manager.set_rules(self.current_project.scraping_rules)
            self.status_bar.showMessage(f"Deleted rule.")

    def handle_add_sub_rule(self, parent_rule_id: str):
        parent_rule = next((r for r in self.current_project.scraping_rules if r.id == parent_rule_id), None)
        if parent_rule:
            self.element_targeter.set_mode_for_sub_field(parent_rule)
            self.selector_btn.setChecked(True)
            self.status_bar.showMessage(f"🎯 Select an element for a new sub-field in '{parent_rule.name}'...")

    def export_project_configuration(self):
        if not self.current_project: QMessageBox.warning(self, "No Project", "Select a project to export."); return
        self.project_manager.save_projects_to_disk()
        QMessageBox.information(self, "Project Saved",
                                f"Current project configuration saved to\n{self.project_manager.get_project_path()}")

    def handle_test_selector_request(self, selector_config: Dict[str, Any]):
        current_url = self.browser.url().toString()
        if not current_url or self.browser.url().isEmpty(): QMessageBox.warning(self, "No Page Loaded",
                                                                                "Load a page to test selectors."); return
        self.status_bar.showMessage(f"Testing selector '{selector_config.get('name')}'...")
        QTimer.singleShot(10, lambda: self._execute_single_selector_test(current_url, selector_config))

    def _execute_single_selector_test(self, url: str, selector_config: Dict[str, Any]):
        results = self.backend_bridge.test_selectors_on_url(url, [selector_config])
        selector_name = selector_config.get('name')
        single_result_data = results.get(selector_name, {"error": "Test result not found."})
        TestResultsDialog({selector_name: single_result_data}, self, test_url=url).exec()
        self.status_bar.showMessage(f"Test for '{selector_name}' complete.", 3000)

    def handle_test_all_rules_request(self):
        if not self.current_project or not self.current_project.scraping_rules: QMessageBox.warning(self, "No Rules",
                                                                                                    "No rules to test."); return
        current_url = self.browser.url().toString()
        if not current_url or self.browser.url().isEmpty(): QMessageBox.warning(self, "No Page Loaded",
                                                                                "Load a page to test rules against."); return
        all_rules_flat = []
        for rule in self.current_project.scraping_rules:
            all_rules_flat.append(rule)
            if rule.sub_selectors: all_rules_flat.extend(rule.sub_selectors)
        selectors_to_test = [{"name": r.name, "selector": r.selector, "extract_type": r.extraction_type,
                              "attribute_name": r.attribute_name} for r in all_rules_flat]
        self.status_bar.showMessage(f"Testing {len(selectors_to_test)} rules...")
        QTimer.singleShot(10, lambda: self._execute_all_rules_test(current_url, selectors_to_test))

    def _execute_all_rules_test(self, url: str, selectors_config_list: List[Dict[str, Any]]):
        results = self.backend_bridge.test_selectors_on_url(url, selectors_config_list)
        TestResultsDialog(results, self, test_url=url).exec()
        self.status_bar.showMessage("Finished testing all rules.", 3000)

    def _prepare_project_data_for_pipeline(self, project: ProjectConfig) -> dict:
        return {"domain_info": {"name": project.name, "description": project.description}, "sources": [
            {"name": project.name.lower().replace(' ', '_'), "seeds": project.target_websites,
             "source_type": project.domain,
             "selectors": {"custom_fields": [asdict(rule) for rule in project.scraping_rules]},
             "crawl": project.rate_limiting, "export": project.output_settings}]}

    def run_extraction_pipeline(self):
        if not self.current_project: QMessageBox.warning(self, "No Project", "Select a project."); return
        if not self.current_project.target_websites: QMessageBox.warning(self, "No Websites",
                                                                         "Add target websites."); return
        if not self.current_project.scraping_rules: QMessageBox.warning(self, "No Rules",
                                                                        "Define scraping rules."); return
        reply = QMessageBox.question(self, "Run Extraction Pipeline",
                                     f"Run extraction for '{self.current_project.name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            self.status_bar.showMessage(f"🚀 Starting extraction for '{self.current_project.name}'...")
            project_data = self._prepare_project_data_for_pipeline(self.current_project)
            # This should be in a QThread for a real app
            enriched_items = self.backend_bridge.run_scraping_pipeline_with_config_data(project_data)
            if enriched_items:
                self.status_bar.showMessage(f"Extraction complete. Found {len(enriched_items)} primary items.", 5000)
                data_to_display, list_field_name = [], "Scraped Items"
                for item in enriched_items:
                    for field_name, field_value in item.custom_fields.items():
                        if isinstance(field_value, list) and field_value and isinstance(field_value[0], dict):
                            data_to_display.extend(field_value)
                            list_field_name = field_name
                            break
                    if data_to_display: break
                if data_to_display:
                    ScrapedDataViewerDialog(data_to_display, self, list_name=list_field_name).exec()
                else:
                    QMessageBox.information(self, "Extraction Complete",
                                            f"Pipeline ran successfully, {len(enriched_items)} items processed.\nNo structured list data was found in the results.")
            else:
                QMessageBox.warning(self, "Extraction Issue", "Pipeline ran but returned no items. Check logs.")
            self.status_bar.showMessage("Extraction pipeline finished.", 5000)

    def show_about_dialog(self):
        QMessageBox.about(self, "About Data Extractor Studio",
                          f"{config.APP_NAME} v{config.VERSION}\n\nA visual tool for defining CSS selectors and extracting structured data from websites.")

    def closeEvent(self, event: QCloseEvent):
        self.project_manager.save_projects_to_disk()
        self.selection_poll_timer.stop()
        super().closeEvent(event)