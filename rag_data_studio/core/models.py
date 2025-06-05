# rag_data_studio/core/models.py
"""
Core data models for the Data Extractor Studio application.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid

@dataclass
class ScrapingRule:
    """Scraping rule for structured data extraction."""
    id: str
    name: str
    selector: str
    description: Optional[str] = ""
    extraction_type: str = "text"
    attribute_name: Optional[str] = None
    is_list: bool = False
    data_type: str = "string"
    required: bool = False
    sub_selectors: List['ScrapingRule'] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)

@dataclass
class ProjectConfig:
    """Project configuration for structured scraping."""
    id: str
    name: str
    description: str
    domain: str
    target_websites: List[str]
    scraping_rules: List[ScrapingRule] = field(default_factory=list)
    output_settings: Dict[str, Any] = field(default_factory=lambda: {"format": "jsonl"})
    rate_limiting: Dict[str, Any] = field(default_factory=lambda: {"delay": 2.0, "respect_robots": True})
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    client_info: Optional[Dict[str, str]] = None