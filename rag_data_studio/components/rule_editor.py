# rag_data_studio/components/rule_editor.py
"""
UI components for defining and managing scraping rules.
"""
import uuid
from typing import List, Optional

from PySide6.QtWidgets import *
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QBrush, QColor

from ..core.models import ScrapingRule


class VisualElementTargeter(QWidget):
    rule_created = Signal(ScrapingRule, str)  # Emits rule and parent_id
    test_selector_requested = Signal(dict)

    def __init__(self):
        super().__init__()
        self.current_selector = ""
        self.current_element_text = ""
        self.current_element_type = ""
        self.parent_rule_id: Optional[str] = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.header = QLabel("🎯 Define New Rule")
        self.header.setFont(QFont("Arial", 14, QFont.Bold))
        self.header.setStyleSheet("color: #4CAF50; margin: 10px 0;")
        selection_group = QGroupBox("Selected Element Preview")
        selection_layout = QFormLayout(selection_group)
        self.selector_display = QLineEdit()
        self.selector_display.setReadOnly(True)
        self.selector_display.setPlaceholderText("Click an element in the browser...")
        self.element_text_display = QTextEdit()
        self.element_text_display.setReadOnly(True)
        self.element_text_display.setMaximumHeight(60)
        selection_layout.addRow("CSS Selector:", self.selector_display)
        selection_layout.addRow("Element Text:", self.element_text_display)
        rule_def_group = QGroupBox("Rule Definition")
        rule_def_layout = QFormLayout(rule_def_group)
        self.field_name_input = QLineEdit()
        self.field_name_input.setPlaceholderText("e.g., player_name, or player_list")
        self.field_description_input = QTextEdit()
        self.field_description_input.setMaximumHeight(60)
        self.field_description_input.setPlaceholderText("Optional description.")
        rule_def_layout.addRow("Field Name:", self.field_name_input)
        rule_def_layout.addRow("Description:", self.field_description_input)
        advanced_group = QGroupBox("Extraction Options")
        advanced_layout = QFormLayout(advanced_group)
        self.extraction_type_combo = QComboBox()
        self.extraction_type_combo.addItems(["text", "attribute", "html", "structured_list"])
        self.attribute_input = QLineEdit()
        self.attribute_input.setPlaceholderText("e.g., href, src")
        self.attribute_input.setEnabled(False)
        self.is_list_check = QCheckBox("Is this a list of simple values?")
        self.is_list_check.setToolTip("For multiple elements. Ignored for 'structured_list'.")
        self.required_check = QCheckBox("This field is required")
        self.data_type_combo = QComboBox()
        self.data_type_combo.addItems(["string", "number", "boolean", "date", "list_of_strings", "list_of_objects"])
        self.data_type_combo.setToolTip("Use 'list_of_objects' for 'structured_list'.")
        self.sub_selector_info_label = QLabel(
            "For 'structured_list', name this rule (e.g., 'players'). Then, add sub-fields to it.")
        self.sub_selector_info_label.setWordWrap(True)
        self.sub_selector_info_label.setStyleSheet("font-size: 9px; color: #cccccc;")
        self.sub_selector_info_label.setVisible(False)
        advanced_layout.addRow("Extract How:", self.extraction_type_combo)
        advanced_layout.addRow("Attribute Name:", self.attribute_input)
        advanced_layout.addRow("Data Type:", self.data_type_combo)
        advanced_layout.addRow("", self.is_list_check)
        advanced_layout.addRow("", self.required_check)
        advanced_layout.addRow(self.sub_selector_info_label)
        action_layout = QHBoxLayout()
        self.test_btn = QPushButton("🧪 Test Selector")
        self.test_btn.setEnabled(False)
        self.save_btn = QPushButton("💾 Save Rule")
        self.save_btn.setProperty("class", "success")
        self.save_btn.setEnabled(False)
        action_layout.addWidget(self.test_btn)
        action_layout.addStretch()
        action_layout.addWidget(self.save_btn)
        layout.addWidget(self.header)
        layout.addWidget(selection_group)
        layout.addWidget(rule_def_group)
        layout.addWidget(advanced_group)
        layout.addLayout(action_layout)
        layout.addStretch()
        self.extraction_type_combo.currentTextChanged.connect(self.on_extraction_type_changed)
        self.save_btn.clicked.connect(self.save_current_rule)
        self.test_btn.clicked.connect(self.test_current_selector_emit)
        self.is_list_check.toggled.connect(self.on_is_list_toggled)  # Connect the new handler

    def set_mode_for_sub_field(self, parent_rule: ScrapingRule):
        self.parent_rule_id = parent_rule.id
        self.header.setText(f"➕ Add Field to '{parent_rule.name}'")
        self.extraction_type_combo.setCurrentText("text")
        self.extraction_type_combo.setEnabled(False)

    def reset_mode(self):
        self.parent_rule_id = None
        self.header.setText("🎯 Define New Rule")
        self.extraction_type_combo.setEnabled(True)
        self._clear_form()

    def on_extraction_type_changed(self, extraction_type: str):
        """Handle changes in the extraction type dropdown."""
        self.attribute_input.setEnabled(extraction_type == "attribute")
        self.sub_selector_info_label.setVisible(extraction_type == "structured_list")

        if extraction_type == "structured_list":
            # Correct logic: disable the checkbox and ensure it's unchecked.
            self.is_list_check.setChecked(False)
            self.is_list_check.setEnabled(False)
            self.data_type_combo.setCurrentText("list_of_objects")
        else:
            # For all other types, the user can decide if it's a list or not.
            self.is_list_check.setEnabled(True)
            # Update data type based on whether the now-enabled checkbox is checked.
            if self.is_list_check.isChecked():
                self.data_type_combo.setCurrentText("list_of_strings")
            else:
                self.data_type_combo.setCurrentText("string")

    def on_is_list_toggled(self, checked: bool):
        """Update data type when 'is list' checkbox is toggled by user."""
        # This handler should only have an effect for non-structured_list types
        if self.extraction_type_combo.currentText() != "structured_list":
            if checked:
                self.data_type_combo.setCurrentText("list_of_strings")
            else:
                self.data_type_combo.setCurrentText("string")

    def update_selection(self, selector: str, text: str, element_type: str):
        self.current_selector = selector
        self.current_element_text = text
        self.current_element_type = element_type
        self.selector_display.setText(selector)
        self.element_text_display.setText(text[:200] + "..." if len(text) > 200 else text)
        self.save_btn.setEnabled(bool(selector))
        self.test_btn.setEnabled(bool(selector))
        if not self.field_name_input.text() and text:
            suggested_name = ''.join(
                c for c in text.lower().replace(" ", "_").replace(":", "") if c.isalnum() or c == '_')
            self.field_name_input.setText(suggested_name[:30])

    def save_current_rule(self):
        if not self.current_selector or not self.field_name_input.text(): QMessageBox.warning(self, "Missing Info",
                                                                                              "Select an element and provide a Field Name."); return
        extraction_type = self.extraction_type_combo.currentText()
        # The is_list property for the backend is True if it's a structured list OR if the checkbox is checked for simple types.
        is_list_for_rule = (extraction_type == "structured_list") or (
                    self.is_list_check.isEnabled() and self.is_list_check.isChecked())

        rule = ScrapingRule(id=f"rule_{uuid.uuid4().hex[:8]}", name=self.field_name_input.text(),
                            description=self.field_description_input.toPlainText(), selector=self.current_selector,
                            extraction_type=extraction_type,
                            attribute_name=self.attribute_input.text() if self.attribute_input.isEnabled() else None,
                            is_list=is_list_for_rule, data_type=self.data_type_combo.currentText(),
                            required=self.required_check.isChecked(), sub_selectors=[])
        self.rule_created.emit(rule, self.parent_rule_id)
        self.reset_mode()
        QMessageBox.information(self, "Rule Saved", f"Rule '{rule.name}' saved!")

    def _clear_form(self):
        self.field_name_input.clear()
        self.field_description_input.clear()
        self.is_list_check.setChecked(False)
        self.required_check.setChecked(False)
        self.extraction_type_combo.setCurrentIndex(0)
        self.data_type_combo.setCurrentIndex(0)
        self.selector_display.clear()
        self.element_text_display.clear()
        self.save_btn.setEnabled(False)
        self.test_btn.setEnabled(False)

    def test_current_selector_emit(self):
        if not self.current_selector: QMessageBox.warning(self, "No Selector", "No selector to test."); return
        self.test_selector_requested.emit({"name": self.field_name_input.text() or f"test_{self.current_element_type}",
                                           "selector": self.current_selector,
                                           "extract_type": self.extraction_type_combo.currentText(),
                                           "attribute_name": self.attribute_input.text() if self.attribute_input.isEnabled() else None})


