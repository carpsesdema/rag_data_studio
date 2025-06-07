# rag_data_studio/main_application.py
"""
RAG Data Studio - Clean & Simple Visual Scraper Builder
Apple-style simplicity, wired to your backend scraper
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
    """Simple scraping rule - matches your backend exactly"""
    id: str
    name: str
    description: str
    selector: str
    extract_type: str = "text"
    attribute_name: Optional[str] = None
    is_list: bool = False
    required: bool = False


@dataclass
class ProjectConfig:
    """Simple project configuration"""
    id: str
    name: str
    description: str
    domain: str
    target_websites: List[str]
    scraping_rules: List[ScrapingRule]
    created_at: str
    updated_at: str


class RuleEditDialog(QDialog):
    """Dialog for editing scraping rules"""

    def __init__(self, rule: ScrapingRule, parent=None):
        super().__init__(parent)
        self.rule = rule
        self.setWindowTitle(f"Edit Rule: {rule.name}")
        self.setModal(True)
        self.resize(500, 400)
        self.init_ui()
        self.load_rule_data()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Form
        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.description_input = QLineEdit()
        self.selector_input = QLineEdit()

        self.extract_type_combo = QComboBox()
        self.extract_type_combo.addItems(["text", "attribute", "html"])

        self.attribute_input = QLineEdit()
        self.attribute_input.setPlaceholderText("e.g., href, src, data-value")

        self.is_list_check = QCheckBox("Extract as list")
        self.required_check = QCheckBox("Required field")

        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Description:", self.description_input)
        form_layout.addRow("Selector:", self.selector_input)
        form_layout.addRow("Extract Type:", self.extract_type_combo)
        form_layout.addRow("Attribute Name:", self.attribute_input)
        form_layout.addRow("", self.is_list_check)
        form_layout.addRow("", self.required_check)

        # Buttons
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 Save Changes")
        self.save_btn.setProperty("class", "success")
        self.cancel_btn = QPushButton("Cancel")

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)

        layout.addLayout(form_layout)
        layout.addLayout(button_layout)

        # Connect signals
        self.save_btn.clicked.connect(self.save_changes)
        self.cancel_btn.clicked.connect(self.reject)
        self.extract_type_combo.currentTextChanged.connect(self.on_extract_type_changed)

    def load_rule_data(self):
        """Load current rule data into form"""
        self.name_input.setText(self.rule.name)
        self.description_input.setText(self.rule.description)
        self.selector_input.setText(self.rule.selector)
        self.extract_type_combo.setCurrentText(self.rule.extract_type)
        self.attribute_input.setText(self.rule.attribute_name or "")
        self.is_list_check.setChecked(self.rule.is_list)
        self.required_check.setChecked(self.rule.required)
        self.on_extract_type_changed(self.rule.extract_type)

    def on_extract_type_changed(self, extract_type):
        """Enable/disable attribute field"""
        self.attribute_input.setEnabled(extract_type == "attribute")

    def save_changes(self):
        """Save changes to rule"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Missing Name", "Please provide a rule name.")
            return

        self.rule.name = self.name_input.text().strip()
        self.rule.description = self.description_input.text().strip()
        self.rule.selector = self.selector_input.text().strip()
        self.rule.extract_type = self.extract_type_combo.currentText()
        self.rule.attribute_name = self.attribute_input.text().strip() if self.attribute_input.isEnabled() else None
        self.rule.is_list = self.is_list_check.isChecked()
        self.rule.required = self.required_check.isChecked()

        self.accept()

    def get_updated_rule(self) -> ScrapingRule:
        """Get the updated rule"""
        return self.rule


