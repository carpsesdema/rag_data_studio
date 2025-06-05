# scraper/rag_models.py
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, HttpUrl, Field
import uuid
from datetime import datetime


class FetchedItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_url: HttpUrl
    content: Optional[str] = None
    content_bytes: Optional[bytes] = None
    content_type_detected: Optional[str] = None
    source_type: str  # User-defined type for the source (e.g., 'tennis_article', 'player_bio')
    query_used: str
    title: Optional[str] = None
    depth: int = 0
    encoding: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtractedLinkInfo(BaseModel):
    url: HttpUrl
    text: Optional[str] = None
    rel: Optional[str] = None


class ParsedItem(BaseModel):
    id: str
    fetched_item_id: str
    source_url: HttpUrl
    source_type: str
    query_used: str

    title: Optional[str] = None
    main_text_content: Optional[str] = None
    extracted_structured_blocks: List[Dict[str, Any]] = Field(default_factory=list)

    custom_fields: Dict[str, Any] = Field(default_factory=dict,
                                          description="Key-value pairs of specifically extracted data points from YAML config.")

    detected_language_of_main_text: Optional[str] = None  # Can be set by parser
    extracted_links: List[ExtractedLinkInfo] = Field(default_factory=list)
    parser_metadata: Dict[str, Any] = Field(default_factory=dict)


class NormalizedItem(BaseModel):
    id: str
    parsed_item_id: str
    source_url: HttpUrl
    source_type: str
    query_used: str

    title: Optional[str] = None
    cleaned_text_content: Optional[str] = None
    cleaned_structured_blocks: List[Dict[str, Any]] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

    is_duplicate: bool = False
    normalization_metadata: Dict[str, Any] = Field(default_factory=dict)
    language_of_main_text: Optional[str] = None  # Propagated from ParsedItem


class EnrichedItem(BaseModel):  # Simplified for structured data extraction focus
    id: str
    # normalized_item_id: str # Can be same as id if normalization is simple
    source_url: HttpUrl
    source_type: str
    query_used: str
    title: Optional[str] = None

    primary_text_content: Optional[str] = None  # The main textual content
    # Enriched structured elements can still be useful (tables, lists etc.)
    enriched_structured_elements: List[Dict[str, Any]] = Field(default_factory=list)

    custom_fields: Dict[str, Any] = Field(default_factory=dict,
                                          description="Key-value data extracted via custom selectors. This is GOLD! ✨")

    # Optional fields, can be populated if basic NLP/heuristics are kept, or removed if not needed
    language_of_primary_text: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    # keyphrases: List[str] = Field(default_factory=list) # Often more NLP heavy
    # overall_entities: List[Dict[str, str]] = Field(default_factory=list) # Often more NLP heavy
    # quality_score: Optional[float] = None # Can be simplified or removed
    # complexity_score: Optional[float] = None # Can be simplified or removed

    # A simple summary for display or quick checks
    displayable_metadata_summary: Dict[str, Any] = Field(default_factory=dict)

    # Ensure 'normalized_item_id' is present if other parts of your code expect it
    # For simplicity now, we can assume EnrichedItem directly uses the ID from previous stage
    # or just use 'id'. If needed, add:
    # normalized_item_id: str

    class Config:
        # If you were using Pydantic V1, this would be for ORM mode.
        # For Pydantic V2, it's less common unless working with ORMs.
        # orm_mode = True # Pydantic V1
        from_attributes = True  # Pydantic V2 equivalent if loading from ORM-like objects