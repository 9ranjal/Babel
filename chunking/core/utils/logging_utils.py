#!/usr/bin/env python3
"""
Logging utilities for the chunking module.
Provides consistent logging across all chunking components.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Set up logging configuration for chunking operations.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for logging
        console_output: Whether to output to console
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("chunking")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance for the specified name.
    
    Args:
        name: Logger name (defaults to 'chunking')
        
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"chunking.{name}")
    return logging.getLogger("chunking")

def log_processing_stats(
    logger: logging.Logger,
    operation: str,
    total_items: int,
    processed_items: int,
    failed_items: int = 0,
    skipped_items: int = 0
) -> None:
    """
    Log processing statistics in a consistent format.
    
    Args:
        logger: Logger instance
        operation: Name of the operation
        total_items: Total number of items
        processed_items: Number of successfully processed items
        failed_items: Number of failed items
        skipped_items: Number of skipped items
    """
    success_rate = (processed_items / total_items * 100) if total_items > 0 else 0
    
    logger.info(f"📊 {operation} Complete:")
    logger.info(f"   Total: {total_items}")
    logger.info(f"   Processed: {processed_items} ({success_rate:.1f}%)")
    if failed_items > 0:
        logger.warning(f"   Failed: {failed_items}")
    if skipped_items > 0:
        logger.info(f"   Skipped: {skipped_items}")

def log_error_with_context(
    logger: logging.Logger,
    error: Exception,
    context: str,
    chunk_id: str = None,
    file_path: str = None
) -> None:
    """
    Log errors with context information.
    
    Args:
        logger: Logger instance
        error: The exception that occurred
        context: Context where the error occurred
        chunk_id: Optional chunk ID for context
        file_path: Optional file path for context
    """
    context_info = []
    if chunk_id:
        context_info.append(f"chunk_id={chunk_id}")
    if file_path:
        context_info.append(f"file={file_path}")
    
    context_str = f" ({', '.join(context_info)})" if context_info else ""
    
    logger.error(f"❌ Error in {context}{context_str}: {str(error)}", exc_info=True)

def log_progress(
    logger: logging.Logger,
    current: int,
    total: int,
    operation: str,
    frequency: int = 100
) -> None:
    """
    Log progress updates at specified frequency.
    
    Args:
        logger: Logger instance
        current: Current item number
        total: Total number of items
        operation: Name of the operation
        frequency: How often to log (every N items)
    """
    if current % frequency == 0 or current == total:
        percentage = (current / total * 100) if total > 0 else 0
        logger.info(f"🔄 {operation}: {current}/{total} ({percentage:.1f}%)")

# Convenience functions for common operations
def log_file_processing(logger: logging.Logger, file_path: Path, chunks_count: int) -> None:
    """Log file processing results."""
    logger.info(f"✅ Processed {file_path.name}: {chunks_count} chunks")

def log_batch_processing(logger: logging.Logger, batch_num: int, batch_size: int, total_batches: int) -> None:
    """Log batch processing progress."""
    logger.info(f"📦 Batch {batch_num}/{total_batches}: {batch_size} items")

def log_qa_summary(logger: logging.Logger, metrics: dict) -> None:
    """Log QA summary statistics."""
    logger.info(f"📊 QA Summary:")
    logger.info(f"   Total chunks: {metrics.get('total_chunks', 0)}")
    logger.info(f"   Usable chunks: {metrics.get('usable_chunks', 0)}")
    logger.info(f"   Omitted chunks: {metrics.get('omit_flag_count', 0)}")
    logger.info(f"   Average word count: {metrics.get('avg_chunk_length', 0):.1f}") 