"""
Utilities for handling embeddings in different storage formats.
"""

import json
import numpy as np
from typing import Dict, Any, List, Union
from datetime import datetime


def prepare_chunk_for_supabase(chunk: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare a chunk for Supabase storage by converting embedding format.
    
    Args:
        chunk: Chunk with nested embedding structure
        
    Returns:
        Chunk with Supabase-compatible embedding format
    """
    supabase_chunk = chunk.copy()
    
    # Handle embedding conversion
    if "embedding" in chunk and chunk["embedding"]:
        embedding_data = chunk["embedding"]
        
        if isinstance(embedding_data, dict):
            # Extract vector from nested structure
            vector = embedding_data.get("vector")
            if vector:
                supabase_chunk["embedding"] = vector
                supabase_chunk["embedding_model"] = embedding_data.get("model")
                supabase_chunk["embedding_dim"] = embedding_data.get("dimension")
                supabase_chunk["embedding_generated_at"] = embedding_data.get("generated_at")
                supabase_chunk["embedding_source"] = embedding_data.get("source")
        elif isinstance(embedding_data, list):
            # Already in vector format
            supabase_chunk["embedding"] = embedding_data
        elif isinstance(embedding_data, str):
            # String format - parse JSON
            try:
                parsed = json.loads(embedding_data)
                if isinstance(parsed, dict):
                    supabase_chunk["embedding"] = parsed.get("vector")
                    supabase_chunk["embedding_model"] = parsed.get("model")
                    supabase_chunk["embedding_dim"] = parsed.get("dimension")
                else:
                    supabase_chunk["embedding"] = parsed
            except json.JSONDecodeError:
                # Invalid JSON - set to None
                supabase_chunk["embedding"] = None
    
    return supabase_chunk


def prepare_chunk_for_json(chunk: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare a chunk for JSON storage with nested embedding structure.
    
    Args:
        chunk: Chunk with flat embedding fields
        
    Returns:
        Chunk with nested embedding structure
    """
    json_chunk = chunk.copy()
    
    # Create nested embedding structure
    embedding_data = {
        "vector": chunk.get("embedding"),
        "model": chunk.get("embedding_model", "bge-large-en-v1.5"),
        "dimension": chunk.get("embedding_dim", 1024),
        "generated_at": chunk.get("embedding_generated_at"),
        "source": chunk.get("embedding_source", "core")
    }
    
    json_chunk["embedding"] = embedding_data
    
    # Remove flat embedding fields
    for field in ["embedding_model", "embedding_dim", "embedding_generated_at", "embedding_source"]:
        json_chunk.pop(field, None)
    
    return json_chunk


def validate_embedding_format(embedding: Union[List[float], str, Dict[str, Any]], 
                            expected_dim: int = 1024) -> bool:
    """
    Validate embedding format and dimensions.
    
    Args:
        embedding: Embedding in any format
        expected_dim: Expected dimension
        
    Returns:
        True if valid, False otherwise
    """
    try:
        if isinstance(embedding, list):
            return len(embedding) == expected_dim
        elif isinstance(embedding, str):
            parsed = json.loads(embedding)
            if isinstance(parsed, dict):
                vector = parsed.get("vector")
                return vector and len(vector) == expected_dim
            else:
                return len(parsed) == expected_dim
        elif isinstance(embedding, dict):
            vector = embedding.get("vector")
            return vector and len(vector) == expected_dim
        else:
            return False
    except (json.JSONDecodeError, TypeError, AttributeError):
        return False


def get_embedding_vector(embedding: Union[List[float], str, Dict[str, Any]]) -> List[float]:
    """
    Extract embedding vector from any format.
    
    Args:
        embedding: Embedding in any format
        
    Returns:
        List of floats representing the embedding vector
    """
    try:
        if isinstance(embedding, list):
            return embedding
        elif isinstance(embedding, str):
            parsed = json.loads(embedding)
            if isinstance(parsed, dict):
                return parsed.get("vector", [])
            else:
                return parsed
        elif isinstance(embedding, dict):
            return embedding.get("vector", [])
        else:
            return []
    except (json.JSONDecodeError, TypeError, AttributeError):
        return []


def create_embedding_metadata(vector: List[float], 
                            model: str = "bge-large-en-v1.5",
                            source: str = "core") -> Dict[str, Any]:
    """
    Create embedding metadata structure.
    
    Args:
        vector: Embedding vector
        model: Model name
        source: Source identifier
        
    Returns:
        Embedding metadata dictionary
    """
    return {
        "vector": vector,
        "model": model,
        "dimension": len(vector),
        "generated_at": datetime.now().isoformat(),
        "source": source
    }
