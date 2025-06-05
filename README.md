# README.md
# RAG Data Studio 🎯

**Professional Visual Scraping Platform for RAG and AI Agent Development**

Transform any website into structured data for your RAG systems with an intuitive visual interface. Perfect for freelance developers building custom AI solutions across diverse domains.

## ✨ Features

### 🎯 **Visual Element Targeting**
- **Click-to-create rules**: Simply click any element on a webpage to generate scraping rules
- **Smart selector generation**: Automatically creates robust CSS selectors  
- **Real-time preview**: See extracted data instantly

### 🧠 **RAG-Optimized Data Extraction**
- **Semantic labeling**: Tag data as `entity_name`, `entity_ranking`, `entity_score`, etc.
- **Importance levels**: Prioritize data as `critical`, `high`, `medium`, or `low`
- **Custom field extraction**: Target specific data points with precision

### 🏢 **Professional Project Management**
- **Multi-client support**: Organize work by client and domain
- **Domain templates**: Pre-configured rules for sports, finance, legal, medical, etc.
- **Export compatibility**: Generates YAML configs for existing scraping pipelines

### 🎨 **Modern Dark UI**
- Optimized for developer productivity
- Professional interface suitable for client demonstrations
- Color-coded elements for quick status identification

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/rag-data-studio.git
cd rag-data-studio

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install spaCy model for NLP features
python -m spacy download en_core_web_sm

# Run the application
python -m rag_data_studio.main_application
```

### Basic Usage

1. **Create a New Project**
   - Click "➕ New" in the Projects panel
   - Enter project name, domain, and target websites

2. **Load Target Website**
   - Enter URL in the browser toolbar
   - Click "🌐 Load" to open the page

3. **Start Targeting Elements**
   - Click "🎯 Target Elements" to enable targeting mode
   - Click any element on the page to create a scraping rule
   - Choose semantic labels and importance levels

4. **Test and Export**
   - Use "🧪 Test All" to validate your rules
   - Click "💾 Export Config" to generate YAML configuration
   - Run "🚀 Run Scrape" to execute the full pipeline

## 📁 Project Structure

```
rag-data-studio/
├── rag_data_studio/           # Main GUI application
│   ├── main_application.py    # Main window and application logic
│   ├── integration/           # Backend integration
│   │   └── backend_bridge.py  # Bridge to existing scraping pipeline
│   └── assets/                # UI assets and resources
├── scraper/                   # Existing scraping backend
│   ├── searcher.py           # Main scraping pipeline
│   ├── config_manager.py     # Configuration management
│   ├── content_router.py     # Content parsing and routing
│   ├── parser.py             # HTML/PDF parsing
│   ├── chunker.py            # RAG chunking
│   └── rag_models.py         # Data models
├── gui/                      # Original GUI components
├── storage/                  # Data storage and export
├── utils/                    # Utilities and helpers
├── wizards/                  # Configuration wizards
├── configs/                  # Configuration templates
├── requirements.txt          # Python dependencies
├── setup.py                 # Package setup
└── README.md                # This file
```

## 🎯 Use Cases

### **Sports Analytics**
Extract player statistics, rankings, match results, and performance metrics from sports websites.

### **Financial Data**
Collect stock prices, company financials, market data, and economic indicators.

### **Legal Research**
Gather case law, court decisions, legal precedents, and regulatory information.

### **Medical Research**
Extract clinical trial data, research papers, drug information, and medical statistics.

### **E-commerce Intelligence**
Monitor product prices, reviews, inventory, and competitive analysis.

## 🔧 Integration

RAG Data Studio integrates seamlessly with existing scraping pipelines:

## 📊 RAG Output Validation

Built-in validation ensures high-quality data for RAG systems:

- **Quality scoring** based on data completeness and structure
- **Semantic label analysis** to ensure proper categorization
- **Entity extraction validation** for knowledge base construction
- **Recommendations** for improving data quality

## 🛠️ Development

### Running Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run with coverage
pytest --cov=rag_data_studio tests/
```

### Code Quality

```bash
# Format code
black rag_data_studio/

# Lint code
flake8 rag_data_studio/

# Type checking
mypy rag_data_studio/
```

## 📦 Distribution

### Building Executable

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --name "RAG Data Studio" --windowed rag_data_studio/main_application.py

