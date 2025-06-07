# scraper/searcher.py
import hashlib
import json
import logging
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Callable, Tuple

import config
from .chunker import Chunker  # Kept for now, though its role is diminished
from .config_manager import ConfigManager  # ExportConfig might be less used here now
from .content_router import ContentRouter
from .fetcher_pool import FetcherPool
from .rag_models import FetchedItem, ParsedItem, NormalizedItem, EnrichedItem  # RAGOutputItem removed

# External dependencies with professional error handling
try:
    from duckduckgo_search import DDGS

    DUCKDUCKGO_AVAILABLE = True
except ImportError:
    DUCKDUCKGO_AVAILABLE = False
    logging.getLogger(getattr(config, 'DEFAULT_LOGGER_NAME', 'ModularRAGScraper')).warning(
        "DuckDuckGo search library not available - autonomous search disabled")

try:
    import spacy
    from langdetect import detect as detect_language, LangDetectException

    NLP_LIBS_AVAILABLE = True
except ImportError:
    NLP_LIBS_AVAILABLE = False
    logging.getLogger(getattr(config, 'DEFAULT_LOGGER_NAME', 'ModularRAGScraper')).warning(
        "NLP libraries not available - advanced analysis disabled")


# Simple fallback deduplicator - no external dependencies
class SmartDeduplicator:
    def __init__(self, logger=None):
        self.seen_hashes = set()
        self.logger = logger or logging.getLogger("FallbackDeduplicator")

    def add_snippet(self, text_content, metadata=None):
        h = hashlib.md5(text_content.encode('utf-8', 'replace')).hexdigest()
        return not (h in self.seen_hashes or self.seen_hashes.add(h))

    def is_duplicate(self, text_content):
        h = hashlib.md5(text_content.encode('utf-8', 'replace')).hexdigest()
        return h in self.seen_hashes, "exact_hash" if h in self.seen_hashes else "unique"


# Professional NLP model loading with fallbacks
NLP_MODEL = None
if NLP_LIBS_AVAILABLE:
    try:
        model_name = getattr(config, 'SPACY_MODEL_NAME', 'en_core_web_sm')
        NLP_MODEL = spacy.load(model_name)
        logging.getLogger(getattr(config, 'DEFAULT_LOGGER_NAME', 'ModularRAGScraper')).info(
            f"Loaded spaCy model: {model_name}")
    except OSError:
        logging.getLogger(getattr(config, 'DEFAULT_LOGGER_NAME', 'ModularRAGScraper')).warning(
            f"spaCy model '{model_name}' not found - continuing without advanced NLP")
        NLP_LIBS_AVAILABLE = False
    except Exception as e:
        logging.getLogger(getattr(config, 'DEFAULT_LOGGER_NAME', 'ModularRAGScraper')).error(
            f"Failed to load spaCy model: {e}")
        NLP_LIBS_AVAILABLE = False


@dataclass
class PipelineMetrics:
    """Professional pipeline performance tracking"""
    start_time: datetime
    end_time: Optional[datetime] = None
    total_urls: int = 0
    successful_fetches: int = 0
    failed_fetches: int = 0
    parsed_items: int = 0
    normalized_items: int = 0
    enriched_items: int = 0
    # rag_chunks: int = 0 # Removed RAG-specific metric
    duplicates_filtered: int = 0
    quality_filtered: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    @property
    def duration(self) -> timedelta:
        end = self.end_time or datetime.now()
        return end - self.start_time

    @property
    def success_rate(self) -> float:
        if self.total_urls == 0:
            return 0.0
        return (self.successful_fetches / self.total_urls) * 100

    def to_dict(self) -> Dict[str, Any]:
        return {
            'duration_seconds': self.duration.total_seconds(),
            'total_urls': self.total_urls,
            'success_rate': f"{self.success_rate:.1f}%",
            'successful_fetches': self.successful_fetches,
            'failed_fetches': self.failed_fetches,
            'parsed_items': self.parsed_items,
            'normalized_items': self.normalized_items,
            'enriched_items': self.enriched_items,
            # 'rag_chunks': self.rag_chunks, # Removed
            'duplicates_filtered': self.duplicates_filtered,
            'quality_filtered': self.quality_filtered,
            'error_count': len(self.errors)
        }


