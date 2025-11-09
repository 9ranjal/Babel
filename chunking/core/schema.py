"""
Chunk schema and template definitions.
Provides a complete, safe chunk structure for all processing stages.
"""

from typing import Dict, Any, List, Optional
from .config import EMBEDDING_MODEL, EMBEDDING_DIM


def build_chunk_template() -> Dict[str, Any]:
    """
    Build a complete chunk template with all possible fields.
    This ensures consistent structure across all processing stages.
    
    Returns:
        Complete chunk template dictionary
    """
    return {
        # ─── Core Identification ───
        "chunk_id": None,
        "chunk_text": None,
        "chunk_word_count": None,
        "chunk_type": None,  # "markdown" or "excel"
        "chunk_hash": None,
        
        # ─── Source Metadata ───
        "source_metadata": {
            "topic": None,
            "author": None,
            "subtopic1": None,
            "subtopic2": None,
            "source_chunk": None,  # e.g., "filename.md#Section1"
            "source_id": None,
            "source_type": None,  # "markdown", "excel", etc.
            "section_heading": None,
            "document_title": None,
            "file_path": None,
            "row_index": None,  # For Excel chunks
            "sheet_name": None,  # For Excel chunks
            "chunk_index": None,  # Sequential index within document/section
        },
        
        # ─── Semantic Classification ───
        "semantic_type": {
            "primary": None,  # "statistical", "definition", "person", etc.
            "secondary": [],
            "domain": None,
            "cognitive_level": None,
            "question_type_affinity": []
        },
        
        # ─── Retrieval Metadata ───
        "retrieval_metadata": {
            "retrieval_score": None,  # 0.0-1.0 - RAG retrieval score
            "retrieval_keywords": [],
            "primary_entities": [],
            "concept_tags": [],
            "context_tags": [],  # e.g., ["cause", "example", "timeline"]
            "entity_density": 0.0,
            "reranker_score": None,
            "reranker_model": None,
        },
        
        # ─── Entity Information ───
        "entities": {
            # HIGH-VALUE ENTITIES (optimized for RAG)
            "person_entities": [],        # Essential for biographical queries
            "org_entities": [],              # Government, institutions 
            "gpe_entities": [],              # Countries, states, cities
            "date_entities": [],            # Historical events, timelines
            "money_entities": [],          # Economic data
            "percent_entities": [],      # Statistics, economic indicators
            "law_entities": [],              # Acts, constitutional articles
            "event_entities": [],          # Historical events, movements
            
            # METADATA
            "entity_counts": {},
            "entity_texts": {},
        },
        
        # ─── QA Metadata ───
        "qa_metadata": {
            "confidence_score": None,  # 0.0-1.0 - overall confidence
            "quality_score": None,  # 0.0-1.0 - composite quality score
            "chunk_quality": None,  # "high", "medium", "low"
            "is_context_dead": False,  # True if chunk is too short/uninformative
            "is_complete_sentence": None,
            "has_numeric_stat": None,
            "primary_entity": None,
            "omit_flag": False,
            "show_skip_reasons": [],
            "quality_flags": [],  # ["low_confidence", "fragment_detected", "no_entities"]
            "entities_expanded": [],  # List of "acronym → full_name"
            "processing_steps": [],  # ["pre_process", "entity_extraction", etc.]
            "original_length": 0,
            "processed_length": 0,
        },
        
        # ─── Excel-Specific Metadata ───
        "excel_metadata": {
            "row_data_completeness": None,  # 0.0-1.0
            "template_success": None,  # True/False
            "source_confidence": None,  # "high", "medium", "low"
            "source_confidence_score": None,  # 0.0-1.0
            "rewritten_flag": False,  # Flag for Excel chunks that were rewritten
            "is_fact_like": False,
        },
        
        # ─── Embedding Information ───
        "embedding": {
            "vector": None,  # Always list of floats
            "model": EMBEDDING_MODEL,
            "dimension": EMBEDDING_DIM,
            "norm": None,  # Optional normalization value
            "generated_at": None,
            "source": "core",  # 'core', 'factual', 'copilot', etc.
        },
        
        # ─── Processing Metadata ───
        "processing_metadata": {
            "timestamp": None,
            "version": "2.0",
            "normalized": False,
            "normalized_at": None,
            "last_enriched_at": None,
        },
        
        # ─── Review and Revision ───
        "review_metadata": {
            "reference_links": [],
            "prev_chunk_text": None,
            "next_chunk_text": None,
            "review_changes": [],
            "last_reviewed": "",
            "last_seen": "",
            "revision_bucket": "",
        },
    }


