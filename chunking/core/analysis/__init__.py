"""
Semantic analysis, scoring, and quality assurance functions.
"""

from .semantics import (
    classify_semantic_type_hierarchical,
    get_primary_type,
    get_secondary_types,
    classify_upsc_domain,
    classify_cognitive_level,
    predict_question_types,
    detect_upsc_patterns
)
from .scoring import calculate_entity_density, calculate_retrieval_score, calculate_chunk_richness_score
from .qa_utils import (
    load_chunks,
    compute_metrics,
    save_sample,
    save_flagged_json,
    export_flagged_csv,
    save_metrics_json,
    save_summary_md,
    analyze_semantic_types_histogram,
    print_semantic_summary,
    save_semantic_analysis
)
from .utils import parse_markdown_sections, is_fact_like

__all__ = [
    # Semantic Analysis
    'classify_semantic_type_hierarchical',
    'get_primary_type',
    'get_secondary_types',
    'classify_upsc_domain',
    'classify_cognitive_level',
    'predict_question_types',
    'detect_upsc_patterns',
    
    # Scoring
    'calculate_entity_density',
    'calculate_retrieval_score',
    'calculate_chunk_richness_score',
    
    # QA Functions
    'load_chunks',
    'compute_metrics',
    'save_sample',
    'save_flagged_json',
    'export_flagged_csv',
    'save_metrics_json',
    'save_summary_md',
    'analyze_semantic_types_histogram',
    'print_semantic_summary',
    'save_semantic_analysis',
    
    # Utilities
    'parse_markdown_sections',
    'is_fact_like'
] 