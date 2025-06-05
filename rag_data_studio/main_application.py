# rag_data_studio/main_application.py
"""
RAG Data Studio - ACTUALLY WORKING VERSION
Simple element targeting that doesn't rely on broken Qt WebChannel
"""

import sys
import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWebEngineWidgets import QWebEngineView

# Dark Theme Stylesheet
DARK_THEME = """
QMainWindow, QWidget {
    background-color: #1e1e1e;
    color: #ffffff;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 11px;
}

QGroupBox {
    font-weight: bold;
    border: 2px solid #404040;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 10px;
    background-color: #2d2d2d;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
    color: #4CAF50;
}

QPushButton {
    background-color: #404040;
    border: 1px solid #606060;
    border-radius: 6px;
    padding: 8px 16px;
    color: white;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #505050;
    border-color: #4CAF50;
}

QPushButton:pressed {
    background-color: #303030;
}

QPushButton[class="success"] {
    background-color: #4CAF50;
    border-color: #45a049;
}

QPushButton[class="success"]:hover {
    background-color: #45a049;
}

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #3a3a3a;
    border: 2px solid #555555;
    border-radius: 6px;
    padding: 6px;
    color: white;
    selection-background-color: #4CAF50;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #4CAF50;
}

QComboBox {
    background-color: #3a3a3a;
    border: 2px solid #555555;
    border-radius: 6px;
    padding: 6px;
    color: white;
    min-width: 100px;
}

QComboBox:hover {
    border-color: #4CAF50;
}

QComboBox::drop-down {
    border: none;
    background-color: #505050;
    border-radius: 3px;
}

QComboBox QAbstractItemView {
    background-color: #3a3a3a;
    border: 1px solid #555555;
    selection-background-color: #4CAF50;
    color: white;
}

QTableWidget {
    background-color: #2a2a2a;
    alternate-background-color: #343434;
    gridline-color: #555555;
    border: 1px solid #555555;
    border-radius: 6px;
}

QTableWidget::item:selected {
    background-color: #4CAF50;
    color: white;
}

QHeaderView::section {
    background-color: #404040;
    color: white;
    padding: 8px;
    border: 1px solid #555555;
    font-weight: bold;
}

QListWidget {
    background-color: #2a2a2a;
    border: 1px solid #555555;
    border-radius: 6px;
    padding: 4px;
}

QListWidget::item:selected {
    background-color: #4CAF50;
    color: white;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #555555;
    border-radius: 3px;
    background-color: #3a3a3a;
}

QCheckBox::indicator:checked {
    background-color: #4CAF50;
    border-color: #4CAF50;
}

QStatusBar {
    background-color: #2a2a2a;
    border-top: 1px solid #555555;
    color: #ffffff;
}

QSplitter::handle {
    background-color: #404040;
}
"""


@dataclass
class ScrapingRule:
    """Professional scraping rule with semantic labeling for RAG"""
    id: str
    name: str
    description: str
    selector: str
    extraction_type: str = "text"
    semantic_label: str = "content"
    rag_importance: str = "medium"
    attribute_name: Optional[str] = None
    is_list: bool = False
    data_type: str = "string"
    validation_regex: Optional[str] = None
    transformation: Optional[str] = None
    required: bool = False
    examples: List[str] = None

    def __post_init__(self):
        if self.examples is None:
            self.examples = []


@dataclass
class ProjectConfig:
    """Professional project configuration"""
    id: str
    name: str
    description: str
    domain: str
    target_websites: List[str]
    scraping_rules: List[ScrapingRule]
    output_settings: Dict[str, Any]
    rate_limiting: Dict[str, Any]
    created_at: str
    updated_at: str
    client_info: Optional[Dict[str, str]] = None


