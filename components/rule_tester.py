from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from bs4 import BeautifulSoup
import requests
import re
from PySide6.QtCore import QThread, Signal


@dataclass
class TestResult:
    rule_name: str
    selector: str
    found_elements: int
    sample_values: List[str]
    success: bool
    error_message: Optional[str] = None


class RuleTester(QThread):
    """Test scraping rules against live pages"""

    results_ready = Signal(list)  # List[TestResult]
    progress_update = Signal(str, int)

    def __init__(self, rules: List, url: str):
        super().__init__()
        self.rules = rules
        self.url = url

    def run(self):
        """Test all rules against the target URL"""
        results = []

        try:
            self.progress_update.emit("Fetching page content...", 10)
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            for i, rule in enumerate(self.rules):
                self.progress_update.emit(f"Testing rule: {rule.name}", 20 + (i * 70 // len(self.rules)))

                try:
                    elements = soup.select(rule.selector)
                    sample_values = []

                    for elem in elements[:5]:  # Sample first 5 matches
                        if rule.extraction_type == "text":
                            value = elem.get_text(strip=True)
                        elif rule.extraction_type == "attribute" and rule.attribute_name:
                            value = elem.get(rule.attribute_name, "")
                        elif rule.extraction_type == "html":
                            value = str(elem)[:100] + "..." if len(str(elem)) > 100 else str(elem)
                        else:
                            value = elem.get_text(strip=True)

                        if value:
                            sample_values.append(str(value))

                    results.append(TestResult(
                        rule_name=rule.name,
                        selector=rule.selector,
                        found_elements=len(elements),
                        sample_values=sample_values,
                        success=len(elements) > 0
                    ))

                except Exception as e:
                    results.append(TestResult(
                        rule_name=rule.name,
                        selector=rule.selector,
                        found_elements=0,
                        sample_values=[],
                        success=False,
                        error_message=str(e)
                    ))

        except Exception as e:
            self.progress_update.emit(f"Error: {e}", 100)
            return

        self.progress_update.emit("Testing complete", 100)
        self.results_ready.emit(results)