class RulesManager(QWidget):
    rule_selection_changed = Signal(str)
    delete_rule_requested = Signal(str)
    add_sub_rule_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        header = QLabel("📋 Defined Selectors")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setStyleSheet("color: #4CAF50; margin: 10px 0;")
        self.rules_tree = QTreeWidget()
        self.rules_tree.setColumnCount(3)
        self.rules_tree.setHeaderLabels(["Field Name", "Extract How", "Selector"])
        self.rules_tree.header().setStretchLastSection(False)
        self.rules_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.rules_tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.rules_tree.header().setSectionResizeMode(2, QHeaderView.Stretch)
        rule_actions_layout = QHBoxLayout()
        self.add_sub_rule_btn = QPushButton("➕ Add Sub-Field")
        self.add_sub_rule_btn.setEnabled(False)
        self.delete_rule_btn = QPushButton("🗑️ Delete Selected")
        self.delete_rule_btn.setEnabled(False)
        rule_actions_layout.addStretch()
        rule_actions_layout.addWidget(self.add_sub_rule_btn)
        rule_actions_layout.addWidget(self.delete_rule_btn)
        layout.addWidget(header)
        layout.addWidget(self.rules_tree)
        layout.addLayout(rule_actions_layout)
        self.rules_tree.itemSelectionChanged.connect(self._on_selection_changed)
        self.add_sub_rule_btn.clicked.connect(self._request_add_sub_rule)
        self.delete_rule_btn.clicked.connect(self._request_delete_selected_rule)

    def _on_selection_changed(self):
        selected_items = self.rules_tree.selectedItems()
        if not selected_items: self.add_sub_rule_btn.setEnabled(False); self.delete_rule_btn.setEnabled(False); return
        selected_item = selected_items[0]
        rule_id = selected_item.data(0, Qt.UserRole)
        is_structured_list = selected_item.text(1) == "structured_list"
        self.add_sub_rule_btn.setEnabled(is_structured_list)
        self.delete_rule_btn.setEnabled(True)
        if rule_id: self.rule_selection_changed.emit(rule_id)

    def _request_add_sub_rule(self):
        if self.rules_tree.selectedItems(): self.add_sub_rule_requested.emit(
            self.rules_tree.selectedItems()[0].data(0, Qt.UserRole))

    def _request_delete_selected_rule(self):
        if self.rules_tree.selectedItems(): self.delete_rule_requested.emit(
            self.rules_tree.selectedItems()[0].data(0, Qt.UserRole))

    def set_rules(self, rules: List[ScrapingRule]):
        self.rules_tree.clear()
        rule_map = {rule.id: rule for rule in rules}
        parent_items = {}
        processed_ids = set()

        def add_item_to_tree(rule, parent_widget):
            if rule.id in processed_ids: return
            item = QTreeWidgetItem(parent_widget)
            item.setText(0, rule.name)
            extract_display = rule.extraction_type
            if rule.extraction_type == "attribute": extract_display += f" ({rule.attribute_name or 'N/A'})"
            item.setText(1, extract_display)
            item.setText(2, rule.selector)
            item.setData(0, Qt.UserRole, rule.id)
            if rule.extraction_type == "structured_list": item.setForeground(0, QBrush(
                QColor("#4CAF50"))); item.setExpanded(True)
            parent_items[rule.id] = item
            processed_ids.add(rule.id)
            for sub_rule in rule.sub_selectors:
                add_item_to_tree(sub_rule, item)

        # Add top-level items first
        for rule in rules:
            add_item_to_tree(rule, self.rules_tree)