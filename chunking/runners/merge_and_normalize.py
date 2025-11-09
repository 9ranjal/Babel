#!/usr/bin/env python3
"""
Enhanced merge and normalize runner for chunking pipeline.
Combines markdown and excel chunks, normalizes them, and generates final output.
"""

import json
import glob
import os
from datetime import datetime

from chunking.core.analysis.qa_utils import (
    load_chunks, compute_metrics, save_sample, save_flagged_json, 
    export_flagged_csv, save_metrics_json, save_summary_md,
    analyze_semantic_types_histogram, print_semantic_summary, save_semantic_analysis
)
from chunking.core.enrichment.metadata import build_chunk_id
from chunking.core.config import (
    QA_MASTER_DIR, TIMESTAMP_FORMAT, FINAL_OUTPUT_DIR
)
from chunking.core.utils.logging_utils import get_logger, log_processing_stats, log_qa_summary
from chunking.core.processing.text_cleaner import normalize_chunks_batch

# Create output directories
QA_MASTER_DIR.mkdir(parents=True, exist_ok=True)

def get_latest_chunk_file(input_dir: str) -> str:
    """
    Get the latest chunk file from a directory.
    
    Args:
        input_dir: Directory path to search for chunk files
        
    Returns:
        Path to the most recently created chunk file
        
    Raises:
        FileNotFoundError: If no chunk files are found in the directory
    """
    files = glob.glob(os.path.join(input_dir, "*_chunks_*.json"))
    if not files:
        raise FileNotFoundError(f"No chunk files found in {input_dir}")
    return max(files, key=os.path.getctime)

def safe_create_symlink(target_path: str, symlink_path: str, logger=None) -> bool:
    """
    Safely create a symlink with atomic operation to avoid race conditions.
    
    Args:
        target_path: Path to the target file
        symlink_path: Path where the symlink should be created
        logger: Logger instance for error reporting
        
    Returns:
        True if symlink was created successfully, False otherwise
    """
    if logger is None:
        logger = get_logger("merge_and_normalize")
    
    try:
        # Create a temporary symlink first
        temp_symlink = f"{symlink_path}.tmp"
        
        # Remove temp symlink if it exists
        if os.path.exists(temp_symlink):
            os.remove(temp_symlink)
        
        # Create new symlink
        os.symlink(os.path.abspath(target_path), temp_symlink)
        
        # Atomic rename
        if os.path.exists(symlink_path):
            os.remove(symlink_path)
        os.rename(temp_symlink, symlink_path)
        
        return True
    except (OSError, IOError) as e:
        logger.error(f"Error creating symlink {symlink_path}: {e}")
        # Clean up temp file if it exists
        if os.path.exists(temp_symlink):
            try:
                os.remove(temp_symlink)
            except (OSError, IOError) as cleanup_error:
                # Ignore cleanup errors - they're not critical
                pass
        return False

def generate_qa_artifacts(chunks: list, qa_dir: str, timestamp: str, logger=None) -> None:
    """
    Generate QA artifacts and semantic analysis for final chunks.
    
    Args:
        chunks: List of normalized chunks to analyze
        qa_dir: Directory to save QA artifacts
        timestamp: Timestamp for file naming
        logger: Logger instance for progress reporting
    """
    if logger is None:
        logger = get_logger("merge_and_normalize")
    
    # Compute QA metrics
    metrics = compute_metrics(chunks)
    
    # Compute semantic analysis
    semantic_histogram = analyze_semantic_types_histogram(chunks)
    
    # Log semantic summary
    logger.info("🎯 Semantic Analysis Summary:")
    print_semantic_summary(semantic_histogram)
    
    # Save metrics JSON
    metrics_path = os.path.join(qa_dir, f"final_chunk_metrics_{timestamp}.json")
    save_metrics_json(metrics, metrics_path, os.path.join(qa_dir, "metrics_history"))
    
    # Create symlink to latest metrics
    metrics_symlink = os.path.join(qa_dir, "chunk_metrics.json")
    if safe_create_symlink(os.path.abspath(metrics_path), metrics_symlink, logger):
        logger.info(f"🔗 Metrics symlink updated: {metrics_symlink} -> {metrics_path}")
    else:
        logger.warning(f"⚠️ Failed to create metrics symlink")
    
    # Save summary markdown
    save_summary_md(metrics, os.path.join(qa_dir, "final_chunk_summary.md"))
    
    # Save sample
    save_sample(chunks, os.path.join(qa_dir, "final_chunk_sample.json"))
    
    # Save flagged chunks
    save_flagged_json(chunks, os.path.join(qa_dir, "final_chunks_flagged.json"))
    
    # Export CSV for human review
    export_flagged_csv(chunks, os.path.join(qa_dir, "final_chunk_qc.csv"))
    
    # Save semantic analysis
    save_semantic_analysis(semantic_histogram, os.path.join(qa_dir, "final_semantic_analysis.json"))

