#!/usr/bin/env python3
"""
Excel-specific chunk processor plugin.
Handles Excel files and extracts chunks from structured data.
"""

import sys
import os
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the parent directory to the path to import chunking modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base import ChunkProcessor
from chunking.core.schema import create_chunk_from_template
from chunking.core.processing.chunker import chunk_sentences, apply_overlap, build_chunks
from chunking.core.enrichment.metadata import extract_metadata_from_filename, build_chunk_id
from chunking.core.enrichment.enhancer import get_spacy_model


class ExcelProcessor(ChunkProcessor):
    """
    Excel file processor plugin.
    
    Processes Excel files by:
    1. Reading Excel data with pandas
    2. Converting rows to text chunks
    3. Extracting metadata from filename
    4. Building chunks with proper schema
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Excel processor.
        
        Args:
            config: Configuration dictionary with processing parameters
        """
        super().__init__(config)
        
        # Default configuration
        self.default_config = {
            "chunk_size": 100,
            "overlap": 0.3,
            "min_chunk_size": 10,
            "max_chunk_size": 500,
            "text_columns": ["Question", "Answer", "Explanation"],
            "separator": " | "
        }
        
        # Merge with provided config
        self.config = {**self.default_config, **self.config}
        
        # Initialize spaCy model
        self.nlp = get_spacy_model()
    
    def can_process(self, file_path: str) -> bool:
        """
        Check if this processor can handle the given file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file is an Excel file (.xlsx, .xls, .csv)
        """
        path = Path(file_path)
        return path.suffix.lower() in ['.xlsx', '.xls', '.csv']
    
    def process(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Process an Excel file and return chunks.
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            List of chunk dictionaries with metadata and text content
            
        Raises:
            ValueError: If file cannot be read or processed
        """
        # Validate file
        if not self.validate_file(file_path):
            raise ValueError(f"Invalid file: {file_path}")
        
        # Pre-process file
        file_info = self.pre_process(file_path)
        
        # Read Excel file with sheet validation
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                # Read Excel file and validate sheet access
                excel_file = pd.ExcelFile(file_path)
                sheet_names = excel_file.sheet_names
                
                # Use first sheet if no specific sheet is specified
                sheet_name = sheet_names[0] if sheet_names else None
                
                if not sheet_names:
                    raise ValueError(f"No sheets found in Excel file: {file_path}")
                
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
        except Exception as e:
            raise ValueError(f"Error reading Excel file {file_path}: {e}")
        
        # Extract metadata from filename
        metadata_base = extract_metadata_from_filename(str(file_path), "excel")
        
        all_chunks = []
        
        # Store current file path for template matching
        self.current_file_path = file_path
        
        # Process each row
        for row_idx, row in df.iterrows():
            # Convert row to text using template system
            row_text = self._row_to_text(row)
            template_success = bool(row_text)
            
            if not row_text.strip():
                continue
            
            # Build section stack for chunk ID
            section_stack = [
                f"row_{row_idx}",
                metadata_base["subtopic1"],
                metadata_base["subtopic2"],
                metadata_base["subtopic3"],
                metadata_base["subtopic4"]
            ]
            
            # Generate source ID
            source_id = build_chunk_id(
                metadata_base["topic"],
                metadata_base["author"],
                section_stack,
                row_idx
            )
            
            # Create metadata using template
            metadata = create_chunk_from_template(
                chunk_type="excel",
                source_metadata={
                    "topic": metadata_base.get("topic"),
                    "author": metadata_base.get("author"),
                    "subtopic1": metadata_base.get("subtopic1"),
                    "subtopic2": metadata_base.get("subtopic2"),
                    "subtopic3": metadata_base.get("subtopic3"),
                    "subtopic4": metadata_base.get("subtopic4"),
                    "subtopic5": metadata_base.get("subtopic5"),
                    "source_chunk": f"{file_path}#row_{row_idx}",
                    "source_id": source_id,
                    "source_type": "excel",
                    "section_heading": f"Row {row_idx}",
                    "document_title": metadata_base.get("topic", "Excel Data"),
                    "file_path": str(file_path),
                    "row_index": row_idx,
                    "sheet_name": None,
                    "chunk_index": row_idx
                },
                retrieval_metadata={
                    "concept_tags": [],
                    "context_tags": []
                },
                review_metadata={
                    "review_changes": [],
                    "last_reviewed": "",
                    "last_seen": "",
                    "revision_bucket": ""
                }
            )
            
            # ✅ FIXED: Create single chunk with template output
            # For Excel, preserve the structured template text as-is
            
            # Remove conflicting fields from metadata to avoid conflicts
            metadata_copy = metadata.copy()
            metadata_copy.pop('chunk_id', None)
            metadata_copy.pop('chunk_text', None)
            metadata_copy.pop('chunk_word_count', None)
            metadata_copy.pop('source_confidence', None)
            
            # Process Excel text through post-processor
            from chunking.core.processing.excel_post_processor import process_excel_text
            processed_text, post_metadata = process_excel_text(row_text, row.to_dict(), file_path)
            
            # Determine source confidence
            from chunking.templates.template_registry import determine_source_confidence
            source_confidence = determine_source_confidence(processed_text, row.to_dict(), file_path, template_success)
            
            # Skip context-dead chunks
            if post_metadata.get("is_context_dead", False):
                logger.debug(f"Skipping context-dead chunk: {processed_text[:50]}...")
                continue
            
            chunk = create_chunk_from_template(
                chunk_id=f"{source_id}_0",
                chunk_text=processed_text,  # Use the processed text
                chunk_word_count=len(processed_text.split()),
                chunk_index=row_idx,  # Set chunk index to row index for Excel
                source_confidence=source_confidence,
                source_confidence_score=post_metadata.get("confidence", 0.5),
                semantic_type=post_metadata.get("semantic_type", "general"),
                **metadata_copy
            )
            
            # Enhance with RAG metadata
            from chunking.core.enrichment.rag_metadata import enhance_rag_metadata
            chunk = enhance_rag_metadata(chunk)
            
            # Apply quality checks
            word_count = len(row_text.split())
            quality = "ok"
            omit_flag = False
            skip_reasons = []
            
            if word_count > 200:  # Excel chunks should be concise
                quality = "too_long"
                omit_flag = True
                skip_reasons.append("too_long")
            elif word_count < 8:
                quality = "fragment"
                omit_flag = True
                skip_reasons.append("fragment")
            
            chunk["chunk_quality"] = quality
            chunk["omit_flag"] = omit_flag
            chunk["show_skip_reasons"] = skip_reasons
            
            if not omit_flag:
                all_chunks.append(chunk)
        
        # Post-process chunks
        processed_chunks = self.post_process(all_chunks, file_info)
        
        return processed_chunks
    
    def _row_to_text(self, row: pd.Series) -> str:
        """
        Convert a pandas row to text format using the template system.
        
        Args:
            row: Pandas Series representing a row from Excel/CSV
            
        Returns:
            Formatted text string using structured templates
        """
        # Convert row to dictionary for templating
        row_dict = row.to_dict()
        
        # Use the template system for structured output
        from ..templates.template_registry import apply_template
        import os
        
        # Get filename for template matching
        filename = os.path.basename(self.current_file_path) if hasattr(self, 'current_file_path') else "unknown.xlsx"
        
        # Try structured templating first
        template_text = apply_template(filename, row_dict)
        
        if template_text:
            return template_text
        
        # Fallback to legacy concatenation if template fails
        text_parts = []
        
        for col in self.config["text_columns"]:
            if col in row and pd.notna(row[col]):
                text_parts.append(str(row[col]))
        
        # If no text columns found, use all columns
        if not text_parts:
            for col in row.index:
                if pd.notna(row[col]):
                    text_parts.append(f"{col}: {row[col]}")
        
        return self.config["separator"].join(text_parts)
    
    def get_processor_info(self) -> Dict[str, Any]:
        """
        Get information about this processor.
        
        Returns:
            Dictionary with processor information
        """
        info = super().get_processor_info()
        info.update({
            "supported_extensions": [".xlsx", ".xls", ".csv"],
            "processing_config": self.config,
            "nlp_model": "spaCy"
        })
        return info 