class VisualElementTargeter(QWidget):
    """Clean, simple element targeting - Apple-style"""

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
        header = QLabel("🎯 Smart Element Targeting")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setStyleSheet("color: #4CAF50; margin: 10px 0;")

        # Current selection
        selection_group = QGroupBox("Current Selection")
        selection_layout = QFormLayout(selection_group)

        self.selector_display = QLineEdit()
        self.selector_display.setReadOnly(True)
        self.selector_display.setPlaceholderText("Click an element in the browser...")

        self.element_text_display = QTextEdit()
        self.element_text_display.setReadOnly(True)
        self.element_text_display.setMaximumHeight(60)

        self.smart_suggestions = QLabel()
        self.smart_suggestions.setStyleSheet("color: #4CAF50; font-weight: bold; padding: 5px;")
        self.smart_suggestions.setWordWrap(True)

        selection_layout.addRow("CSS Selector:", self.selector_display)
        selection_layout.addRow("Element Text:", self.element_text_display)
        selection_layout.addRow("AI Suggestion:", self.smart_suggestions)

        # Simple field definition
        field_group = QGroupBox("🏷️ Field Definition")
        field_layout = QFormLayout(field_group)

        self.field_name_input = QLineEdit()
        self.field_name_input.setPlaceholderText("e.g., player_name, ranking_position")

        self.field_description = QLineEdit()
        self.field_description.setPlaceholderText("Brief description...")

        field_layout.addRow("Field Name:", self.field_name_input)
        field_layout.addRow("Description:", self.field_description)

        # Smart actions
        pattern_group = QGroupBox("🔍 Smart Actions")
        pattern_layout = QVBoxLayout(pattern_group)

        self.bulk_extract_btn = QPushButton("📋 Extract All Similar Items")
        self.bulk_extract_btn.setEnabled(False)
        self.bulk_extract_btn.clicked.connect(self.create_bulk_extraction)

        self.container_select_btn = QPushButton("📦 Select Parent Container")
        self.container_select_btn.setEnabled(False)
        self.container_select_btn.clicked.connect(self.select_container)

        pattern_layout.addWidget(self.bulk_extract_btn)
        pattern_layout.addWidget(self.container_select_btn)

        # Options
        options_group = QGroupBox("Options")
        options_layout = QFormLayout(options_group)

        self.extraction_type_combo = QComboBox()
        self.extraction_type_combo.addItems(["text", "attribute", "html"])

        self.attribute_input = QLineEdit()
        self.attribute_input.setPlaceholderText("e.g., href, src, data-value")
        self.attribute_input.setEnabled(False)

        self.is_list_check = QCheckBox("Extract as list")
        self.required_check = QCheckBox("Required field")

        options_layout.addRow("Extract Type:", self.extraction_type_combo)
        options_layout.addRow("Attribute Name:", self.attribute_input)
        options_layout.addRow("", self.is_list_check)
        options_layout.addRow("", self.required_check)

        # Action buttons
        action_layout = QHBoxLayout()
        self.test_btn = QPushButton("🧪 Test")
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
        layout.addWidget(field_group)
        layout.addWidget(pattern_group)
        layout.addWidget(options_group)
        layout.addLayout(action_layout)
        layout.addStretch()

        # Connect signals
        self.extraction_type_combo.currentTextChanged.connect(self.on_extraction_type_changed)
        self.save_btn.clicked.connect(self.save_current_rule)
        self.test_btn.clicked.connect(self.test_current_selector)

    def detect_content_type(self, text: str, element_type: str, selector: str) -> dict:
        """Simple content detection"""
        text = text.strip().lower()

        # Name detection
        if any(pattern in text for pattern in ['. ', ' jr', ' sr', ' iii']) or \
                (len(text.split()) >= 2 and text.replace(' ', '').replace('.', '').isalpha()):
            return {
                'type': 'person_name',
                'suggested_field': 'player_name' if 'rank' in selector else 'person_name'
            }

        # Ranking detection
        if text.isdigit() and int(text) <= 1000 and ('rank' in selector or 'position' in selector):
            return {
                'type': 'ranking',
                'suggested_field': 'ranking_position'
            }

        # Score/Points detection
        if text.replace(',', '').replace('.', '').isdigit() and len(text) >= 3:
            return {
                'type': 'score',
                'suggested_field': 'points' if 'point' in selector else 'score'
            }

        # Default
        return {
            'type': 'text',
            'suggested_field': 'data_field'
        }

    def detect_container_pattern(self, selector: str) -> dict:
        """Detect if this is part of a repeating pattern"""
        patterns = {
            'table_row': 'tr' in selector or 'tbody' in selector,
            'list_item': 'li' in selector or 'ul' in selector or 'ol' in selector,
            'card': 'card' in selector or 'item' in selector,
            'grid': 'grid' in selector or 'col' in selector
        }

        for pattern_type, detected in patterns.items():
            if detected:
                return {
                    'type': pattern_type,
                    'bulk_possible': True,
                    'container_suggestion': f"Extract all {pattern_type.replace('_', ' ')}s"
                }

        return {'type': 'single', 'bulk_possible': False}

    def update_selection(self, selector: str, text: str, element_type: str):
        """Enhanced selection with smart detection"""
        self.current_selector = selector
        self.current_element_text = text
        self.current_element_type = element_type

        self.selector_display.setText(selector)
        self.element_text_display.setText(text[:200] + "..." if len(text) > 200 else text)

        # Smart content detection
        content_info = self.detect_content_type(text, element_type, selector)
        pattern_info = self.detect_container_pattern(selector)

        # Update suggestions
        suggestion_text = f"🧠 Detected: {content_info['type'].replace('_', ' ').title()}"
        if pattern_info['bulk_possible']:
            suggestion_text += f" | 📋 {pattern_info['container_suggestion']}"

        self.smart_suggestions.setText(suggestion_text)

        # Auto-fill fields
        self.field_name_input.setText(content_info['suggested_field'])

        # Enable buttons
        self.save_btn.setEnabled(True)
        self.test_btn.setEnabled(True)
        self.bulk_extract_btn.setEnabled(pattern_info['bulk_possible'])
        self.container_select_btn.setEnabled(True)

    def create_bulk_extraction(self):
        """Create structured list extraction for similar items"""
        reply = QMessageBox.question(self, "Bulk Extraction",
                                     f"Create a structured list to extract all similar items?\n\n"
                                     f"This will capture multiple records with the same pattern.")

        if reply == QMessageBox.Yes:
            rule = ScrapingRule(
                id=f"bulk_rule_{uuid.uuid4().hex[:8]}",
                name=f"{self.field_name_input.text()}_list",
                description=f"Bulk extraction of {self.field_name_input.text()} data",
                selector=self.suggest_container_selector(),
                extract_type="structured_list",
                is_list=True
            )

            self.rule_created.emit(rule)
            QMessageBox.information(self, "Bulk Rule Created",
                                    f"Created structured list rule: {rule.name}")

    def select_container(self):
        """Select parent container of current element"""
        container_selector = self.suggest_container_selector()
        self.selector_display.setText(container_selector)
        self.current_selector = container_selector

    def suggest_container_selector(self) -> str:
        """Suggest container selector based on current selection"""
        if 'td' in self.current_selector:
            return self.current_selector.replace('td', 'tr').split(' td')[0] + ' tr'
        elif 'li' in self.current_selector:
            return self.current_selector.replace('li', 'ul li').split(' li')[0] + ' li'
        else:
            return self.current_selector

    def on_extraction_type_changed(self, extraction_type):
        """Enable/disable attribute field"""
        self.attribute_input.setEnabled(extraction_type == "attribute")

    def save_current_rule(self):
        """Save current selection as scraping rule"""
        if not self.current_selector or not self.field_name_input.text():
            QMessageBox.warning(self, "Missing Information",
                                "Please select an element and provide a field name.")
            return

        rule = ScrapingRule(
            id=f"rule_{uuid.uuid4().hex[:8]}",
            name=self.field_name_input.text(),
            description=self.field_description.text() or f"Extracts {self.field_name_input.text()}",
            selector=self.current_selector,
            extract_type=self.extraction_type_combo.currentText(),
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
        self.smart_suggestions.clear()
        self.save_btn.setEnabled(False)
        self.test_btn.setEnabled(False)
        self.bulk_extract_btn.setEnabled(False)

        QMessageBox.information(self, "Rule Saved", f"Saved: {rule.name}")

    def test_current_selector(self):
        """Test current selector"""
        if self.current_selector:
            QMessageBox.information(self, "Test Results",
                                    f"Testing: {self.current_selector}\n\n"
                                    f"Sample text: {self.current_element_text[:100]}...")


class InteractiveBrowser(QWebEngineView):
    """Browser with smart element targeting"""

    element_selected = Signal(str, str, str)

    def __init__(self):
        super().__init__()
        self.targeting_widget = None
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.check_selection)
        self.is_targeting_active = False

    def set_targeting_widget(self, widget):
        self.targeting_widget = widget

    def check_selection(self):
        """Check if user selected an element"""
        check_js = "window._ragSelection || null;"

        def handle_result(result):
            if result:
                try:
                    data = json.loads(result) if isinstance(result, str) else result
                    selector = data.get('selector', '')
                    text = data.get('text', '')
                    element_type = data.get('type', '')

                    self.poll_timer.stop()
                    self.page().runJavaScript("window._ragSelection = null;")

                    self.element_selected.emit(selector, text, element_type)
                    if self.targeting_widget:
                        self.targeting_widget.update_selection(selector, text, element_type)

                except (json.JSONDecodeError, TypeError) as e:
                    print(f"🎯 Parse error: {e}")

        self.page().runJavaScript(check_js, handle_result)

    def enable_selector_mode(self):
        """Enable element selection mode with proper cleanup"""
        if self.is_targeting_active:
            return  # Already active, don't double-inject

        self.is_targeting_active = True

        js_code = """
        // Clean up any existing targeting
        if (window._ragTargetingCleanup) {
            window._ragTargetingCleanup();
        }

        console.log('🎯 Starting smart targeting mode');
        window._ragSelection = null;

        let isSelecting = true;
        let highlighted = null;
        let overlay = null;
        let tooltip = null;

        // Create overlay
        overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(76, 175, 80, 0.1); z-index: 999999;
            pointer-events: none; border: 3px solid #4CAF50;
        `;
        document.body.appendChild(overlay);

        // Create tooltip
        tooltip = document.createElement('div');
        tooltip.style.cssText = `
            position: fixed; top: 20px; right: 20px;
            background: #4CAF50; color: white; padding: 10px 15px;
            border-radius: 6px; z-index: 1000000; font-family: Arial;
            font-size: 14px; font-weight: bold;
        `;
        tooltip.textContent = '🎯 Click any element to create scraping rule';
        document.body.appendChild(tooltip);

        function highlight(element) {
            if (highlighted) {
                highlighted.style.outline = '';
                highlighted.style.backgroundColor = '';
            }
            element.style.outline = '3px solid #FF5722';
            element.style.backgroundColor = 'rgba(255, 87, 34, 0.1)';
            highlighted = element;
        }

        function makeSmartSelector(element) {
            if (element.id) {
                return '#' + element.id;
            }

            let selector = element.tagName.toLowerCase();

            // For table cells, include the row context
            if (selector === 'td') {
                let row = element.closest('tr');
                if (row) {
                    let cellIndex = Array.from(row.children).indexOf(element);
                    selector = `tr td:nth-child(${cellIndex + 1})`;
                }
            }

            // For list items
            if (selector === 'li') {
                let list = element.closest('ul, ol');
                if (list) {
                    selector = `${list.tagName.toLowerCase()} li`;
                }
            }

            // Add specific classes if they exist
            if (element.className && element.className.trim()) {
                let classes = element.className.trim().split(/\\s+/)
                    .filter(cls => !['active', 'selected', 'hover', 'focus'].includes(cls))
                    .slice(0, 2);
                if (classes.length > 0) {
                    selector += '.' + classes.join('.');
                }
            }

            return selector;
        }

        // Event handlers
        function handleMouseOver(e) {
            if (isSelecting) {
                e.preventDefault();
                e.stopPropagation();
                highlight(e.target);
            }
        }

        function handleClick(e) {
            if (isSelecting) {
                e.preventDefault();
                e.stopPropagation();

                let selector = makeSmartSelector(e.target);
                let text = e.target.textContent.trim();
                let elementType = e.target.tagName.toLowerCase();

                window._ragSelection = JSON.stringify({
                    selector: selector,
                    text: text,
                    type: elementType
                });

                cleanup();
            }
        }

        function cleanup() {
            isSelecting = false;
            if (highlighted) {
                highlighted.style.outline = '';
                highlighted.style.backgroundColor = '';
            }
            if (overlay) overlay.remove();
            if (tooltip) tooltip.remove();

            document.removeEventListener('mouseover', handleMouseOver, true);
            document.removeEventListener('click', handleClick, true);
        }

        // Store cleanup function globally
        window._ragTargetingCleanup = cleanup;

        // Add event listeners
        document.addEventListener('mouseover', handleMouseOver, true);
        document.addEventListener('click', handleClick, true);
        """

        self.page().runJavaScript(js_code)
        self.poll_timer.start(500)

    def disable_selector_mode(self):
        """Disable targeting mode"""
        self.is_targeting_active = False
        self.poll_timer.stop()
        cleanup_js = """
        if (window._ragTargetingCleanup) {
            window._ragTargetingCleanup();
        }
        window._ragSelection = null;
        """
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

        header = QLabel("📁 Projects")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setStyleSheet("color: #4CAF50; margin: 10px 0;")

        self.project_list = QListWidget()
        self.project_list.itemClicked.connect(self.on_project_selected)

        actions_layout = QHBoxLayout()
        self.new_btn = QPushButton("➕ New")
        self.edit_btn = QPushButton("✏️ Edit")
        self.delete_btn = QPushButton("🗑️ Delete")

        for btn in [self.new_btn, self.edit_btn, self.delete_btn]:
            btn.setMaximumHeight(35)
            actions_layout.addWidget(btn)

        layout.addWidget(header)
        layout.addWidget(self.project_list)
        layout.addLayout(actions_layout)

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
    """Project creation dialog - FIXED VERSION"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Project")
        self.setModal(True)
        self.resize(500, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
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

        button_layout = QHBoxLayout()
        self.ok_btn = QPushButton("Create Project")
        self.ok_btn.setProperty("class", "success")
        self.cancel_btn = QPushButton("Cancel")

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.ok_btn)

        layout.addLayout(form_layout)
        layout.addLayout(button_layout)

        # FIXED: Connect signals properly
        self.ok_btn.clicked.connect(self.validate_and_accept)
        self.cancel_btn.clicked.connect(self.reject)

    def validate_and_accept(self):
        """Validate form before accepting"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Missing Name", "Please enter a project name.")
            return

        if not self.websites_input.toPlainText().strip():
            QMessageBox.warning(self, "Missing Websites", "Please enter at least one target website.")
            return

        self.accept()

    def get_project_config(self) -> ProjectConfig:
        """Get project configuration"""
        websites = [line.strip() for line in self.websites_input.toPlainText().split('\n') if line.strip()]

        return ProjectConfig(
            id=f"project_{uuid.uuid4().hex[:8]}",
            name=self.name_input.text().strip(),
            description=self.description_input.toPlainText().strip(),
            domain=self.domain_combo.currentText(),
            target_websites=websites,
            scraping_rules=[],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )


class RulesManager(QWidget):
    """Manage scraping rules with edit/delete functionality"""

    rule_updated = Signal(ScrapingRule)
    rule_deleted = Signal(str)  # rule_id

    def __init__(self):
        super().__init__()
        self.current_rules = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel("📋 Scraping Rules")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setStyleSheet("color: #4CAF50; margin: 10px 0;")

        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(3)
        self.rules_table.setHorizontalHeaderLabels(["Name", "Type", "Selector"])
        self.rules_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        # Rule actions
        rule_actions_layout = QHBoxLayout()
        self.edit_rule_btn = QPushButton("✏️ Edit Rule")
        self.delete_rule_btn = QPushButton("🗑️ Delete Rule")
        self.edit_rule_btn.setEnabled(False)
        self.delete_rule_btn.setEnabled(False)

        rule_actions_layout.addWidget(self.edit_rule_btn)
        rule_actions_layout.addWidget(self.delete_rule_btn)
        rule_actions_layout.addStretch()

        # Export actions
        export_actions_layout = QHBoxLayout()
        self.test_all_btn = QPushButton("🧪 Test All")
        self.export_btn = QPushButton("💾 Export Config")
        self.run_scrape_btn = QPushButton("🚀 Run Scraper")
        self.run_scrape_btn.setProperty("class", "success")

        export_actions_layout.addWidget(self.test_all_btn)
        export_actions_layout.addWidget(self.export_btn)
        export_actions_layout.addStretch()
        export_actions_layout.addWidget(self.run_scrape_btn)

        layout.addWidget(header)
        layout.addWidget(self.rules_table)
        layout.addLayout(rule_actions_layout)
        layout.addLayout(export_actions_layout)

        # Connect signals
        self.rules_table.selectionModel().selectionChanged.connect(self.on_rule_selected)
        self.edit_rule_btn.clicked.connect(self.edit_selected_rule)
        self.delete_rule_btn.clicked.connect(self.delete_selected_rule)
        self.export_btn.clicked.connect(self.export_config)

    def on_rule_selected(self):
        """Handle rule selection"""
        selected_rows = self.rules_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        self.edit_rule_btn.setEnabled(has_selection)
        self.delete_rule_btn.setEnabled(has_selection)

    def edit_selected_rule(self):
        """Edit the selected rule"""
        selected_rows = self.rules_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        if 0 <= row < len(self.current_rules):
            rule = self.current_rules[row]
            dialog = RuleEditDialog(rule, self)
            if dialog.exec() == QDialog.Accepted:
                updated_rule = dialog.get_updated_rule()
                self.current_rules[row] = updated_rule
                self.refresh_rules_table()
                self.rule_updated.emit(updated_rule)

                # Update in parent project
                main_window = self.window()
                if hasattr(main_window, 'current_project') and main_window.current_project:
                    for i, project_rule in enumerate(main_window.current_project.scraping_rules):
                        if project_rule.id == updated_rule.id:
                            main_window.current_project.scraping_rules[i] = updated_rule
                            break

    def delete_selected_rule(self):
        """Delete the selected rule"""
        selected_rows = self.rules_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        if 0 <= row < len(self.current_rules):
            rule = self.current_rules[row]

            reply = QMessageBox.question(self, "Delete Rule",
                                         f"Are you sure you want to delete the rule '{rule.name}'?",
                                         QMessageBox.Yes | QMessageBox.No)

            if reply == QMessageBox.Yes:
                removed_rule = self.current_rules.pop(row)
                self.refresh_rules_table()
                self.rule_deleted.emit(removed_rule.id)

                # Remove from parent project
                main_window = self.window()
                if hasattr(main_window, 'current_project') and main_window.current_project:
                    main_window.current_project.scraping_rules = [
                        r for r in main_window.current_project.scraping_rules
                        if r.id != removed_rule.id
                    ]

    def add_rule(self, rule: ScrapingRule):
        """Add rule to display"""
        self.current_rules.append(rule)
        self.refresh_rules_table()

    def refresh_rules_table(self):
        """Refresh rules table"""
        self.rules_table.setRowCount(len(self.current_rules))

        for row, rule in enumerate(self.current_rules):
            self.rules_table.setItem(row, 0, QTableWidgetItem(rule.name))
            self.rules_table.setItem(row, 1, QTableWidgetItem(rule.extract_type))
            self.rules_table.setItem(row, 2, QTableWidgetItem(rule.selector[:50] + "..."))

        self.rules_table.resizeColumnsToContents()

    def export_config(self):
        """Export configuration for your scraping tool"""
        if not self.current_rules:
            QMessageBox.warning(self, "No Rules", "Please create some scraping rules first.")
            return

        # Get the parent window to access project info
        main_window = self.window()
        if not hasattr(main_window, 'current_project') or not main_window.current_project:
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return

        project = main_window.current_project

        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Scraper Config",
            f"{project.name.lower().replace(' ', '_')}_config.yaml",
            "YAML files (*.yaml *.yml)"
        )

        if filename:
            # Format EXACTLY like your backend expects
            config_data = {
                "domain_info": {
                    "name": project.name,
                    "description": project.description,
                    "domain": project.domain
                },
                "sources": [{
                    "name": project.name.lower().replace(' ', '_'),
                    "seeds": project.target_websites,
                    "source_type": project.domain,
                    "selectors": {
                        "custom_fields": [
                            {
                                "name": rule.name,
                                "selector": rule.selector,
                                "extract_type": rule.extract_type,
                                "attribute_name": rule.attribute_name,
                                "is_list": rule.is_list,
                                "required": rule.required
                            } for rule in self.current_rules
                        ]
                    },
                    "crawl": {
                        "depth": 1,
                        "delay_seconds": 2.0,
                        "respect_robots_txt": True
                    },
                    "export": {
                        "format": "jsonl",
                        "output_path": f"./data_exports/{project.domain}/{project.name.lower().replace(' ', '_')}.jsonl"
                    }
                }]
            }

            import yaml
            with open(filename, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)

            QMessageBox.information(self, "Export Complete",
                                    f"Scraper config exported to {filename}\n\n"
                                    f"Run with: python main.py --mode backend\n"
                                    f"Then load: {filename}")


