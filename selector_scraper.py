# selector_scraper.py
"""
Clean working version - no bloat, just what you need
"""

import sys
import json
import uuid
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWebEngineWidgets import QWebEngineView

try:
    from scraper_service import ScraperClient
except ImportError:
    print("Warning: scraper_service not found, client features disabled")
    ScraperClient = None

DARK_THEME = """
QMainWindow, QWidget { background-color: #1e1e1e; color: #ffffff; font-family: Arial, sans-serif; }
QPushButton { background-color: #404040; border: 1px solid #606060; border-radius: 4px; padding: 8px 16px; color: white; }
QPushButton:hover { background-color: #505050; border-color: #4CAF50; }
QPushButton[class="go"] { background-color: #4CAF50; }
QLineEdit, QTextEdit { background-color: #3a3a3a; border: 1px solid #555555; border-radius: 4px; padding: 6px; color: white; }
QComboBox { background-color: #3a3a3a; border: 1px solid #555555; border-radius: 4px; padding: 6px; color: white; }
QTableWidget { background-color: #2a2a2a; gridline-color: #555555; border: 1px solid #555555; }
QTableWidget::item:selected { background-color: #4CAF50; color: white; }
QGroupBox { border: 1px solid #404040; border-radius: 4px; margin-top: 10px; padding-top: 10px; }
QGroupBox::title { color: #4CAF50; }
QListWidget { background-color: #2a2a2a; border: 1px solid #555555; }
QListWidget::item:selected { background-color: #4CAF50; }
QTabWidget::pane { border: 1px solid #404040; }
QTabBar::tab { background-color: #404040; color: white; padding: 8px 16px; }
QTabBar::tab:selected { background-color: #4CAF50; }
"""


