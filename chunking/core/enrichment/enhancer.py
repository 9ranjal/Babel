# chunking/enhancer.py
# NLP and enhancement logic

import hashlib
import re
import numpy as np
import logging
from typing import Dict, Any, List, Optional
from spacy.language import Language
import spacy

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pre-compile regex patterns for performance
NUMBER_PATTERN = re.compile(r'\b\d+(?:\.\d+)?(?:%|st|nd|rd|th)?\b')
DATE_PATTERNS = [
    re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', re.IGNORECASE),
    re.compile(r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b', re.IGNORECASE),
    re.compile(r'\b\d{4}\b')
]
# ORG_PATTERN = re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b')  # REMOVED: This was extracting garbage
WORD_PATTERN = re.compile(r'\b[A-Z][a-z]+\b|\b[a-z]{5,}\b')
FACT_INDICATORS = [
    re.compile(r'\b(is|are|was|were|has|have|had)\b', re.IGNORECASE),
    re.compile(r'\b(consists of|comprises|includes|contains)\b', re.IGNORECASE)
]
REFERENCE_PATTERNS = [
    re.compile(r'\b(as per|according to|states that|mentioned in|as stated by|report says|committee observed)\b', re.IGNORECASE)
]
DEFINITION_PATTERNS = [
    re.compile(r'\b(means|refers to|defined as|is known as|called|termed as|concept of|principle of)\b', re.IGNORECASE)
]

from ..config import (
    SPACY_MODEL, BATCH_SIZE, N_PROCESS, MAX_MEMORY_CHUNKS,
    MARKDOWN_RETRIEVAL_THRESHOLD, EXCEL_RETRIEVAL_THRESHOLD,
    ENTITY_DENSITY_THRESHOLD, PROTECTED_TYPES, ENTITY_TYPES,
    DOMAIN_TAG_MAPPING, STOP_WORDS
)
from ..schema import build_chunk_template, get_chunk_field_safe
from .metadata import generate_concept_tags, map_ner_to_domain_tags, extract_hierarchical_metadata
from .domain_classifier import DomainClassifier
from .concept_analyzer import ConceptAnalyzer
from .context_tagger import generate_context_tags
from ..analysis.semantics import classify_semantic_type_hierarchical
from ..analysis.scoring import calculate_entity_density, calculate_retrieval_score
from .excel_rewriter import rewrite_list_chunk
from .embedding import get_embedding, compute_embeddings
from ..processing.text_cleaner import normalize_chunk_text

# Singleton for spaCy models
_spacy_models = {}

def get_spacy_model(model_name: str = SPACY_MODEL) -> Language:
    """Get spaCy model singleton to avoid reloading."""
    if model_name not in _spacy_models:
        _spacy_models[model_name] = spacy.load(model_name)
    return _spacy_models[model_name]

def preprocess_excel_text(text: str) -> str:
    """Preprocess Excel text for better NLP processing."""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    # Remove bullet points and numbering
    text = re.sub(r'^[\d\-\.\*]+\.?\s*', '', text)
    return text

def extract_custom_entities(text: str, chunk: Dict[str, Any]) -> Dict[str, list]:
    """Extract custom entities using regex patterns."""
    entities = {
        "person_entities": [],
        "org_entities": [],
        "gpe_entities": [],
        "date_entities": [],
        "number_entities": [],
        "event_entities": [],
        "law_entities": [],
        "norp_entities": [],
        "workofart_entities": [],
        "language_entities": [],
        # New entity fields
        "loc_entities": [],
        "fac_entities": [],
        "product_entities": [],
        "percent_entities": [],
        "money_entities": [],
        "quantity_entities": [],
        "cardinal_entities": [],
        "ordinal_entities": [],
        "time_entities": [],
        "facility_entities": [],
        "institution_entities": []
    }
    
    # Extract numbers using pre-compiled pattern
    numbers = NUMBER_PATTERN.findall(text)
    entities["number_entities"] = numbers
    
    # Extract dates using pre-compiled patterns
    dates = []
    for pattern in DATE_PATTERNS:
        dates.extend(pattern.findall(text))
    entities["date_entities"] = dates
    
    # Extract organizations using pre-compiled pattern
    # FIXED: Only extract actual organizations, not any capitalized words
    # This was causing garbage like "Stars", "Larger", "Some", "Millions" to be extracted
    # We'll rely on spaCy NER for proper organization detection
    # orgs = ORG_PATTERN.findall(text)
    # entities["org_entities"] = [org for org in orgs if len(org.split()) >= 1]
    
    return entities

def extract_primary_entities(chunk: Dict[str, Any]) -> List[str]:
    """
    Extract primary named entities only (PERSON, ORG, GPE).
    Focuses on specific named concepts for entity-based retrieval.
    """
    primary_entities = []
    
    # Only extract named entities (not numbers, dates, etc.)
    entity_data = chunk.get("entities", {})
    named_entity_lists = [
        entity_data.get("person_entities", []),
        entity_data.get("org_entities", []),
        entity_data.get("gpe_entities", [])
    ]
    
    # Flatten and deduplicate
    for entity_list in named_entity_lists:
        if isinstance(entity_list, list):
            primary_entities.extend(entity_list)
    
    # Quality filtering: remove phrases that are not proper named entities
    filtered_entities = []
    for entity in primary_entities:
        # Skip if entity is too long (likely a phrase, not a name)
        if len(entity.split()) > 4:
            continue
        
        # Skip if entity contains common non-name words
        non_name_words = ["growth", "development", "increase", "decrease", "change", "process", "system"]
        if any(word.lower() in entity.lower() for word in non_name_words):
            continue
        
        # Skip if entity is all lowercase (likely not a proper noun)
        if entity.islower() and len(entity.split()) == 1:
            continue
        
        # Skip if entity contains numbers (likely not a name)
        if any(char.isdigit() for char in entity):
            continue
        
        filtered_entities.append(entity)
    
    # Remove duplicates and limit to top 5 most important
    primary_entities = list(set(filtered_entities))[:5]
    
    return primary_entities

def enhance_chunk_metadata(chunk: Dict[str, Any], filepath: str = None, corpus_context: List[str] = None) -> Dict[str, Any]:
    """
    Enhance chunk with advanced metadata extraction.
    
    Args:
        chunk: Chunk dictionary
        filepath: Optional filepath for hierarchical metadata
        corpus_context: Optional corpus context for concept analysis
        
    Returns:
        Enhanced chunk with additional metadata
    """
    # 1. Enhanced hierarchical metadata
    if filepath:
        hierarchical_meta = extract_hierarchical_metadata(filepath)
        chunk.update(hierarchical_meta)
    
    # 2. Document structure extraction (if markdown)
    if chunk.get("source_type") == "markdown" and chunk.get("sections"):
        from ..analysis.utils import extract_document_structure
        doc_structure = extract_document_structure(chunk.get("sections", []))
        chunk.update(doc_structure)
    
    # 3. Domain classification
    domain_classifier = DomainClassifier()
    chunk["domain_tags"] = domain_classifier.classify_domain(chunk)
    
    # 4. Enhanced concept tag extraction
    concept_analyzer = ConceptAnalyzer()
    chunk["concept_tags"] = concept_analyzer.extract_concept_tags(chunk, corpus_context)
    
    # 5. Enhanced retrieval keywords
    chunk["retrieval_keywords"] = extract_enhanced_retrieval_keywords(chunk)
    
    # 6. Primary entities
    chunk["primary_entities"] = extract_primary_entities(chunk)
    
    return chunk

def extract_enhanced_retrieval_keywords(chunk: Dict[str, Any]) -> List[str]:
    """
    Extract retrieval keywords optimized for dense+BM25 hybrid search.
    Focuses on TF/IDF terms and chunk context for retrieval.
    """
    keywords = set()
    
    # Extract heading from source_chunk (context)
    source_chunk = get_chunk_field_safe(chunk, "source_chunk", "")
    if "#" in source_chunk:
        heading = source_chunk.split("#")[-1].strip()
        # Clean up markdown formatting
        heading = re.sub(r'[\[\]\*\*\-\_\.]', ' ', heading)
        heading = re.sub(r'\s+', ' ', heading).strip()
        if heading:
            # Extract specific terms from heading
            heading_terms = [term for term in heading.lower().split() 
                           if len(term) > 3 and term not in STOP_WORDS]
            keywords.update(heading_terms[:5])  # Limit heading terms
    
    # Extract specific, searchable terms from chunk_text (TF-IDF style)
    text = get_chunk_field_safe(chunk, "chunk_text", "").lower()
    
    # Focus on specific terms: proper nouns, technical terms, numbers
    # Proper nouns (capitalized words) - with noise filtering
    proper_nouns = re.findall(r'\b[A-Z][a-z]+\b', text)
    
    # Filter out noise terms
    noise_terms = {"Driven", "Than", "The", "This", "That", "These", "Those", "First", "Second", "Third", "Fourth", "Fifth"}
    filtered_nouns = [noun for noun in proper_nouns if noun not in noise_terms and len(noun) > 2]
    keywords.update(filtered_nouns[:8])
    
    # Technical terms (longer words, likely domain-specific)
    technical_terms = [word for word in text.split() 
                      if len(word) > 6 and word not in STOP_WORDS]
    keywords.update(technical_terms[:5])
    
    # Numbers and statistics (important for retrieval)
    numbers = re.findall(r'\b\d{4}\b|\d+\.?\d*', text)
    keywords.update(numbers[:3])
    
    # Add topic and subtopics (hierarchical context)
    topic = chunk.get("topic", "")
    if topic:
        keywords.add(topic.lower())
    
    for i in range(1, 6):
        subtopic = chunk.get(f"subtopic{i}", "")
        if subtopic:
            keywords.add(subtopic.lower())
    
    # Add domain tags (for domain-specific retrieval)
    domain_tags = chunk.get("domain_tags", [])
    keywords.update([tag.lower() for tag in domain_tags])
    
    # Filter out common words and short terms
    keywords = {kw for kw in keywords if kw not in STOP_WORDS and len(kw) > 2}

    # Incorporate critical abbreviations and codes from entities (ensure coverage)
    entity_texts = chunk.get("entities", {}).get("entity_texts", {})
    for entity_list in entity_texts.values():
        for entity in entity_list:
            if not entity:
                continue
            # Abbreviations: all caps 2-5 chars (e.g., GDP, RBI)
            if entity.isupper() and 2 <= len(entity) <= 5:
                keywords.add(entity.lower())
            # Article/Section numbers (e.g., Article 370)
            if entity.lower().startswith("article "):
                parts = entity.split()
                if parts and parts[-1].isdigit():
                    keywords.add(parts[-1])
            # Plain years (e.g., 2019)
            import re as _re
            if _re.fullmatch(r"\d{4}", entity.strip()):
                keywords.add(entity.strip())

    # Normalize trailing punctuation (e.g., '2019.' -> '2019')
    normalized = set()
    for kw in keywords:
        normalized.add(kw.rstrip('.,;:'))
    keywords = normalized
    
    # Merge similar keywords to reduce redundancy
    merged_keywords = _merge_similar_keywords(list(keywords))
    
    return merged_keywords[:5]  # Limit to top 5 keywords (compact for RAG)

def _merge_similar_keywords(keywords: List[str]) -> List[str]:
    """
    Merge similar keywords to reduce redundancy.
    
    Args:
        keywords: List of keywords to merge
        
    Returns:
        List of merged keywords
    """
    if not keywords:
        return []
    
    # Sort by length (longer keywords first)
    sorted_keywords = sorted(keywords, key=len, reverse=True)
    merged = []
    
    for keyword in sorted_keywords:
        # Check if this keyword is already covered by a longer keyword
        is_covered = False
        for existing in merged:
            # If existing keyword contains this one, skip
            if keyword.lower() in existing.lower() and len(keyword) < len(existing):
                is_covered = True
                break
            # If this keyword contains existing one, replace
            elif existing.lower() in keyword.lower() and len(existing) < len(keyword):
                merged.remove(existing)
                break
        
        if not is_covered:
            merged.append(keyword)
    
    return merged

def extract_retrieval_keywords(chunk: Dict[str, Any]) -> List[str]:
    """Extract MINIMAL retrieval keywords - only critical abbreviations and codes.
    
    OPTIMIZATION: Reduced 80% - modern embeddings handle semantic similarity.
    Focus only on exact-match terms that embeddings might miss.
    """
    keywords = set()
    
    # Extract only critical abbreviations and codes
    text = get_chunk_field_safe(chunk, "chunk_text", "")
    
    # Critical patterns: abbreviations, codes, acts, years
    critical_patterns = [
        r'\b[A-Z]{2,5}\b',  # Abbreviations: GDP, SEZ, UPSC, etc.
        r'\b\d{4}\b',       # Years: 1991, 2000, etc.
        r'\w+\s+Act\b',     # Acts: Sarfaesi Act, etc.
        r'\bArticle\s+\d+', # Constitutional articles
        r'\bSection\s+\d+'  # Legal sections
    ]
    
    for pattern in critical_patterns:
        matches = re.findall(pattern, text)
        keywords.update([m.lower() for m in matches])
    
    # Add only entity abbreviations (not full names - embeddings handle those)
    entity_texts = chunk.get("entities", {}).get("entity_texts", {})
    for entity_list in entity_texts.values():
        for entity in entity_list:
            # Only add if it's an abbreviation (all caps, 2-5 chars)
            if entity and entity.isupper() and 2 <= len(entity) <= 5:
                keywords.add(entity.lower())
    
    # Filter for only the most critical terms
    keywords = {kw for kw in keywords if len(kw) >= 2}
    
    # DRASTICALLY reduced: max 5 keywords (was 20)
    return list(keywords)[:5]

def batch_enrich_chunks_streaming(chunks: List[Dict[str, Any]], model_name: str = SPACY_MODEL, n_process: int = N_PROCESS, batch_size: int = BATCH_SIZE, max_memory_chunks: int = MAX_MEMORY_CHUNKS) -> List[Dict[str, Any]]:
    """Process chunks in memory-managed batches for large datasets."""
    try:
        if len(chunks) <= max_memory_chunks:
            return batch_enrich_chunks(chunks, model_name, n_process, batch_size)
        
        enriched_chunks = []
        total_batches = (len(chunks) + max_memory_chunks - 1) // max_memory_chunks
        
        for i in range(0, len(chunks), max_memory_chunks):
            batch_num = (i // max_memory_chunks) + 1
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(chunks[i:i + max_memory_chunks])} chunks)")
            
            try:
                batch = chunks[i:i + max_memory_chunks]
                enriched_batch = batch_enrich_chunks(batch, model_name, n_process, batch_size)
                enriched_chunks.extend(enriched_batch)
                
                # Let Python's garbage collector handle memory
                logger.debug(f"Batch {batch_num} completed successfully")
                
            except Exception as e:
                logger.error(f"Error processing batch {batch_num}: {str(e)}")
                # Continue with next batch instead of failing completely
                continue
        
        logger.info(f"Streaming enrichment completed: {len(enriched_chunks)} chunks processed")
        return enriched_chunks
        
    except Exception as e:
        logger.error(f"Critical error in batch_enrich_chunks_streaming: {str(e)}")
        raise

