#!/usr/bin/env python3
"""
RAG Data Studio - Setup Test Script

Test if all components are properly installed and configured.
"""

import sys
import os
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))


def test_basic_imports():
    """Test basic Python imports"""
    print("🔍 Testing basic imports...")

    tests = [
        ("config", "Configuration module"),
        ("utils.logger", "Logger utilities"),
        ("scraper.rag_models", "RAG data models"),
        ("scraper.searcher", "Main scraper"),
        ("storage.saver", "Storage utilities"),
    ]

    results = []
    for module, description in tests:
        try:
            __import__(module)
            print(f"  ✅ {description}")
            results.append(True)
        except ImportError as e:
            print(f"  ❌ {description}: {e}")
            results.append(False)

    return all(results)


def test_dependencies():
    """Test external dependencies"""
    print("\n📦 Testing dependencies...")

    deps = [
        ("requests", "HTTP requests"),
        ("beautifulsoup4", "HTML parsing"),
        ("yaml", "YAML parsing"),
        ("pydantic", "Data validation"),
        ("trafilatura", "Content extraction"),
        ("spacy", "NLP processing"),
        ("langdetect", "Language detection"),
        ("duckduckgo_search", "Web search"),
        ("tqdm", "Progress bars"),
    ]

    results = []
    for module, description in deps:
        try:
            if module == "yaml":
                import yaml
            elif module == "beautifulsoup4":
                import bs4
            elif module == "duckduckgo_search":
                import duckduckgo_search
            else:
                __import__(module)
            print(f"  ✅ {description}")
            results.append(True)
        except ImportError as e:
            print(f"  ❌ {description}: {e}")
            results.append(False)

    return all(results)


def test_gui_dependencies():
    """Test GUI dependencies"""
    print("\n🖥️  Testing GUI dependencies...")

    gui_deps = [
        ("PySide6.QtWidgets", "Qt Widgets"),
        ("PySide6.QtCore", "Qt Core"),
        ("PySide6.QtGui", "Qt GUI"),
    ]

    results = []
    for module, description in gui_deps:
        try:
            __import__(module)
            print(f"  ✅ {description}")
            results.append(True)
        except ImportError as e:
            print(f"  ❌ {description}: {e}")
            results.append(False)

    if not all(results):
        print("  💡 Install with: pip install PySide6")

    return all(results)


def test_optional_dependencies():
    """Test optional dependencies"""
    print("\n🔧 Testing optional dependencies...")

    optional_deps = [
        ("selenium", "Web automation (optional)"),
        ("spacy", "Advanced NLP (requires model)"),
    ]

    for module, description in optional_deps:
        try:
            __import__(module)
            print(f"  ✅ {description}")
        except ImportError:
            print(f"  ⚠️  {description}: Not installed (optional)")


def test_spacy_model():
    """Test spaCy model installation"""
    print("\n🧠 Testing spaCy model...")

    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        print("  ✅ spaCy English model loaded")
        return True
    except OSError:
        print("  ❌ spaCy English model not found")
        print("  💡 Install with: python -m spacy download en_core_web_sm")
        return False
    except ImportError:
        print("  ❌ spaCy not installed")
        return False


def test_directories():
    """Test directory structure"""
    print("\n📁 Testing directory structure...")

    required_dirs = ["logs", "data_exports", "configs"]

    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"  ✅ {dir_name}/ directory exists")
        else:
            try:
                os.makedirs(dir_name, exist_ok=True)
                print(f"  ✅ {dir_name}/ directory created")
            except Exception as e:
                print(f"  ❌ Failed to create {dir_name}/: {e}")
                return False

    return True


def test_backend_functionality():
    """Test basic backend functionality"""
    print("\n⚙️  Testing backend functionality...")

    try:
        from utils.logger import setup_logger
        logger = setup_logger("test_logger", log_file="logs/test.log")
        logger.info("Test log message")
        print("  ✅ Logger setup working")

        from scraper.rag_models import FetchedItem
        from pydantic import HttpUrl
        test_item = FetchedItem(
            source_url=HttpUrl("https://example.com"),
            source_type="test",
            query_used="test_query"
        )
        print("  ✅ RAG models working")

        return True
    except Exception as e:
        print(f"  ❌ Backend test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🎯 RAG Data Studio - Setup Test")
    print("=" * 50)

    all_passed = True

    # Run tests
    all_passed &= test_basic_imports()
    all_passed &= test_dependencies()
    all_passed &= test_gui_dependencies()
    test_optional_dependencies()  # Don't fail on optional
    test_spacy_model()  # Don't fail on this
    all_passed &= test_directories()
    all_passed &= test_backend_functionality()

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All core tests passed! Your setup looks good.")
        print("\n🚀 Try running:")
        print("   python main.py --mode visual")
        print("   python main.py --mode backend")
    else:
        print("❌ Some tests failed. Please install missing dependencies:")
        print("   pip install -r requirements.txt")
        print("   python -m spacy download en_core_web_sm")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())