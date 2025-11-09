# chunking/markdown_runner.py
# Markdown chunking orchestration logic

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from rich.console import Console
from rich.progress import track
from chunking.core.utils.logging_utils import get_logger, log_error_with_context

from chunking.core.config import (
    FURNACE_INPUT_DIR, MARKDOWN_OUTPUT_DIR, QA_MARKDOWN_DIR,
    CHUNK_FILE_PATTERN, TIMESTAMP_FORMAT, SAMPLE_SIZE, CSV_EXPORT_LIMIT
)
from chunking.core.schema import create_chunk_from_template
from chunking.core.processing.chunker import chunk_sentences, apply_overlap, build_chunks
from chunking.core.enrichment.metadata import build_chunk_id, generate_concept_tags, map_ner_to_domain_tags, extract_author_from_filename, extract_metadata_from_filename
from chunking.core.enrichment.enhancer import batch_enrich_chunks, get_spacy_model
from chunking.core.analysis.utils import parse_markdown_sections

# 🔧 FIX: Use better spaCy model for improved NER detection
SPACY_MODEL = os.getenv("SPACY_MODEL", "en_core_web_trf")
nlp = get_spacy_model(SPACY_MODEL)

# 🔧 FIX: Configurable input directory
# FURNACE_INPUT_DIR = os.getenv("FURNACE_INPUT_DIR", "/Users/pranjalsingh/Desktop/alchemy-bot (feeder data) /furnace")
# OUTPUT_DIR = "data/chunks/markdown"
# QA_DIR = "data/qa/base"
# os.makedirs(OUTPUT_DIR, exist_ok=True)
# os.makedirs(QA_DIR, exist_ok=True)
# os.makedirs("data/chunks", exist_ok=True)  # Ensure parent directory exists for symlink

# timestamp = datetime.now().strftime("%Y%m%d_%H%M")
# output_path = os.path.join(OUTPUT_DIR, f"notes_chunks_{timestamp}.json")
# latest_symlink = os.path.join(OUTPUT_DIR, "notes_chunks.json")

console = Console()
logger = get_logger("markdown_runner")

# Output paths
output_path = MARKDOWN_OUTPUT_DIR / f"notes_chunks_{datetime.now().strftime(TIMESTAMP_FORMAT)}.json"
latest_symlink = MARKDOWN_OUTPUT_DIR / "notes_chunks.json"
CHECKPOINT_FILE = MARKDOWN_OUTPUT_DIR / "tmp_checkpoint.json"

# Create output directories
MARKDOWN_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
QA_MARKDOWN_DIR.mkdir(parents=True, exist_ok=True)

all_chunks: List[Dict] = []

def save_checkpoint(data: list, path: str) -> None:
    """Save checkpoint data to JSON file."""
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def load_checkpoint(path: str) -> list:
    """Load checkpoint data from JSON file."""
    with open(path, "r") as f:
        return json.load(f)

def find_markdown_files(input_dir: str) -> List[Path]:
    """Find all markdown files in the input directory and subdirectories."""
    return list(Path(input_dir).rglob("*.md"))

def extract_metadata_from_path(md_path: Path) -> Dict[str, str]:
    """Extract metadata from markdown file path."""
    # Use consolidated metadata extraction
    metadata_info = extract_metadata_from_filename(str(md_path), file_type="markdown")
    return metadata_info

def process_markdown_file(md_path: Path) -> List[Dict]:
    """Process a single markdown file into chunks."""
    chunks = []
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract metadata
        metadata_base = extract_metadata_from_path(md_path)
        
        # Parse markdown sections
        sections = parse_markdown_sections(content.split('\n'))
        
        # Load spaCy model
        nlp = get_spacy_model()
        
        all_section_chunks = []
        for section_idx, (section_title, section_content) in enumerate(sections):
            if not section_content.strip():
                continue
            
            # Extract section heading and document title
            section_heading = section_title.strip()
            document_title = metadata_base.get("topic", "Unknown")
            
            # Process sentences
            sentences = chunk_sentences(section_content, nlp)
            if not sentences:
                continue
            windows = apply_overlap(sentences, chunk_size=100, overlap=0.3)
            section_stack = [section_title] + [metadata_base["subtopic1"], metadata_base["subtopic2"], metadata_base["subtopic3"], metadata_base["subtopic4"]]
            source_id = build_chunk_id(metadata_base["topic"], metadata_base["author"], section_stack, section_idx)
            
            # Create metadata dictionary for build_chunks
            metadata = {
                **metadata_base,
                "source_chunk": f"{md_path}#{section_title}",
                "source_id": source_id,
                "concept_tags": [],
                "review_changes": [],
                "chunk_type": "markdown",
                "source_type": "markdown",
                "last_reviewed": "",
                "last_seen": "",
                "revision_bucket": "",
                "section_heading": section_heading,
                "document_title": document_title,
                "file_path": str(md_path)
            }
            
            # Build chunks for this section
            section_chunks = build_chunks(windows, metadata, nlp=nlp)
            
            # Apply post-processing to each chunk
            from chunking.core.processing.markdown_post_processor import process_markdown_text
            from chunking.core.schema import update_chunk_field
            
            processed_chunks = []
            for chunk in section_chunks:
                # Process through Markdown post-processor
                processed_text, post_metadata = process_markdown_text(
                    chunk["chunk_text"], 
                    chunk, 
                    {"file_path": str(md_path)}
                )
                
                # Skip context-dead chunks
                if post_metadata.get("qa_metadata", {}).get("is_context_dead", False):
                    logger.debug(f"Skipping context-dead chunk: {processed_text[:50]}...")
                    continue
                
                # Update existing chunk instead of creating new one to preserve metadata
                from chunking.core.schema import update_chunk_field
                
                # Update the text and word count in the existing chunk
                new_chunk = update_chunk_field(chunk, "chunk_text", processed_text)
                new_chunk = update_chunk_field(new_chunk, "chunk_word_count", len(processed_text.split()))
                
                # Merge post-processing metadata (do not overwrite source metadata; skip None values)
                for section, section_data in post_metadata.items():
                    if section == "source_metadata":
                        continue
                    if isinstance(section_data, dict):
                        for key, value in section_data.items():
                            if value is None:
                                continue
                            new_chunk = update_chunk_field(new_chunk, f"{section}.{key}", value)
                
                processed_chunks.append(new_chunk)
            
            all_section_chunks.append(processed_chunks)
        
        # Flatten and add prev/next context
        flat_chunks = [chunk for section in all_section_chunks for chunk in section]
        for i, chunk in enumerate(flat_chunks):
            chunk["prev_chunk_text"] = flat_chunks[i-1]["chunk_text"] if i > 0 else ""
            chunk["next_chunk_text"] = flat_chunks[i+1]["chunk_text"] if i < len(flat_chunks)-1 else ""

        # Enrich chunks in-batch before returning (integration tests expect enriched output)
        if flat_chunks:
            from chunking.core.enrichment.enhancer import batch_enrich_chunks
            flat_chunks = batch_enrich_chunks(flat_chunks)

        # Add chunks to the collection
        chunks.extend(flat_chunks)
    except Exception as e:
        log_error_with_context(logger, e, "markdown processing", str(md_path))
    return chunks