class RAGDataStudio(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.current_project = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("RAG Data Studio - Visual Scraper Builder")
        self.setGeometry(100, 100, 1600, 1000)
        self.setStyleSheet(DARK_THEME)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_splitter = QSplitter(Qt.Horizontal)

        # Left panel - Projects
        self.project_manager = ProjectManager()
        self.project_manager.setMaximumWidth(300)
        main_splitter.addWidget(self.project_manager)

        # Center panel - Browser
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

        self.browser = InteractiveBrowser()

        center_layout.addLayout(toolbar_layout)
        center_layout.addWidget(self.browser)
        main_splitter.addWidget(center_widget)

        # Right panel - Targeting and rules
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        self.element_targeter = VisualElementTargeter()
        self.rules_manager = RulesManager()

        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.addWidget(self.element_targeter)
        right_splitter.addWidget(self.rules_manager)
        right_splitter.setSizes([400, 300])

        right_layout.addWidget(right_splitter)
        right_widget.setMaximumWidth(450)
        main_splitter.addWidget(right_widget)

        main_splitter.setSizes([280, 870, 450])
        main_layout.addWidget(main_splitter)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Create a project and start building scrapers")

        # Connect signals
        self.load_btn.clicked.connect(self.load_page)
        self.selector_btn.clicked.connect(self.toggle_selector_mode)
        self.project_manager.project_selected.connect(self.load_project)
        self.element_targeter.rule_created.connect(self.add_rule_to_project)
        self.browser.set_targeting_widget(self.element_targeter)

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
        self.status_bar.showMessage(f"Added rule: {rule.name}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("RAG Data Studio")
    app.setStyle("Fusion")

    window = RAGDataStudio()
    window.show()

    sys.exit(app.exec())