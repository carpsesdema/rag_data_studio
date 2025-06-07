# rag_data_studio/integration/backend_bridge.py
"""
Integration bridge between RAG Data Studio GUI and the scraping backend.
Focuses on running the pipeline with GUI-generated config and testing selectors.
"""

import logging  # Use standard logging
import os
import tempfile
from typing import List, Dict, Any, Optional

import yaml
from PySide6.QtGui import QColor
# GUI Extensions that were in this file (or a similar one)
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLabel

from scraper.rag_models import EnrichedItem  # RAGOutputItem removed
from scraper.searcher import run_professional_pipeline
from utils.logger import setup_logger  # Assuming setup_logger is in utils


# Add existing scraper modules to path if this script can be run standalone
# This might not be necessary if backend_bridge is always imported by main_application
# which should already handle sys.path.
# current_dir = Path(__file__).parent
# project_root = current_dir.parent.parent # Adjust based on your actual project structure
# sys.path.append(str(project_root))
# sys.path.append(str(project_root / "scraper"))


class RAGStudioBridge:
    """Bridge between GUI and scraping backend"""

    def __init__(self):
        # It's better if the main application passes a logger instance.
        # If this bridge is instantiated by the GUI, the GUI's logger can be passed.
        self.logger = logging.getLogger("RAGStudioBridge")
        if not self.logger.handlers:
            # Fallback basic setup if no logger is configured by the caller
            self.logger = setup_logger("RAGStudioBridge", log_file="rag_studio_bridge.log")
        self.logger.info("RAGStudioBridge initialized.")

    def run_scraping_pipeline_with_config_data(
            self,
            project_config_data: Dict[str, Any],
            progress_callback_gui: Optional[callable] = None
    ) -> List[EnrichedItem]:
        """
        Run scraping pipeline using existing backend with GUI-generated config data.

        Args:
            project_config_data: Python dictionary representing the YAML configuration.
            progress_callback_gui: Optional callback for GUI progress updates.

        Returns:
            List of enriched items from scraping pipeline.
        """
        temp_config_path = None
        try:
            # Create temporary YAML config file from the dictionary
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as temp_file:
                yaml.dump(project_config_data, temp_file, default_flow_style=False, indent=2, allow_unicode=True)
                temp_config_path = temp_file.name

            self.logger.info(f"Running scraping pipeline with temporary config: {temp_config_path}")

            # Use existing search_and_fetch function (which calls run_professional_pipeline)
            # Pass the GUI's progress callback directly to search_and_fetch
            enriched_items, _ = run_professional_pipeline(  # search_and_fetch returns (items, metrics)
                query_or_config_path=temp_config_path,
                logger_instance=self.logger,  # Pass the bridge's logger or a dedicated pipeline logger
                progress_callback=progress_callback_gui  # Pass the GUI's callback
            )

            self.logger.info(f"Scraping pipeline completed. Processed {len(enriched_items)} items using temp config.")
            return enriched_items

        except Exception as e:
            self.logger.error(f"Error running scraping pipeline with config data: {e}", exc_info=True)
            return []
        finally:
            if temp_config_path and os.path.exists(temp_config_path):
                try:
                    os.unlink(temp_config_path)
                    self.logger.debug(f"Cleaned up temporary config file: {temp_config_path}")
                except Exception as e_unlink:
                    self.logger.warning(f"Could not delete temp config file {temp_config_path}: {e_unlink}")

    # _progress_callback is removed as we pass the GUI's callback directly.

    def test_selectors_on_url(self, url: str, selectors_config: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Test scraping rules (selectors) against a specific URL.

        Args:
            url: Target URL to test.
            selectors_config: List of selector configurations. Each dict should contain
                              at least 'name' and 'selector'. Optional fields include
                              'extract_type', 'attribute_name'.

        Returns:
            Test results for each selector:
            {
                'selector_name_1': {
                    'success': bool,
                    'found_count': int,
                    'sample_values': List[str],
                    'error': Optional[str]
                }, ...
            }
        """
        results = {}
        if not url or not selectors_config:
            self.logger.warning("Test selectors: URL or selectors config is empty.")
            return {"error": "URL or selector definitions cannot be empty."}

        try:
            import requests  # Keep requests import local to this method if only used here
            from bs4 import BeautifulSoup

            self.logger.info(f"Testing {len(selectors_config)} selectors on URL: {url}")
            response = requests.get(url, timeout=15, headers={'User-Agent': 'RAGDataStudio-SelectorTester/1.0'})
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            for sel_config in selectors_config:
                name = sel_config.get('name', 'UnnamedSelector')
                selector_str = sel_config.get('selector')
                extract_type = sel_config.get('extract_type', 'text')  # Default to 'text'
                attribute_name = sel_config.get('attribute_name')  # For 'attribute' type
                # is_list = sel_config.get('is_list', False) # For future use if needed

                if not selector_str:
                    results[name] = {'success': False, 'found_count': 0, 'sample_values': [],
                                     'error': 'Selector string is empty.'}
                    continue

                current_result = {'success': False, 'found_count': 0, 'sample_values': [], 'error': None}
                try:
                    elements = soup.select(selector_str)
                    current_result['found_count'] = len(elements)

                    if elements:
                        current_result['success'] = True
                        sample_values = []
                        for elem in elements[:5]:  # Sample first 5 matches
                            value = None
                            if extract_type == "text":
                                value = elem.get_text(strip=True)
                            elif extract_type == "attribute" and attribute_name:
                                value = elem.get(attribute_name)
                                if isinstance(value, list):  # Some attributes return a list
                                    value = " ".join(value)
                            elif extract_type == "html":
                                value = str(elem)
                            else:  # Fallback or if extract_type is unknown
                                value = elem.get_text(strip=True)

                            if value is not None:  # Ensure value is not None before converting to str
                                value_str = str(value)
                                sample_values.append(value_str[:150] + '...' if len(value_str) > 150 else value_str)

                        current_result['sample_values'] = sample_values
                    else:
                        current_result['error'] = "No elements found matching selector."

                except Exception as e_select:
                    self.logger.warning(f"Error testing selector '{name}' ({selector_str}) on {url}: {e_select}")
                    current_result['error'] = str(e_select)

                results[name] = current_result

            self.logger.info(f"Selector testing completed for {url}. Results: {len(results)} selectors tested.")

        except requests.exceptions.RequestException as e_req:
            self.logger.error(f"Request failed for URL {url} during selector testing: {e_req}")
            return {"error": f"Failed to fetch URL: {e_req}"}
        except Exception as e_general:
            self.logger.error(f"General error during selector testing for {url}: {e_general}", exc_info=True)
            return {"error": f"An unexpected error occurred: {e_general}"}

        return results

    # validate_rag_output and _generate_recommendations are removed.


class TestResultsDialog(QDialog):
    """Dialog to show selector testing results"""

    def __init__(self, results: Dict[str, Any], parent=None, test_url="N/A"):
        super().__init__(parent)
        self.setWindowTitle(f"Selector Test Results for: {test_url}")
        self.setModal(True)
        self.resize(800, 600)

        layout = QVBoxLayout(self)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)  # Name, Status, Count, Samples
        self.results_table.setHorizontalHeaderLabels([
            "Rule Name", "Status", "Found Count", "Sample Values (up to 5)"
        ])
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setWordWrap(True)  # Allow text wrapping in cells

        if "error" in results:  # Handle global error like URL fetch failure
            self.results_table.setRowCount(1)
            self.results_table.setItem(0, 0, QTableWidgetItem("Error"))
            error_item = QTableWidgetItem(results["error"])
            self.results_table.setItem(0, 1, error_item)
            self.results_table.setSpan(0, 1, 1, 3)  # Span error message across other columns
        else:
            self.results_table.setRowCount(len(results))
            for row, (name, result_data) in enumerate(results.items()):
                self.results_table.setItem(row, 0, QTableWidgetItem(name))

                status_text = "✅ Success" if result_data.get('success') else "❌ Failed"
                if result_data.get('error'):
                    status_text += f" ({result_data.get('error')})"

                status_item = QTableWidgetItem(status_text)
                if result_data.get('success'):
                    status_item.setBackground(QColor(200, 255, 200))  # Light green
                else:
                    status_item.setBackground(QColor(255, 200, 200))  # Light red
                self.results_table.setItem(row, 1, status_item)

                self.results_table.setItem(row, 2, QTableWidgetItem(str(result_data.get('found_count', 0))))

                sample_text = "\n---\n".join(result_data.get('sample_values', []))
                if not sample_text and not result_data.get('success') and not result_data.get('error'):
                    sample_text = "No elements found."
                elif not sample_text and result_data.get('error'):
                    sample_text = "Error during extraction."

                self.results_table.setItem(row, 3, QTableWidgetItem(sample_text))

        self.results_table.resizeColumnsToContents()
        self.results_table.resizeRowsToContents()
        # Set horizontal header to stretch last section
        self.results_table.horizontalHeader().setStretchLastSection(True)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)

        layout.addWidget(QLabel(f"Test Results for URL: {test_url}"))
        layout.addWidget(self.results_table)
        layout.addWidget(close_btn)


# RAGValidationDialog is removed.

# Example usage (if this module were run directly)
if __name__ == "__main__":
    # This example assumes you have a local web server or a public site to test against.
    # For a real test, you'd need the RAG Data Studio GUI to create a project_config.

    # Basic logger for standalone run
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    bridge = RAGStudioBridge()

    # --- Example for run_scraping_pipeline_with_config_data ---
    example_project_config_data = {
        "domain_info": {"name": "Tennis Test Project", "domain": "sports"},
        "sources": [{
            "name": "atp_rankings_page",
            "seeds": ["https://www.atptour.com/en/rankings/singles"],  # A real URL
            "source_type": "player_rankings",
            "selectors": {
                "custom_fields": [
                    {"name": "page_title", "selector": "title", "extract_type": "text"},
                    {
                        "name": "player_rows", "selector": "table.desktop-table tbody tr",
                        "extract_type": "structured_list", "is_list": True,
                        "sub_selectors": [
                            {"name": "rank", "selector": "td.rank-cell", "extract_type": "text"},
                            {"name": "player_name", "selector": ".player-cell a", "extract_type": "text"}
                        ]
                    }
                ]
            },
            "crawl_config": {"depth": 0, "delay_seconds": 1},  # Aliased as "crawl" in config file
            "export_config": {"format": "jsonl", "output_path": "./temp_export.jsonl"}  # Aliased as "export"
        }]
    }

    print("\n--- Testing run_scraping_pipeline_with_config_data ---")


    # Dummy progress callback for testing
    def gui_progress(msg, percent):
        print(f"GUI Progress: {percent}% - {msg}")


    # enriched_items_from_pipeline = bridge.run_scraping_pipeline_with_config_data(
    #     example_project_config_data,
    #     progress_callback_gui=gui_progress
    # )
    # if enriched_items_from_pipeline:
    #     print(f"Pipeline run successful. Got {len(enriched_items_from_pipeline)} enriched items.")
    #     print("First item's custom fields:", enriched_items_from_pipeline[0].custom_fields)
    # else:
    #     print("Pipeline run did not return items or failed.")

    # --- Example for test_selectors_on_url ---
    print("\n--- Testing test_selectors_on_url ---")
    test_url_for_selectors = "https://www.atptour.com/en/rankings/singles"  # Make sure this URL is accessible
    selectors_to_test = [
        {"name": "Page Title", "selector": "title", "extract_type": "text"},
        {"name": "NonExistentElement", "selector": "#this-id-does-not-exist", "extract_type": "text"},
        {"name": "Player Names", "selector": ".player-cell a", "extract_type": "text", "is_list": True},
        {"name": "Player Ranks", "selector": "td.rank-cell", "extract_type": "text", "is_list": True},
        {"name": "Invalid Selector Syntax", "selector": "td[attribute='value", "extract_type": "text"},
    ]

    test_sel_results = bridge.test_selectors_on_url(test_url_for_selectors, selectors_to_test)
    print("Selector Test Results (raw dict):")
    import json

    print(json.dumps(test_sel_results, indent=2))

    # To show the dialog (requires a QApplication instance)
    # This part won't run well without a full Qt app loop, but shows instantiation.
    # if __name__ == '__main__' and 'QApplication' not in sys.modules: # Check if running in a Qt context
    # try:
    #     from PySide6.QtWidgets import QApplication
    #     app_instance = QApplication.instance() or QApplication(sys.argv)

    #     dialog = TestResultsDialog(test_sel_results, test_url=test_url_for_selectors)
    #     dialog.show()
    #     # In a real app, app_instance.exec() would be running.
    #     # For a simple script, you might need dialog.exec() if it's the only window.
    #     # dialog.exec() # This would block here

    # except ImportError:
    #     print("PySide6 not found, cannot show TestResultsDialog example.")
    # except RuntimeError as e:
    #     print(f"Could not create QApplication for dialog test: {e}")

    print("\nBridge testing finished.")