if __name__ == "__main__":
    # Main processing
    files = find_markdown_files(FURNACE_INPUT_DIR)
    logger.info(f"📁 Found {len(files)} markdown files to chunk")

    # Resume from checkpoint if available
    processed_files = set()
    if os.path.exists(CHECKPOINT_FILE):
        all_chunks = load_checkpoint(CHECKPOINT_FILE)
        # Safely extract file paths from source_chunk, handling different formats
        for chunk in all_chunks:
            source_chunk = chunk.get('source_chunk', '')
            if source_chunk and '#' in source_chunk:
                file_path = source_chunk.split('#')[0]
                processed_files.add(file_path)
            elif source_chunk:
                # Handle case where source_chunk doesn't have '#'
                processed_files.add(source_chunk)
        logger.info(f"🔄 Resuming from checkpoint. {len(processed_files)} files already processed.")

    files_to_process = [f for f in files if str(f) not in processed_files]

    for i, path in enumerate(track(files_to_process, description="🔁 Chunking markdown files...")):
        file_chunks = process_markdown_file(path)
        all_chunks.extend(file_chunks)
        
        # Save checkpoint every 100 files
        if (i + 1) % 100 == 0:
            save_checkpoint(all_chunks, CHECKPOINT_FILE)
            logger.info(f"💾 Checkpoint saved at file {i+1}/{len(files_to_process)}")

    # Perform all enrichment in a single, batched, parallelized step
    logger.info(f"🔍 Enriching {len(all_chunks)} chunks with full NLP pipeline...")
    all_chunks = batch_enrich_chunks(all_chunks)

    # Save all chunks
    with open(output_path, "w") as f:
        json.dump(all_chunks, f, indent=2)

    # Clean up checkpoint file after successful run
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)

    # Update symlink
    if os.path.islink(latest_symlink) or os.path.exists(latest_symlink):
        os.remove(latest_symlink)
    os.symlink(output_path, latest_symlink)

    logger.info("✅ Markdown Chunking Complete")
    logger.info(f"📦 Total markdown chunks written: {len(all_chunks)}")
    logger.info(f"📄 Output file: {output_path}")
    logger.info(f"🔗 Symlink updated: {latest_symlink}")

    # Generate QA metrics and semantic analysis
    logger.info("📊 Generating QA metrics and semantic analysis...")
    from chunking.core.analysis.qa_utils import (
        compute_metrics, save_metrics_json, save_summary_md, save_sample, 
        save_flagged_json, export_flagged_csv, analyze_semantic_types_histogram,
        print_semantic_summary, save_semantic_analysis
    )
    from chunking.core.analysis.qa_summary import generate_qa_summary, print_qa_summary

    # Compute QA metrics
    metrics = compute_metrics(all_chunks)
    history_dir = os.path.join(QA_MARKDOWN_DIR, "metrics_history")
    os.makedirs(history_dir, exist_ok=True)

    # Compute semantic analysis
    semantic_histogram = analyze_semantic_types_histogram(all_chunks)

    # Log semantic summary
    logger.info("🎯 Semantic Analysis Summary:")
    print_semantic_summary(semantic_histogram)

    # Save QA artifacts
    save_metrics_json(metrics, os.path.join(QA_MARKDOWN_DIR, "chunk_metrics.json"), history_dir)
    save_summary_md(metrics, os.path.join(QA_MARKDOWN_DIR, "chunk_summary.md"))
    save_sample(all_chunks, os.path.join(QA_MARKDOWN_DIR, "chunk_sample.json"))
    save_flagged_json(all_chunks, os.path.join(QA_MARKDOWN_DIR, "chunks_flagged.json"))
    export_flagged_csv(all_chunks, os.path.join(QA_MARKDOWN_DIR, "chunk_qc.csv"))

    # Save semantic analysis
    save_semantic_analysis(semantic_histogram, os.path.join(QA_MARKDOWN_DIR, "semantic_analysis.json"))
    
    # Generate and save QA summary
    qa_summary = generate_qa_summary(all_chunks, QA_MARKDOWN_DIR, "markdown_batch")
    print_qa_summary(qa_summary)

    logger.info(f"📊 QA metrics and semantic analysis saved to: {QA_MARKDOWN_DIR}") 