def create_chunk_from_template(**kwargs) -> Dict[str, Any]:
    """
    Create a new chunk from template with provided values.
    
    Args:
        **kwargs: Key-value pairs to set in the chunk
        
    Returns:
        New chunk dictionary
    """
    template = build_chunk_template()
    
    # Handle nested updates
    for key, value in kwargs.items():
        if key in template:
            # If it's a dictionary in the template, merge it
            if isinstance(template[key], dict) and isinstance(value, dict):
                template[key].update(value)
            else:
                # Direct assignment for non-dict values
                template[key] = value
        else:
            # Try to find nested location
            for section, section_data in template.items():
                if isinstance(section_data, dict) and key in section_data:
                    template[section][key] = value
                    break
            else:
                # If not found in any section, add to root (for backward compatibility)
                template[key] = value
    
    # Calculate quality_score if not provided but chunk_text is available
    if template["qa_metadata"]["quality_score"] is None and template["chunk_text"]:
        from chunking.core.processing.base_post_processor import BaseChunkPostProcessor
        
        # Create a temporary processor to calculate quality
        class TempProcessor(BaseChunkPostProcessor):
            def _get_glossary_map(self) -> dict:
                return {}
            def _get_entity_map(self) -> dict:
                return {}
        
        temp_processor = TempProcessor()
        quality_metrics = temp_processor._assess_quality(template["chunk_text"])
        template["qa_metadata"]["quality_score"] = quality_metrics.get("quality_score", 0.5)
        template["qa_metadata"]["chunk_quality"] = quality_metrics.get("chunk_quality", "medium")
        template["qa_metadata"]["quality_flags"] = quality_metrics.get("quality_flags", [])
    
    return template