class Browser(QWebEngineView):
    """Browser with smart element targeting"""

    element_selected = Signal(str, str, dict)  # selector, text, suggestions

    def __init__(self):
        super().__init__()
        self.targeting_active = False

    def enable_targeting(self):
        """Enable smart targeting with visual feedback"""
        self.targeting_active = True

        js = """
        console.log('🎯 Smart targeting enabled');

        let targeting = true;
        let overlays = [];

        // Create tooltip
        let tooltip = document.createElement('div');
        tooltip.style.cssText = `
            position: fixed; top: 20px; right: 20px; z-index: 1000000;
            background: #4CAF50; color: white; padding: 10px 15px;
            border-radius: 6px; font-family: Arial; font-size: 14px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        `;
        tooltip.innerHTML = '🎯 Click element to select<br><small>ESC to cancel</small>';
        document.body.appendChild(tooltip);

        function makeSelector(el) {
            if (el.id) return '#' + el.id;

            let selector = el.tagName.toLowerCase();
            if (el.className) {
                let classes = el.className.trim().split(/\\s+/)
                    .filter(c => !['active', 'hover', 'focus'].includes(c))
                    .slice(0, 2);
                if (classes.length > 0) {
                    selector += '.' + classes.join('.');
                }
            }
            return selector;
        }

        function getElementType(el) {
            let classes = el.className.toLowerCase();
            let text = el.textContent.trim();

            if (classes.includes('name') || classes.includes('title')) return 'name';
            if (classes.includes('price') || text.match(/\\$|€|£/)) return 'price';
            if (classes.includes('rating')) return 'rating';
            if (text.match(/^\\d+$/)) return 'number';
            return 'content';
        }

        function createOverlay(el, color, label) {
            let rect = el.getBoundingClientRect();

            let overlay = document.createElement('div');
            overlay.style.cssText = `
                position: fixed; z-index: 999999; pointer-events: none;
                left: ${rect.left}px; top: ${rect.top}px;
                width: ${rect.width}px; height: ${rect.height}px;
                border: 3px solid ${color}; background: ${color}15;
                border-radius: 4px;
            `;

            let labelEl = document.createElement('div');
            labelEl.style.cssText = `
                position: fixed; z-index: 999999; pointer-events: none;
                left: ${rect.left}px; top: ${rect.top - 25}px;
                background: ${color}; color: white; padding: 4px 8px;
                font-size: 12px; border-radius: 4px; font-family: Arial;
            `;
            labelEl.textContent = label;

            document.body.appendChild(overlay);
            document.body.appendChild(labelEl);
            overlays.push(overlay, labelEl);
        }

        function clearOverlays() {
            overlays.forEach(el => el.remove());
            overlays = [];
        }

        function showSuggestions(target) {
            clearOverlays();

            // Current element (green)
            createOverlay(target, '#4CAF50', 'Current');

            // Parent element (blue) 
            if (target.parentElement) {
                createOverlay(target.parentElement, '#2196F3', 'Parent');
            }

            // Container (orange) - find meaningful container
            let container = target.closest('tr, li, .card, .item, [class*="row"]');
            if (container && container !== target && container !== target.parentElement) {
                createOverlay(container, '#FF9800', 'Container');
            }
        }

        document.addEventListener('mouseover', function(e) {
            if (targeting) {
                e.preventDefault();
                showSuggestions(e.target);
            }
        }, true);

        document.addEventListener('click', function(e) {
            if (targeting) {
                e.preventDefault();
                e.stopPropagation();

                let suggestions = {
                    current: {
                        selector: makeSelector(e.target),
                        text: e.target.textContent.trim(),
                        type: getElementType(e.target)
                    },
                    parent: null,
                    container: null
                };

                if (e.target.parentElement) {
                    suggestions.parent = {
                        selector: makeSelector(e.target.parentElement),
                        text: e.target.parentElement.textContent.trim()
                    };
                }

                let container = e.target.closest('tr, li, .card, .item, [class*="row"]');
                if (container && container !== e.target && container !== e.target.parentElement) {
                    suggestions.container = {
                        selector: makeSelector(container),
                        text: container.textContent.trim()
                    };
                }

                window.selectedElement = {
                    selector: suggestions.current.selector,
                    text: suggestions.current.text,
                    suggestions: suggestions
                };

                targeting = false;
                clearOverlays();
                tooltip.remove();

                console.log('✅ Element selected:', suggestions);
            }
        }, true);

        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && targeting) {
                targeting = false;
                clearOverlays();
                tooltip.remove();
                window.selectedElement = {cancelled: true};
            }
        });
        """

        self.page().runJavaScript(js)

        # Start polling for selection
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.check_selection)
        self.poll_timer.start(500)

    def check_selection(self):
        """Check for element selection"""

        def handle_result(result):
            if result:
                self.poll_timer.stop()
                self.targeting_active = False

                # Clear selection
                self.page().runJavaScript("window.selectedElement = null;")

                if result.get('cancelled'):
                    return

                # Emit selection
                selector = result.get('selector', '')
                text = result.get('text', '')
                suggestions = result.get('suggestions', {})
                self.element_selected.emit(selector, text, suggestions)

        self.page().runJavaScript("window.selectedElement || null;", handle_result)

    def disable_targeting(self):
        """Disable targeting"""
        self.targeting_active = False
        if hasattr(self, 'poll_timer'):
            self.poll_timer.stop()