class ProfessionalQualityFilter:
    """Advanced content quality assessment and filtering"""

    def __init__(self, logger):
        self.logger = logger
        self.quality_thresholds = {
            'minimum_length': getattr(config, 'QUALITY_MIN_LENGTH', 100),
            'substantial_length': getattr(config, 'QUALITY_SUBSTANTIAL_LENGTH', 500),
            'comprehensive_length': getattr(config, 'QUALITY_COMPREHENSIVE_LENGTH', 2000),
            'minimum_score': getattr(config, 'QUALITY_MIN_SCORE', 3)
        }

    def assess_content_quality(self, item: NormalizedItem) -> Tuple[int, Dict[str, Any]]:
        content = (item.cleaned_text_content or '') + ' ' + (item.title or '')
        content_length = len(content)
        quality_details = {'length_score': 0, 'structure_score': 0, 'data_richness_score': 0, 'authority_score': 0,
                           'penalty_score': 0, 'reasons': []}

        if content_length >= self.quality_thresholds['comprehensive_length']:
            quality_details['length_score'] = 4
        elif content_length >= self.quality_thresholds['substantial_length']:
            quality_details['length_score'] = 3
        elif content_length >= self.quality_thresholds['minimum_length']:
            quality_details['length_score'] = 2
        else:
            quality_details['reasons'].append(f"Content too short ({content_length} chars)")

        if item.cleaned_structured_blocks:
            quality_details['structure_score'] = len(item.cleaned_structured_blocks)
            quality_details['reasons'].append(f"Has {len(item.cleaned_structured_blocks)} structured elements")
        if item.custom_fields:
            populated_fields = sum(1 for v in item.custom_fields.values() if v and str(v).strip())
            quality_details['data_richness_score'] = populated_fields * 2  # Custom fields are important
            if populated_fields > 0: quality_details['reasons'].append(f"Rich data: {populated_fields} custom fields")

        url_str = str(item.source_url).lower()
        if any(domain in url_str for domain in
               ['gov', 'edu', 'org', 'official', 'wikipedia']):  # Example authoritative domains
            quality_details['authority_score'] = 2
            quality_details['reasons'].append("Authoritative domain")

        penalty_indicators = ['error 404', 'page not found', 'access denied', 'cookies required', 'javascript required',
                              'please enable', 'subscribe to continue', 'login required', 'paywall']
        penalty_count = sum(1 for indicator in penalty_indicators if indicator in content.lower())
        quality_details['penalty_score'] = -penalty_count * 2
        if penalty_count > 0: quality_details['reasons'].append(f"Quality penalties: {penalty_count}")

        total_score = sum(quality_details[k] for k in
                          ['length_score', 'structure_score', 'data_richness_score', 'authority_score',
                           'penalty_score'])
        return total_score, quality_details

    def filter_by_quality(self, items: List[NormalizedItem]) -> Tuple[List[NormalizedItem], int]:
        if not getattr(config, 'QUALITY_FILTER_ENABLED', True):
            self.logger.info("Quality filter is disabled. Passing all items.")
            return items, 0

        high_quality_items = []
        filtered_count = 0
        for item in items:
            score, details = self.assess_content_quality(item)
            if score >= self.quality_thresholds['minimum_score']:
                high_quality_items.append(item)
                self.logger.debug(f"Quality PASS: {item.source_url} (score: {score})")
            else:
                filtered_count += 1
                self.logger.debug(
                    f"Quality FILTER: {item.source_url} (score: {score}, reasons: {'; '.join(details['reasons'][:3])})")
        self.logger.info(
            f"Quality filter: {len(high_quality_items)}/{len(items)} items passed (filtered: {filtered_count})")
        return high_quality_items, filtered_count


