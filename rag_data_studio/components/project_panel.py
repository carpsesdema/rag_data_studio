# rag_data_studio/components/project_panel.py
"""
UI components for managing projects: the list panel and the new/edit dialog.
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from PySide6.QtWidgets import *
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from ..core.models import ProjectConfig, ScrapingRule

class ProjectManager(QWidget):
    project_selected = Signal(ProjectConfig)
    new_project_requested = Signal()

    def __init__(self):
        super().__init__()
        self.projects: Dict[str, ProjectConfig] = {}
        self.init_ui()
        self.load_projects_from_disk()

    def init_ui(self):
        layout = QVBoxLayout(self)
        header = QLabel("📁 Projects")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setStyleSheet("color: #4CAF50; margin: 10px 0;")
        self.project_list_widget = QListWidget()
        self.project_list_widget.itemClicked.connect(self.on_project_list_item_selected)
        actions_layout = QHBoxLayout()
        self.new_btn = QPushButton("➕ New Project")
        self.delete_btn = QPushButton("🗑️ Delete Project")
        for btn in [self.new_btn, self.delete_btn]:
            btn.setMaximumHeight(35)
            actions_layout.addWidget(btn)
        layout.addWidget(header)
        layout.addWidget(self.project_list_widget)
        layout.addLayout(actions_layout)
        self.new_btn.clicked.connect(self.handle_new_project_request)
        self.delete_btn.clicked.connect(self.delete_selected_project)

    def handle_new_project_request(self): self.new_project_requested.emit()

    def add_or_update_project(self, project: ProjectConfig):
        self.projects[project.id] = project
        self.refresh_project_list_display()
        self.save_projects_to_disk()
        for i in range(self.project_list_widget.count()):
            item = self.project_list_widget.item(i)
            if item.data(Qt.UserRole) == project.id:
                self.project_list_widget.setCurrentItem(item)
                self.on_project_list_item_selected(item)
                break

    def refresh_project_list_display(self):
        self.project_list_widget.clear()
        for project_id, project_obj in sorted(self.projects.items(), key=lambda item: item[1].name):
            item = QListWidgetItem(f"{project_obj.name} ({project_obj.domain})")
            item.setData(Qt.UserRole, project_id)
            self.project_list_widget.addItem(item)

    def on_project_list_item_selected(self, list_item: QListWidgetItem):
        if list_item:
            project_id = list_item.data(Qt.UserRole)
            project_obj = self.projects.get(project_id)
            if project_obj: self.project_selected.emit(project_obj)

    def get_project_path(self):
        data_dir = Path.home() / ".data_extractor_studio_projects"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "projects_config.json"

    def save_projects_to_disk(self):
        try:
            projects_data_to_save = {pid: asdict(p) for pid, p in self.projects.items()}
            with open(self.get_project_path(), "w", encoding="utf-8") as f: json.dump(projects_data_to_save, f, indent=2)
            print(f"Projects saved to {self.get_project_path()}")
        except Exception as e: print(f"Error saving projects: {e}")

    def load_projects_from_disk(self):
        try:
            project_file = self.get_project_path()
            if project_file.exists():
                with open(project_file, "r", encoding="utf-8") as f: projects_data_loaded = json.load(f)
                for pid, p_data in projects_data_loaded.items():
                    rules_data = p_data.get("scraping_rules", [])
                    p_data["scraping_rules"] = [ScrapingRule(**{k:v for k,v in rule_data.items() if k in ScrapingRule.__annotations__}) for rule_data in rules_data]
                    self.projects[pid] = ProjectConfig(**{k:v for k,v in p_data.items() if k in ProjectConfig.__annotations__})
                self.refresh_project_list_display()
                print(f"Loaded {len(self.projects)} projects from {project_file}")
        except Exception as e: print(f"Error loading projects: {e}"); self.projects = {}

    def delete_selected_project(self):
        current_item = self.project_list_widget.currentItem()
        if not current_item: QMessageBox.warning(self, "No Project Selected", "Select a project to delete."); return
        project_id = current_item.data(Qt.UserRole); project_name = self.projects[project_id].name
        reply = QMessageBox.question(self, "Delete Project", f"Delete project '{project_name}'?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            del self.projects[project_id]; self.refresh_project_list_display(); self.save_projects_to_disk()
            QMessageBox.information(self, "Project Deleted", f"Project '{project_name}' deleted.")

class ProjectDialog(QDialog):
    def __init__(self, parent=None, project_to_edit: Optional[ProjectConfig] = None):
        super().__init__(parent); self.project_to_edit = project_to_edit
        self.setWindowTitle("New Project" if not project_to_edit else "Edit Project"); self.setModal(True); self.resize(500, 350); self.init_ui()
        if project_to_edit: self.populate_for_edit(project_to_edit)

    def init_ui(self):
        layout = QVBoxLayout(self); form_layout = QFormLayout()
        self.name_input = QLineEdit(); self.description_input = QTextEdit(); self.description_input.setMaximumHeight(70)
        self.domain_combo = QComboBox(); self.domain_combo.setEditable(True); self.domain_combo.addItems(["tennis_stats", "sports_general", "finance", "news", "ecommerce", "custom"])
        self.websites_input = QTextEdit(); self.websites_input.setPlaceholderText("Enter target URLs, one per line"); self.websites_input.setMaximumHeight(80)
        form_layout.addRow("Project Name*:", self.name_input); form_layout.addRow("Description:", self.description_input)
        form_layout.addRow("Primary Domain*:", self.domain_combo); form_layout.addRow("Target Websites:", self.websites_input)
        button_layout = QHBoxLayout()
        self.ok_btn = QPushButton("Save Project" if self.project_to_edit else "Create Project"); self.ok_btn.setProperty("class", "success")
        self.cancel_btn = QPushButton("Cancel")
        button_layout.addStretch(); button_layout.addWidget(self.cancel_btn); button_layout.addWidget(self.ok_btn)
        layout.addLayout(form_layout); layout.addLayout(button_layout)
        self.ok_btn.clicked.connect(self.on_ok_clicked); self.cancel_btn.clicked.connect(self.reject)

    def populate_for_edit(self, project: ProjectConfig):
        self.name_input.setText(project.name); self.description_input.setPlainText(project.description)
        self.domain_combo.setCurrentText(project.domain); self.websites_input.setPlainText("\n".join(project.target_websites))

    def on_ok_clicked(self):
        if not self.name_input.text().strip() or not self.domain_combo.currentText().strip():
            QMessageBox.warning(self, "Missing Information", "Project Name and Primary Domain are required."); return
        self.accept()

    def get_project_config(self) -> ProjectConfig:
        websites = [line.strip() for line in self.websites_input.toPlainText().split('\n') if line.strip()]
        if self.project_to_edit:
            self.project_to_edit.name = self.name_input.text(); self.project_to_edit.description = self.description_input.toPlainText()
            self.project_to_edit.domain = self.domain_combo.currentText(); self.project_to_edit.target_websites = websites
            self.project_to_edit.updated_at = datetime.now().isoformat(); return self.project_to_edit
        else:
            return ProjectConfig(id=f"proj_{uuid.uuid4().hex[:10]}", name=self.name_input.text(),
                description=self.description_input.toPlainText(), domain=self.domain_combo.currentText(), target_websites=websites)