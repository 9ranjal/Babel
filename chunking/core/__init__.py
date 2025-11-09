"""
Chunking Core Module - Main entry point for chunking functionality.
"""

# Core processing functions
from .processing import (
    chunk_sentences,
    apply_overlap,
    build_chunks,
    normalize_chunk_text,
    slugify
)

# Enrichment functions
from .enrichment.enhancer import (
    batch_enrich_chunks,
    batch_enrich_chunks_streaming,
    get_spacy_model
)
from .enrichment.metadata import (
    build_chunk_id,
    generate_concept_tags,
    map_ner_to_domain_tags,
    extract_metadata_from_filename
)
from .enrichment.excel_rewriter import rewrite_list_chunk

# Schema and validation functions
from .schema import (
    build_chunk_template,
    validate_chunk_schema,
    create_chunk_from_template,
    merge_chunk_updates,
    get_chunk_field_safe,
    ensure_chunk_completeness
)

# Analysis and QA functions
from .analysis import (
    load_chunks,
    compute_metrics,
    save_sample,
    save_flagged_json,
    parse_markdown_sections,
    classify_semantic_type_hierarchical,
    calculate_entity_density,
    calculate_retrieval_score
)

# Configuration
from .config import *

__all__ = [
    # Processing
    'chunk_sentences',
    'apply_overlap',
    'build_chunks',
    'normalize_chunk_text',
    'slugify',
    
    # Enrichment
    'batch_enrich_chunks',
    'batch_enrich_chunks_streaming',
    'get_spacy_model',
    'build_chunk_id',
    'generate_concept_tags',
    'map_ner_to_domain_tags',
    'extract_metadata_from_filename',
    'rewrite_list_chunk',
    
    # Schema and Validation
    'build_chunk_template',
    'validate_chunk_schema',
    'create_chunk_from_template',
    'merge_chunk_updates',
    'get_chunk_field_safe',
    'ensure_chunk_completeness',
    
    # Analysis and QA
    'classify_semantic_type_hierarchical',
    'calculate_entity_density',
    'calculate_retrieval_score',
    'load_chunks',
    'compute_metrics',
    'save_sample',
    'save_flagged_json',
    'parse_markdown_sections',
    
    # Configuration
    'FURNACE_INPUT_DIR',
    'EXCEL_INPUT_DIR',
    'MARKDOWN_OUTPUT_DIR',
    'EXCEL_OUTPUT_DIR',
    'MASTER_OUTPUT_DIR',
    'FINAL_OUTPUT_DIR',
    'QA_MARKDOWN_DIR',
    'QA_EXCEL_DIR',
    'QA_MASTER_DIR',
    'EMBEDDING_MODEL',
    'EMBEDDING_DIM',
    'SPACY_MODEL',
    'BATCH_SIZE',
    'N_PROCESS',
    'MARKDOWN_MAX_WORDS',
    'EXCEL_MAX_WORDS',
    'MERGE_MAX_WORDS',
    'MIN_RETRIEVAL_SCORE',
    'ENTITY_DENSITY_THRESHOLD'
]