class ProfessionalContentEnricher:
    def __init__(self, nlp_model, logger):
        self.nlp = nlp_model
        self.logger = logger
        # Value patterns can be useful for identifying specific types of data in text
        self.value_patterns = {
            'numerical_data': r'\d+(?:\.\d+)?(?:%|\$|€|£|pts?|kg|lbs?|mph|km/h)',  # Example
            'dates': r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})\b',  # Example
        }

    def enrich_item(self, item: NormalizedItem) -> EnrichedItem:
        try:
            categories = self._generate_smart_categories(item)
            language = self._detect_language(item)

            # NLP processing for tags and entities can be optional or simplified
            tags, keyphrases, entities = [], [], []  # Default to empty
            if NLP_LIBS_AVAILABLE and self.nlp:
                tags_nlp, keyphrases_nlp, entities_nlp = self._nlp_process(item)
                tags.extend(tags_nlp)
                # keyphrases.extend(keyphrases_nlp) # Keyphrases might be too RAG specific
                # entities.extend(entities_nlp) # Entities might be useful for stats

            quality_score = self._calculate_quality_score(item, entities, tags)
            # complexity_score = self._calculate_complexity_score(item) # May not be needed

            enriched_elements = []
            for element in item.cleaned_structured_blocks:
                enhanced = element.copy()
                enhanced['enriched_at'] = datetime.now().isoformat()
                if 'language' not in enhanced: enhanced['language'] = language
                enriched_elements.append(enhanced)

            metadata_summary = self._create_metadata_summary(item, language, categories, tags, entities,
                                                             enriched_elements, quality_score)

            return EnrichedItem(
                id=item.id,
                # normalized_item_id=item.id, # Assuming id is consistent
                source_url=item.source_url,
                source_type=item.source_type,
                query_used=item.query_used,
                title=item.title or "Untitled Content",
                primary_text_content=item.cleaned_text_content,
                enriched_structured_elements=enriched_elements,
                custom_fields=item.custom_fields,
                categories=categories,
                tags=tags,
                # keyphrases=keyphrases, # Optional
                # overall_entities=entities, # Optional
                language_of_primary_text=language,
                quality_score=quality_score,
                # complexity_score=complexity_score, # Optional
                displayable_metadata_summary=metadata_summary
            )
        except Exception as e:
            self.logger.error(f"Enrichment failed for {item.source_url}: {e}", exc_info=True)
            return self._create_fallback_enriched_item(item)

    def _nlp_process(self, item: NormalizedItem) -> Tuple[List[str], List[str], List[Dict[str, str]]]:
        tags, keyphrases, entities = set(), [], []
        content = item.cleaned_text_content or ''
        if not content: return [], [], []

        try:
            doc = self.nlp(content[:5000])  # Limit NLP processing length
            for token in doc:
                if not token.is_stop and not token.is_punct and len(token.lemma_) > 2 and token.pos_ in ['NOUN',
                                                                                                         'PROPN',
                                                                                                         'ADJ']:
                    tags.add(token.lemma_.lower())
            # Keyphrase extraction might be too RAG-specific, can be removed or simplified
            # for chunk in doc.noun_chunks:
            #     phrase = chunk.text.lower().strip()
            #     if len(phrase.split()) >= 2 and len(phrase) > 5 and not any(sw in phrase for sw in ['this', 'that']):
            #         keyphrases.append(phrase)

            # Entity extraction can be useful for stats (player names, scores, etc.)
            # seen_entities = set()
            # for ent in doc.ents:
            #     if len(ent.text.strip()) > 2:
            #         key = (ent.text.lower().strip(), ent.label_)
            #         if key not in seen_entities:
            #             entities.append({'text': ent.text.strip(), 'label': ent.label_, 'description': spacy.explain(ent.label_) or ent.label_})
            #             seen_entities.add(key)
            # keyphrases = sorted(list(set(keyphrases)), key=len, reverse=True)
        except Exception as e:
            self.logger.debug(f"NLP processing sub-step failed: {e}")
        return sorted(list(tags))[:15], keyphrases[:10], entities[:20]

    def _generate_smart_categories(self, item: NormalizedItem) -> List[str]:
        categories = set([item.source_type])
        url_parts = str(item.source_url).lower().split('/')
        domain_parts = url_parts[2].split('.') if len(url_parts) > 2 else []
        for part in domain_parts + url_parts[3:6]:  # Consider path segments for categories
            if len(part) > 2 and part not in ['www', 'com', 'org', 'net', 'html', 'php', 'index', 'en']:
                categories.add(part.replace('-', '_'))
        content_len = len(item.cleaned_text_content or '')
        if content_len > 2000:
            categories.add('long_form')
        elif content_len > 500:
            categories.add('standard_length')
        else:
            categories.add('short_form')
        return sorted(list(filter(None, categories)))[:10]

    def _detect_language(self, item: NormalizedItem) -> str:
        content_for_lang_detect = item.cleaned_text_content or item.title or ''
        if not content_for_lang_detect.strip(): return 'unknown'
        try:
            # Use a smaller sample for language detection for performance
            return detect_language(content_for_lang_detect[:1500])
        except LangDetectException:
            self.logger.debug(
                f"Language detection failed for content snippet from {item.source_url}, defaulting to 'en'.")
            return 'en'  # Default to English or make it 'unknown'

    def _calculate_quality_score(self, item: NormalizedItem, entities: List, tags: List) -> float:
        score = 5.0  # Base score
        content = item.cleaned_text_content or ''
        if len(content) > 2000:
            score += 2.0
        elif len(content) > 1000:
            score += 1.0
        elif len(content) < 100 and not item.custom_fields:
            score -= 2.0

        if item.cleaned_structured_blocks: score += min(len(item.cleaned_structured_blocks) * 0.4, 1.5)
        if item.custom_fields: score += min(sum(1 for v in item.custom_fields.values() if v and str(v).strip()) * 0.8,
                                            2.5)  # Higher weight for custom fields
        # if entities: score += min(len(entities) * 0.1, 1.0) # Optional
        if tags: score += min(len(tags) * 0.05, 0.5)
        return round(min(max(score, 0.5), 10.0), 1)

    # _calculate_complexity_score might be overkill, can be removed
    # def _calculate_complexity_score(self, item: NormalizedItem) -> float: ...

    def _create_metadata_summary(self, item, lang, cats, tags, ents, struct_elems, qual):
        return {
            'url': str(item.source_url), 'title': item.title or "N/A",
            'source_type': item.source_type, 'lang': lang,
            'cats': cats[:3], 'top_tags': tags[:3],
            # 'ents_count': len(ents), # Optional
            'struct_elems_count': len(struct_elems),
            'custom_fields_count': len(item.custom_fields),
            'qual_score': qual,
            'retrieved_ts': datetime.now().isoformat()
        }

    def _create_fallback_enriched_item(self, item: NormalizedItem) -> EnrichedItem:
        return EnrichedItem(
            id=item.id,
            # normalized_item_id=item.id,
            source_url=item.source_url, source_type=item.source_type, query_used=item.query_used,
            title=item.title or "Untitled", primary_text_content=item.cleaned_text_content,
            enriched_structured_elements=item.cleaned_structured_blocks,
            custom_fields=item.custom_fields, categories=[item.source_type, 'fallback_enrichment'],
            tags=['enrichment_failed'], language_of_primary_text='unknown', quality_score=2.0,
            displayable_metadata_summary={'url': str(item.source_url), 'title': item.title or "N/A",
                                          'status': 'enrichment_fallback'}
        )


