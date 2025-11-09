"""
Compression utilities for chunk storage and embedding optimization.
"""

import gzip
import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Union
from datetime import datetime

from chunking.core.config import (
    COMPRESS_JSON_FILES, 
    EMBEDDING_COMPRESSION_LEVEL,
    SAVE_VECTORS_IN_JSON,
    VALIDATE_EMBEDDINGS
)


def save_compressed_chunks(chunks: List[Dict[str, Any]], filepath: Path, 
                          optimize_embeddings: bool = True) -> None:
    """
    Save chunks with gzip compression and optional embedding optimization.
    
    Args:
        chunks: List of chunk dictionaries
        filepath: Output file path
        optimize_embeddings: Whether to optimize embedding storage
    """
    processed_chunks = chunks.copy()
    
    if optimize_embeddings and not SAVE_VECTORS_IN_JSON:
        # Remove embedding vectors to reduce file size
        for chunk in processed_chunks:
            if "embedding" in chunk and isinstance(chunk["embedding"], dict):
                # Keep metadata but remove vector
                embedding_meta = chunk["embedding"].copy()
                embedding_meta.pop("vector", None)
                chunk["embedding"] = embedding_meta
    
    if COMPRESS_JSON_FILES:
        # Save with gzip compression
        with gzip.open(filepath, 'wt', encoding='utf-8', 
                      compresslevel=EMBEDDING_COMPRESSION_LEVEL) as f:
            json.dump(processed_chunks, f, separators=(',', ':'), indent=None)
    else:
        # Save uncompressed
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(processed_chunks, f, separators=(',', ':'), indent=2)


def load_compressed_chunks(filepath: Path) -> List[Dict[str, Any]]:
    """
    Load chunks from compressed or uncompressed JSON file.
    
    Args:
        filepath: Input file path
        
    Returns:
        List of chunk dictionaries
    """
    if filepath.suffix == '.gz' or COMPRESS_JSON_FILES:
        # Load from gzip compressed file
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Load from uncompressed file
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)


def save_embeddings_separately(chunks: List[Dict[str, Any]], 
                              embeddings_file: Path,
                              metadata_file: Path) -> None:
    """
    Save embeddings separately from chunks for large datasets.
    
    Args:
        chunks: List of chunk dictionaries
        embeddings_file: Path for .npy file with vectors
        metadata_file: Path for JSON file with embedding metadata
    """
    # Extract vectors and metadata
    vectors = []
    metadata = []
    
    for chunk in chunks:
        if "embedding" in chunk and isinstance(chunk["embedding"], dict):
            embedding_data = chunk["embedding"]
            vector = embedding_data.get("vector")
            
            if vector and isinstance(vector, list):
                vectors.append(vector)
                metadata.append({
                    "chunk_id": chunk.get("chunk_id"),
                    "model": embedding_data.get("model"),
                    "dimension": embedding_data.get("dimension"),
                    "generated_at": embedding_data.get("generated_at"),
                    "source": embedding_data.get("source")
                })
    
    # Save vectors as numpy array
    if vectors:
        np.save(embeddings_file, np.array(vectors))
        
        # Save metadata
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)


def load_embeddings_separately(embeddings_file: Path, 
                              metadata_file: Path) -> tuple:
    """
    Load embeddings from separate files.
    
    Returns:
        Tuple of (vectors, metadata)
    """
    vectors = np.load(embeddings_file)
    
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    return vectors, metadata


def get_file_size_mb(filepath: Path) -> float:
    """Get file size in MB."""
    return filepath.stat().st_size / (1024 * 1024)


def estimate_compression_ratio(original_size_mb: float, 
                             compressed_size_mb: float) -> float:
    """Calculate compression ratio (0.0 = no compression, 1.0 = 100% compression)."""
    return 1.0 - (compressed_size_mb / original_size_mb)


def validate_chunk_embeddings(chunks: List[Dict[str, Any]], 
                             expected_dim: int = 1024) -> Dict[str, Any]:
    """
    Validate embedding format and dimensions across all chunks.
    
    Args:
        chunks: List of chunk dictionaries
        expected_dim: Expected embedding dimension
        
    Returns:
        Validation results dictionary
    """
    if not VALIDATE_EMBEDDINGS:
        return {"valid": True, "total": len(chunks), "valid_count": len(chunks)}
    
    valid_count = 0
    invalid_chunks = []
    
    for chunk in chunks:
        if "embedding" not in chunk:
            invalid_chunks.append({
                "chunk_id": chunk.get("chunk_id"),
                "error": "Missing embedding field"
            })
            continue
            
        embedding = chunk["embedding"]
        
        if isinstance(embedding, dict):
            vector = embedding.get("vector")
            if not vector:
                invalid_chunks.append({
                    "chunk_id": chunk.get("chunk_id"),
                    "error": "Missing vector in embedding dict"
                })
                continue
                
            if not isinstance(vector, list):
                invalid_chunks.append({
                    "chunk_id": chunk.get("chunk_id"),
                    "error": f"Vector is not a list: {type(vector)}"
                })
                continue
                
            if len(vector) != expected_dim:
                invalid_chunks.append({
                    "chunk_id": chunk.get("chunk_id"),
                    "error": f"Wrong dimension: {len(vector)} != {expected_dim}"
                })
                continue
                
        elif isinstance(embedding, list):
            if len(embedding) != expected_dim:
                invalid_chunks.append({
                    "chunk_id": chunk.get("chunk_id"),
                    "error": f"Wrong dimension: {len(embedding)} != {expected_dim}"
                })
                continue
        else:
            invalid_chunks.append({
                "chunk_id": chunk.get("chunk_id"),
                "error": f"Invalid embedding type: {type(embedding)}"
            })
            continue
            
        valid_count += 1
    
    return {
        "valid": valid_count == len(chunks),
        "total": len(chunks),
        "valid_count": valid_count,
        "invalid_count": len(invalid_chunks),
        "invalid_chunks": invalid_chunks
    }


def create_embedding_summary(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create a summary of embedding statistics.
    
    Args:
        chunks: List of chunk dictionaries
        
    Returns:
        Summary dictionary
    """
    total_chunks = len(chunks)
    chunks_with_embeddings = 0
    embedding_models = {}
    embedding_sources = {}
    total_vector_size = 0
    
    for chunk in chunks:
        if "embedding" in chunk and chunk["embedding"]:
            chunks_with_embeddings += 1
            
            embedding = chunk["embedding"]
            if isinstance(embedding, dict):
                model = embedding.get("model", "unknown")
                source = embedding.get("source", "unknown")
                vector = embedding.get("vector", [])
                
                embedding_models[model] = embedding_models.get(model, 0) + 1
                embedding_sources[source] = embedding_sources.get(source, 0) + 1
                
                if isinstance(vector, list):
                    total_vector_size += len(vector) * 4  # 4 bytes per float
            elif isinstance(embedding, list):
                total_vector_size += len(embedding) * 4
    
    return {
        "total_chunks": total_chunks,
        "chunks_with_embeddings": chunks_with_embeddings,
        "embedding_coverage": chunks_with_embeddings / total_chunks if total_chunks > 0 else 0,
        "embedding_models": embedding_models,
        "embedding_sources": embedding_sources,
        "total_vector_size_mb": total_vector_size / (1024 * 1024),
        "average_vector_size_kb": (total_vector_size / chunks_with_embeddings) / 1024 if chunks_with_embeddings > 0 else 0
    }
