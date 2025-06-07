#!/usr/bin/env python3
"""
RAG Data Studio - Main Entry Point

Launch either the visual scraping GUI or the backend scraping interface.
"""

import sys
import os
import time
import threading
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def launch_visual_studio():
    """Launch the main RAG Data Studio visual interface"""
    try:
        from rag_data_studio.main_application import QApplication, RAGDataStudio, DARK_THEME

        app = QApplication(sys.argv)
        app.setApplicationName("RAG Data Studio")
        app.setStyle("Fusion")

        window = RAGDataStudio()
        window.show()

        return app.exec()
    except ImportError as e:
        print(f"❌ Failed to import RAG Data Studio GUI: {e}")
        print("💡 Try installing missing dependencies: pip install PySide6")
        return 1


def launch_backend_gui():
    """Launch the backend scraping GUI"""
    try:
        from gui.main_window import QApplication, EnhancedMainWindow
        from utils.logger import setup_logger
        import config

        app = QApplication(sys.argv)
        app.setApplicationName("RAG Scraper Backend")

        # Setup logging
        logger = setup_logger(name=config.APP_NAME, log_file=config.LOG_FILE_PATH)
        logger.info("Starting RAG Scraper Backend GUI")

        window = EnhancedMainWindow()
        window.show()

        return app.exec()
    except ImportError as e:
        print(f"❌ Failed to import Backend GUI: {e}")
        return 1


def launch_selector_tool():
    """Launch the selector to scraper tool with integrated service"""
    try:
        from PySide6.QtWidgets import QApplication
        from scraper_service import ScraperService
        from selector_scraper import SelectorScraperTool, DARK_THEME

        print("🚀 Starting Selector to Scraper Tool...")

        # Start scraper service in background thread
        def start_service():
            try:
                service = ScraperService()
                service.start_service()
            except Exception as e:
                print(f"Scraper service error: {e}")

        service_thread = threading.Thread(target=start_service, daemon=True)
        service_thread.start()

        # Give service a moment to start
        time.sleep(1)
        print("✅ Scraper service starting in background")

        # Start GUI
        app = QApplication(sys.argv)
        app.setStyleSheet(DARK_THEME)

        window = SelectorScraperTool()
        window.show()

        print("✅ GUI started")
        print("📋 Ready: Load page → Target elements → Send to scraper")

        return app.exec()

    except ImportError as e:
        print(f"❌ Failed to import Selector Tool: {e}")
        print("💡 Make sure scraper_service.py and selector_scraper.py are available")
        return 1


def run_scraper_cli(query_or_config):
    """Run the scraper from command line"""
    try:
        from scraper.searcher import search_and_fetch
        from utils.logger import setup_logger
        import config

        logger = setup_logger(name=config.APP_NAME, log_file=config.LOG_FILE_PATH)
        logger.info(f"Starting CLI scraper for: {query_or_config}")

        enriched_items = search_and_fetch(
            query_or_config_path=query_or_config,
            logger=logger
        )

        print(f"\n🎯 Scraping completed!")
        print(f"📊 Processed {len(enriched_items)} items")
        print(f"📁 Data exported to: {config.DEFAULT_EXPORT_DIR}")

        return 0
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(description="RAG Data Studio - Professional Scraping Platform")
    parser.add_argument("--mode", choices=["visual", "backend", "selector", "cli"], default="selector",
                        help="Launch mode: visual (main GUI), backend (scraper GUI), selector (new tool), or cli (command line)")
    parser.add_argument("--query", type=str, help="Query or config file path for CLI mode")

    args = parser.parse_args()

    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data_exports", exist_ok=True)
    os.makedirs("configs", exist_ok=True)

    print("🎯 RAG Data Studio")
    print("=" * 50)

    if args.mode == "visual":
        print("🚀 Launching Visual Scraping Studio...")
        return launch_visual_studio()
    elif args.mode == "backend":
        print("🔧 Launching Backend GUI...")
        return launch_backend_gui()
    elif args.mode == "selector":
        print("🎯 Launching Selector to Scraper Tool...")
        return launch_selector_tool()
    elif args.mode == "cli":
        if not args.query:
            print("❌ CLI mode requires --query parameter")
            return 1
        print(f"⚡ Running CLI scraper for: {args.query}")
        return run_scraper_cli(args.query)


if __name__ == "__main__":
    sys.exit(main())