# RobustExporter is removed from here. Saving will be handled by storage.saver via the GUI's SaveWorker.
# If backend-driven export is still needed for some reason, it would need to be adapted to save EnrichedItems.


def _clean_text_for_dedup(text: Optional[str]) -> str:
    if not text: return ""
    return re.sub(r'\s+', ' ', text.lower().strip())


def run_professional_pipeline(
        query_or_config_path: str,
        logger_instance=None,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        initial_content_type_hint: Optional[str] = None,
        max_retries: int = 3
) -> Tuple[List[EnrichedItem], PipelineMetrics]:
    logger = logger_instance if logger_instance else logging.getLogger(
        getattr(config, 'DEFAULT_LOGGER_NAME', 'ModularRAGScraper'))
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    metrics = PipelineMetrics(start_time=datetime.now())
    fetcher_pool = None

    def update_progress(step_name: str, current_step: int, total_steps: int = 8):  # Reduced total steps
        percentage = int((current_step / total_steps) * 100)
        if progress_callback:
            progress_callback(f"{step_name} ({current_step}/{total_steps})", percentage)
        logger.info(f"🔄 Pipeline progress: {step_name} - {percentage}%")

    try:
        update_progress("Initializing Configuration", 1)
        path_exists = os.path.exists(query_or_config_path)
        is_valid_extension = query_or_config_path.lower().endswith((".yaml", ".yml", ".json"))
        is_config_file_mode = path_exists and is_valid_extension

        cfg_manager: ConfigManager
        domain_query_for_log = query_or_config_path

        if is_config_file_mode:
            cfg_manager = ConfigManager(config_path=query_or_config_path, logger_instance=logger)
            if not cfg_manager.config:
                error_msg = f"Failed to load or validate configuration file: '{query_or_config_path}'"
                metrics.errors.append(error_msg)
                logger.error(f"❌ {error_msg}.")
                return [], metrics
            if cfg_manager.config.domain_info and cfg_manager.config.domain_info.get('name'):
                domain_query_for_log = cfg_manager.config.domain_info.get('name')
        else:
            cfg_manager = ConfigManager(logger_instance=logger)

        logger.info(f"🚀 Professional pipeline starting for: '{domain_query_for_log}'")

        update_progress("Initializing Components", 2)
        try:
            fetcher_pool = FetcherPool(num_workers=getattr(config, 'MAX_CONCURRENT_FETCHERS', 3), logger=logger)
            content_router = ContentRouter(config_manager=cfg_manager, logger_instance=logger)
            deduplicator = SmartDeduplicator(logger=logger)
            # Chunker is still initialized but its output is not used for RAG export
            chunker = Chunker(logger_instance=logger)
            quality_filter = ProfessionalQualityFilter(logger=logger)
            enricher = ProfessionalContentEnricher(nlp_model=NLP_MODEL, logger=logger)
        except Exception as e:
            metrics.errors.append(f"Component initialization failed: {e}")
            logger.error(f"❌ Component initialization failed: {e}", exc_info=True)
            return [], metrics

        update_progress("Preparing Fetch Tasks", 3)
        tasks_to_fetch = []
        if is_config_file_mode and cfg_manager.config and cfg_manager.config.sources:
            for src_cfg_model in cfg_manager.get_sources():
                for seed_url_model in src_cfg_model.seeds:
                    tasks_to_fetch.append(
                        (str(seed_url_model), src_cfg_model.source_type or src_cfg_model.name, domain_query_for_log,
                         None)
                    )
        elif not is_config_file_mode:  # Query/URL mode
            query_str = query_or_config_path
            if query_str.startswith(("http://", "https://")):
                tasks_to_fetch.append((query_str, "direct_url_input", query_str, None))
            elif DUCKDUCKGO_AVAILABLE:
                logger.info(f"🔍 Performing autonomous search for: '{query_str}'")
                try:
                    time.sleep(getattr(config, 'DUCKDUCKGO_SEARCH_DELAY', 1.5))
                    with DDGS(timeout=10) as ddgs:
                        ddgs_results = list(
                            ddgs.text(query_str, max_results=getattr(config, 'AUTONOMOUS_SEARCH_MAX_RESULTS', 5)))
                    for res in ddgs_results:
                        if res.get('href'): tasks_to_fetch.append(
                            (res['href'], "web_search_result", query_str, res.get('title')))
                except Exception as e_search:
                    metrics.errors.append(f"Autonomous search failed: {e_search}")
                    logger.error(f"❌ Autonomous search failed: {e_search}", exc_info=True)
                    return [], metrics  # Early exit if search fails
            else:
                error_msg = f"Input '{query_str}' is not a URL, and autonomous search is not available."
                metrics.errors.append(error_msg)
                logger.error(f"❌ {error_msg}")
                return [], metrics
        else:
            error_msg = "No sources found in configuration or invalid input."
            metrics.errors.append(error_msg)
            logger.error(f"❌ {error_msg}")
            return [], metrics

        if not tasks_to_fetch:
            metrics.errors.append("No URLs prepared for fetching.")
            logger.error("❌ No URLs for fetching.")
            return [], metrics
        metrics.total_urls = len(tasks_to_fetch)
        logger.info(f"📋 Prepared {metrics.total_urls} URLs for fetching.")
        for url, source_type, query_used_log, item_title in tasks_to_fetch:
            fetcher_pool.submit_task(url, source_type, query_used_log, item_title)

        update_progress(f"Fetching Content ({metrics.total_urls} URLs)", 4)
        fetched_items_all: List[FetchedItem] = fetcher_pool.get_results()
        metrics.successful_fetches = len(fetched_items_all)
        metrics.failed_fetches = metrics.total_urls - metrics.successful_fetches
        if not fetched_items_all: logger.warning("⚠️ No content was successfully fetched.")
        logger.info(f"✅ Fetched {metrics.successful_fetches} items (success rate: {metrics.success_rate:.1f}%)")

        update_progress("Parsing Content", 5)
        parsed_items_all: List[ParsedItem] = []
        for item_fetched in fetched_items_all:
            if item_fetched.content_bytes or item_fetched.content:
                try:
                    parsed = content_router.route_and_parse(item_fetched)
                    if parsed: parsed_items_all.append(parsed)
                except Exception as e_parse:
                    metrics.errors.append(f"Parse error for {item_fetched.source_url}: {e_parse}")
                    logger.warning(f"⚠️ Parse failed for {item_fetched.source_url}: {e_parse}", exc_info=True)
        metrics.parsed_items = len(parsed_items_all)
        logger.info(f"✅ Parsed {metrics.parsed_items} items.")

        update_progress("Normalizing & Deduplicating", 6)
        normalized_items_all: List[NormalizedItem] = []
        for p_item in parsed_items_all:
            try:
                # Simplified deduplication signature
                text_for_dedup = _clean_text_for_dedup(p_item.main_text_content or "") + \
                                 _clean_text_for_dedup(json.dumps(p_item.custom_fields, sort_keys=True))

                is_dup, _ = deduplicator.is_duplicate(text_for_dedup)
                if not is_dup:
                    deduplicator.add_snippet(text_for_dedup)
                    norm_item = NormalizedItem(
                        id=p_item.id, parsed_item_id=p_item.id, source_url=p_item.source_url,
                        source_type=p_item.source_type, query_used=p_item.query_used, title=p_item.title,
                        cleaned_text_content=p_item.main_text_content,
                        cleaned_structured_blocks=p_item.extracted_structured_blocks,
                        custom_fields=p_item.custom_fields,
                        language_of_main_text=p_item.detected_language_of_main_text
                    )
                    normalized_items_all.append(norm_item)
                else:
                    metrics.duplicates_filtered += 1
            except Exception as e_norm:
                metrics.errors.append(f"Normalization error for {p_item.source_url}: {e_norm}")
                logger.warning(f"⚠️ Normalization error for {p_item.source_url}: {e_norm}", exc_info=True)
        metrics.normalized_items = len(normalized_items_all)
        logger.info(
            f"✅ Normalized {metrics.normalized_items} unique items (filtered {metrics.duplicates_filtered} duplicates)")

        update_progress("Quality Filtering", 7)
        high_quality_items, filtered_count = quality_filter.filter_by_quality(normalized_items_all)
        metrics.quality_filtered = filtered_count

        update_progress("Enriching Content", 8)  # Renamed from "Enriching Metadata"
        enriched_items_all: List[EnrichedItem] = []
        for n_item in high_quality_items:
            try:
                enriched_items_all.append(enricher.enrich_item(n_item))
            except Exception as e_enrich:
                metrics.errors.append(f"Enrichment error for {n_item.source_url}: {e_enrich}")
                enriched_items_all.append(enricher._create_fallback_enriched_item(n_item))
        metrics.enriched_items = len(enriched_items_all)
        logger.info(f"✅ Enriched {metrics.enriched_items} items")
        if hasattr(logger, 'enhanced_snippet_data'):  # For GUI
            logger.enhanced_snippet_data = [item.displayable_metadata_summary for item in enriched_items_all]

        # Removed RAG Chunking and RAG Exporting steps
        # The Chunker is still available if some other form of content segmentation is needed
        # The final output of this pipeline is List[EnrichedItem]

        metrics.end_time = datetime.now()
        logger.info(f"""
🎉 Professional pipeline completed!
📊 Summary:
   • Duration: {metrics.duration.total_seconds():.1f}s
   • URLs Attempted: {metrics.total_urls}
   • Successful Fetches: {metrics.successful_fetches} (Rate: {metrics.success_rate:.1f}%)
   • Parsed Items: {metrics.parsed_items}
   • Unique Items (post-dedup): {metrics.normalized_items}
   • Quality Filtered Out: {metrics.quality_filtered}
   • Final Enriched Items: {metrics.enriched_items} 
   • Errors during pipeline: {len(metrics.errors)}
""")
        if metrics.errors:
            logger.warning(f"⚠️ {len(metrics.errors)} errors logged. First few:")
            for i, err_msg in enumerate(metrics.errors[:3], 1): logger.warning(f"  {i}. {err_msg}")

        return enriched_items_all, metrics

    except KeyboardInterrupt:
        error_msg = "Pipeline interrupted by user."
        logger.warning(f"🛑 {error_msg}")
        if metrics: metrics.errors.append(error_msg); metrics.end_time = datetime.now()
        return [], metrics
    except Exception as e_pipeline:
        error_msg = f"Critical pipeline failure: {e_pipeline}"
        logger.error(f"💥 {error_msg}", exc_info=True)
        if metrics: metrics.errors.append(error_msg); metrics.end_time = datetime.now()
        return [], metrics
    finally:
        if fetcher_pool:
            fetcher_pool.shutdown()