def flatten_chunk_for_backward_compatibility(chunk: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flatten a chunk to legacy format for backward compatibility.
    
    Args:
        chunk: Chunk with nested structure
        
    Returns:
        Flattened chunk in legacy format
    """
    flattened = {}
    
    # Core fields
    for field in ["chunk_id", "chunk_text", "chunk_word_count", "chunk_type", "chunk_hash"]:
        if field in chunk:
            flattened[field] = chunk[field]
    
    # Source metadata
    if "source_metadata" in chunk:
        for key, value in chunk["source_metadata"].items():
            flattened[key] = value
    
    # Semantic type
    if "semantic_type" in chunk:
        flattened["semantic_type"] = chunk["semantic_type"]
    
    # Retrieval metadata
    if "retrieval_metadata" in chunk:
        for key, value in chunk["retrieval_metadata"].items():
            flattened[key] = value
    
    # Entities
    if "entities" in chunk:
        for key, value in chunk["entities"].items():
            flattened[key] = value
    
    # QA metadata
    if "qa_metadata" in chunk:
        for key, value in chunk["qa_metadata"].items():
            flattened[key] = value
    
    # Excel metadata
    if "excel_metadata" in chunk:
        for key, value in chunk["excel_metadata"].items():
            flattened[key] = value
    
    # Embedding
    if "embedding" in chunk:
        embedding_data = chunk["embedding"]
        flattened["embedding"] = embedding_data.get("vector")
        flattened["embedding_model"] = embedding_data.get("model")
        flattened["embedding_dim"] = embedding_data.get("dimension")
        flattened["embedding_generated_at"] = embedding_data.get("generated_at")
        flattened["embedding_source"] = embedding_data.get("source")
    
    # Processing metadata
    if "processing_metadata" in chunk:
        for key, value in chunk["processing_metadata"].items():
            if key == "timestamp":
                flattened["processing_timestamp"] = value
            else:
                flattened[key] = value
    
    # Review metadata
    if "review_metadata" in chunk:
        for key, value in chunk["review_metadata"].items():
            flattened[key] = value
    
    return flattened





def validate_chunk_schema(chunk: Dict[str, Any]) -> List[str]:
    """
    Validate a chunk schema.
    
    Args:
        chunk: Chunk dictionary to validate
        
    Returns:
        List of validation errors
    """
    errors = []
    
    # Required fields
    required_fields = ["chunk_id", "chunk_text", "chunk_word_count", "chunk_type"]
    for field in required_fields:
        if field not in chunk or chunk[field] is None:
            errors.append(f"Missing required field: {field}")
    
    # Required nested sections
    required_sections = ["source_metadata", "semantic_type", "retrieval_metadata", 
                        "entities", "qa_metadata", "excel_metadata", "embedding",
                        "processing_metadata", "review_metadata"]
    
    for section in required_sections:
        if section not in chunk:
            errors.append(f"Missing required section: {section}")
        elif not isinstance(chunk[section], dict):
            errors.append(f"Section {section} must be a dictionary")
    
    # Validate semantic_type structure
    if "semantic_type" in chunk and isinstance(chunk["semantic_type"], dict):
        if "primary" not in chunk["semantic_type"]:
            errors.append("semantic_type.primary is required")
    
    # Validate retrieval_metadata compactness (avoid large entity arrays duplication)
    if "retrieval_metadata" in chunk and isinstance(chunk["retrieval_metadata"], dict):
        rm = chunk["retrieval_metadata"]
        # Disallow entity_* arrays inside retrieval_metadata (should live under entities)
        forbidden_keys = [
            "person_entities", "org_entities", "gpe_entities", "date_entities",
            "money_entities", "percent_entities", "law_entities", "event_entities",
            "entity_texts"
        ]
        for fk in forbidden_keys:
            if fk in rm:
                errors.append(f"retrieval_metadata.{fk} is not allowed; use entities section")

    # Validate embedding
    if "embedding" in chunk and isinstance(chunk["embedding"], dict):
        if "vector" not in chunk["embedding"]:
            errors.append("embedding.vector is required")
    
    return errors


def get_chunk_field_safe(chunk: Dict[str, Any], field_path: str, default: Any = None) -> Any:
    """
    Safely get a nested field from a chunk.
    
    Args:
        chunk: Chunk dictionary
        field_path: Dot-separated field path (e.g., "source_metadata.topic")
        default: Default value if field not found
        
    Returns:
        Field value or default
    """
    if "." not in field_path:
        return chunk.get(field_path, default)
    
    parts = field_path.split(".")
    current = chunk
    
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    
    return current


def update_chunk_field(chunk: Dict[str, Any], field_path: str, value: Any) -> Dict[str, Any]:
    """
    Safely update a nested field in a chunk.
    
    Args:
        chunk: Chunk dictionary
        field_path: Dot-separated field path (e.g., "qa_metadata.confidence_score")
        value: Value to set
        
    Returns:
        Updated chunk dictionary
    """
    if "." not in field_path:
        chunk[field_path] = value
        return chunk
    
    parts = field_path.split(".")
    current = chunk
    
    # Navigate to the parent of the target field
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]
    
    # Set the final field
    current[parts[-1]] = value
    return chunk


def merge_chunk_updates(base_chunk: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge updates into a base chunk.
    
    Args:
        base_chunk: Base chunk dictionary
        updates: Updates to apply
        
    Returns:
        Updated chunk dictionary
    """
    result = base_chunk.copy()
    
    for key, value in updates.items():
        if key in result:
            if isinstance(result[key], dict) and isinstance(value, dict):
                result[key].update(value)
            else:
                result[key] = value
        else:
            result[key] = value
    
    return result


def ensure_chunk_completeness(chunk: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure a chunk has all required fields with default values.
    
    Args:
        chunk: Chunk dictionary
        
    Returns:
        Complete chunk dictionary
    """
    template = build_chunk_template()
    
    # Merge template defaults with chunk
    for key, default_value in template.items():
        if key not in chunk or chunk[key] is None:
            chunk[key] = default_value
    
    return chunk
