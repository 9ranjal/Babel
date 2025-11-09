"""
QA Summary Generator for chunk quality metrics.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

from chunking.core.utils.logging_utils import get_logger

logger = get_logger("qa_summary")

def generate_qa_summary(chunks: List[Dict[str, Any]], output_dir: str, batch_name: str = None) -> Dict[str, Any]:
    """
    Generate comprehensive QA summary for a batch of chunks.
    
    Args:
        chunks: List of processed chunks
        output_dir: Directory to save summary
        batch_name: Optional batch identifier
        
    Returns:
        Summary dictionary
    """
    if not chunks:
        return _create_empty_summary()
    
    # Calculate quality distribution
    quality_distribution = _calculate_quality_distribution(chunks)
    
    # Calculate flag counts
    flag_counts = _calculate_flag_counts(chunks)
    
    # Calculate semantic type distribution
    semantic_distribution = _calculate_semantic_distribution(chunks)
    
    # Calculate entity statistics
    entity_stats = _calculate_entity_statistics(chunks)
    
    # Calculate academic signals (for markdown)
    academic_stats = _calculate_academic_statistics(chunks)
    
    # Create summary
    summary = {
        "batch_info": {
            "batch_name": batch_name or "unknown",
            "total_chunks": len(chunks),
            "generated_at": datetime.now().isoformat(),
            "chunk_types": _get_chunk_type_distribution(chunks)
        },
        "quality_distribution": quality_distribution,
        "flag_counts": flag_counts,
        "semantic_distribution": semantic_distribution,
        "entity_statistics": entity_stats,
        "academic_statistics": academic_stats,
        "processing_metadata": {
            "avg_word_count": _calculate_avg_word_count(chunks),
            "avg_quality_score": _calculate_avg_quality_score(chunks),
            "chunks_with_embeddings": _count_chunks_with_embeddings(chunks),
            "compression_ratio": _estimate_compression_ratio(chunks)
        }
    }
    
    # Save summary to file
    _save_qa_summary(summary, output_dir, batch_name)
    
    return summary

def _create_empty_summary() -> Dict[str, Any]:
    """Create empty summary structure."""
    return {
        "batch_info": {
            "batch_name": "empty",
            "total_chunks": 0,
            "generated_at": datetime.now().isoformat(),
            "chunk_types": {}
        },
        "quality_distribution": {
            "high_quality": 0,
            "medium_quality": 0,
            "low_quality": 0
        },
        "flag_counts": {},
        "semantic_distribution": {},
        "entity_statistics": {},
        "academic_statistics": {},
        "processing_metadata": {
            "avg_word_count": 0,
            "avg_quality_score": 0,
            "chunks_with_embeddings": 0,
            "compression_ratio": 0
        }
    }

def _calculate_quality_distribution(chunks: List[Dict[str, Any]]) -> Dict[str, int]:
    """Calculate quality distribution."""
    distribution = {"high_quality": 0, "medium_quality": 0, "low_quality": 0}
    
    for chunk in chunks:
        quality = chunk.get("qa_metadata", {}).get("chunk_quality", "medium")
        if quality in distribution:
            distribution[quality] += 1
    
    return distribution

def _calculate_flag_counts(chunks: List[Dict[str, Any]]) -> Dict[str, int]:
    """Calculate flag counts."""
    flag_counts = {}
    
    for chunk in chunks:
        flags = chunk.get("qa_metadata", {}).get("quality_flags", [])
        for flag in flags:
            flag_counts[flag] = flag_counts.get(flag, 0) + 1
    
    return flag_counts

def _calculate_semantic_distribution(chunks: List[Dict[str, Any]]) -> Dict[str, int]:
    """Calculate semantic type distribution."""
    semantic_counts = {}
    
    for chunk in chunks:
        primary = chunk.get("semantic_type", {}).get("primary", "unknown")
        semantic_counts[primary] = semantic_counts.get(primary, 0) + 1
    
    return semantic_counts

def _calculate_entity_statistics(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate entity statistics."""
    total_entities = 0
    chunks_with_entities = 0
    entity_type_counts = {}
    
    for chunk in chunks:
        entities = chunk.get("entities", {})
        chunk_entity_count = 0
        
        for entity_type, entity_list in entities.items():
            if isinstance(entity_list, list):
                count = len(entity_list)
                chunk_entity_count += count
                entity_type_counts[entity_type] = entity_type_counts.get(entity_type, 0) + count
        
        if chunk_entity_count > 0:
            chunks_with_entities += 1
        total_entities += chunk_entity_count
    
    return {
        "total_entities": total_entities,
        "chunks_with_entities": chunks_with_entities,
        "avg_entities_per_chunk": total_entities / len(chunks) if chunks else 0,
        "entity_type_distribution": entity_type_counts
    }