# The executable will be in dist/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Full documentation](https://docs.rag-data-studio.com)
- **Issues**: [GitHub Issues](https://github.com/yourusername/rag-data-studio/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/rag-data-studio/discussions)

## 🙏 Acknowledgments

- Built on top of [PySide6](https://doc.qt.io/qtforpython/) for the GUI framework
- Uses [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) and [Trafilatura](https://trafilatura.readthedocs.io/) for web scraping
- Powered by [spaCy](https://spacy.io/) for natural language processing

---

**Made with ❤️ for the RAG and AI development community**

---

# pyproject.toml
[build-system]
requires = ["setuptools>=65.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "rag-data-studio"
version = "1.0.0"
description = "Professional Visual Scraping Platform for RAG and AI Agent Development"
readme = "README.md"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
maintainers = [
    {name = "Your Name", email = "your.email@example.com"}
]
keywords = [
    "rag", "scraping", "ai", "data-extraction", "web-scraping", 
    "machine-learning", "gui", "visual-scraping", "data-studio"
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Operating System :: OS Independent",
]
requires-python = ">=3.8"
dependencies = [
    "PySide6>=6.5.0,<7.0.0",
    "PyQt6-WebEngine>=6.5.0,<7.0.0",
    "requests>=2.28.0,<3.0.0",
    "beautifulsoup4>=4.11.0,<5.0.0",
    "lxml>=4.9.0,<5.0.0",
    "trafilatura>=1.6.0,<2.0.0",
    "pydantic>=1.10.0,<3.0.0",
    "PyYAML>=6.0,<7.0",
    "spacy>=3.5.0,<4.0.0",
    "langdetect>=1.0.9,<2.0.0",
    "duckduckgo-search>=3.8.0,<4.0.0",
    "pdfminer.six>=20221105",
    "rich>=13.0.0,<14.0.0",
    "loguru>=0.6.0,<1.0.0",
    "tqdm>=4.64.0,<5.0.0",
    "click>=8.1.0,<9.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.2.0,<8.0.0",
    "pytest-qt>=4.2.0,<5.0.0",
    "pytest-asyncio>=0.21.0,<1.0.0",
    "pytest-cov>=4.0.0,<5.0.0",
    "black>=23.1.0,<24.0.0",
    "flake8>=6.0.0,<7.0.0",
    "mypy>=1.1.0,<2.0.0",
    "isort>=5.12.0,<6.0.0",
    "pre-commit>=3.1.0,<4.0.0",
]
docs = [
    "sphinx>=6.1.0,<7.0.0",
    "sphinx-rtd-theme>=1.2.0,<2.0.0",
    "myst-parser>=1.0.0,<2.0.0",
]
ai = [
    "openai>=0.27.0,<1.0.0",
    "transformers>=4.27.0,<5.0.0",
    "sentence-transformers>=2.2.0,<3.0.0",
    "chromadb>=0.3.0,<1.0.0",
]

[project.scripts]
rag-studio = "rag_data_studio.main_application:main"
rag-scraper = "scraper.searcher:main"

[project.urls]
Homepage = "https://github.com/yourusername/rag-data-studio"
Repository = "https://github.com/yourusername/rag-data-studio.git"
Documentation = "https://docs.rag-data-studio.com"
"Bug Tracker" = "https://github.com/yourusername/rag-data-studio/issues"

[tool.setuptools.packages.find]
where = ["."]
include = ["rag_data_studio*", "scraper*", "gui*", "storage*", "utils*", "wizards*"]

[tool.setuptools.package-data]
rag_data_studio = ["assets/*", "templates/*", "styles/*.qss"]
gui = ["*.qss"]

# Black configuration
[tool.black]
line-length = 100
target-version = ['py38', 'py39', 'py310', 'py311']
include = '\.pyi?
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''

# isort configuration
[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true

# mypy configuration
[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
ignore_missing_imports = true

# pytest configuration
[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --strict-markers"
testpaths = ["tests"]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "gui: marks tests as GUI tests requiring display",
]

# Coverage configuration
[tool.coverage.run]
source = ["rag_data_studio", "scraper", "gui", "storage", "utils"]
omit = [
    "*/tests/*",
    "*/test_*",
    "setup.py",
    "*/venv/*",
    "*/__pycache__/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:",
    "class .*\bProtocol\):",
    "@(abc\.)?abstractmethod",
]

---

# requirements-dev.txt
# Development dependencies for RAG Data Studio

# Testing Framework
pytest>=7.2.0,<8.0.0
pytest-qt>=4.2.0,<5.0.0           # Qt GUI testing
pytest-asyncio>=0.21.0,<1.0.0     # Async testing support
pytest-cov>=4.0.0,<5.0.0          # Coverage reporting
pytest-mock>=3.10.0,<4.0.0        # Mocking utilities
pytest-xdist>=3.2.0,<4.0.0        # Parallel test execution

# Code Quality and Formatting
black>=23.1.0,<24.0.0             # Code formatting
flake8>=6.0.0,<7.0.0              # Linting
mypy>=1.1.0,<2.0.0                # Type checking
isort>=5.12.0,<6.0.0              # Import sorting
pre-commit>=3.1.0,<4.0.0          # Git hooks

# Additional linting tools
flake8-docstrings>=1.7.0,<2.0.0   # Docstring linting
flake8-import-order>=0.18.0,<1.0.0 # Import order checking
bandit>=1.7.0,<2.0.0              # Security linting

# Documentation
sphinx>=6.1.0,<7.0.0              # Documentation generation
sphinx-rtd-theme>=1.2.0,<2.0.0    # Read the Docs theme
myst-parser>=1.0.0,<2.0.0         # Markdown support
sphinx-autodoc-typehints>=1.22.0,<2.0.0  # Type hints in docs

# Development tools
ipython>=8.10.0,<9.0.0            # Enhanced Python shell
ipdb>=0.13.0,<1.0.0               # Enhanced debugger
memory-profiler>=0.60.0,<1.0.0    # Memory profiling
line-profiler>=4.0.0,<5.0.0       # Line-by-line profiling

# Build and packaging
build>=0.10.0,<1.0.0              # Build tool
twine>=4.0.0,<5.0.0               # Package uploading
wheel>=0.40.0,<1.0.0              # Wheel building

---

# Makefile
# RAG Data Studio - Development Makefile

.PHONY: help install install-dev clean test test-gui lint format type-check docs build package run

# Default target
help:
	@echo "RAG Data Studio - Development Commands"
	@echo "======================================"
	@echo "install      - Install production dependencies"
	@echo "install-dev  - Install development dependencies"
	@echo "clean        - Clean build artifacts and cache"
	@echo "test         - Run all tests"
	@echo "test-gui     - Run GUI tests (requires display)"
	@echo "lint         - Run code linting"
	@echo "format       - Format code with black and isort"
	@echo "type-check   - Run type checking with mypy"
	@echo "docs         - Build documentation"
	@echo "build        - Build package"
	@echo "package      - Create distributable package"
	@echo "run          - Run RAG Data Studio"
	@echo "run-dev      - Run in development mode"

# Installation
install:
	pip install -r requirements.txt
	python -m spacy download en_core_web_sm

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	python -m spacy download en_core_web_sm
	pre-commit install

# Cleaning
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

# Testing
test:
	pytest tests/ -v

test-gui:
	pytest tests/gui/ -v --capture=no

test-coverage:
	pytest --cov=rag_data_studio --cov-report=html --cov-report=term

# Code quality
lint:
	flake8 rag_data_studio/ scraper/ gui/ storage/ utils/
	bandit -r rag_data_studio/ scraper/

format:
	black rag_data_studio/ scraper/ gui/ storage/ utils/ tests/
	isort rag_data_studio/ scraper/ gui/ storage/ utils/ tests/

type-check:
	mypy rag_data_studio/ scraper/

# Documentation
docs:
	cd docs && make html

docs-clean:
	cd docs && make clean

# Building and packaging
build:
	python -m build

package: clean build
	twine check dist/*

# Running
run:
	python -m rag_data_studio.main_application

run-dev:
	PYTHONPATH=. python rag_data_studio/main_application.py

# Pre-commit hooks
pre-commit:
	pre-commit run --all-files

---

# .pre-commit-config.yaml
# Pre-commit hooks for RAG Data Studio

repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: debug-statements
      - id: check-docstring-first

  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        language_version: python3
        args: [--line-length=100]

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile=black, --line-length=100]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        additional_dependencies: [flake8-docstrings, flake8-import-order]
        args: [--max-line-length=100, --ignore=E203,W503]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.1.1
    hooks:
      - id: mypy
        additional_dependencies: [types-PyYAML, types-requests]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]
        additional_dependencies: ["bandit[toml]"]

---

# docker/Dockerfile
# RAG Data Studio - Docker Container
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DISPLAY=:0

# Install system dependencies for GUI and web scraping
RUN apt-get update && apt-get install -y \
    qtbase5-dev \
    qtchooser \
    qt5-qmake \
    qtbase5-dev-tools \
    libqt5webkit5-dev \
    xvfb \
    x11vnc \
    fluxbox \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY . .

# Install the application
RUN pip install -e .

# Create non-root user
RUN useradd -m -s /bin/bash raguser
RUN chown -R raguser:raguser /app
USER raguser

# Expose port for VNC
EXPOSE 5900

# Start script
COPY docker/start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]

---

# docker/start.sh
#!/bin/bash
# Start script for RAG Data Studio Docker container

# Start Xvfb
Xvfb :0 -screen 0 1920x1080x24 &

# Start VNC server
x11vnc -display :0 -nopw -listen localhost -xkb &

# Start window manager
fluxbox &

# Wait a moment for X server to start
sleep 2

# Start RAG Data Studio
cd /app
python -m rag_data_studio.main_application

---

# docker/docker-compose.yml
version: '3.8'

services:
  rag-data-studio:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: rag-data-studio
    ports:
      - "5900:5900"  # VNC port
    volumes:
      - ../data_exports:/app/data_exports
      - ../configs:/app/configs
      - ../logs:/app/logs
    environment:
      - DISPLAY=:0
      - PYTHONPATH=/app
    restart: unless-stopped

  # Optional: Database for storing project configurations
  postgres:
    image: postgres:15
    container_name: rag-studio-db
    environment:
      POSTGRES_DB: rag_studio
      POSTGRES_USER: raguser
      POSTGRES_PASSWORD: ragpass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:

---

# scripts/install.sh
#!/bin/bash
# Installation script for RAG Data Studio

set -e

echo "🎯 RAG Data Studio Installation Script"
echo "====================================="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Install development dependencies (optional)
read -p "Install development dependencies? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pip install -r requirements-dev.txt
    echo "✅ Development dependencies installed"
fi

# Download spaCy model
echo "📚 Downloading spaCy language model..."
python -m spacy download en_core_web_sm

# Install pre-commit hooks (if dev dependencies installed)
if [ -f "requirements-dev.txt" ] && [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🪝 Installing pre-commit hooks..."
    pre-commit install
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data_exports
mkdir -p configs
mkdir -p logs
mkdir -p temp

# Set permissions
chmod +x scripts/*.sh

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "To start RAG Data Studio:"
echo "  source venv/bin/activate"
echo "  python -m rag_data_studio.main_application"
echo ""
echo "For development:"
echo "  make run-dev"
echo ""

---

# scripts/build_executable.sh
#!/bin/bash
# Build standalone executable for RAG Data Studio

set -e

echo "🔨 Building RAG Data Studio Executable"
echo "====================================="

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "📦 Installing PyInstaller..."
    pip install pyinstaller
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/

# Build executable
echo "🏗️ Building executable..."
pyinstaller \
    --name "RAG Data Studio" \
    --windowed \
    --onefile \
    --add-data "gui/styles.qss:gui/" \
    --add-data "rag_data_studio/assets:rag_data_studio/assets/" \
    --hidden-import "PySide6.QtWebEngineWidgets" \
    --hidden-import "spacy" \
    --hidden-import "en_core_web_sm" \
    rag_data_studio/main_application.py

echo "✅ Build completed!"
echo "📦 Executable location: dist/RAG Data Studio"

# Create distribution package
echo "📦 Creating distribution package..."
cd dist/
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    zip -r "RAG-Data-Studio-macOS.zip" "RAG Data Studio.app"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    zip -r "RAG-Data-Studio-Windows.zip" "RAG Data Studio.exe"
else
    # Linux
    tar -czf "RAG-Data-Studio-Linux.tar.gz" "RAG Data Studio"
fi

echo "🎉 Distribution package created!"

---

# LICENSE
MIT License

Copyright (c) 2024 RAG Data Studio

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.