def main() -> None:
    logger = get_logger("merge_and_normalize")
    
    # Load chunks from the latest files automatically
    markdown_dir = "data/chunks/markdown"
    excel_dir = "data/chunks/excel"
    
    try:
        markdown_file = get_latest_chunk_file(markdown_dir)
        excel_file = get_latest_chunk_file(excel_dir)
        
        logger.info(f"📁 Loading latest markdown chunks from: {markdown_file}")
        logger.info(f"📁 Loading latest excel chunks from: {excel_file}")
        
        markdown_chunks = load_chunks(markdown_file)
        excel_chunks = load_chunks(excel_file)
        all_chunks = markdown_chunks + excel_chunks
        
        logger.info(f"✅ Loaded {len(markdown_chunks)} markdown chunks and {len(excel_chunks)} excel chunks")
        
    except FileNotFoundError as e:
        logger.error(f"❌ Error: {e}")
        return

    # Normalize chunks using consolidated function
    logger.info(f"🔧 Normalizing {len(all_chunks)} chunks...")
    normalization_result = normalize_chunks_batch(all_chunks, preserve_original=False)
    normalized_chunks = normalization_result["chunks"]
    stats = normalization_result["stats"]
    
    logger.info(f"✅ Normalization complete: {stats['normalized_count']} processed, {stats['skipped_count']} skipped")
    if stats['error_count'] > 0:
        logger.warning(f"⚠️ {stats['error_count']} errors encountered")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_path = os.path.join(FINAL_OUTPUT_DIR, f"final_chunks_{timestamp}.json.gz")
    symlink_path = os.path.join(FINAL_OUTPUT_DIR, "final_chunks.json.gz")

    # Ensure final directory exists
    os.makedirs(FINAL_OUTPUT_DIR, exist_ok=True)

    # Save with compression and embedding optimization
    from chunking.core.utils.compression import save_compressed_chunks, create_embedding_summary
    
    save_compressed_chunks(normalized_chunks, output_path, optimize_embeddings=True)
    
    # Create embedding summary
    embedding_summary = create_embedding_summary(normalized_chunks)
    logger.info(f"📊 Embedding Summary:")
    logger.info(f"   - Total chunks: {embedding_summary['total_chunks']}")
    logger.info(f"   - Chunks with embeddings: {embedding_summary['chunks_with_embeddings']}")
    logger.info(f"   - Embedding coverage: {embedding_summary['embedding_coverage']:.1%}")
    logger.info(f"   - Total vector size: {embedding_summary['total_vector_size_mb']:.1f} MB")
    logger.info(f"   - Average vector size: {embedding_summary['average_vector_size_kb']:.1f} KB")

    if safe_create_symlink(os.path.abspath(output_path), symlink_path, logger):
        logger.info(f"✅ Generated {len(normalized_chunks)} final chunks into {output_path}")
        logger.info(f"🔗 Symlink updated: {symlink_path} -> {output_path}")
    else:
        logger.warning(f"⚠️ Failed to create final symlink")

    # Generate QA artifacts and semantic analysis
    generate_qa_artifacts(normalized_chunks, QA_MASTER_DIR, timestamp, logger)
    logger.info(f"📊 QA artifacts and semantic analysis saved to {QA_MASTER_DIR}/")

if __name__ == "__main__":
    main() 