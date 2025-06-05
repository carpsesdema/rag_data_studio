# scraper/chunker.py
import logging
from typing import List, Dict, Optional, Any
from .rag_models import EnrichedItem  # RAGOutputItem removed

# from config import DEFAULT_CHUNK_SIZE, CHUNK_OVERLAP, MIN_CHUNK_SIZE # No longer primary focus

logger = logging.getLogger(__name__)


class Chunker:
    def __init__(self, logger_instance=None,
                 # max_chunk_size_chars: int = DEFAULT_CHUNK_SIZE, # Configurable but not used in this simplified version
                 # min_chunk_size_chars: int = MIN_CHUNK_SIZE,   # Configurable but not used
                 # overlap_size_chars: int = CHUNK_OVERLAP      # Configurable but not used
                 ):
        self.logger = logger_instance if logger_instance else logger
        # self.max_chunk_size = max_chunk_size_chars
        # self.min_chunk_size = min_chunk_size_chars
        # self.overlap_size = overlap_size_chars
        self.logger.info("Chunker initialized (simplified for non-RAG focus).")

    # _create_rag_item and _chunk_single_content_piece are removed as they produce RAGOutputItem

    def chunk_item(self, enriched_item: EnrichedItem) -> List[Any]:  # Return type changed, effectively empty
        """
        Placeholder for chunking logic. In a non-RAG setup focused on structured data,
        this component might be repurposed or removed.
        Currently, it does not produce RAG-specific chunks.
        """
        self.logger.debug(f"Chunking called for item {enriched_item.id}, but RAG-specific chunking is disabled.")
        # If there was any generic text segmentation or processing needed for EnrichedItem fields
        # before saving, it could go here. For now, it returns an empty list
        # as the primary output (RAGOutputItem) is no longer generated.

        # Example: if you still needed to break down primary_text_content into smaller pieces
        # for some other purpose (not RAG Chunks for a vector DB), that logic could live here.
        # For now, we assume EnrichedItem itself is the desired output structure.

        return []  # No RAGOutputItems are generated