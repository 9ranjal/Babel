#!/usr/bin/env python3
"""
Plugin-based runner for chunking pipeline.
Uses the plugin architecture to process files dynamically.
"""

import sys
import os
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from chunking.plugins import plugin_manager
from chunking.core.analysis.qa_utils import validate_chunks_batch, analyze_semantic_types_histogram
from chunking.core.utils.logging_utils import get_logger, log_error_with_context, log_processing_stats


def process_with_plugins(
    source_path: str,
    output_file: str,
    config: Optional[Dict[str, Any]] = None,
    validate: bool = False,
    limit: Optional[int] = None,
    strict: bool = False,
    logger = None
) -> List[Dict[str, Any]]:
    """
    Process files using the plugin architecture.
    
    Args:
        source_path: Path to source file or directory
        output_file: Path to output JSON file
        config: Configuration for processors
        validate: Whether to validate chunks
        limit: Limit number of files to process
        strict: Whether to stop on first error
        logger: Logger instance for structured logging
        
    Returns:
        List of processed chunks
    """
    if logger is None:
        logger = get_logger("plugin_runner")
    
    logger.info(f"🚀 Starting plugin-based processing...")
    logger.info(f"   Source: {source_path}")
    logger.info(f"   Output: {output_file}")
    logger.info(f"   Strict mode: {strict}")
    
    # List available processors
    processors = plugin_manager.list_processors()
    logger.info(f"📋 Available processors:")
    for proc in processors:
        logger.info(f"   - {proc['name']}: {proc['description']}")
    
    source_path_obj = Path(source_path)
    all_chunks = []
    
    if source_path_obj.is_file():
        # Process single file
        logger.info(f"📄 Processing single file: {source_path}")
        try:
            chunks = plugin_manager.process_file(source_path, config)
            all_chunks.extend(chunks)
            logger.info(f"✅ Generated {len(chunks)} chunks")
        except Exception as e:
            log_error_with_context(logger, e, "plugin processing", "single_file", source_path)
            if strict:
                logger.error(f"❌ Strict mode enabled - stopping on error")
                raise
            return []
    
    elif source_path_obj.is_dir():
        # Process directory
        logger.info(f"📁 Processing directory: {source_path}")
        
        # Get all files
        files = list(source_path_obj.rglob("*"))
        files = [f for f in files if f.is_file()]
        
        if limit:
            files = files[:limit]
            logger.info(f"   Limited to {limit} files")
        
        processed_files = 0
        failed_files = 0
        total_chunks = 0
        
        for file_path in files:
            try:
                chunks = plugin_manager.process_file(str(file_path), config)
                all_chunks.extend(chunks)
                processed_files += 1
                total_chunks += len(chunks)
                logger.info(f"✅ {file_path.name}: {len(chunks)} chunks")
            except Exception as e:
                failed_files += 1
                log_error_with_context(logger, e, "plugin processing", str(file_path.name), str(file_path))
                if strict:
                    logger.error(f"❌ Strict mode enabled - stopping on error at {file_path.name}")
                    raise
        
        # Log processing statistics
        log_processing_stats(logger, "Directory Processing", len(files), processed_files, failed_files, total_chunks)
        
        logger.info(f"📊 Directory processing complete:")
        logger.info(f"   Files processed: {processed_files}")
        logger.info(f"   Files failed: {failed_files}")
        logger.info(f"   Total chunks: {len(all_chunks)}")
    
    else:
        logger.error(f"❌ Invalid source path: {source_path}")
        return []
    
    # Validate chunks if requested
    if validate and all_chunks:
        logger.info(f"🔍 Validating chunks...")
        
        # Basic validation
        valid_chunks = 0
        invalid_chunks = []
        for i, chunk in enumerate(all_chunks):
            required_fields = ['chunk_id', 'chunk_text', 'chunk_word_count', 'topic', 'author']
            if all(chunk.get(field) for field in required_fields):
                valid_chunks += 1
            else:
                invalid_chunks.append(i)
        
        logger.info(f"✅ Valid chunks: {valid_chunks}/{len(all_chunks)}")
        if invalid_chunks:
            logger.warning(f"⚠️ Invalid chunks found at indices: {invalid_chunks[:10]}{'...' if len(invalid_chunks) > 10 else ''}")
        
        # Validation analysis
        validation_report = validate_chunks_batch(all_chunks)
        logger.info(f"📊 Validation report: {validation_report}")
        
        # Semantic type analysis
        semantic_report = analyze_semantic_types_histogram(all_chunks)
        logger.info(f"🏷️  Semantic types: {semantic_report}")
    
    # Save chunks
    if all_chunks:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(all_chunks, f, indent=2)
        
        logger.info(f"💾 Chunks saved to: {output_file}")
        
        # Save summary
        summary = {
            "total_chunks": len(all_chunks),
            "source_path": source_path,
            "output_file": output_file,
            "processors_used": [p['name'] for p in processors],
            "config": config
        }
        
        summary_file = output_file.replace('.json', '_summary.json')
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"📋 Summary saved to: {summary_file}")
    
    return all_chunks


def main():
    """Main entry point for the plugin runner."""
    parser = argparse.ArgumentParser(description="Plugin-based chunking pipeline")
    parser.add_argument("--source", required=True, help="Source file or directory")
    parser.add_argument("--out", required=True, help="Output JSON file")
    parser.add_argument("--config", help="Configuration JSON file")
    parser.add_argument("--validate", action="store_true", help="Validate chunks")
    parser.add_argument("--limit", type=int, help="Limit number of files to process")
    parser.add_argument("--strict", action="store_true", help="Stop on first error")
    
    args = parser.parse_args()
    
    # Load configuration
    config = None
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Process files
    chunks = process_with_plugins(
        source_path=args.source,
        output_file=args.out,
        config=config,
        validate=args.validate,
        limit=args.limit,
        strict=args.strict
    )
    
    if chunks:
        print(f"\n🎉 Processing complete! Generated {len(chunks)} chunks.")
    else:
        print(f"\n❌ No chunks generated.")
        sys.exit(1)


if __name__ == "__main__":
    main() 