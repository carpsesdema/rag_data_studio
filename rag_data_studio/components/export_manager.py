# rag_data_studio/components/export_manager.py
"""
Professional export and deployment manager for RAG Data Studio
"""
import os
from typing import Dict
from pathlib import Path
import json
import yaml
from datetime import datetime

from rag_data_studio.main_application import ProjectConfig


class ExportManager:
    """Manage exports for different client needs"""

    def __init__(self):
        self.export_formats = {
            "yaml_config": self.export_yaml_config,
            "python_script": self.export_python_script,
            "docker_container": self.export_docker_setup,
            "api_endpoint": self.export_api_config,
            "documentation": self.export_documentation
        }

    def export_yaml_config(self, project: 'ProjectConfig', output_path: str) -> bool:
        """Export as YAML configuration for your existing system"""
        try:
            config_data = {
                "domain_info": {
                    "name": project.name,
                    "description": project.description,
                    "domain": project.domain,
                    "created_at": project.created_at,
                    "client": project.client_info
                },
                "global_user_agent": f"RAGScraper/{project.name}",
                "sources": [{
                    "name": project.name.lower().replace(' ', '_'),
                    "seeds": project.target_websites,
                    "source_type": project.domain,
                    "selectors": {
                        "custom_fields": [
                            {
                                "name": rule.name,
                                "selector": rule.selector,
                                "extract_type": rule.extraction_type,
                                "attribute_name": rule.attribute_name,
                                "is_list": rule.is_list,
                                "data_type": rule.data_type,
                                "semantic_label": rule.semantic_label,
                                "rag_importance": rule.rag_importance,
                                "validation_regex": rule.validation_regex,
                                "transformation": rule.transformation,
                                "required": rule.required
                            } for rule in project.scraping_rules
                        ]
                    },
                    "crawl": {
                        "depth": 1,
                        "delay_seconds": project.rate_limiting.get("delay", 2.0),
                        "respect_robots_txt": project.rate_limiting.get("respect_robots", True)
                    },
                    "export": {
                        "format": project.output_settings.get("format", "jsonl"),
                        "output_path": f"./data_exports/{project.domain}/{project.name.lower().replace(' ', '_')}.jsonl"
                    }
                }]
            }

            # Write YAML file
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2, allow_unicode=True)

            return True

        except Exception as e:
            print(f"Error exporting YAML config: {e}")
            return False

    def export_python_script(self, project: 'ProjectConfig', output_path: str) -> bool:
        """Export as standalone Python script"""
        try:
            script_content = f'''#!/usr/bin/env python3
"""
Generated scraping script for: {project.name}
Client: {project.client_info.get("name", "N/A") if project.client_info else "N/A"}
Generated: {datetime.now().isoformat()}
"""

import sys
import os
from pathlib import Path

# Add the RAG scraper to path
sys.path.append(str(Path(__file__).parent))

from scraper.searcher import search_and_fetch
from utils.logger import setup_logger

def main():
    # Setup logging
    logger = setup_logger("{project.name.lower().replace(' ', '_')}_scraper")

    # Configuration for {project.name}
    config_path = "configs/{project.name.lower().replace(' ', '_')}_config.yaml"

    try:
        logger.info("Starting scraping for: {project.name}")

        # Run the scraping pipeline
        enriched_items = search_and_fetch(
            query_or_config_path=config_path,
            logger=logger
        )

        logger.info(f"Scraping completed. Processed {{len(enriched_items)}} items")

        # Display summary
        print(f"\\n🎯 Scraping Results for {project.name}")
        print(f"{'=' * 50}")
        print(f"Total items processed: {{len(enriched_items)}}")

        for item in enriched_items[:5]:  # Show first 5 items
            print(f"\\n📄 {{item.title or 'Untitled'}}")
            print(f"   URL: {{item.source_url}}")
            print(f"   Custom fields: {{len(item.custom_fields)}}")
            if item.custom_fields:
                for field_name, field_value in item.custom_fields.items():
                    if field_value:
                        print(f"     {{field_name}}: {{str(field_value)[:100]}}...")

        if len(enriched_items) > 5:
            print(f"\\n... and {{len(enriched_items) - 5}} more items")

        print(f"\\n✅ Data exported to: ./data_exports/{project.domain}/")

    except Exception as e:
        logger.error(f"Scraping failed: {{e}}", exc_info=True)
        print(f"❌ Error: {{e}}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
'''

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(script_content)

            # Make executable
            os.chmod(output_path, 0o755)
            return True

        except Exception as e:
            print(f"Error exporting Python script: {e}")
            return False

    def export_docker_setup(self, project: 'ProjectConfig', output_dir: str) -> bool:
        """Export Docker configuration for deployment"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Dockerfile
            dockerfile_content = f'''FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    wget \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data_exports logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PROJECT_NAME="{project.name}"
ENV DOMAIN="{project.domain}"

# Run the scraper
CMD ["python", "-m", "scraper.searcher", "configs/{project.name.lower().replace(' ', '_')}_config.yaml"]
'''

            with open(output_path / "Dockerfile", 'w') as f:
                f.write(dockerfile_content)

            # Docker Compose
            compose_content = f'''version: '3.8'

services:
  {project.name.lower().replace(' ', '-')}-scraper:
    build: .
    container_name: {project.name.lower().replace(' ', '-')}-scraper
    volumes:
      - ./data_exports:/app/data_exports
      - ./logs:/app/logs
      - ./configs:/app/configs
    environment:
      - PROJECT_NAME={project.name}
      - DOMAIN={project.domain}
      - LOG_LEVEL=INFO
    restart: unless-stopped

  # Optional: Add a database for storing results
  # postgres:
  #   image: postgres:15
  #   environment:
  #     POSTGRES_DB: {project.name.lower().replace(' ', '_')}_db
  #     POSTGRES_USER: scraper
  #     POSTGRES_PASSWORD: scraper_pass
  #   volumes:
  #     - postgres_data:/var/lib/postgresql/data
  #   ports:
  #     - "5432:5432"

# volumes:
#   postgres_data:
'''

            with open(output_path / "docker-compose.yml", 'w') as f:
                f.write(compose_content)

            # Build script
            build_script = f'''#!/bin/bash
# Build script for {project.name} scraper

echo "🐳 Building Docker image for {project.name}"

# Build the image
docker build -t {project.name.lower().replace(' ', '-')}-scraper .

# Run the container
echo "🚀 Starting scraper..."
docker-compose up -d

echo "✅ {project.name} scraper is running!"
echo "📊 Check logs with: docker-compose logs -f"
echo "📁 Data will be saved to: ./data_exports/"
'''

            with open(output_path / "build.sh", 'w') as f:
                f.write(build_script)

            os.chmod(output_path / "build.sh", 0o755)
            return True

        except Exception as e:
            print(f"Error exporting Docker setup: {e}")
            return False

    def export_api_config(self, project: 'ProjectConfig', output_path: str) -> bool:
        """Export API endpoint configuration"""
        try:
            api_config = {
                "api_info": {
                    "name": f"{project.name} Scraping API",
                    "description": f"REST API for {project.name} data extraction",
                    "version": "1.0.0",
                    "domain": project.domain
                },
                "endpoints": {
                    f"/scrape/{project.name.lower().replace(' ', '_')}": {
                        "method": "POST",
                        "description": f"Trigger scraping for {project.name}",
                        "parameters": {
                            "urls": {
                                "type": "array",
                                "description": "List of URLs to scrape",
                                "default": project.target_websites
                            },
                            "format": {
                                "type": "string",
                                "description": "Output format",
                                "enum": ["json", "jsonl", "csv"],
                                "default": "json"
                            }
                        },
                        "response": {
                            "type": "object",
                            "properties": {
                                "status": {"type": "string"},
                                "items_processed": {"type": "integer"},
                                "data": {"type": "array"},
                                "metadata": {"type": "object"}
                            }
                        }
                    }
                },
                "data_schema": {
                    "type": "object",
                    "properties": {
                        field["name"]: {
                            "type": field["data_type"],
                            "description": f"Extracted using selector: {field['selector']}",
                            "semantic_label": field["semantic_label"],
                            "rag_importance": field["rag_importance"],
                            "required": field["required"]
                        } for field in [
                            {
                                "name": rule.name,
                                "selector": rule.selector,
                                "data_type": rule.data_type,
                                "semantic_label": rule.semantic_label,
                                "rag_importance": rule.rag_importance,
                                "required": rule.required
                            } for rule in project.scraping_rules
                        ]
                    }
                },
                "rate_limiting": project.rate_limiting,
                "authentication": {
                    "type": "bearer_token",
                    "description": "Include Bearer token in Authorization header"
                }
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(api_config, f, indent=2)

            return True

        except Exception as e:
            print(f"Error exporting API config: {e}")
            return False

    def export_documentation(self, project: 'ProjectConfig', output_dir: str) -> bool:
        """Export comprehensive documentation"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Main README
            readme_content = f'''# {project.name} - Data Extraction Documentation

**Domain:** {project.domain}  
**Created:** {project.created_at}  
**Client:** {project.client_info.get("name", "N/A") if project.client_info else "N/A"}

## Overview

This documentation describes the data extraction configuration for **{project.name}**.

## Target Websites

{chr(10).join(f"- {url}" for url in project.target_websites)}

## Data Fields Extracted

The following data fields are extracted from each target website:

| Field Name | Semantic Label | Importance | Data Type | Required | Selector |
|------------|---------------|------------|-----------|----------|----------|
{chr(10).join(f"| {rule.name} | {rule.semantic_label} | {rule.rag_importance} | {rule.data_type} | {'Yes' if rule.required else 'No'} | `{rule.selector}` |" for rule in project.scraping_rules)}

## Semantic Labels for RAG

The extracted data uses semantic labels optimized for RAG systems:

### High Importance Fields
{chr(10).join(f"- **{rule.name}** ({rule.semantic_label}): {rule.description}" for rule in project.scraping_rules if rule.rag_importance == 'high')}

### Medium Importance Fields  
{chr(10).join(f"- **{rule.name}** ({rule.semantic_label}): {rule.description}" for rule in project.scraping_rules if rule.rag_importance == 'medium')}

### Low Importance Fields
{chr(10).join(f"- **{rule.name}** ({rule.semantic_label}): {rule.description}" for rule in project.scraping_rules if rule.rag_importance == 'low')}

## Configuration

### Rate Limiting
- **Delay between requests:** {project.rate_limiting.get("delay", 2.0)} seconds
- **Respect robots.txt:** {project.rate_limiting.get("respect_robots", True)}

### Output Settings
- **Format:** {project.output_settings.get("format", "jsonl")}
- **Include metadata:** {project.output_settings.get("include_metadata", True)}

## Usage

### Command Line
```bash
python -m scraper.searcher configs/{project.name.lower().replace(' ', '_')}_config.yaml
```

### Docker
```bash
docker-compose up -d
```

### Python API
```python
from scraper.searcher import search_and_fetch
from utils.logger import setup_logger

logger = setup_logger("{project.name.lower().replace(' ', '_')}")
enriched_items = search_and_fetch(
    query_or_config_path="configs/{project.name.lower().replace(' ', '_')}_config.yaml",
    logger=logger
)
```

## Output Data Structure

Each extracted item contains:

```json
{{
  "id": "unique_item_id",
  "source_url": "source_website_url",
  "title": "extracted_title",
  "custom_fields": {{
{chr(10).join(f'    "{rule.name}": "extracted_value",' for rule in project.scraping_rules)}
  }},
  "categories": ["category1", "category2"],
  "tags": ["tag1", "tag2"],
  "language": "detected_language",
  "quality_score": 8.5,
  "timestamp": "2024-01-01T12:00:00Z"
}}
```

## RAG Integration

This data is optimized for RAG (Retrieval-Augmented Generation) systems:

1. **Semantic Labels**: Each field has a semantic label (e.g., `entity_name`, `entity_ranking`)
2. **Importance Levels**: Fields are prioritized for RAG retrieval
3. **Structured Format**: Consistent JSON/JSONL output for vector databases
4. **Quality Scoring**: Each item includes quality metrics

## Support

For questions or issues:
- **Configuration**: Check the YAML config file
- **Logs**: Review scraper logs in `./logs/`
- **Data**: Output saved to `./data_exports/{project.domain}/`

---
*Generated by RAG Data Studio v1.0*
'''

            with open(output_path / "README.md", 'w', encoding='utf-8') as f:
                f.write(readme_content)

            # Technical specification
            tech_spec = f'''# Technical Specification - {project.name}

## System Requirements

- Python 3.8+
- 4GB RAM minimum
- 10GB disk space for data storage
- Network access to target websites

## Dependencies

See `requirements.txt` for complete dependency list.

## Configuration File Structure

```yaml
domain_info:
  name: "{project.name}"
  description: "{project.description}"
  domain: "{project.domain}"

sources:
  - name: "{project.name.lower().replace(' ', '_')}"
    seeds: {project.target_websites}
    source_type: "{project.domain}"
    selectors:
      custom_fields:
{chr(10).join(f'        - name: "{rule.name}"' + chr(10) + f'          selector: "{rule.selector}"' + chr(10) + f'          extract_type: "{rule.extraction_type}"' + chr(10) + f'          semantic_label: "{rule.semantic_label}"' + chr(10) + f'          rag_importance: "{rule.rag_importance}"' for rule in project.scraping_rules)}
```

## Error Handling

The scraper includes robust error handling:
- Network timeouts and retries
- Invalid selector detection
- Data validation and cleaning
- Comprehensive logging

## Performance Optimization

- Concurrent request processing
- Intelligent rate limiting
- Memory-efficient data processing
- Incremental data updates

## Monitoring

Monitor scraping performance through:
- Log files in `./logs/`
- Progress indicators
- Quality score metrics
- Error rate tracking
'''

            with open(output_path / "TECHNICAL_SPEC.md", 'w', encoding='utf-8') as f:
                f.write(tech_spec)

            return True

        except Exception as e:
            print(f"Error exporting documentation: {e}")
            return False

    def export_all(self, project: 'ProjectConfig', output_dir: str) -> Dict[str, bool]:
        """Export all formats to specified directory"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = {}

        # YAML Configuration
        yaml_path = output_path / f"{project.name.lower().replace(' ', '_')}_config.yaml"
        results['yaml_config'] = self.export_yaml_config(project, str(yaml_path))

        # Python Script
        script_path = output_path / f"{project.name.lower().replace(' ', '_')}_scraper.py"
        results['python_script'] = self.export_python_script(project, str(script_path))

        # Docker Setup
        docker_dir = output_path / "docker"
        results['docker_container'] = self.export_docker_setup(project, str(docker_dir))

        # API Configuration
        api_path = output_path / f"{project.name.lower().replace(' ', '_')}_api.json"
        results['api_endpoint'] = self.export_api_config(project, str(api_path))

        # Documentation
        docs_dir = output_path / "docs"
        results['documentation'] = self.export_documentation(project, str(docs_dir))

        return results


# Example usage
if __name__ == "__main__":
    # This would typically be called from the main GUI
    pass