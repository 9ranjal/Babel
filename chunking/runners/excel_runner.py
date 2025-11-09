# chunking/runner.py
# Main orchestration logic (replaces chunk_notes.py)

import os
import json
import re
import pandas as pd
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from datetime import datetime
from typing import List, Dict, Any
from chunking.core.utils.logging_utils import get_logger, log_processing_stats, log_error_with_context
from chunking.core.utils.performance_profiler import get_profiler, profile_stage
from chunking.core.utils.early_skip import should_skip_row, analyze_skip_effectiveness
from chunking.core.utils.checkpointing import CheckpointManager

from chunking.core.config import (
    EXCEL_INPUT_DIR, EXCEL_OUTPUT_DIR, QA_EXCEL_DIR,
    TIMESTAMP_FORMAT, SAMPLE_SIZE, CSV_EXPORT_LIMIT
)
from chunking.core.schema import create_chunk_from_template
from chunking.core.processing.chunker import chunk_sentences, apply_overlap, build_chunks
from chunking.core.enrichment.enhancer import batch_enrich_chunks, get_spacy_model
from chunking.core.enrichment.metadata import generate_concept_tags, map_ner_to_domain_tags, extract_metadata_from_filename, build_chunk_id
from chunking.core.processing.text_cleaner import (
    clean_mnemonic_patterns,
    remove_generic_tags,
    normalize_chunk_text,
    is_tautological_or_broken,
    strip_stub_prefixes,
    strip_intro_prefixes
)
from chunking.templates.template_registry import apply_template, save_discarded_rows_report, clear_discarded_rows

console = Console()
logger = get_logger("excel_runner")

# Output paths
output_path = EXCEL_OUTPUT_DIR / f"excel_chunks_{datetime.now().strftime(TIMESTAMP_FORMAT)}.json"
latest_symlink = EXCEL_OUTPUT_DIR / "excel_chunks.json"

# Create output directories
EXCEL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
QA_EXCEL_DIR.mkdir(parents=True, exist_ok=True)

# Load spaCy model (lazy loading to avoid blocking progress)
nlp = None

def get_nlp_model():
    """Lazy load spaCy model to avoid blocking progress display."""
    global nlp
    if nlp is None:
        nlp = get_spacy_model()
    return nlp

def is_malformed_row(row):
    """Check if a row has insufficient data for meaningful chunking."""
    non_empty = [v for v in row.values() if v and str(v).strip().lower() not in ["nan", "none", "-"]]
    return len(non_empty) <= 2

def is_sentence_like(row):
    """Check if row data already forms a coherent sentence."""
    text = ". ".join([str(v) for v in row.values() if isinstance(v, str) and str(v).strip()])
    return text.count(".") >= 2 and len(text.split()) > 12

all_chunks = []

