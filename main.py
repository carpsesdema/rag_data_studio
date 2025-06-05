#!/usr/bin/env python3
"""
Data Extractor Studio - Main Entry Point

Launch either the visual scraping GUI or the backend scraping interface.
"""

import sys
import os
import argparse
from pathlib import Path

# Add the project root to the Python path.
# This ensures that imports like `from rag_data_studio.components...` work correctly.
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def launch_visual_studio():
    """Launch the main Data Extractor Studio visual interface"""
    try:
        # Import the main window class and the application object
        from PySide6.QtWidgets import QApplication
        from rag_data_studio.main_application import DataExtractorStudio, DARK_THEME

        app = QApplication(sys.argv)
        app.setApplicationName("Data Extractor Studio")
        app.setStyle("Fusion")

        window = DataExtractorStudio()
        window.setStyleSheet(DARK_THEME)  # Apply the theme
        window.show()

        return app.exec()
    except ImportError as e:
        print(f"❌ Failed to import Data Extractor Studio GUI: {e}")
        print("💡 This might be a path issue or missing dependencies.")
        print("💡 Try running: pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"❌ An unexpected error occurred while launching the GUI: {e}")
        import traceback
        traceback.print_exc()
        return 1


def launch_backend_gui():
    """Launch the legacy backend scraping GUI"""
    try:
        from PySide6.QtWidgets import QApplication
        from gui.main_window import EnhancedMainWindow
        from utils.logger import setup_logger
        import config

        app = QApplication(sys.argv)
        app.setApplicationName("Legacy Scraper Backend")

        # Setup logging
        logger = setup_logger(name=config.APP_NAME, log_file=config.LOG_FILE_PATH)
        logger.info("Starting Legacy Scraper Backend GUI")

        window = EnhancedMainWindow()
        window.show()

        return app.exec()
    except ImportError as e:
        print(f"❌ Failed to import Legacy Backend GUI: {e}")
        return 1


def run_scraper_cli(query_or_config):
    """Run the scraper from command line"""
    try:
        from scraper.searcher import search_and_fetch
        from utils.logger import setup_logger
        import config

        logger = setup_logger(name=config.APP_NAME, log_file=config.LOG_FILE_PATH)
        logger.info(f"Starting CLI scraper for: {query_or_config}")

        enriched_items, _ = search_and_fetch(  # search_and_fetch now returns (items, metrics)
            query_or_config_path=query_or_config,
            logger=logger
        )

        print(f"\n🎯 Scraping completed!")
        print(f"📊 Processed {len(enriched_items)} items")
        # Note: The backend doesn't directly save anymore, so this message might be misleading.
        # The GUI handles saving. For CLI runs, you might want to add a save step here.
        print(f"ℹ️  To save results from a CLI run, an explicit save step would be needed.")

        return 0
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Data Extractor Studio Platform")
    parser.add_argument("--mode", choices=["visual", "backend", "cli"], default="visual",
                        help="Launch mode: 'visual' (main GUI), 'backend' (legacy GUI), or 'cli' (command line)")
    parser.add_argument("--query", type=str, help="Query or config file path for CLI mode")

    args = parser.parse_args()

    # Create necessary directories if they don't exist
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data_exports", exist_ok=True)
    os.makedirs("configs", exist_ok=True)

    print("🎯 Data Extractor Studio")
    print("=" * 50)

    if args.mode == "visual":
        print("🚀 Launching Visual Studio...")
        return launch_visual_studio()
    elif args.mode == "backend":
        print("🔧 Launching Legacy Backend GUI...")
        return launch_backend_gui()
    elif args.mode == "cli":
        if not args.query:
            print("❌ CLI mode requires a --query argument (e.g., a URL or config file path)")
            return 1
        print(f"⚡ Running CLI scraper for: {args.query}")
        return run_scraper_cli(args.query)

    return 0


if __name__ == "__main__":
    sys.exit(main())