def _calculate_academic_statistics(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate academic statistics for markdown chunks."""
    academic_scores = []
    citation_densities = []
    chunks_with_citations = 0
    
    for chunk in chunks:
        if chunk.get("chunk_type") == "markdown":
            qa_metadata = chunk.get("qa_metadata", {})
            
            academic_score = qa_metadata.get("academic_score", 0)
            citation_density = qa_metadata.get("citation_density", 0)
            has_citation = qa_metadata.get("has_citation", False)
            
            if academic_score > 0:
                academic_scores.append(academic_score)
            if citation_density > 0:
                citation_densities.append(citation_density)
            if has_citation:
                chunks_with_citations += 1
    
    return {
        "avg_academic_score": sum(academic_scores) / len(academic_scores) if academic_scores else 0,
        "avg_citation_density": sum(citation_densities) / len(citation_densities) if citation_densities else 0,
        "chunks_with_citations": chunks_with_citations,
        "markdown_chunks": len([c for c in chunks if c.get("chunk_type") == "markdown"])
    }

def _get_chunk_type_distribution(chunks: List[Dict[str, Any]]) -> Dict[str, int]:
    """Get chunk type distribution."""
    type_counts = {}
    
    for chunk in chunks:
        chunk_type = chunk.get("chunk_type", "unknown")
        type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1
    
    return type_counts

def _calculate_avg_word_count(chunks: List[Dict[str, Any]]) -> float:
    """Calculate average word count."""
    total_words = sum(chunk.get("chunk_word_count", 0) for chunk in chunks)
    return total_words / len(chunks) if chunks else 0

def _calculate_avg_quality_score(chunks: List[Dict[str, Any]]) -> float:
    """Calculate average quality score."""
    scores = [chunk.get("qa_metadata", {}).get("quality_score", 0) for chunk in chunks]
    valid_scores = [s for s in scores if s is not None]
    return sum(valid_scores) / len(valid_scores) if valid_scores else 0

def _count_chunks_with_embeddings(chunks: List[Dict[str, Any]]) -> int:
    """Count chunks with embeddings."""
    return sum(1 for chunk in chunks if chunk.get("embedding", {}).get("vector"))

def _estimate_compression_ratio(chunks: List[Dict[str, Any]]) -> float:
    """Estimate compression ratio."""
    # Simple estimation based on embedding presence
    chunks_with_vectors = _count_chunks_with_embeddings(chunks)
    total_chunks = len(chunks)
    
    if total_chunks == 0:
        return 0.0
    
    # Assume vectors take up significant space
    return 1.0 - (chunks_with_vectors / total_chunks)

def _save_qa_summary(summary: Dict[str, Any], output_dir: str, batch_name: str = None) -> None:
    """Save QA summary to file."""
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"quality_metrics_summary_{batch_name or 'batch'}_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Create symlink to latest
    symlink_path = os.path.join(output_dir, "quality_metrics_summary.json")
    if os.path.exists(symlink_path):
        os.remove(symlink_path)
    os.symlink(filepath, symlink_path)
    
    logger.info(f"💾 QA Summary saved: {filepath}")
    logger.info(f"📊 Quality Distribution: {summary['quality_distribution']}")
    logger.info(f"🚩 Top Flags: {dict(sorted(summary['flag_counts'].items(), key=lambda x: x[1], reverse=True)[:3])}")

def print_qa_summary(summary: Dict[str, Any]) -> None:
    """Print formatted QA summary."""
    print("\n📊 QA Summary Report")
    print("=" * 50)
    
    batch_info = summary["batch_info"]
    print(f"📦 Batch: {batch_info['batch_name']}")
    print(f"📄 Total Chunks: {batch_info['total_chunks']}")
    print(f"🕒 Generated: {batch_info['generated_at']}")
    
    quality_dist = summary["quality_distribution"]
    print(f"\n🎯 Quality Distribution:")
    print(f"   High Quality: {quality_dist['high_quality']}")
    print(f"   Medium Quality: {quality_dist['medium_quality']}")
    print(f"   Low Quality: {quality_dist['low_quality']}")
    
    flag_counts = summary["flag_counts"]
    if flag_counts:
        print(f"\n🚩 Top Quality Flags:")
        for flag, count in sorted(flag_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {flag}: {count}")
    
    semantic_dist = summary["semantic_distribution"]
    if semantic_dist:
        print(f"\n🎯 Top Semantic Types:")
        for sem_type, count in sorted(semantic_dist.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {sem_type}: {count}")
    
    entity_stats = summary["entity_statistics"]
    print(f"\n🏷️ Entity Statistics:")
    print(f"   Total Entities: {entity_stats['total_entities']}")
    print(f"   Chunks with Entities: {entity_stats['chunks_with_entities']}")
    print(f"   Avg Entities per Chunk: {entity_stats['avg_entities_per_chunk']:.1f}")
    
    academic_stats = summary["academic_statistics"]
    print(f"\n📚 Academic Statistics:")
    print(f"   Avg Academic Score: {academic_stats['avg_academic_score']:.3f}")
    print(f"   Avg Citation Density: {academic_stats['avg_citation_density']:.3f}")
    print(f"   Chunks with Citations: {academic_stats['chunks_with_citations']}")
    print(f"   Markdown Chunks: {academic_stats['markdown_chunks']}")
    
    processing_meta = summary["processing_metadata"]
    print(f"\n⚙️ Processing Metadata:")
    print(f"   Avg Word Count: {processing_meta['avg_word_count']:.1f}")
    print(f"   Avg Quality Score: {processing_meta['avg_quality_score']:.3f}")
    print(f"   Chunks with Embeddings: {processing_meta['chunks_with_embeddings']}")
    print(f"   Compression Ratio: {processing_meta['compression_ratio']:.1%}")
    
    print("\n" + "=" * 50)