class VisualElementTargeter(QWidget):
    """Visual element targeting widget"""

    rule_created = Signal(ScrapingRule)

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.current_selector = ""
        self.current_element_text = ""
        self.current_element_type = ""

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("🎯 Visual Element Targeting")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setStyleSheet("color: #4CAF50; margin: 10px 0;")

        # Current selection display
        selection_group = QGroupBox("Current Selection")
        selection_layout = QFormLayout(selection_group)

        self.selector_display = QLineEdit()
        self.selector_display.setReadOnly(True)
        self.selector_display.setPlaceholderText("Click an element in the browser...")

        self.element_text_display = QTextEdit()
        self.element_text_display.setReadOnly(True)
        self.element_text_display.setMaximumHeight(60)

        selection_layout.addRow("CSS Selector:", self.selector_display)
        selection_layout.addRow("Element Text:", self.element_text_display)

        # Semantic labeling for RAG
        semantic_group = QGroupBox("🧠 RAG Semantic Labeling")
        semantic_layout = QFormLayout(semantic_group)

        self.field_name_input = QLineEdit()
        self.field_name_input.setPlaceholderText("e.g., player_name, ranking_position, match_score")

        self.semantic_label_combo = QComboBox()
        self.semantic_label_combo.setEditable(True)
        self.semantic_label_combo.addItems([
            "entity_name", "entity_ranking", "entity_score", "entity_stats",
            "entity_description", "entity_category", "entity_location",
            "entity_date", "entity_value", "entity_metadata", "content_title",
            "content_body", "content_summary", "data_metric", "data_timestamp"
        ])

        self.rag_importance_combo = QComboBox()
        self.rag_importance_combo.addItems(["low", "medium", "high", "critical"])
        self.rag_importance_combo.setCurrentText("medium")

        self.field_description = QTextEdit()
        self.field_description.setMaximumHeight(60)
        self.field_description.setPlaceholderText("Brief description for RAG context...")

        semantic_layout.addRow("Field Name:", self.field_name_input)
        semantic_layout.addRow("Semantic Label:", self.semantic_label_combo)
        semantic_layout.addRow("RAG Importance:", self.rag_importance_combo)
        semantic_layout.addRow("Description:", self.field_description)

        # Quick label buttons
        quick_layout = QHBoxLayout()
        quick_layout.addWidget(QLabel("Quick Labels:"))

        buttons = [
            ("Name/Title", "entity_name", "high"),
            ("Ranking", "entity_ranking", "high"),
            ("Score", "entity_score", "medium"),
            ("Stats", "entity_stats", "medium"),
            ("Metadata", "entity_metadata", "low")
        ]

        for text, label, importance in buttons:
            btn = QPushButton(text)
            btn.setMaximumHeight(30)
            btn.clicked.connect(lambda checked, l=label, i=importance: self.set_quick_label(l, i))
            quick_layout.addWidget(btn)

        quick_layout.addStretch()

        # Advanced options
        advanced_group = QGroupBox("Advanced Options")
        advanced_layout = QFormLayout(advanced_group)

        self.extraction_type_combo = QComboBox()
        self.extraction_type_combo.addItems(["text", "attribute", "html"])

        self.attribute_input = QLineEdit()
        self.attribute_input.setPlaceholderText("e.g., href, src, data-value")
        self.attribute_input.setEnabled(False)

        self.is_list_check = QCheckBox("Extract as list")
        self.required_check = QCheckBox("Required field")

        advanced_layout.addRow("Extract Type:", self.extraction_type_combo)
        advanced_layout.addRow("Attribute Name:", self.attribute_input)
        advanced_layout.addRow("", self.is_list_check)
        advanced_layout.addRow("", self.required_check)

        # Action buttons
        action_layout = QHBoxLayout()
        self.test_btn = QPushButton("🧪 Test Selector")
        self.test_btn.setEnabled(False)

        self.save_btn = QPushButton("💾 Save Rule")
        self.save_btn.setProperty("class", "success")
        self.save_btn.setEnabled(False)

        action_layout.addWidget(self.test_btn)
        action_layout.addStretch()
        action_layout.addWidget(self.save_btn)

        # Add all components
        layout.addWidget(header)
        layout.addWidget(selection_group)
        layout.addWidget(semantic_group)
        layout.addLayout(quick_layout)
        layout.addWidget(advanced_group)
        layout.addLayout(action_layout)
        layout.addStretch()

        # Connect signals
        self.extraction_type_combo.currentTextChanged.connect(self.on_extraction_type_changed)
        self.save_btn.clicked.connect(self.save_current_rule)
        self.test_btn.clicked.connect(self.test_current_selector)

    def set_quick_label(self, label: str, importance: str):
        """Set quick semantic label and importance"""
        self.semantic_label_combo.setCurrentText(label)
        self.rag_importance_combo.setCurrentText(importance)

        if not self.field_name_input.text():
            field_name = label.replace("entity_", "").replace("content_", "")
            self.field_name_input.setText(field_name)

    def on_extraction_type_changed(self, extraction_type):
        """Enable/disable attribute field"""
        self.attribute_input.setEnabled(extraction_type == "attribute")

    def update_selection(self, selector: str, text: str, element_type: str):
        """Update current selection from browser"""
        print(f"🎯 UPDATING SELECTION: {selector}")

        self.current_selector = selector
        self.current_element_text = text
        self.current_element_type = element_type

        self.selector_display.setText(selector)
        self.element_text_display.setText(text[:200] + "..." if len(text) > 200 else text)

        self.save_btn.setEnabled(True)
        self.test_btn.setEnabled(True)

        # Auto-suggest based on content
        if not self.field_name_input.text() and text:
            clean_text = text.lower().strip()
            if clean_text.isdigit() and int(clean_text) < 100:
                self.set_quick_label("entity_ranking", "high")
            elif clean_text.isdigit():
                self.set_quick_label("entity_score", "medium")
            elif any(char.isalpha() for char in clean_text):
                self.set_quick_label("entity_name", "high")

    def save_current_rule(self):
        """Save current selection as scraping rule"""
        if not self.current_selector or not self.field_name_input.text():
            QMessageBox.warning(self, "Missing Information",
                                "Please select an element and provide a field name.")
            return

        rule = ScrapingRule(
            id=f"rule_{uuid.uuid4().hex[:8]}",
            name=self.field_name_input.text(),
            description=self.field_description.toPlainText() or f"Extracts {self.field_name_input.text()}",
            selector=self.current_selector,
            extraction_type=self.extraction_type_combo.currentText(),
            semantic_label=self.semantic_label_combo.currentText(),
            rag_importance=self.rag_importance_combo.currentText(),
            attribute_name=self.attribute_input.text() if self.attribute_input.isEnabled() else None,
            is_list=self.is_list_check.isChecked(),
            required=self.required_check.isChecked()
        )

        self.rule_created.emit(rule)

        # Clear form
        self.field_name_input.clear()
        self.field_description.clear()
        self.selector_display.clear()
        self.element_text_display.clear()
        self.save_btn.setEnabled(False)
        self.test_btn.setEnabled(False)

        QMessageBox.information(self, "Rule Saved",
                                f"RAG scraping rule '{rule.name}' saved successfully!")

    def test_current_selector(self):
        """Test current selector"""
        if self.current_selector:
            QMessageBox.information(self, "Test Results",
                                    f"Testing: {self.current_selector}\n\n"
                                    f"Sample text: {self.current_element_text[:100]}...")