def search_and_fetch(
        query_or_config_path: str,
        logger: logging.Logger,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        content_type_gui: Optional[str] = None
) -> List[EnrichedItem]:
    if not query_or_config_path or not query_or_config_path.strip():
        logger.error("❌ No query or config path provided.")
        if progress_callback: progress_callback("Error: No input", 100)
        return []

    logger.info(f"🎯 Search initiated: '{query_or_config_path}' (GUI hint: {content_type_gui})")

    enriched_items, metrics_data = run_professional_pipeline(
        query_or_config_path,
        logger_instance=logger,
        progress_callback=progress_callback,
        initial_content_type_hint=content_type_gui
    )

    if metrics_data:
        logger.info(f"📈 Final Pipeline Metrics: {json.dumps(metrics_data.to_dict(), indent=2)}")
    else:
        logger.error("❌ Pipeline did not return metrics data.")

    if progress_callback:
        final_msg = "Processing complete."
        if metrics_data and metrics_data.errors:
            final_msg = f"Completed with {len(metrics_data.errors)} error(s)."
        elif not enriched_items and not (metrics_data and metrics_data.errors):
            final_msg = "Completed. No data extracted or all items filtered."
        progress_callback(final_msg, 100)

    return enriched_items


# Legacy functions (can be removed if truly unused)
def fetch_stdlib_docs(m, l): return []


def fetch_stackoverflow_snippets(q, l, t=None): return [], []


def fetch_github_readme_snippets(q, l, mr=None, spr=None): return []


def fetch_github_file_snippets(q, l, mr=None, fprt=None): return [], []


def detect_content_type(q: str, l): return getattr(config, 'DEFAULT_CONTENT_TYPE_FOR_GUI', 'html')