def process_excel_files(
    excel_files: List[Path],
    enable_profiling: bool = False,
    enable_checkpointing: bool = False,
    skip_polishing: bool = False,
    enrich_at_end: bool = True,
) -> List[Dict[str, Any]]:
    """Process a list of Excel files and return all chunks."""
    all_chunks = []
    discarded_chunks = []
    flagged_chunks = []
    
    # Initialize profiler
    profiler = get_profiler(enabled=enable_profiling)
    total_rows = 0
    
    # Initialize checkpointing
    checkpoint_manager = None
    if enable_checkpointing:
        checkpoint_manager = CheckpointManager(
            checkpoint_dir=EXCEL_OUTPUT_DIR / "checkpoints",
            checkpoint_interval=50  # Save every 50 rows
        )
        
        # Try to load existing checkpoint
        checkpoint_data = checkpoint_manager.load_checkpoint()
        if checkpoint_data:
            print("🔄 Resuming from checkpoint...")
            # Could implement resume logic here
    
    # Count total rows for profiling
    skipped_rows = []
    if enable_profiling:
        for path in excel_files:
            try:
                xls = pd.read_excel(path, sheet_name=None)
                for df in xls.values():
                    total_rows += len(df)
            except:
                pass
        profiler.start_session(total_rows)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        
        # Main task for file processing
        file_task = progress.add_task("📄 Processing Excel files...", total=len(excel_files))
        
        for path in excel_files:
            progress.update(file_task, description=f"📄 Processing {path.name}...")
            xls = pd.read_excel(path, sheet_name=None)
            for sheet_name, df in xls.items():
                # Use consolidated metadata extraction with sheet name
                metadata_info = extract_metadata_from_filename(str(path), file_type="excel", sheet_name=sheet_name)
                topic = metadata_info["topic"]
                subtopic1 = metadata_info["subtopic1"]
                subtopic2 = metadata_info["subtopic2"]
                author = metadata_info["author"]
                
                # Get headers for structured processing
                headers = list(df.columns)
                
                df = df.fillna("")
                df = df.reset_index(drop=True)
                
                for row_num, row in enumerate(df.itertuples(index=False), start=1):
                    # Convert row to dictionary for templating
                    row_dict = dict(zip(headers, row))
                    
                    # ✅ STEP 0: Early row skipping for performance
                    should_skip, skip_reason = should_skip_row(row_dict, os.path.basename(path))
                    if should_skip:
                        skipped_rows.append({
                            "row_data": row_dict,
                            "skip_reason": skip_reason,
                            "source": f"{os.path.basename(path)}#{sheet_name}#Row{row_num}"
                        })
                        continue
                    
                    # ✅ Legacy malformed row check (for compatibility)
                    if is_malformed_row(row_dict):
                        discarded_chunks.append({
                            "text": "",
                            "reason": "insufficient data (≤2 non-empty fields)",
                            "source": f"{os.path.basename(path)}#{sheet_name}#Row{row_num}",
                            "file": os.path.basename(path),
                            "sheet": sheet_name,
                            "row": row_num,
                            "row_data": row_dict
                        })
                        continue
                    
                    # ✅ STEP 1: Try structured templating
                    with profile_stage("template_application", chunk_count=1):
                        text = apply_template(os.path.basename(path), row_dict)
                        template_success = bool(text)
                    
                    # ✅ Fallback to legacy concatenation
                    if not text:
                        values = [str(v).strip() for v in row if str(v).strip() and str(v).strip().lower() not in ["nan", "none", "-"]]
                        text = ". ".join(values)
                    
                    if not text:
                        continue
                    
                    # ✅ STEP 2: Clean and validate
                    with profile_stage("text_cleaning", chunk_count=1):
                        text = normalize_chunk_text(text)
                        text = clean_mnemonic_patterns(text)
                        text = remove_generic_tags(text)
                        text = strip_stub_prefixes(text)
                        text = strip_intro_prefixes(text)
                    
                    # ✅ STEP 3: Quality check and logging
                    word_count = len(text.split())
                    
                    # Log suspect chunks
                    is_suspect = False
                    suspect_reasons = []
                    
                    if word_count < 8:
                        is_suspect = True
                        suspect_reasons.append(f"too short ({word_count} words)")
                    
                    if re.match(r"^(shows|miscellaneous|examples?|includes?)", text, re.IGNORECASE):
                        is_suspect = True
                        suspect_reasons.append("starts with problematic prefix")
                    
                    # Count null fields in original row
                    null_fields = sum(1 for v in row_dict.values() if not v or str(v).strip().lower() in ["nan", "none", "-"])
                    if null_fields > 3:
                        is_suspect = True
                        suspect_reasons.append(f"too many null fields ({null_fields})")
                    
                    if is_suspect:
                        flagged_chunks.append({
                            "text": text,
                            "reasons": suspect_reasons,
                            "word_count": word_count,
                            "null_fields": null_fields,
                            "source": f"{os.path.basename(path)}#{sheet_name}#Row{row_num}",
                            "file": os.path.basename(path),
                            "sheet": sheet_name,
                            "row": row_num,
                            "row_data": row_dict
                        })
                    
                    # Use conservative discard: check after normalization and only flag here
                    if is_tautological_or_broken(text):
                        flagged_chunks.append({
                            "text": text,
                            "reasons": ["possibly_tautological_or_malformed (pre-polish)"],
                            "word_count": word_count,
                            "source": f"{os.path.basename(path)}#{sheet_name}#Row{row_num}",
                            "file": os.path.basename(path),
                            "sheet": sheet_name,
                            "row": row_num,
                            "row_data": row_dict
                        })
                    
                    # ✅ STEP 4: Preserve template output for Excel chunks
                    # For Excel chunks, we want to preserve the structured template output
                    # rather than breaking it into sentences and re-joining
                    
                    # Use consolidated chunk ID generation
                    chunk_id_base = build_chunk_id(
                        topic=topic,
                        author=author,
                        section_stack=[subtopic1, os.path.basename(path)],
                        chunk_idx=row_num,
                        chunk_type="excel",
                        additional_info=f"row{row_num}"
                    )
                    
                    try:
                        # ✅ FIXED: Create single chunk with template output
                        # For Excel, preserve the structured template text as-is
                        
                        # Override topic/subtopics from row when available to reflect row-level metadata
                        row_topic = str(row_dict.get('Topic', '')).strip() if 'Topic' in row_dict else ''
                        row_sub1 = str(row_dict.get('Subtopic1', '')).strip() if 'Subtopic1' in row_dict else ''
                        row_sub2 = str(row_dict.get('Subtopic2', '')).strip() if 'Subtopic2' in row_dict else ''
                        if row_topic:
                            topic_use = row_topic
                        else:
                            topic_use = topic
                        if row_sub1:
                            subtopic1_use = row_sub1
                        else:
                            subtopic1_use = subtopic1
                        subtopic2_use = row_sub2 or subtopic2

                        # Create metadata dictionary
                        metadata = {
                            "topic": topic_use,
                            "author": author,
                            "subtopic1": subtopic1_use,
                            "subtopic2": subtopic2_use,
                            "subtopic3": "",
                            "subtopic4": "",
                            "subtopic5": "",
                            "source_chunk": f"{os.path.basename(path)}#{sheet_name}#Row{row_num}",
                            "source_id": chunk_id_base,
                            "source_type": "excel",
                            "concept_tags": [],
                            "review_changes": [],
                            "last_reviewed": "",
                            "last_seen": "",
                            "revision_bucket": ""
                        }
                        
                        # Remove conflicting fields from metadata to avoid conflicts
                        metadata_copy = metadata.copy()
                        metadata_copy.pop('chunk_id', None)
                        metadata_copy.pop('chunk_text', None)
                        metadata_copy.pop('chunk_word_count', None)
                        metadata_copy.pop('source_confidence', None)
                        
                        # Process Excel text through post-processor
                        from chunking.core.processing.excel_post_processor import process_excel_text
                        from chunking.core.schema import create_chunk_from_template, update_chunk_field
                        
                        with profile_stage("excel_post_processing", chunk_count=1, metadata={"text_length": len(text), "skip_polishing": skip_polishing}):
                            # Override text polishing if skip flag is set
                            if skip_polishing:
                                from chunking.core.processing.excel_post_processor import get_excel_processor
                                processor = get_excel_processor(enable_text_polishing=False)
                                processed_text, post_metadata = processor.process(text, row_dict, os.path.basename(path))
                            else:
                                processed_text, post_metadata = process_excel_text(text, row_dict, os.path.basename(path))
                        
                        # Skip context-dead chunks (after polishing)
                        if post_metadata.get("qa_metadata", {}).get("is_context_dead", False):
                            logger.debug(f"Skipping context-dead chunk: {processed_text[:50]}...")
                            continue
                        
                        # Create chunk using schema
                        with profile_stage("schema_creation", chunk_count=1):
                            chunk = create_chunk_from_template(
                                chunk_id=f"{chunk_id_base}_0",
                                chunk_text=processed_text,
                                chunk_word_count=len(processed_text.split()),
                                chunk_type="excel",
                                **metadata_copy
                            )
                            
                            # Merge post-processing metadata (avoid overwriting source metadata; skip None values)
                            for section, section_data in post_metadata.items():
                                if section == "source_metadata":
                                    continue
                                if isinstance(section_data, dict):
                                    for key, value in section_data.items():
                                        if value is None:
                                            continue
                                        chunk = update_chunk_field(chunk, f"{section}.{key}", value)
                        
                        # Apply quality checks (pre-enrichment)
                        with profile_stage("quality_assessment", chunk_count=1):
                            word_count = len(processed_text.split())
                            quality = "ok"
                            omit_flag = False
                            skip_reasons = []
                            
                            if word_count > 200:  # Excel chunks should be concise
                                quality = "too_long"
                                omit_flag = True
                                skip_reasons.append("too_long")
                            elif word_count < 8:
                                quality = "fragment"
                                # Do not omit here; allow downstream enrichment/entity checks to recover
                                omit_flag = False
                                skip_reasons.append("fragment")
                            
                            chunk["chunk_quality"] = quality
                            chunk["omit_flag"] = omit_flag
                            chunk["show_skip_reasons"] = skip_reasons
                        
                        if not omit_flag:
                            all_chunks.append(chunk)
                            
                        # Periodic checkpointing
                        if checkpoint_manager and checkpoint_manager.should_checkpoint(len(all_chunks)):
                            metadata = checkpoint_manager.create_metadata(
                                total_files=len(excel_files),
                                processed_files=excel_files.index(path),
                                total_rows=total_rows,
                                processed_rows=len(all_chunks),
                                current_file=os.path.basename(path),
                                current_row=row_num,
                                performance_stats={"chunks_processed": len(all_chunks)}
                            )
                            checkpoint_manager.save_checkpoint(metadata, all_chunks)
                            
                    except Exception as e:
                        log_error_with_context(logger, e, "chunking", f"row_{row_num}", os.path.basename(path))
            
            # Advance progress after processing each file
            progress.advance(file_task)
    
    # Save discarded chunks for audit (consolidated per run + stable symlink)
    if discarded_chunks:
        # Consolidate into a single JSON per run
        report = {
            "summary": {
                "total_discarded": len(discarded_chunks),
                "generated_at": datetime.now().isoformat(),
            },
            "discarded_rows": discarded_chunks,
        }
        discarded_file = EXCEL_OUTPUT_DIR / f"discarded_chunks_{datetime.now().strftime(TIMESTAMP_FORMAT)}.json"
        with open(discarded_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        # Maintain stable symlink to latest discarded
        latest_discarded = EXCEL_OUTPUT_DIR / "discarded_chunks.json"
        try:
            if os.path.islink(latest_discarded) or os.path.exists(latest_discarded):
                os.remove(latest_discarded)
            os.symlink(discarded_file, latest_discarded)
        except OSError:
            pass
        logger.warning(f"📊 Discarded {len(discarded_chunks)} rows. See: {discarded_file}")
    
    # Save flagged chunks for review (consolidated per run + stable symlink)
    if flagged_chunks:
        flagged_file = EXCEL_OUTPUT_DIR / f"flagged_chunks_{datetime.now().strftime(TIMESTAMP_FORMAT)}.json"
        with open(flagged_file, 'w') as f:
            json.dump(flagged_chunks, f, indent=2, default=str)
        # Maintain stable symlink to latest flagged
        latest_flagged = EXCEL_OUTPUT_DIR / "flagged_chunks.json"
        try:
            if os.path.islink(latest_flagged) or os.path.exists(latest_flagged):
                os.remove(latest_flagged)
            os.symlink(flagged_file, latest_flagged)
        except OSError:
            pass
        logger.info(f"🚩 Flagged {len(flagged_chunks)} suspect chunks. See: {flagged_file}")
    
    # Analyze skipping effectiveness
    if skipped_rows:
        skip_analysis = analyze_skip_effectiveness(all_chunks, skipped_rows)
        logger.info(f"⚡ Row skipping analysis: {skip_analysis['efficiency_gain']}")
        logger.info(f"📊 Skipped {len(skipped_rows)} rows, estimated time saved: {skip_analysis['estimated_time_saved_seconds']:.1f}s")
    
    # End profiling session and save results
    if enable_profiling:
        results = profiler.end_session()
        profiler.print_summary(results)
        
        # Save detailed report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = EXCEL_OUTPUT_DIR / f"performance_profile_{timestamp}.json"
        profiler.save_report(results, report_path)
    
    # Finalize checkpointing
    if checkpoint_manager:
        checkpoint_manager.finalize_session(all_chunks)

    # Perform enrichment here if requested (default True for tests and programmatic use)
    if enrich_at_end and all_chunks:
        logger.info(f"🔍 Enriching {len(all_chunks)} Excel chunks with full NLP pipeline (in-function)...")
        if enable_profiling:
            profiler = get_profiler()
            with profile_stage("batch_enrichment", chunk_count=len(all_chunks)):
                all_chunks = batch_enrich_chunks(all_chunks)
        else:
            all_chunks = batch_enrich_chunks(all_chunks)

    return all_chunks

if __name__ == "__main__":
    # Find Excel files
    files = list(Path(EXCEL_INPUT_DIR).glob("*.xlsx"))
    logger.info(f"📁 Found {len(files)} Excel files to chunk")

    # Parse CLI arguments for debug tools
    import sys
    enable_profiling = "--profile" in sys.argv or "--log-times" in sys.argv
    enable_checkpointing = "--checkpoint" in sys.argv
    skip_polishing = "--skip-polishing" in sys.argv or "--fast" in sys.argv
    
    if skip_polishing:
        logger.info("⚡ FAST MODE: Text polishing disabled for maximum speed")
    
    if enable_checkpointing:
        logger.info("💾 Checkpointing enabled for crash recovery")
    
    all_chunks = process_excel_files(
        files,
        enable_profiling=enable_profiling,
        enable_checkpointing=enable_checkpointing,
        skip_polishing=skip_polishing,
        enrich_at_end=False  # Avoid double enrichment; handled below
    )

    # Perform enrichment here for CLI path
    if all_chunks:
        logger.info(f"🔍 Enriching {len(all_chunks)} Excel chunks with full NLP pipeline...")
        if enable_profiling:
            profiler = get_profiler()
            with profile_stage("batch_enrichment", chunk_count=len(all_chunks)):
                all_chunks = batch_enrich_chunks(all_chunks)
        else:
            all_chunks = batch_enrich_chunks(all_chunks)

    # Save all chunks
    with open(output_path, "w") as f:
        json.dump(all_chunks, f, indent=2)

    if os.path.islink(latest_symlink) or os.path.exists(latest_symlink):
        os.remove(latest_symlink)
    os.symlink(output_path, latest_symlink)

    logger.info("✅ Excel Chunking Complete")
    logger.info(f"📦 Total Excel chunks written: {len(all_chunks)}")
    logger.info(f"📄 Output file: {output_path}")

    # Generate QA metrics and semantic analysis
    logger.info("📊 Generating QA metrics and semantic analysis...")
    from chunking.core.analysis.qa_utils import (
        compute_metrics, save_metrics_json, save_summary_md, save_sample, 
        save_flagged_json, export_flagged_csv, analyze_semantic_types_histogram,
        print_semantic_summary, save_semantic_analysis
    )

    # Compute QA metrics
    metrics = compute_metrics(all_chunks)
    history_dir = os.path.join(QA_EXCEL_DIR, "metrics_history")
    os.makedirs(history_dir, exist_ok=True)

    # Compute semantic analysis
    semantic_histogram = analyze_semantic_types_histogram(all_chunks)

    # Log semantic summary
    logger.info("🎯 Semantic Analysis Summary:")
    print_semantic_summary(semantic_histogram)

    # Save QA artifacts
    save_metrics_json(metrics, os.path.join(QA_EXCEL_DIR, "chunk_metrics.json"), history_dir)
    save_summary_md(metrics, os.path.join(QA_EXCEL_DIR, "chunk_summary.md"))
    save_sample(all_chunks, os.path.join(QA_EXCEL_DIR, "chunk_sample.json"))
    save_flagged_json(all_chunks, os.path.join(QA_EXCEL_DIR, "chunks_flagged.json"))
    export_flagged_csv(all_chunks, os.path.join(QA_EXCEL_DIR, "chunk_qc.csv"))

    # Save semantic analysis
    save_semantic_analysis(semantic_histogram, os.path.join(QA_EXCEL_DIR, "semantic_analysis.json"))

    logger.info(f"📊 QA metrics and semantic analysis saved to: {QA_EXCEL_DIR}")
    
    # Save discarded rows report for QA analysis
    discarded_report_path = save_discarded_rows_report()
    if discarded_report_path != "No discarded rows to report":
        logger.warning(f"📋 Discarded rows report saved to: {discarded_report_path}")
    else:
        logger.info(f"✅ No rows were discarded during processing")
    
    # Clear discarded rows for next run
    clear_discarded_rows() 