class SelectorPanel(QWidget):
    """Panel for managing selectors"""

    selector_created = Signal(dict)

    def __init__(self):
        super().__init__()
        self.selectors = []
        self.current_suggestions = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Current selection
        selection_group = QGroupBox("Element Selection")
        selection_layout = QVBoxLayout(selection_group)

        form_layout = QFormLayout()
        self.selector_input = QLineEdit()
        self.selector_input.setReadOnly(True)

        self.text_preview = QTextEdit()
        self.text_preview.setMaximumHeight(60)
        self.text_preview.setReadOnly(True)

        form_layout.addRow("Selector:", self.selector_input)
        form_layout.addRow("Text:", self.text_preview)

        # Suggestion buttons
        buttons_layout = QHBoxLayout()
        self.current_btn = QPushButton("✓ Current")
        self.current_btn.setProperty("class", "go")
        self.parent_btn = QPushButton("Parent")
        self.container_btn = QPushButton("Container")

        buttons_layout.addWidget(self.current_btn)
        buttons_layout.addWidget(self.parent_btn)
        buttons_layout.addWidget(self.container_btn)
        buttons_layout.addStretch()

        self.current_btn.clicked.connect(lambda: self.use_suggestion('current'))
        self.parent_btn.clicked.connect(lambda: self.use_suggestion('parent'))
        self.container_btn.clicked.connect(lambda: self.use_suggestion('container'))

        selection_layout.addLayout(form_layout)
        selection_layout.addLayout(buttons_layout)

        # Labeling
        label_group = QGroupBox("RAG Labeling")
        label_layout = QFormLayout(label_group)

        self.field_name = QLineEdit()
        self.field_name.setPlaceholderText("e.g., product_name, price, rating")

        self.semantic_label = QComboBox()
        self.semantic_label.addItems([
            "entity_name", "entity_score", "entity_ranking", "entity_location",
            "entity_date", "content_title", "content_body"
        ])

        self.importance = QComboBox()
        self.importance.addItems(["high", "medium", "low"])
        self.importance.setCurrentText("medium")

        label_layout.addRow("Field Name:", self.field_name)
        label_layout.addRow("Semantic Label:", self.semantic_label)
        label_layout.addRow("Importance:", self.importance)

        # Save button
        self.save_btn = QPushButton("Save Selector")
        self.save_btn.setProperty("class", "go")
        self.save_btn.clicked.connect(self.save_selector)
        self.save_btn.setEnabled(False)

        # Selectors list
        list_group = QGroupBox("Saved Selectors")
        list_layout = QVBoxLayout(list_group)

        self.selectors_list = QListWidget()

        list_buttons = QHBoxLayout()
        self.delete_btn = QPushButton("Delete")
        self.clear_btn = QPushButton("Clear All")

        self.delete_btn.clicked.connect(self.delete_selected)
        self.clear_btn.clicked.connect(self.clear_all)

        list_buttons.addWidget(self.delete_btn)
        list_buttons.addWidget(self.clear_btn)
        list_buttons.addStretch()

        list_layout.addWidget(self.selectors_list)
        list_layout.addLayout(list_buttons)

        # Project buttons
        project_layout = QHBoxLayout()
        self.save_project_btn = QPushButton("💾 Save Project")
        self.load_project_btn = QPushButton("📁 Load Project")

        self.save_project_btn.clicked.connect(self.save_project)
        self.load_project_btn.clicked.connect(self.load_project)

        project_layout.addWidget(self.save_project_btn)
        project_layout.addWidget(self.load_project_btn)
        project_layout.addStretch()

        layout.addWidget(selection_group)
        layout.addWidget(label_group)
        layout.addWidget(self.save_btn)
        layout.addWidget(list_group)
        layout.addLayout(project_layout)

        # Disable suggestion buttons initially
        self.parent_btn.setEnabled(False)
        self.container_btn.setEnabled(False)
        self.current_btn.setEnabled(False)

    def update_selection(self, selector, text, suggestions):
        """Update with new element selection"""
        self.current_suggestions = suggestions

        # Show current selection
        self.selector_input.setText(selector)
        self.text_preview.setText(text[:200] + "..." if len(text) > 200 else text)

        # Enable/update suggestion buttons
        self.current_btn.setEnabled(True)
        self.current_btn.setText("✓ Current")

        if suggestions.get('parent'):
            self.parent_btn.setEnabled(True)
            self.parent_btn.setText("Parent")
        else:
            self.parent_btn.setEnabled(False)

        if suggestions.get('container'):
            self.container_btn.setEnabled(True)
            self.container_btn.setText("Container")
        else:
            self.container_btn.setEnabled(False)

        self.save_btn.setEnabled(True)

        # Auto-suggest field name
        if not self.field_name.text():
            element_type = suggestions.get('current', {}).get('type', '')
            if element_type == 'name':
                self.field_name.setText("name")
                self.semantic_label.setCurrentText("entity_name")
                self.importance.setCurrentText("high")
            elif element_type == 'price':
                self.field_name.setText("price")
                self.semantic_label.setCurrentText("entity_score")
                self.importance.setCurrentText("high")
            elif element_type == 'rating':
                self.field_name.setText("rating")
                self.semantic_label.setCurrentText("entity_score")
            elif element_type == 'number':
                if text.isdigit() and int(text) < 100:
                    self.field_name.setText("ranking")
                    self.semantic_label.setCurrentText("entity_ranking")
                    self.importance.setCurrentText("high")

    def use_suggestion(self, suggestion_type):
        """Use a suggested selector"""
        if suggestion_type not in self.current_suggestions:
            return

        suggestion = self.current_suggestions[suggestion_type]
        self.selector_input.setText(suggestion['selector'])
        self.text_preview.setText(
            suggestion['text'][:200] + "..." if len(suggestion['text']) > 200 else suggestion['text'])

        # Update button states
        self.current_btn.setText("Current")
        self.parent_btn.setText("Parent")
        self.container_btn.setText("Container")

        if suggestion_type == 'current':
            self.current_btn.setText("✓ Current")
        elif suggestion_type == 'parent':
            self.parent_btn.setText("✓ Parent")
        elif suggestion_type == 'container':
            self.container_btn.setText("✓ Container")

    def save_selector(self):
        """Save current selector"""
        if not self.field_name.text() or not self.selector_input.text():
            QMessageBox.warning(self, "Missing Info", "Please provide field name and selector")
            return

        selector_data = {
            "name": self.field_name.text(),
            "selector": self.selector_input.text(),
            "semantic_label": self.semantic_label.currentText(),
            "rag_importance": self.importance.currentText(),
            "extraction_type": "text"
        }

        self.selectors.append(selector_data)
        self.selectors_list.addItem(f"{selector_data['name']} ({selector_data['semantic_label']})")

        self.selector_created.emit(selector_data)

        # Clear form
        self.field_name.clear()
        self.selector_input.clear()
        self.text_preview.clear()
        self.save_btn.setEnabled(False)
        self.current_btn.setEnabled(False)
        self.parent_btn.setEnabled(False)
        self.container_btn.setEnabled(False)

    def delete_selected(self):
        """Delete selected selector"""
        current_row = self.selectors_list.currentRow()
        if current_row >= 0:
            self.selectors_list.takeItem(current_row)
            if current_row < len(self.selectors):
                del self.selectors[current_row]

    def clear_all(self):
        """Clear all selectors"""
        reply = QMessageBox.question(self, "Clear All", "Clear all selectors?")
        if reply == QMessageBox.Yes:
            self.selectors.clear()
            self.selectors_list.clear()

    def save_project(self):
        """Save project to file"""
        if not self.selectors:
            QMessageBox.warning(self, "No Data", "No selectors to save")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Project", "project.json", "JSON files (*.json)"
        )

        if filename:
            project_data = {
                "name": "Selector Project",
                "created": datetime.now().isoformat(),
                "selectors": self.selectors
            }

            try:
                with open(filename, 'w') as f:
                    json.dump(project_data, f, indent=2)
                QMessageBox.information(self, "Saved", f"Project saved to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save: {e}")

    def load_project(self):
        """Load project from file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Project", "", "JSON files (*.json)"
        )

        if filename:
            try:
                with open(filename, 'r') as f:
                    project_data = json.load(f)

                self.selectors = project_data.get('selectors', [])

                # Update list
                self.selectors_list.clear()
                for selector in self.selectors:
                    self.selectors_list.addItem(f"{selector['name']} ({selector['semantic_label']})")

                QMessageBox.information(self, "Loaded", f"Loaded {len(self.selectors)} selectors")

                # Send to scraper panel
                for selector in self.selectors:
                    self.selector_created.emit(selector)

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load: {e}")


class ScraperPanel(QWidget):
    """Panel for scraper communication"""

    def __init__(self):
        super().__init__()
        self.client = ScraperClient() if ScraperClient else None
        self.selectors = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Connection status
        self.status_label = QLabel("🔴 Not connected")

        # Target URL
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("Target URL:"))
        self.target_url = QLineEdit()
        url_layout.addWidget(self.target_url)

        # Selectors count
        self.count_label = QLabel("📋 0 selectors ready")

        # Control buttons
        buttons_layout = QHBoxLayout()

        self.connect_btn = QPushButton("Connect")
        self.scrape_btn = QPushButton("Start Scraping")
        self.scrape_btn.setProperty("class", "go")

        self.connect_btn.clicked.connect(self.connect_to_service)
        self.scrape_btn.clicked.connect(self.start_scraping)

        buttons_layout.addWidget(self.connect_btn)
        buttons_layout.addWidget(self.scrape_btn)
        buttons_layout.addStretch()

        # Progress and log
        self.progress_bar = QProgressBar()
        self.log_text = QPlainTextEdit()
        self.log_text.setMaximumHeight(120)

        layout.addWidget(self.status_label)
        layout.addLayout(url_layout)
        layout.addWidget(self.count_label)
        layout.addLayout(buttons_layout)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.log_text)

        # Initial state
        self.scrape_btn.setEnabled(False)

    def connect_to_service(self):
        """Connect to scraper service"""
        if not self.client:
            self.log_text.appendPlainText("❌ Scraper client not available")
            return

        if self.client.ping():
            self.status_label.setText("🟢 Connected")
            self.connect_btn.setText("Connected")
            self.connect_btn.setEnabled(False)
            self.scrape_btn.setEnabled(len(self.selectors) > 0)
            self.log_text.appendPlainText("✅ Connected to scraper service")
        else:
            self.log_text.appendPlainText("❌ Connection failed")
            self.log_text.appendPlainText("💡 Start service: python scraper_service.py --service")

    def add_selector(self, selector_data):
        """Add selector from selector panel"""
        self.selectors.append(selector_data)
        self.count_label.setText(f"📋 {len(self.selectors)} selectors ready")
        self.log_text.appendPlainText(f"Added: {selector_data['name']}")

        if self.status_label.text() == "🟢 Connected":
            self.scrape_btn.setEnabled(True)

    def start_scraping(self):
        """Start scraping"""
        if not self.client:
            return

        url = self.target_url.text().strip()
        if not url:
            self.log_text.appendPlainText("❌ Need target URL")
            return

        if not self.selectors:
            self.log_text.appendPlainText("❌ Need selectors")
            return

        response = self.client.start_scraping(
            selectors=self.selectors,
            target_urls=[url],
            project_name="scrape_job"
        )

        if response.get("status") == "started":
            self.log_text.appendPlainText(f"🚀 Started: {response['job_id']}")
            self.scrape_btn.setEnabled(False)

            # Monitor progress
            self.progress_timer = QTimer()
            self.progress_timer.timeout.connect(self.update_progress)
            self.progress_timer.start(2000)
        else:
            self.log_text.appendPlainText(f"❌ Failed: {response.get('message')}")

    def update_progress(self):
        """Update scraping progress"""
        if not self.client:
            return

        response = self.client.get_status()

        if response.get("status") == "ok":
            job = response.get("job", {})
            progress = job.get("progress", 0)
            self.progress_bar.setValue(progress)

            if not job.get("running", False):
                self.progress_timer.stop()
                self.scrape_btn.setEnabled(True)
                items = job.get("items_scraped", 0)
                self.log_text.appendPlainText(f"✅ Complete: {items} items")


class SelectorScraperTool(QMainWindow):
    """Main application"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Selector to Scraper Tool")
        self.setGeometry(100, 100, 1400, 800)

        # Main layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        # Left: Browser
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # URL bar
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter URL...")

        self.load_btn = QPushButton("Load")
        self.target_btn = QPushButton("Target Elements")
        self.target_btn.setProperty("class", "go")

        url_layout.addWidget(QLabel("URL:"))
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(self.load_btn)
        url_layout.addWidget(self.target_btn)

        # Browser
        self.browser = Browser()

        left_layout.addLayout(url_layout)
        left_layout.addWidget(self.browser)

        # Right: Tabs
        right_tabs = QTabWidget()
        right_tabs.setMaximumWidth(450)

        self.selector_panel = SelectorPanel()
        self.scraper_panel = ScraperPanel()

        right_tabs.addTab(self.selector_panel, "Selectors")
        right_tabs.addTab(self.scraper_panel, "Scraper")

        layout.addWidget(left_widget, 2)
        layout.addWidget(right_tabs, 1)

        # Connect signals
        self.load_btn.clicked.connect(self.load_page)
        self.target_btn.clicked.connect(self.toggle_targeting)
        self.browser.element_selected.connect(self.selector_panel.update_selection)
        self.selector_panel.selector_created.connect(self.scraper_panel.add_selector)
        self.selector_panel.selector_created.connect(self.auto_fill_url)

    def load_page(self):
        """Load page"""
        url = self.url_input.text().strip()
        if url:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            self.browser.load(QUrl(url))

    def toggle_targeting(self):
        """Toggle targeting mode"""
        if self.target_btn.text() == "Target Elements":
            self.browser.enable_targeting()
            self.target_btn.setText("Stop Targeting")
            self.target_btn.setProperty("class", "")
            self.target_btn.style().polish(self.target_btn)
        else:
            self.browser.disable_targeting()
            self.target_btn.setText("Target Elements")
            self.target_btn.setProperty("class", "go")
            self.target_btn.style().polish(self.target_btn)

    def auto_fill_url(self, selector_data):
        """Auto-fill target URL"""
        current_url = self.browser.url().toString()
        if current_url and current_url != "about:blank":
            self.scraper_panel.target_url.setText(current_url)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME)

    window = SelectorScraperTool()
    window.show()

    sys.exit(app.exec())