# selector_scraper.py
"""
FIXED VERSION - Element selection now works properly
"""

import sys
import json
import uuid
import time
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
QPushButton[class="success"] { background-color: #2E7D32; border-color: #4CAF50; }
QPushButton:disabled { background-color: #2a2a2a; color: #666666; }
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
QLabel[class="success"] { color: #4CAF50; font-weight: bold; }
QLabel[class="fade"] { color: #888888; }
"""


class Browser(QWebEngineView):
    """Browser with WORKING element targeting"""

    element_selected = Signal(str, str, dict)  # selector, text, suggestions

    def __init__(self):
        super().__init__()
        self.targeting_active = False
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.check_selection)

    def enable_targeting(self):
        """Enable targeting mode"""
        print("🎯 Enabling targeting mode...")
        self.targeting_active = True

        # Simple, reliable JavaScript
        js_code = """
        console.log('🎯 Targeting mode enabled');

        // Clean up any existing
        if (window.cleanupTargeting) {
            window.cleanupTargeting();
        }

        window.selectedElement = null;
        let targeting = true;

        // Create visual feedback
        let tooltip = document.createElement('div');
        tooltip.id = 'targeting-tooltip';
        tooltip.style.cssText = `
            position: fixed; top: 20px; right: 20px; z-index: 999999;
            background: #4CAF50; color: white; padding: 10px 15px;
            border-radius: 6px; font-family: Arial; font-size: 14px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        `;
        tooltip.innerHTML = '🎯 Click any element to select it';
        document.body.appendChild(tooltip);

        // Simple selector generation
        function makeSelector(el) {
            if (el.id) return '#' + el.id;

            let selector = el.tagName.toLowerCase();
            if (el.className) {
                let classes = el.className.trim().split(/\\s+/).slice(0, 2);
                if (classes.length > 0) {
                    selector += '.' + classes.join('.');
                }
            }
            return selector;
        }

        // Highlight element on hover
        let highlighted = null;
        function highlight(el) {
            if (highlighted) {
                highlighted.style.outline = '';
                highlighted.style.backgroundColor = '';
            }
            el.style.outline = '3px solid #4CAF50';
            el.style.backgroundColor = 'rgba(76, 175, 80, 0.1)';
            highlighted = el;
        }

        function clearHighlight() {
            if (highlighted) {
                highlighted.style.outline = '';
                highlighted.style.backgroundColor = '';
                highlighted = null;
            }
        }

        // Event handlers
        function handleMouseOver(e) {
            if (targeting) {
                e.preventDefault();
                highlight(e.target);
            }
        }

        function handleMouseOut(e) {
            if (targeting) {
                clearHighlight();
            }
        }

        function handleClick(e) {
            if (targeting) {
                e.preventDefault();
                e.stopPropagation();

                console.log('Element clicked:', e.target);

                let selector = makeSelector(e.target);
                let text = e.target.textContent.trim();

                // Find container (table row, list item, etc.)
                let container = e.target.closest('tr, li, .card, .item, [class*="row"]');
                let parent = e.target.parentElement;

                let suggestions = {
                    current: {
                        selector: selector,
                        text: text,
                        type: e.target.tagName.toLowerCase()
                    }
                };

                if (parent) {
                    suggestions.parent = {
                        selector: makeSelector(parent),
                        text: parent.textContent.trim()
                    };
                }

                if (container && container !== e.target && container !== parent) {
                    suggestions.container = {
                        selector: makeSelector(container),
                        text: container.textContent.trim()
                    };
                }

                window.selectedElement = {
                    selector: selector,
                    text: text,
                    suggestions: suggestions
                };

                console.log('Selection saved:', window.selectedElement);
                clearHighlight();
            }
        }

        // Cleanup function
        window.cleanupTargeting = function() {
            targeting = false;
            document.removeEventListener('mouseover', handleMouseOver, true);
            document.removeEventListener('mouseout', handleMouseOut, true);
            document.removeEventListener('click', handleClick, true);
            clearHighlight();
            let tooltip = document.getElementById('targeting-tooltip');
            if (tooltip) tooltip.remove();
        };

        // Add listeners
        document.addEventListener('mouseover', handleMouseOver, true);
        document.addEventListener('mouseout', handleMouseOut, true);
        document.addEventListener('click', handleClick, true);

        console.log('✅ Targeting setup complete');
        """

        self.page().runJavaScript(js_code)
        self.poll_timer.start(500)
        print("✅ Targeting JavaScript injected, polling started")

    def check_selection(self):
        """Check for element selection"""
        if not self.targeting_active:
            return

        def handle_result(result):
            if result and result != "null":
                print(f"📡 Received selection: {result}")
                try:
                    if isinstance(result, str):
                        data = json.loads(result)
                    else:
                        data = result

                    # Clear the selection but keep targeting active
                    self.page().runJavaScript("window.selectedElement = null;")

                    # Emit the selection
                    selector = data.get('selector', '')
                    text = data.get('text', '')
                    suggestions = data.get('suggestions', {})

                    print(f"🎯 Emitting selection: {selector}")
                    self.element_selected.emit(selector, text, suggestions)

                except Exception as e:
                    print(f"❌ Error parsing selection: {e}")

        # Get the selection from JavaScript
        self.page().runJavaScript("JSON.stringify(window.selectedElement)", handle_result)

    def disable_targeting(self):
        """Disable targeting"""
        print("🛑 Disabling targeting mode...")
        self.targeting_active = False
        self.poll_timer.stop()

        self.page().runJavaScript("""
        if (window.cleanupTargeting) {
            window.cleanupTargeting();
        }
        window.selectedElement = null;
        """)


class SelectorPanel(QWidget):
    """Panel for managing selectors with working save functionality"""

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
        self.selector_input.setPlaceholderText("Click an element to select it...")

        self.text_preview = QTextEdit()
        self.text_preview.setMaximumHeight(60)
        self.text_preview.setReadOnly(True)
        self.text_preview.setPlaceholderText("Element text will appear here...")

        form_layout.addRow("Selector:", self.selector_input)
        form_layout.addRow("Text:", self.text_preview)

        # Suggestion buttons
        buttons_layout = QHBoxLayout()
        self.current_btn = QPushButton("Current")
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

        # Field definition
        label_group = QGroupBox("Field Definition")
        label_layout = QFormLayout(label_group)

        self.field_name = QLineEdit()
        self.field_name.setPlaceholderText("e.g., player_name, ranking, points")

        self.semantic_label = QComboBox()
        self.semantic_label.addItems([
            "entity_name", "entity_score", "entity_ranking", "entity_location",
            "entity_date", "content_title", "content_body"
        ])

        # Status label for feedback
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.hide()

        label_layout.addRow("Field Name:", self.field_name)
        label_layout.addRow("Semantic Label:", self.semantic_label)
        label_layout.addRow("", self.status_label)

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

        # Disable buttons initially
        self.disable_all_buttons()

        # Timer for status message fadeout
        self.status_timer = QTimer()
        self.status_timer.setSingleShot(True)
        self.status_timer.timeout.connect(self.fade_status)

    def disable_all_buttons(self):
        """Disable all suggestion buttons"""
        self.current_btn.setEnabled(False)
        self.parent_btn.setEnabled(False)
        self.container_btn.setEnabled(False)
        self.save_btn.setEnabled(False)

    def show_status(self, message, is_success=True):
        """Show status message with visual feedback"""
        self.status_label.setText(message)
        if is_success:
            self.status_label.setProperty("class", "success")
        else:
            self.status_label.setProperty("class", "")
        self.status_label.style().polish(self.status_label)
        self.status_label.show()

        # Auto-hide after 3 seconds
        self.status_timer.start(3000)

    def fade_status(self):
        """Fade out status message"""
        self.status_label.setProperty("class", "fade")
        self.status_label.style().polish(self.status_label)

        # Hide completely after fade
        QTimer.singleShot(1000, self.status_label.hide)

    def update_selection(self, selector, text, suggestions):
        """Update with new element selection"""
        print(f"🎯 SelectorPanel received: {selector}, text: {text[:50]}...")

        self.current_suggestions = suggestions

        # Auto-choose container if available, otherwise current
        if suggestions.get('container'):
            selected_suggestion = suggestions['container']
            self.selector_input.setText(selected_suggestion['selector'])
            self.text_preview.setText(
                selected_suggestion['text'][:200] + "..." if len(selected_suggestion['text']) > 200 else
                selected_suggestion['text'])

            # Update button states
            self.current_btn.setText("Current")
            self.parent_btn.setText("Parent")
            self.container_btn.setText("✓ Container")
            self.show_status("🎯 Auto-selected Container for better data capture", True)
        else:
            # Show current selection if no container
            self.selector_input.setText(selector)
            self.text_preview.setText(text[:200] + "..." if len(text) > 200 else text)
            self.current_btn.setText("✓ Current")
            self.parent_btn.setText("Parent")
            self.container_btn.setText("Container")

        # Enable appropriate buttons
        self.current_btn.setEnabled(True)

        if suggestions.get('parent'):
            self.parent_btn.setEnabled(True)
        else:
            self.parent_btn.setEnabled(False)

        if suggestions.get('container'):
            self.container_btn.setEnabled(True)
        else:
            self.container_btn.setEnabled(False)

        # ALWAYS enable save button when we have a selection
        self.save_btn.setEnabled(True)

        # Auto-suggest field name
        if not self.field_name.text():
            self.auto_suggest_field_name(text, suggestions)

    def auto_suggest_field_name(self, text, suggestions):
        """Auto-suggest field name based on content"""
        text_lower = text.lower()

        # Check if it looks like a name
        if any(word in text_lower for word in ['player', 'name']) or self.looks_like_name(text):
            self.field_name.setText("player_name")
            self.semantic_label.setCurrentText("entity_name")
        # Check if it's a number (ranking or rating)
        elif text.strip().isdigit():
            num = int(text.strip())
            if num < 100:  # Likely a ranking
                self.field_name.setText("ranking")
                self.semantic_label.setCurrentText("entity_ranking")
            else:  # Likely a rating/score
                self.field_name.setText("elo_rating")
                self.semantic_label.setCurrentText("entity_score")
        # Check for rating/score keywords
        elif any(word in text_lower for word in ['elo', 'rating', 'score', 'points']):
            self.field_name.setText("elo_rating")
            self.semantic_label.setCurrentText("entity_score")
        else:
            # Generic fallback
            self.field_name.setText("data_field")

    def looks_like_name(self, text):
        """Check if text looks like a person's name"""
        words = text.strip().split()
        if len(words) >= 2:
            # Check if words start with capital letters (likely names)
            return all(word[0].isupper() for word in words if word)
        return False

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
        print("💾 Save button clicked!")

        field_name = self.field_name.text().strip()
        selector = self.selector_input.text().strip()

        if not field_name:
            self.show_status("❌ Please provide a field name", False)
            return

        if not selector:
            self.show_status("❌ No selector available", False)
            return

        selector_data = {
            "name": field_name,
            "selector": selector,
            "semantic_label": self.semantic_label.currentText(),
            "rag_importance": "medium",
            "extraction_type": "text"
        }

        self.selectors.append(selector_data)
        list_item_text = f"✅ {selector_data['name']} ({selector_data['semantic_label']})"
        self.selectors_list.addItem(list_item_text)

        # Visual feedback
        self.show_status(f"✅ Saved '{selector_data['name']}' successfully!", True)

        # Brief success animation on save button
        self.save_btn.setProperty("class", "success")
        self.save_btn.style().polish(self.save_btn)
        QTimer.singleShot(1000, self.reset_save_button)

        # Emit signal
        self.selector_created.emit(selector_data)
        print(f"📡 Emitted selector: {selector_data}")

        # Clear form for next selection
        self.field_name.clear()
        self.selector_input.clear()
        self.text_preview.clear()
        self.disable_all_buttons()

        # Reset button text
        self.current_btn.setText("Current")
        self.parent_btn.setText("Parent")
        self.container_btn.setText("Container")

    def reset_save_button(self):
        """Reset save button styling"""
        self.save_btn.setProperty("class", "go")
        self.save_btn.style().polish(self.save_btn)

    def delete_selected(self):
        """Delete selected selector"""
        current_row = self.selectors_list.currentRow()
        if current_row >= 0:
            self.selectors_list.takeItem(current_row)
            if current_row < len(self.selectors):
                deleted_name = self.selectors[current_row]['name']
                del self.selectors[current_row]
                self.show_status(f"🗑️ Deleted '{deleted_name}'", True)

    def clear_all(self):
        """Clear all selectors"""
        if not self.selectors:
            self.show_status("No selectors to clear", False)
            return

        reply = QMessageBox.question(self, "Clear All", "Clear all selectors?")
        if reply == QMessageBox.Yes:
            count = len(self.selectors)
            self.selectors.clear()
            self.selectors_list.clear()
            self.show_status(f"🗑️ Cleared {count} selectors", True)

    def save_project(self):
        """Save project to file"""
        if not self.selectors:
            self.show_status("❌ No selectors to save", False)
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Project", "tennis_project.json", "JSON files (*.json)"
        )

        if filename:
            project_data = {
                "name": "Tennis Selector Project",
                "created": datetime.now().isoformat(),
                "selectors": self.selectors
            }

            try:
                with open(filename, 'w') as f:
                    json.dump(project_data, f, indent=2)
                self.show_status(f"💾 Project saved to {Path(filename).name}", True)
            except Exception as e:
                self.show_status(f"❌ Save failed: {e}", False)

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
                    self.selectors_list.addItem(f"✅ {selector['name']} ({selector['semantic_label']})")

                self.show_status(f"📁 Loaded {len(self.selectors)} selectors", True)

                # Send to scraper panel
                for selector in self.selectors:
                    self.selector_created.emit(selector)

            except Exception as e:
                self.show_status(f"❌ Load failed: {e}", False)


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
        self.log_text.setMaximumHeight(100)

        # Results button
        self.view_results_btn = QPushButton("📊 View Results")
        self.view_results_btn.clicked.connect(self.view_results)
        self.view_results_btn.setEnabled(False)

        layout.addWidget(self.status_label)
        layout.addLayout(url_layout)
        layout.addWidget(self.count_label)
        layout.addLayout(buttons_layout)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.view_results_btn)
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
        print(f"📋 ScraperPanel received selector: {selector_data}")
        self.selectors.append(selector_data)
        self.count_label.setText(f"📋 {len(self.selectors)} selectors ready")
        self.log_text.appendPlainText(f"✅ Added: {selector_data['name']}")

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
            project_name="tennis_scrape"
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
                self.view_results_btn.setEnabled(True)  # Enable results button
                items = job.get("items_scraped", 0)
                self.log_text.appendPlainText(f"✅ Complete: {items} items")

    def view_results(self):
        """View extracted data with thorough search"""
        try:
            from pathlib import Path
            import json
            import os

            # Search in multiple possible locations
            possible_dirs = [
                Path("data_exports"),
                Path("./data_exports"),
                Path("../data_exports"),
                Path(os.getcwd()) / "data_exports",
                Path("temp_exports"),
                Path(".")  # Current directory
            ]

            all_files = []
            search_info = []

            for search_dir in possible_dirs:
                search_info.append(f"Checking: {search_dir.absolute()}")
                if search_dir.exists():
                    # Look for any JSON or JSONL files
                    json_files = list(search_dir.rglob("*.json*"))
                    all_files.extend(json_files)
                    search_info.append(f"  Found {len(json_files)} files")
                else:
                    search_info.append(f"  Directory doesn't exist")

            # Also check for any recent files in current directory
            current_dir = Path(".")
            recent_files = [f for f in current_dir.glob("*") if
                            f.suffix in ['.json', '.jsonl'] and f.stat().st_mtime > (time.time() - 3600)]
            all_files.extend(recent_files)

            if not all_files:
                # Show detailed search info
                debug_msg = "No data files found. Search details:\n\n" + "\n".join(search_info)
                debug_msg += f"\n\nCurrent working directory: {os.getcwd()}"
                debug_msg += f"\nFiles in current dir: {[f.name for f in Path('.').iterdir() if f.is_file()]}"

                QMessageBox.information(self, "Debug Info", debug_msg)
                return

            # Get the most recent file
            latest_file = max(all_files, key=lambda f: f.stat().st_mtime)

            # Try to read the data
            results = []
            file_content = ""

            try:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    file_content = f.read()

                # Try JSONL format first (one JSON object per line)
                if latest_file.suffix == '.jsonl':
                    for line in file_content.split('\n'):
                        if line.strip():
                            results.append(json.loads(line))
                else:
                    # Try regular JSON
                    results = [json.loads(file_content)]

            except json.JSONDecodeError:
                # Show raw content if can't parse as JSON
                pass

            # Show results dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Data from: {latest_file.name}")
            dialog.setModal(True)
            dialog.resize(900, 700)

            layout = QVBoxLayout(dialog)

            # File info
            info_label = QLabel(
                f"File: {latest_file.absolute()}\nSize: {latest_file.stat().st_size} bytes\nModified: {latest_file.stat().st_mtime}")
            info_label.setStyleSheet("font-weight: bold; color: #4CAF50; background: #2a2a2a; padding: 10px;")

            # Show the data
            text_area = QTextEdit()
            text_area.setReadOnly(True)
            text_area.setFont(QFont("Consolas", 10))

            if results:
                formatted_data = json.dumps(results, indent=2)
                text_area.setText(formatted_data)
                summary = QLabel(f"✅ Found {len(results)} JSON objects")
            else:
                text_area.setText(file_content)
                summary = QLabel(f"📄 Raw file content ({len(file_content)} chars)")

            summary.setStyleSheet("font-weight: bold; color: #4CAF50;")

            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)

            layout.addWidget(info_label)
            layout.addWidget(summary)
            layout.addWidget(text_area)
            layout.addWidget(close_btn)

            dialog.exec()

        except Exception as e:
            import traceback
            error_msg = f"Error: {e}\n\nTraceback:\n{traceback.format_exc()}"
            QMessageBox.critical(self, "View Results Error", error_msg)


class SelectorScraperTool(QMainWindow):
    """Main application"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Selector to Scraper Tool - FIXED VERSION")
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

        # Connect signals - THIS IS CRITICAL!
        self.load_btn.clicked.connect(self.load_page)
        self.target_btn.clicked.connect(self.toggle_targeting)
        self.browser.element_selected.connect(self.selector_panel.update_selection)
        self.selector_panel.selector_created.connect(self.scraper_panel.add_selector)
        self.selector_panel.selector_created.connect(self.auto_fill_url)

        print("🎯 SelectorScraperTool initialized with all signal connections")

    def load_page(self):
        """Load page"""
        url = self.url_input.text().strip()
        if url:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            print(f"🌐 Loading: {url}")
            self.browser.load(QUrl(url))

    def toggle_targeting(self):
        """Toggle targeting mode"""
        if self.target_btn.text() == "Target Elements":
            print("🎯 Starting targeting mode...")
            self.browser.enable_targeting()
            self.target_btn.setText("Stop Targeting")
            self.target_btn.setProperty("class", "")
            self.target_btn.style().polish(self.target_btn)
            print("✅ Targeting mode active - click elements on the page!")
        else:
            print("🛑 Stopping targeting mode...")
            self.browser.disable_targeting()
            self.target_btn.setText("Target Elements")
            self.target_btn.setProperty("class", "go")
            self.target_btn.style().polish(self.target_btn)

    def auto_fill_url(self, selector_data):
        """Auto-fill target URL"""
        current_url = self.browser.url().toString()
        if current_url and current_url != "about:blank":
            self.scraper_panel.target_url.setText(current_url)
            print(f"🔗 Auto-filled URL: {current_url}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME)

    print("🚀 Starting Selector to Scraper Tool...")
    window = SelectorScraperTool()
    window.show()

    sys.exit(app.exec())