def batch_enrich_chunks(chunks: List[Dict[str, Any]], model_name: str = SPACY_MODEL, n_process: int = N_PROCESS, batch_size: int = BATCH_SIZE) -> List[Dict[str, Any]]:
    """Enrich chunks with NLP processing in batches - optimized for macOS."""
    try:
        if not chunks:
            logger.info("No chunks provided for enrichment")
            return []
        
        logger.info(f"Starting enrichment of {len(chunks)} chunks")
        import time
        start_time = time.time()
        
        # 🔧 NEW: Pre-enrichment comprehensive normalization for better performance
        print(f"🧹 Pre-enrichment comprehensive normalization for {len(chunks)} chunks...")
        pre_norm_start = time.time()
        
        from ..processing.text_cleaner import normalize_chunks_batch
        normalization_result = normalize_chunks_batch(chunks, preserve_original=False)
        chunks = normalization_result["chunks"]
        norm_stats = normalization_result["stats"]
        
        pre_norm_time = time.time() - pre_norm_start
        print(f"🧹 Pre-normalization complete: {norm_stats['normalized_count']} normalized, {norm_stats['skipped_count']} skipped, {norm_stats['error_count']} errors in {pre_norm_time:.2f}s")
        
        # Load spaCy model
        nlp = get_spacy_model(model_name)
        
        # Extract texts for batch processing
        texts = [chunk.get("chunk_text", "") for chunk in chunks]
        
        # Process with spaCy in batches - macOS optimized
        enriched_chunks = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        for i in range(0, len(texts), batch_size):
            batch_start = time.time()
            batch_texts = texts[i:i + batch_size]
            batch_chunks = chunks[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            # Process batch with spaCy - sequential for macOS stability
            docs = [nlp(text) for text in batch_texts]  # Sequential processing
            
            batch_enrichment_start = time.time()
            
            for j, (doc, chunk) in enumerate(zip(docs, batch_chunks)):
                enriched_chunk = chunk.copy()
                
                # --- 1. Entity Extraction (v2 schema: restrict to 8 high-value types) ---
                entities = {k: [] for k in [
                    "person_entities",     # PERSON
                    "org_entities",        # ORG
                    "gpe_entities",        # GPE
                    "date_entities",       # DATE
                    "money_entities",      # MONEY
                    "percent_entities",    # PERCENT
                    "law_entities",        # LAW
                    "event_entities",      # EVENT
                    "loc_entities",        # LOC
                    "cardinal_entities",   # CARDINAL
                    "quantity_entities",   # QUANTITY
                    "norp_entities",       # NORP
                    "fac_entities",        # FAC
                    "product_entities",    # PRODUCT
                    "workofart_entities",  # WORK_OF_ART
                    "language_entities",   # LANGUAGE
                    "time_entities",       # TIME
                    "ordinal_entities"     # ORDINAL
                ]}
                entity_counts = {}
                entity_texts = {}
                
                # Entity type to field mapping
                # OPTIMIZED: Focus on high-value entity types for RAG
                # Reduced from 22 to 8 most critical types
                entity_field_mapping = {
                    # HIGH-VALUE ENTITIES (keep)
                    "PERSON": "person_entities",        # Essential for biographical queries
                    "ORG": "org_entities",              # Government, institutions 
                    "GPE": "gpe_entities",              # Countries, states, cities
                    "DATE": "date_entities",            # Historical events, timelines
                    "MONEY": "money_entities",          # Economic data
                    "PERCENT": "percent_entities",      # Statistics, economic indicators
                    "LAW": "law_entities",              # Acts, constitutional articles
                    "EVENT": "event_entities",          # Historical events, movements

                    # Newly included entities
                    "LOC": "loc_entities",              # Non-political locations
                    "CARDINAL": "cardinal_entities",    # Cardinal numbers / counts
                    "QUANTITY": "quantity_entities",    # Measurements and numeric quantities
                    "NORP": "norp_entities",            # Nationalities, religious/political groups
                    "FAC": "fac_entities",              # Facilities
                    "PRODUCT": "product_entities",      # Products
                    "WORK_OF_ART": "workofart_entities",# Works of art
                    "LANGUAGE": "language_entities",    # Languages
                    "TIME": "time_entities",            # Times smaller than a day
                    "ORDINAL": "ordinal_entities",      # First, second, etc.
                    
                    # REMOVED LOW-VALUE ENTITIES for RAG:
                    # "NUMBER", "NORP", "WORK_OF_ART", "LANGUAGE", "LOC", "FAC", 
                    # "PRODUCT", "QUANTITY", "CARDINAL", "ORDINAL", "TIME", 
                    # "FACILITY", "INSTITUTION" - too noisy for domain content
                }
                
                for ent in doc.ents:
                    ent_type = ent.label_
                    ent_text = ent.text.strip()
                    
                    # Debug logging
                    print(f"🔍 Processing entity: {ent_type} = '{ent_text}'")
                    
                    if ent_type in ENTITY_TYPES:
                        print(f"✅ Entity type '{ent_type}' recognized")
                        
                        # Map entity type to field name
                        field_name = entity_field_mapping.get(ent_type)
                        if field_name:
                            entities[field_name].append(ent_text)
                            print(f"🔍 Added to {field_name}: {entities[field_name]}")
                        
                        # Update counts
                        entity_counts[ent_type] = entity_counts.get(ent_type, 0) + 1
                        
                        # Update entity texts
                        if ent_type not in entity_texts:
                            entity_texts[ent_type] = []
                        entity_texts[ent_type].append(ent_text)
                    else:
                        print(f"❌ Entity type '{ent_type}' not in ENTITY_TYPES: {ENTITY_TYPES}")
                
                # Custom regex entities disabled for v2 (avoid schema bloat)
                # If needed in future, merge only into allowed fields explicitly.
                
                # Update enriched chunk with all entities (save to nested entities structure)
                if "entities" not in enriched_chunk:
                    enriched_chunk["entities"] = {}
                for field_name, entity_list in entities.items():
                    enriched_chunk["entities"][field_name] = entity_list
                
                # Also save entity counts and texts to nested structure
                enriched_chunk["entities"]["entity_counts"] = entity_counts
                enriched_chunk["entities"]["entity_texts"] = entity_texts
                
                # --- 2. Entity Flags (DISABLED in v2 schema) ---
                # Legacy boolean flags like ner_PERSON/ner_ORG polluted the schema.
                # We now rely solely on nested `entities` lists and counts.
                # Keeping this block disabled to prevent reintroduction.
                # for ent_type in ENTITY_TYPES:
                #     flag_name = f"ner_{ent_type}"
                #     enriched_chunk[flag_name] = entity_counts.get(ent_type, 0) > 0
                
                # --- 3. Entity Density and Quality Assessment ---
                entity_density = calculate_entity_density(enriched_chunk)
                enriched_chunk["entity_density"] = entity_density
                
                # Quality assessment for short chunks (fact-likeness already determined in normalization)
                if enriched_chunk.get("chunk_word_count", 0) < 50:
                    # Promote short chunks with valuable content
                    if entity_density > ENTITY_DENSITY_THRESHOLD or enriched_chunk.get("is_fact_like", False):
                        enriched_chunk["chunk_quality"] = "ok"

                        enriched_chunk["omit_flag"] = False
                        enriched_chunk["show_skip_reasons"] = []
                    else:
                        enriched_chunk["chunk_quality"] = "poor"

                        enriched_chunk["omit_flag"] = True
                        enriched_chunk["show_skip_reasons"] = ["low_entity_density"]
                else:
                    enriched_chunk["chunk_quality"] = "ok"
                    # quality_flag deprecated - using chunk_quality only
                    enriched_chunk["omit_flag"] = False
                    enriched_chunk["show_skip_reasons"] = []
                
                enriched_chunks.append(enriched_chunk)
            
            # Progress monitoring
            batch_time = time.time() - batch_start
            if batch_num % 5 == 0 or batch_num == total_batches:
                elapsed = time.time() - start_time
                rate = (batch_num * batch_size) / elapsed if elapsed > 0 else 0
                print(f"⚡ Batch {batch_num}/{total_batches}: {len(batch_chunks)} chunks in {batch_time:.2f}s (avg: {rate:.1f} chunks/s)")
        
        nlp_time = time.time() - start_time
        print(f"🧠 NLP processing complete: {len(enriched_chunks)} chunks in {nlp_time:.2f}s ({len(enriched_chunks)/nlp_time:.1f} chunks/s)")
        
        # --- 3. Final Processing (consolidated from process_chunk_for_rag) ---
        final_processing_start = time.time()
        print(f"🚀 Starting final processing for {len(enriched_chunks)} chunks...")
        
        for i, enriched_chunk in enumerate(enriched_chunks):
            # Rewrite list chunks
            enriched_chunk = rewrite_list_chunk(enriched_chunk)
            
            # Text already normalized in pre-enrichment step
            
            # Enhanced metadata extraction  
            entities_before = enriched_chunk.get('entities', {}).get('person_entities', [])
            print(f"🔍 Before enhance_chunk_metadata - person_entities: {entities_before}")
            enriched_chunk = enhance_chunk_metadata(enriched_chunk)
            entities_after = enriched_chunk.get('entities', {}).get('person_entities', [])
            print(f"🔍 After enhance_chunk_metadata - person_entities: {entities_after}")
            
            # Classify semantic type and ensure dict structure
            semantic_type = classify_semantic_type_hierarchical(enriched_chunk)
            if isinstance(semantic_type, dict):
                enriched_chunk["semantic_type"] = semantic_type
            else:
                enriched_chunk["semantic_type"] = {
                    "primary": semantic_type,
                    "secondary": [],
                    "domain": None,
                    "cognitive_level": None,
                    "question_type_affinity": []
                }
            
            # Generate context tags
            context_tags = generate_context_tags(enriched_chunk)
            enriched_chunk["context_tags"] = context_tags
            
            # Calculate entity density (store under retrieval_metadata for ranking, keep top-level for backward compatibility)
            ed = calculate_entity_density(enriched_chunk)
            enriched_chunk["entity_density"] = ed
            
            # Calculate retrieval score (save to nested retrieval_metadata structure)
            retrieval_score = calculate_retrieval_score(enriched_chunk) or 0.0
            if "retrieval_metadata" not in enriched_chunk:
                enriched_chunk["retrieval_metadata"] = {}
            enriched_chunk["retrieval_metadata"]["retrieval_score"] = retrieval_score
            print(f"🔍 Retrieval score set to: {retrieval_score}")

            # Map high-value RAG fields into nested retrieval_metadata
            # - retrieval_keywords (from enhanced extraction)
            # - primary_entities (list)
            # - concept_tags and context_tags
            # - entity_density
            try:
                keywords = extract_enhanced_retrieval_keywords(enriched_chunk)
            except Exception:
                # Fallback to critical-term extractor for robustness
                try:
                    keywords = extract_retrieval_keywords(enriched_chunk)
                except Exception:
                    keywords = []
            # Enforce compact keyword set (≤5)
            enriched_chunk["retrieval_metadata"]["retrieval_keywords"] = (keywords or [])[:5]

            primary_entities = enriched_chunk.get("primary_entities", [])
            if not isinstance(primary_entities, list):
                primary_entities = [primary_entities] if primary_entities else []
            enriched_chunk["retrieval_metadata"]["primary_entities"] = primary_entities

            concept_tags = enriched_chunk.get("concept_tags", [])
            if not isinstance(concept_tags, list):
                concept_tags = [concept_tags] if concept_tags else []
            enriched_chunk["retrieval_metadata"]["concept_tags"] = concept_tags

            enriched_chunk["retrieval_metadata"]["context_tags"] = context_tags or []
            enriched_chunk["retrieval_metadata"]["entity_density"] = ed

            # Store primary entity under retrieval_metadata (best for RAG)
            if primary_entities:
                enriched_chunk["retrieval_metadata"]["primary_entity"] = primary_entities[0]

            # Populate reranker fields (placeholder heuristic)
            # In absence of query, approximate a confidence-based reranker score
            rr_model = "bge-reranker-v1.5"
            rr_score = min(1.0, max(0.0, retrieval_score + 0.12))
            enriched_chunk["retrieval_metadata"]["reranker_model"] = rr_model
            enriched_chunk["retrieval_metadata"]["reranker_score"] = rr_score

            # Add quality flags based on confidence and entities
            quality_flags = enriched_chunk.get("qa_metadata", {}).get("quality_flags", [])
            conf = enriched_chunk.get("qa_metadata", {}).get("confidence_score", 0.5) or 0.5
            if conf < 0.7 and "low_confidence" not in quality_flags:
                quality_flags.append("low_confidence")
            gpes = enriched_chunk.get("entities", {}).get("gpe_entities", [])
            if not gpes and "missing_gpe" not in quality_flags:
                quality_flags.append("missing_gpe")
            enriched_chunk["qa_metadata"]["quality_flags"] = quality_flags
            
            # Primary entities already extracted in enhance_chunk_metadata()
            
            # Retrieval keywords already extracted in enhance_chunk_metadata()
            
            # ── Unified Omit Logic (post-enrichment) ──
            omit_reasons: List[str] = []
            qa = enriched_chunk.get("qa_metadata", {})
            rm = enriched_chunk.get("retrieval_metadata", {})
            em = enriched_chunk.get("excel_metadata", {})

            word_count = enriched_chunk.get("chunk_word_count", 0) or 0
            is_context_dead = qa.get("is_context_dead", False)
            quality_score = qa.get("quality_score", 0.5) or 0.5
            confidence_score = qa.get("confidence_score", 0.5) or 0.5
            is_complete_sentence = qa.get("is_complete_sentence", True)
            retrieval_score = rm.get("retrieval_score", 0.0) or 0.0
            entity_density = rm.get("entity_density", enriched_chunk.get("entity_density", 0.0)) or 0.0
            is_fact_like = em.get("is_fact_like", False)

            # Named protections (Article <num>, policy + year, LAW entities)
            import re as _re
            text_lower = (enriched_chunk.get("chunk_text") or "").lower()
            has_law = bool(enriched_chunk.get("entities", {}).get("law_entities"))
            has_article_num = bool(_re.search(r"\barticle\s+\d+\b", text_lower))
            has_policy_year = bool(_re.search(r"\b(policy|scheme|act)\b.*\b\d{4}\b", text_lower))

            # Always keep overrides
            kept_due_to_override = False
            if retrieval_score > 0.4 or has_law or has_article_num or has_policy_year:
                kept_due_to_override = True
                qa_flags = qa.get("quality_flags", [])
                if "kept_due_to_retrieval_score" not in qa_flags and retrieval_score > 0.4:
                    qa_flags.append("kept_due_to_retrieval_score")
                enriched_chunk["qa_metadata"]["quality_flags"] = qa_flags

            # Hard skips
            if is_context_dead and word_count <= 15 and not kept_due_to_override:
                omit_reasons.append("context_dead")
            if quality_score < 0.4 and not kept_due_to_override:
                omit_reasons.append("very_low_quality")
            if confidence_score < 0.4 and (is_complete_sentence is False) and not kept_due_to_override:
                omit_reasons.append("incoherent_low_confidence")

            # Soft logic (short only)
            if word_count < 30 and (retrieval_score < 0.3) and (entity_density < 0.01) and (not is_fact_like) and not kept_due_to_override:
                omit_reasons.append("low_signal_short")

            # Context-dead but long: review flag, keep
            if is_context_dead and word_count > 25 and not omit_reasons:
                qa_flags = enriched_chunk.get("qa_metadata", {}).get("quality_flags", [])
                if "context_dead_review" not in qa_flags:
                    qa_flags.append("context_dead_review")
                enriched_chunk["qa_metadata"]["quality_flags"] = qa_flags

            # Standardize flags for size
            std_flags = []
            for f in enriched_chunk["qa_metadata"].get("quality_flags", []):
                if f in ("fragment", "too_long", "low_signal_short", "low_confidence", "context_dead_review"):
                    std_flags.append(f)
            enriched_chunk["qa_metadata"]["quality_flags"] = std_flags

            # Apply omission
            if omit_reasons:
                enriched_chunk["qa_metadata"]["omit_reason"] = omit_reasons
                enriched_chunk["omit_flag"] = True
                ssr = enriched_chunk.get("show_skip_reasons", []) or []
                enriched_chunk["show_skip_reasons"] = list(set(ssr + omit_reasons))
            else:
                enriched_chunk["qa_metadata"].pop("omit_reason", None)
                enriched_chunk["omit_flag"] = False

        # Batch generate embeddings for better performance
        print(f"🧠 Generating embeddings for {len(enriched_chunks)} chunks...")
        embedding_start = time.time()
        
        texts_for_embedding = [chunk["chunk_text"] for chunk in enriched_chunks]
        embeddings = compute_embeddings(texts_for_embedding)
        
        # Assign embeddings back to chunks
        for i, enriched_chunk in enumerate(enriched_chunks):
            enriched_chunk["embedding"] = embeddings[i]
        
        embedding_time = time.time() - embedding_start
        print(f"🧠 Embeddings complete: {len(enriched_chunks)} chunks in {embedding_time:.2f}s ({len(enriched_chunks)/embedding_time:.1f} chunks/s)")
            
        # Generate hashes for all chunks
        for i, enriched_chunk in enumerate(enriched_chunks):
            norm_text = enriched_chunk["chunk_text"]
            enriched_chunk["chunk_hash"] = hashlib.sha256(norm_text.encode("utf-8")).hexdigest()
            
            # Final omit logic based on retrieval score
            chunk_type = enriched_chunk.get("chunk_type", "markdown")
            retrieval_score = enriched_chunk.get("retrieval_metadata", {}).get("retrieval_score", 0) or 0.0
            
            # Safety check for None values
            if retrieval_score is None:
                retrieval_score = 0
                if "retrieval_metadata" not in enriched_chunk:
                    enriched_chunk["retrieval_metadata"] = {}
                enriched_chunk["retrieval_metadata"]["retrieval_score"] = 0
            
            if chunk_type == "excel":
                threshold = EXCEL_RETRIEVAL_THRESHOLD
            else:
                threshold = MARKDOWN_RETRIEVAL_THRESHOLD
            
            if retrieval_score < threshold:
                enriched_chunk["omit_flag"] = True
                enriched_chunk["show_skip_reasons"].append("low_retrieval_score")
            
            # Progress monitoring for final processing
            if (i + 1) % 100 == 0 or (i + 1) == len(enriched_chunks):
                elapsed = time.time() - final_processing_start
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                print(f"⚡ Final processing: {i + 1}/{len(enriched_chunks)} chunks ({rate:.1f} chunks/s)")
        
        # Final performance summary
        total_time = time.time() - start_time
        final_time = time.time() - final_processing_start
        print(f"🎉 Enrichment complete: {len(enriched_chunks)} chunks in {total_time:.2f}s")
        print(f"   - Pre-normalization: {pre_norm_time:.2f}s")
        print(f"   - NLP processing: {nlp_time:.2f}s ({len(enriched_chunks)/nlp_time:.1f} chunks/s)")
        print(f"   - Final processing: {final_time:.2f}s")
        print(f"   - Embedding generation: {embedding_time:.2f}s ({len(enriched_chunks)/embedding_time:.1f} chunks/s)")
        
        # 🔧 NEW: Integrated QA generation for immediate feedback
        if len(enriched_chunks) > 0:
            print(f"📊 Generating integrated QA metrics...")
            qa_start = time.time()
            
            try:
                from ..analysis.qa_utils import compute_metrics, analyze_semantic_types_histogram
                
                # Compute basic metrics
                metrics = compute_metrics(enriched_chunks)
                semantic_histogram = analyze_semantic_types_histogram(enriched_chunks)
                
                # Print key metrics to console
                print(f"📈 QA Summary:")
                print(f"   - Total chunks: {metrics['total_chunks']}")
                print(f"   - Usable chunks: {metrics['usable_chunks']} ({metrics['usable_chunks']/metrics['total_chunks']*100:.1f}%)")
                print(f"   - Omitted chunks: {metrics['omit_flag_count']}")
                print(f"   - Avg word count: {metrics['avg_chunk_length']:.1f}")
                print(f"   - Fact-like chunks: {metrics['fact_like_count']}")
                
                qa_time = time.time() - qa_start
                print(f"📊 QA generation: {qa_time:.2f}s")
            except Exception as e:
                logger.error(f"Error generating QA metrics: {str(e)}")
                print(f"⚠️ QA generation failed: {str(e)}")
        
        logger.info(f"Enrichment completed successfully: {len(enriched_chunks)} chunks processed")
        return enriched_chunks
        
    except Exception as e:
        logger.error(f"Critical error in batch_enrich_chunks: {str(e)}")
        print(f"❌ Enrichment failed: {str(e)}")
        # Return whatever chunks we managed to process
        return enriched_chunks if 'enriched_chunks' in locals() else [] 