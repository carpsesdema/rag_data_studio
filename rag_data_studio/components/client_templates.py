# rag_data_studio/components/client_templates.py
"""
Pre-built templates for common client domains
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class DomainTemplate:
    name: str
    description: str
    common_selectors: Dict[str, str]
    sample_rules: List[Dict[str, Any]]
    recommended_settings: Dict[str, Any]


class ClientTemplateManager:
    """Manage domain-specific templates for quick project setup"""

    def __init__(self):
        self.templates = self._load_built_in_templates()

    def _load_built_in_templates(self) -> Dict[str, DomainTemplate]:
        """Load built-in templates for common domains"""
        return {
            "legal": DomainTemplate(
                name="Legal Documents & Case Law",
                description="Extract legal documents, case citations, court decisions",
                common_selectors={
                    "case_title": "h1, .case-title, .decision-title",
                    "court_name": ".court-name, .jurisdiction",
                    "date_decided": ".date-decided, .decision-date",
                    "case_number": ".case-number, .docket-number",
                    "judge_name": ".judge, .authored-by",
                    "full_text": ".opinion-text, .decision-text, .full-text"
                },
                sample_rules=[
                    {
                        "name": "case_citation",
                        "selector": ".citation, .case-cite",
                        "extract_type": "text",
                        "data_type": "string",
                        "required": True
                    },
                    {
                        "name": "legal_topics",
                        "selector": ".topics a, .subject-tags a",
                        "extract_type": "text",
                        "is_list": True
                    }
                ],
                recommended_settings={
                    "rate_limiting": {"delay": 3.0, "respect_robots": True},
                    "output_format": "jsonl",
                    "include_metadata": True
                }
            ),

            "financial": DomainTemplate(
                name="Financial Data & Reports",
                description="Extract stock prices, financial statements, market data",
                common_selectors={
                    "company_name": "h1, .company-name, .ticker-name",
                    "stock_price": ".price, .current-price, .last-price",
                    "price_change": ".change, .price-change",
                    "market_cap": ".market-cap, .mktcap",
                    "volume": ".volume, .trading-volume",
                    "financial_metrics": ".metrics tr, .financial-data tr"
                },
                sample_rules=[
                    {
                        "name": "stock_symbol",
                        "selector": ".symbol, .ticker",
                        "extract_type": "text",
                        "data_type": "string",
                        "required": True
                    },
                    {
                        "name": "quarterly_revenue",
                        "selector": ".revenue, .quarterly-revenue",
                        "extract_type": "text",
                        "data_type": "number"
                    }
                ],
                recommended_settings={
                    "rate_limiting": {"delay": 1.0, "respect_robots": True},
                    "output_format": "jsonl",
                    "real_time_updates": True
                }
            ),

            "medical": DomainTemplate(
                name="Medical Research & Publications",
                description="Extract research papers, clinical trials, medical data",
                common_selectors={
                    "paper_title": "h1, .title, .article-title",
                    "authors": ".authors a, .author-list a",
                    "abstract": ".abstract, .summary",
                    "publication_date": ".pub-date, .published",
                    "journal": ".journal, .publication",
                    "doi": ".doi, [data-doi]",
                    "keywords": ".keywords a, .tags a"
                },
                sample_rules=[
                    {
                        "name": "clinical_trial_id",
                        "selector": ".trial-id, .nct-number",
                        "extract_type": "text",
                        "validation_regex": r"NCT\d{8}"
                    },
                    {
                        "name": "patient_count",
                        "selector": ".patient-count, .study-size",
                        "extract_type": "text",
                        "data_type": "number"
                    }
                ],
                recommended_settings={
                    "rate_limiting": {"delay": 2.0, "respect_robots": True},
                    "output_format": "jsonl",
                    "include_citations": True
                }
            ),

            "ecommerce": DomainTemplate(
                name="E-commerce & Product Data",
                description="Extract product information, prices, reviews",
                common_selectors={
                    "product_name": "h1, .product-title, .item-name",
                    "price": ".price, .current-price, .sale-price",
                    "original_price": ".original-price, .list-price",
                    "rating": ".rating, .stars, .review-score",
                    "review_count": ".review-count, .num-reviews",
                    "description": ".description, .product-details",
                    "images": ".product-images img",
                    "availability": ".stock, .availability"
                },
                sample_rules=[
                    {
                        "name": "product_sku",
                        "selector": ".sku, .model-number",
                        "extract_type": "text",
                        "required": True
                    },
                    {
                        "name": "product_features",
                        "selector": ".features li, .specs tr",
                        "extract_type": "text",
                        "is_list": True
                    }
                ],
                recommended_settings={
                    "rate_limiting": {"delay": 2.0, "respect_robots": True},
                    "output_format": "jsonl",
                    "include_images": False
                }
            ),

            "real_estate": DomainTemplate(
                name="Real Estate Listings",
                description="Extract property listings, prices, details",
                common_selectors={
                    "property_title": "h1, .listing-title, .property-title",
                    "price": ".price, .listing-price, .sale-price",
                    "address": ".address, .property-address",
                    "bedrooms": ".beds, .bedrooms",
                    "bathrooms": ".baths, .bathrooms",
                    "square_feet": ".sqft, .square-feet, .area",
                    "lot_size": ".lot-size, .land-area",
                    "property_type": ".property-type, .home-type"
                },
                sample_rules=[
                    {
                        "name": "mls_number",
                        "selector": ".mls, .listing-id",
                        "extract_type": "text",
                        "required": True
                    },
                    {
                        "name": "amenities",
                        "selector": ".amenities li, .features li",
                        "extract_type": "text",
                        "is_list": True
                    }
                ],
                recommended_settings={
                    "rate_limiting": {"delay": 2.5, "respect_robots": True},
                    "output_format": "jsonl",
                    "geocoding": True
                }
            )
        }

    def get_template(self, domain: str) -> Optional[DomainTemplate]:
        """Get template for a specific domain"""
        return self.templates.get(domain.lower())

    def get_all_domains(self) -> List[str]:
        """Get list of all available domains"""
        return list(self.templates.keys())

    def apply_template_to_project(self, project_config: 'ProjectConfig', domain: str) -> 'ProjectConfig':
        """Apply a template to a project configuration"""
        template = self.get_template(domain)
        if not template:
            return project_config

        # Add template rules to project
        from rag_data_studio.core.main_window import ScrapingRule
        import uuid
        from datetime import datetime

        for rule_data in template.sample_rules:
            rule = ScrapingRule(
                id=f"template_rule_{uuid.uuid4().hex[:8]}",
                name=rule_data["name"],
                description=f"Template rule for {domain}",
                selector=rule_data["selector"],
                extraction_type=rule_data["extract_type"],
                attribute_name=rule_data.get("attribute_name"),
                is_list=rule_data.get("is_list", False),
                data_type=rule_data.get("data_type", "string"),
                validation_regex=rule_data.get("validation_regex"),
                required=rule_data.get("required", False)
            )
            project_config.scraping_rules.append(rule)

        # Apply recommended settings
        project_config.rate_limiting.update(template.recommended_settings.get("rate_limiting", {}))
        project_config.output_settings.update({
            k: v for k, v in template.recommended_settings.items()
            if k != "rate_limiting"
        })

        return project_config