class InteractiveBrowser(QWebEngineView):
    """Browser with WORKING element targeting - NO COMPLEX QT BULLSHIT"""

    element_selected = Signal(str, str, str)

    def __init__(self):
        super().__init__()
        self.targeting_widget = None
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.check_selection)

    def set_targeting_widget(self, widget):
        self.targeting_widget = widget

    def check_selection(self):
        """Check if user selected an element"""
        check_js = "window._ragSelection || null;"

        def handle_result(result):
            if result:
                print(f"🎯 GOT SELECTION: {result}")
                try:
                    data = json.loads(result) if isinstance(result, str) else result
                    selector = data.get('selector', '')
                    text = data.get('text', '')
                    element_type = data.get('type', '')

                    # Stop polling
                    self.poll_timer.stop()

                    # Clear the selection
                    self.page().runJavaScript("window._ragSelection = null;")

                    # Emit signal
                    self.element_selected.emit(selector, text, element_type)
                    if self.targeting_widget:
                        self.targeting_widget.update_selection(selector, text, element_type)

                except (json.JSONDecodeError, TypeError) as e:
                    print(f"🎯 Parse error: {e}")

        self.page().runJavaScript(check_js, handle_result)

    def enable_selector_mode(self):
        """Enable element selection mode"""
        print("🎯 ENABLING TARGETING")

        js_code = """
        console.log('🎯 Starting targeting mode');

        // Clear any previous selection
        window._ragSelection = null;

        let isSelecting = true;
        let highlighted = null;

        // Create overlay
        let overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(76, 175, 80, 0.1); z-index: 999999;
            pointer-events: none; border: 3px solid #4CAF50;
        `;
        document.body.appendChild(overlay);

        // Create tooltip
        let tooltip = document.createElement('div');
        tooltip.style.cssText = `
            position: fixed; top: 20px; right: 20px;
            background: #4CAF50; color: white; padding: 10px 15px;
            border-radius: 6px; z-index: 1000000; font-family: Arial;
            font-size: 14px; font-weight: bold;
        `;
        tooltip.textContent = '🎯 Click any element to create scraping rule';
        document.body.appendChild(tooltip);

        function highlight(element) {
            // Remove previous highlight
            if (highlighted) {
                highlighted.style.outline = '';
                highlighted.style.backgroundColor = '';
            }
            // Add new highlight
            element.style.outline = '3px solid #FF5722';
            element.style.backgroundColor = 'rgba(255, 87, 34, 0.1)';
            highlighted = element;
        }

        function makeSelector(element) {
            // Simple selector generation that actually works
            if (element.id) {
                return '#' + element.id;
            }

            let selector = element.tagName.toLowerCase();

            // Add classes if they exist
            if (element.className && element.className.trim()) {
                let classes = element.className.trim().split(/\\s+/).slice(0, 2);
                selector += '.' + classes.join('.');
            }

            return selector;
        }

        // Add event listeners
        document.addEventListener('mouseover', function(e) {
            if (isSelecting) {
                e.preventDefault();
                e.stopPropagation();
                highlight(e.target);
            }
        }, true);

        document.addEventListener('click', function(e) {
            if (isSelecting) {
                console.log('🎯 Element clicked:', e.target);
                e.preventDefault();
                e.stopPropagation();

                let selector = makeSelector(e.target);
                let text = e.target.textContent.trim();
                let elementType = e.target.tagName.toLowerCase();

                console.log('🎯 Generated selector:', selector);
                console.log('🎯 Element text:', text.substring(0, 50));

                // Store selection data
                window._ragSelection = JSON.stringify({
                    selector: selector,
                    text: text,
                    type: elementType
                });

                // Clean up
                isSelecting = false;
                if (highlighted) {
                    highlighted.style.outline = '';
                    highlighted.style.backgroundColor = '';
                }
                overlay.remove();
                tooltip.remove();

                console.log('🎯 Selection stored');
            }
        }, true);

        console.log('🎯 Event listeners attached');
        """

        self.page().runJavaScript(js_code)
        self.poll_timer.start(500)  # Check every 500ms

    def disable_selector_mode(self):
        """Disable targeting mode"""
        self.poll_timer.stop()
        cleanup_js = "window._ragSelection = null;"
        self.page().runJavaScript(cleanup_js)


