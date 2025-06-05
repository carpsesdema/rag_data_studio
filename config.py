# config.py - Main Configuration File for RAG Data Studio

import os
from pathlib import Path

# =============================================================================
# Application Settings
# =============================================================================
APP_NAME = "RAGDataStudio"
VERSION = "1.0.0"

# =============================================================================
# Logging Configuration
# =============================================================================
DEFAULT_LOGGER_NAME = "rag_scraper"
LOG_FILE_PATH = "logs/rag_scraper.log"
LOG_LEVEL_CONSOLE = "INFO"
LOG_LEVEL_FILE = "DEBUG"

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# =============================================================================
# GUI Configuration
# =============================================================================
DEFAULT_WINDOW_TITLE = "RAG Data Studio - Professional Scraping Platform"
DEFAULT_WINDOW_WIDTH = 1400
DEFAULT_WINDOW_HEIGHT = 900

SHOW_CONTENT_TYPE_SELECTOR_GUI = True
DEFAULT_CONTENT_TYPE_FOR_GUI = "auto"

# Content type display names for GUI
LANGUAGE_DISPLAY_NAMES_GUI = {
    "auto": "Auto-detect",
    "html": "HTML/Web Pages",
    "pdf": "PDF Documents",
    "text": "Plain Text",
    "json": "JSON Data",
    "xml": "XML/RSS Feeds"
}

# Content types enabled
CONTENT_TYPES = {
    "auto": True,
    "html": True,
    "pdf": True,
    "text": True,
    "json": True,
    "xml": True
}

# =============================================================================
# HTTP/Fetching Configuration
# =============================================================================
USER_AGENT = "RAGDataStudio/1.0 (+https://github.com/yourusername/rag-data-studio)"
DEFAULT_REQUEST_TIMEOUT = 30
MAX_CONCURRENT_FETCHERS = 3

# =============================================================================
# Search Configuration
# =============================================================================
AUTONOMOUS_SEARCH_MAX_RESULTS = 5
DUCKDUCKGO_SEARCH_DELAY = 1.5
SEARCH_SOURCES_COUNT = 5

# =============================================================================
# Content Processing Configuration
# =============================================================================
DEFAULT_CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MIN_CHUNK_SIZE = 100
MIN_CHUNK_SIZE_EXPORT = 50

# =============================================================================
# Quality Filter Configuration
# =============================================================================
QUALITY_FILTER_ENABLED = True
QUALITY_MIN_LENGTH = 100
QUALITY_SUBSTANTIAL_LENGTH = 500
QUALITY_COMPREHENSIVE_LENGTH = 2000
QUALITY_MIN_SCORE = 3

# =============================================================================
# Export Configuration
# =============================================================================
DEFAULT_EXPORT_DIR = "./data_exports"
DEFAULT_EXPORT_FORMATS_SUPPORTED = ["jsonl", "markdown", "csv", "json"]
EXPORT_VALIDATION_ENABLED = True

# Create export directory if it doesn't exist
os.makedirs(DEFAULT_EXPORT_DIR, exist_ok=True)

# =============================================================================
# NLP Configuration
# =============================================================================
SPACY_MODEL_NAME = "en_core_web_sm"

# =============================================================================
# Rate Limiting Configuration
# =============================================================================
DEFAULT_DELAY_BETWEEN_REQUESTS = 2.0
RESPECT_ROBOTS_TXT = True

# =============================================================================
# File Paths
# =============================================================================
BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "configs"
TEMP_DIR = BASE_DIR / "temp"
DATA_DIR = BASE_DIR / "data"

# Create directories if they don't exist
for dir_path in [CONFIG_DIR, TEMP_DIR, DATA_DIR]:
    dir_path.mkdir(exist_ok=True)

# =============================================================================
# Debug Settings
# =============================================================================
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
VERBOSE_LOGGING = DEBUG_MODE