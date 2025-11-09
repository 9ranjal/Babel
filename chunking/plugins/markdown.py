#!/usr/bin/env python3
"""
Markdown-specific chunk processor plugin.
Handles markdown files and extracts chunks with proper metadata.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the parent directory to the path to import chunking modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base import ChunkProcessor
from chunking.core.schema import create_chunk_from_template
from chunking.core.processing.chunker import chunk_sentences, apply_overlap, build_chunks
from chunking.core.enrichment.metadata import extract_metadata_from_filename, build_chunk_id
from chunking.core.enrichment.enhancer import get_spacy_model
from chunking.core.analysis.utils import parse_markdown_sections


class MarkdownProcessor(ChunkProcessor):
    """
    Markdown file processor plugin.
    
    Processes markdown files by:
    1. Parsing markdown sections
    2. Extracting metadata from filename
    3. Chunking content with overlap
    4. Building chunks with proper schema
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the markdown processor.
        
        Args:
            config: Configuration dictionary with chunking parameters
        """
        super().__init__(config)
        
        # Default configuration
        self.default_config = {
            "chunk_size": 100,
            "overlap": 0.3,
            "min_chunk_size": 10,
            "max_chunk_size": 500
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
            True if the file is a markdown file
        """
        path = Path(file_path)
        return path.suffix.lower() in ['.md', '.markdown']
    
    def process(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Process a markdown file and return chunks.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            List of chunk dictionaries
        """
        # Validate file
        if not self.validate_file(file_path):
            raise ValueError(f"Invalid file: {file_path}")
        
        # Pre-process file
        file_info = self.pre_process(file_path)
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract metadata from filename
        metadata_base = extract_metadata_from_filename(str(file_path), "markdown")
        
        # Parse markdown sections
        sections = parse_markdown_sections(content.split('\n'))
        
        all_chunks = []
        
        for section_idx, (section_title, section_content) in enumerate(sections):
            if not section_content.strip():
                continue
            
            # Extract section heading and document title
            section_heading = section_title.strip()
            document_title = metadata_base.get("topic", "Unknown")
            
            # Process sentences
            sentences = chunk_sentences(section_content, self.nlp)
            if not sentences:
                continue
            
            # Apply overlap to create windows
            windows = apply_overlap(
                sentences, 
                chunk_size=self.config["chunk_size"], 
                overlap=self.config["overlap"]
            )
            
            # Build section stack for chunk ID
            section_stack = [
                section_title,
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
                section_idx
            )
            
            # Create metadata using template
            metadata = create_chunk_from_template(
                chunk_type="markdown",
                source_metadata={
                    "topic": metadata_base.get("topic"),
                    "author": metadata_base.get("author"),
                    "subtopic1": metadata_base.get("subtopic1"),
                    "subtopic2": metadata_base.get("subtopic2"),
                    "subtopic3": metadata_base.get("subtopic3"),
                    "subtopic4": metadata_base.get("subtopic4"),
                    "subtopic5": metadata_base.get("subtopic5"),
                    "source_chunk": f"{file_path}#{section_title}",
                    "source_id": source_id,
                    "source_type": "markdown",
                    "section_heading": section_heading,
                    "document_title": document_title,
                    "file_path": str(file_path),
                    "row_index": None,
                    "sheet_name": None,
                    "chunk_index": section_idx
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
            
            # Build chunks for this section
            section_chunks = build_chunks(windows, metadata, nlp=self.nlp)
            all_chunks.extend(section_chunks)
        
        # Post-process chunks
        processed_chunks = self.post_process(all_chunks, file_info)
        
        return processed_chunks
    
    def get_processor_info(self) -> Dict[str, Any]:
        """
        Get information about this processor.
        
        Returns:
            Dictionary with processor information
        """
        info = super().get_processor_info()
        info.update({
            "supported_extensions": [".md", ".markdown"],
            "chunking_config": self.config,
            "nlp_model": "spaCy"
        })
        return info 