class ProjectManager(QWidget):
    """Project management panel"""

    project_selected = Signal(ProjectConfig)

    def __init__(self):
        super().__init__()
        self.projects = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("📁 Projects")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setStyleSheet("color: #4CAF50; margin: 10px 0;")

        # Project list
        self.project_list = QListWidget()
        self.project_list.itemClicked.connect(self.on_project_selected)

        # Actions
        actions_layout = QHBoxLayout()
        self.new_btn = QPushButton("➕ New")
        self.edit_btn = QPushButton("✏️ Edit")
        self.delete_btn = QPushButton("🗑️ Delete")

        for btn in [self.new_btn, self.edit_btn, self.delete_btn]:
            btn.setMaximumHeight(35)
            actions_layout.addWidget(btn)

        # Add components
        layout.addWidget(header)
        layout.addWidget(self.project_list)
        layout.addLayout(actions_layout)

        # Connect signals
        self.new_btn.clicked.connect(self.create_new_project)

    def create_new_project(self):
        """Create new project"""
        dialog = ProjectDialog(self)
        if dialog.exec() == QDialog.Accepted:
            project = dialog.get_project_config()
            self.projects.append(project)
            self.refresh_project_list()

    def refresh_project_list(self):
        """Refresh project list"""
        self.project_list.clear()
        for project in self.projects:
            item = QListWidgetItem(f"{project.name} ({project.domain})")
            item.setData(Qt.UserRole, project)
            self.project_list.addItem(item)

    def on_project_selected(self, item):
        """Handle project selection"""
        project = item.data(Qt.UserRole)
        self.project_selected.emit(project)


class ProjectDialog(QDialog):
    """Project creation dialog"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Project")
        self.setModal(True)
        self.resize(500, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Form
        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)

        self.domain_combo = QComboBox()
        self.domain_combo.setEditable(True)
        self.domain_combo.addItems([
            "sports", "finance", "legal", "medical", "e-commerce",
            "real-estate", "news", "research", "education", "technology"
        ])

        self.websites_input = QTextEdit()
        self.websites_input.setPlaceholderText("Enter target websites, one per line")
        self.websites_input.setMaximumHeight(100)

        form_layout.addRow("Project Name:", self.name_input)
        form_layout.addRow("Description:", self.description_input)
        form_layout.addRow("Domain:", self.domain_combo)
        form_layout.addRow("Target Websites:", self.websites_input)

        # Buttons
        button_layout = QHBoxLayout()
        self.ok_btn = QPushButton("Create Project")
        self.ok_btn.setProperty("class", "success")
        self.cancel_btn = QPushButton("Cancel")

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.ok_btn)

        layout.addLayout(form_layout)
        layout.addLayout(button_layout)

        # Connect signals
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def get_project_config(self) -> ProjectConfig:
        """Get project configuration"""
        websites = [line.strip() for line in self.websites_input.toPlainText().split('\n') if line.strip()]

        return ProjectConfig(
            id=f"project_{uuid.uuid4().hex[:8]}",
            name=self.name_input.text(),
            description=self.description_input.toPlainText(),
            domain=self.domain_combo.currentText(),
            target_websites=websites,
            scraping_rules=[],
            output_settings={"format": "jsonl", "include_metadata": True},
            rate_limiting={"delay": 2.0, "respect_robots": True},
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )


class RulesManager(QWidget):
    """Manage scraping rules"""

    def __init__(self):
        super().__init__()
        self.current_rules = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("📋 Scraping Rules")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setStyleSheet("color: #4CAF50; margin: 10px 0;")

        # Rules table
        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(4)
        self.rules_table.setHorizontalHeaderLabels(["Name", "Semantic Label", "Importance", "Selector"])

        # Actions
        actions_layout = QHBoxLayout()
        self.test_all_btn = QPushButton("🧪 Test All")
        self.export_btn = QPushButton("💾 Export Config")
        self.run_scrape_btn = QPushButton("🚀 Run Scrape")
        self.run_scrape_btn.setProperty("class", "success")

        actions_layout.addWidget(self.test_all_btn)
        actions_layout.addWidget(self.export_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(self.run_scrape_btn)

        layout.addWidget(header)
        layout.addWidget(self.rules_table)
        layout.addLayout(actions_layout)

    def add_rule(self, rule: ScrapingRule):
        """Add rule to display"""
        self.current_rules.append(rule)
        self.refresh_rules_table()

    def refresh_rules_table(self):
        """Refresh rules table"""
        self.rules_table.setRowCount(len(self.current_rules))

        for row, rule in enumerate(self.current_rules):
            self.rules_table.setItem(row, 0, QTableWidgetItem(rule.name))
            self.rules_table.setItem(row, 1, QTableWidgetItem(rule.semantic_label))
            self.rules_table.setItem(row, 2, QTableWidgetItem(rule.rag_importance))
            self.rules_table.setItem(row, 3, QTableWidgetItem(rule.selector[:50] + "..."))

        self.rules_table.resizeColumnsToContents()


class RAGDataStudio(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.current_project = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("RAG Data Studio - Professional Scraping Platform")
        self.setGeometry(100, 100, 1600, 1000)

        # Apply dark theme
        self.setStyleSheet(DARK_THEME)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout with splitters
        main_layout = QHBoxLayout(central_widget)
        main_splitter = QSplitter(Qt.Horizontal)

        # Left panel - Projects
        self.project_manager = ProjectManager()
        self.project_manager.setMaximumWidth(300)
        main_splitter.addWidget(self.project_manager)

        # Center panel - Browser and controls
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)

        # Browser toolbar
        toolbar_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter URL to analyze...")

        self.load_btn = QPushButton("🌐 Load")
        self.selector_btn = QPushButton("🎯 Target Elements")
        self.selector_btn.setProperty("class", "success")

        toolbar_layout.addWidget(QLabel("URL:"))
        toolbar_layout.addWidget(self.url_input)
        toolbar_layout.addWidget(self.load_btn)
        toolbar_layout.addWidget(self.selector_btn)

        # Browser
        self.browser = InteractiveBrowser()

        center_layout.addLayout(toolbar_layout)
        center_layout.addWidget(self.browser)

        main_splitter.addWidget(center_widget)

        # Right panel - Targeting and rules
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Element targeter
        self.element_targeter = VisualElementTargeter()

        # Rules manager
        self.rules_manager = RulesManager()

        # Right splitter
        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.addWidget(self.element_targeter)
        right_splitter.addWidget(self.rules_manager)
        right_splitter.setSizes([400, 300])

        right_layout.addWidget(right_splitter)
        right_widget.setMaximumWidth(450)
        main_splitter.addWidget(right_widget)

        # Set splitter proportions
        main_splitter.setSizes([280, 870, 450])
        main_layout.addWidget(main_splitter)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Create a project and start building scrapers")

        # Menu bar
        self.create_menu_bar()

        # Connect signals
        self.load_btn.clicked.connect(self.load_page)
        self.selector_btn.clicked.connect(self.toggle_selector_mode)
        self.project_manager.project_selected.connect(self.load_project)
        self.element_targeter.rule_created.connect(self.add_rule_to_project)
        self.browser.set_targeting_widget(self.element_targeter)

    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('File')
        new_action = QAction('New Project', self)
        new_action.triggered.connect(self.project_manager.create_new_project)
        file_menu.addAction(new_action)

        file_menu.addSeparator()
        export_action = QAction('Export Configuration', self)
        export_action.triggered.connect(self.export_configuration)
        file_menu.addAction(export_action)

        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        test_action = QAction('Test All Rules', self)
        test_action.triggered.connect(self.test_all_rules)
        tools_menu.addAction(test_action)

        scrape_action = QAction('Run Scraping Pipeline', self)
        scrape_action.triggered.connect(self.run_scraping_pipeline)
        tools_menu.addAction(scrape_action)

        # Help menu
        help_menu = menubar.addMenu('Help')
        about_action = QAction('About RAG Data Studio', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def load_page(self):
        """Load page in browser"""
        url = self.url_input.text().strip()
        if url:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            self.browser.load(QUrl(url))
            self.status_bar.showMessage(f"Loading: {url}")

    def toggle_selector_mode(self):
        """Toggle visual element targeting mode"""
        if self.selector_btn.text() == "🎯 Target Elements":
            self.browser.enable_selector_mode()
            self.selector_btn.setText("❌ Stop Targeting")
            self.selector_btn.setProperty("class", "")
            self.selector_btn.style().unpolish(self.selector_btn)
            self.selector_btn.style().polish(self.selector_btn)
            self.status_bar.showMessage("🎯 Targeting mode enabled - Click elements to create scraping rules")
        else:
            self.browser.disable_selector_mode()
            self.selector_btn.setText("🎯 Target Elements")
            self.selector_btn.setProperty("class", "success")
            self.selector_btn.style().unpolish(self.selector_btn)
            self.selector_btn.style().polish(self.selector_btn)
            self.status_bar.showMessage("Targeting mode disabled")

    def load_project(self, project: ProjectConfig):
        """Load selected project"""
        self.current_project = project
        self.rules_manager.current_rules = project.scraping_rules.copy()
        self.rules_manager.refresh_rules_table()

        if project.target_websites:
            self.url_input.setText(project.target_websites[0])

        self.status_bar.showMessage(f"Loaded project: {project.name} ({len(project.scraping_rules)} rules)")

    def add_rule_to_project(self, rule: ScrapingRule):
        """Add new rule to current project"""
        if not self.current_project:
            QMessageBox.warning(self, "No Project", "Please select or create a project first.")
            return

        self.current_project.scraping_rules.append(rule)
        self.current_project.updated_at = datetime.now().isoformat()

        self.rules_manager.add_rule(rule)
        self.status_bar.showMessage(f"Added rule: {rule.name} ({rule.semantic_label})")

    def export_configuration(self):
        """Export current project as YAML configuration"""
        if not self.current_project:
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Configuration",
            f"{self.current_project.name.lower().replace(' ', '_')}_config.yaml",
            "YAML files (*.yaml *.yml)"
        )

        if filename:
            config_data = self.convert_to_yaml_format(self.current_project)

            import yaml
            with open(filename, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)

            QMessageBox.information(self, "Export Complete",
                                    f"Configuration exported to {filename}")

    def convert_to_yaml_format(self, project: ProjectConfig) -> dict:
        """Convert project to YAML configuration format"""
        return {
            "domain_info": {
                "name": project.name,
                "description": project.description,
                "domain": project.domain,
                "created_at": project.created_at
            },
            "global_user_agent": f"RAGScraper/{project.name}",
            "sources": [{
                "name": project.name.lower().replace(' ', '_'),
                "seeds": project.target_websites,
                "source_type": project.domain,
                "selectors": {
                    "custom_fields": [
                        {
                            "name": rule.name,
                            "selector": rule.selector,
                            "extract_type": rule.extraction_type,
                            "attribute_name": rule.attribute_name,
                            "is_list": rule.is_list,
                            "semantic_label": rule.semantic_label,
                            "rag_importance": rule.rag_importance,
                            "required": rule.required
                        } for rule in project.scraping_rules
                    ]
                },
                "crawl": {
                    "depth": 1,
                    "delay_seconds": project.rate_limiting.get("delay", 2.0),
                    "respect_robots_txt": project.rate_limiting.get("respect_robots", True)
                },
                "export": {
                    "format": project.output_settings.get("format", "jsonl"),
                    "output_path": f"./data_exports/{project.domain}/{project.name.lower().replace(' ', '_')}.jsonl"
                }
            }]
        }

    def test_all_rules(self):
        """Test all rules against current page"""
        if not self.current_project or not self.current_project.scraping_rules:
            QMessageBox.warning(self, "No Rules", "Please create some scraping rules first.")
            return

        QMessageBox.information(self, "Testing",
                                f"Testing {len(self.current_project.scraping_rules)} rules against current page...")

    def run_scraping_pipeline(self):
        """Run the full scraping pipeline"""
        if not self.current_project:
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return

        reply = QMessageBox.question(self, "Run Scraper",
                                     f"Run scraping pipeline for project '{self.current_project.name}'?\n\n"
                                     f"Target websites: {len(self.current_project.target_websites)}\n"
                                     f"Scraping rules: {len(self.current_project.scraping_rules)}")

        if reply == QMessageBox.Yes:
            self.status_bar.showMessage("🚀 Starting scraping pipeline...")

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About RAG Data Studio",
                          "RAG Data Studio v1.0\n\n"
                          "Professional Visual Scraping Platform\n"
                          "for RAG and AI Agent Development\n\n"
                          "Build custom scrapers with semantic labeling\n"
                          "for optimal RAG ingestion across any domain.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("RAG Data Studio")
    app.setStyle("Fusion")

    window = RAGDataStudio()
    window.show()

    sys.exit(app.exec())