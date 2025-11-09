# chunking/chunker.py
# Core chunking logic

import re
from typing import List, Optional
from spacy.language import Language
from ..config import (
    MARKDOWN_MAX_WORDS, MARKDOWN_MIN_WORDS, MARKDOWN_SHORT_THRESHOLD,
    EXCEL_MAX_WORDS, EXCEL_MIN_WORDS, EXCEL_SHORT_THRESHOLD,
    MERGE_MAX_WORDS, CHUNK_SIZE, OVERLAP_RATIO
)
from ..schema import build_chunk_template, create_chunk_from_template

# Context-dead starters (chunks that don't provide useful context)
CONTEXT_DEAD_STARTERS = [
    "click here", "see above", "see below", "as mentioned", "as stated",
    "as discussed", "refer to", "see also", "for more", "for details",
    "for information", "for example", "for instance", "such as",
    "including", "namely", "that is", "i.e.", "e.g.", "etc."
]

def chunk_sentences(text: str, nlp: Language) -> List[str]:
    """Split text into sentences using spaCy."""
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    return sentences

def apply_overlap(sentences: List[str], chunk_size: int = CHUNK_SIZE, overlap: float = OVERLAP_RATIO) -> List[List[str]]:
    """Apply overlapping windows to sentences."""
    if not sentences:
        return []
    
    windows = []
    step = max(1, int(chunk_size * (1 - overlap)))
    
    for i in range(0, len(sentences), step):
        window = sentences[i:i + chunk_size]
        if window:
            windows.append(window)
    
    return windows

def build_chunks(sentence_chunks: list, metadata: dict, nlp: Optional[Language] = None) -> list:
    """Build chunks from sentence windows with metadata."""
    output_chunks = []
    chunk_counter = 0  # Separate counter for chunk_id generation
    
    idx = 0
    while idx < len(sentence_chunks):
        sent_list = sentence_chunks[idx]
        chunk_text = " ".join(sent_list)
        word_count = len(chunk_text.split())

        # --- Header + Bullet merging logic
        if word_count < 20 and any(sent.startswith(('.underline', '-', '*', '•')) for sent in sent_list):
            # Try to merge with next chunk if this is a short header/bullet
            if idx < len(sentence_chunks) - 1:
                next_sent_list = sentence_chunks[idx + 1]
                merged_text = chunk_text + " " + " ".join(next_sent_list)
                merged_word_count = len(merged_text.split())
                
                # Only merge if the result is reasonable size
                if merged_word_count <= MERGE_MAX_WORDS:
                    chunk_text = merged_text
                    word_count = merged_word_count
                    # Skip the next chunk since we merged it
                    idx += 1

        # --- Metadata filtering
        filtered_metadata = metadata.copy()
        for key in ['topic', 'subtopic1', 'subtopic2', 'subtopic3', 'subtopic4', 'subtopic5']:
            value = filtered_metadata.get(key)
            if value and value.lower() == 'introduction':
                filtered_metadata[key] = ''

        # --- Construct base chunk using template
        # Remove fields from metadata to avoid duplicate arguments
        chunk_metadata = filtered_metadata.copy()
        chunk_metadata.pop('chunk_id', None)
        chunk_metadata.pop('chunk_text', None)
        chunk_metadata.pop('chunk_word_count', None)
        
        chunk = create_chunk_from_template(
            chunk_id=f"{filtered_metadata['source_id']}_{chunk_counter}",
            chunk_text=chunk_text,
            chunk_word_count=word_count,
            chunk_index=chunk_counter,  # Set sequential chunk index
            **chunk_metadata
        )
        
        chunk_counter += 1  # Increment chunk counter for next chunk

        # --- Quality checks
        skip_reasons = []
        quality = "ok"
        omit_flag = False
        chunk_type = filtered_metadata.get("chunk_type", "markdown")

        # Different quality thresholds for Excel vs Markdown
        if chunk_type == "excel":
            # Excel chunks are naturally short - more lenient thresholds
            if word_count > EXCEL_MAX_WORDS:
                quality = "too_long"
                omit_flag = True
                skip_reasons.append("too_long")
            elif word_count < EXCEL_MIN_WORDS:
                quality = "fragment"
                omit_flag = True
                skip_reasons.append("fragment")
            elif word_count < EXCEL_SHORT_THRESHOLD:
                # For short Excel chunks, we'll do a basic quality check
                # Entity and fact-like checks will be done after NER processing
                quality = "short"
                omit_flag = True
                skip_reasons.append("short")
            else:
                quality = "ok"
                omit_flag = False
        else:
            # Markdown chunks - original thresholds
            if word_count > MARKDOWN_MAX_WORDS:
                quality = "too_long"
                omit_flag = True
                skip_reasons.append("too_long")
            elif word_count < MARKDOWN_MIN_WORDS:
                quality = "fragment"
                # Do not auto-omit; flag only (handled later in unified omit logic)
                omit_flag = False
                skip_reasons.append("fragment")
            elif word_count < MARKDOWN_SHORT_THRESHOLD:
                # For short markdown chunks, we'll flag as short but not omit
                quality = "short"
                omit_flag = False
                skip_reasons.append("short")
            else:
                quality = "ok"
                omit_flag = False

        # --- Context-dead check
        first_word = chunk_text.lower().split()[0] if chunk_text else ""
        normalized_text = chunk_text.lower()
        if any(normalized_text.startswith(p) for p in CONTEXT_DEAD_STARTERS):
            quality = "context_dead"
            omit_flag = True
            skip_reasons.append("context_dead")

        # --- Final assignment
        chunk["chunk_quality"] = quality  # PRIMARY QUALITY FIELD

        chunk["omit_flag"] = omit_flag
        chunk["show_skip_reasons"] = skip_reasons

        # Only add non-empty chunks
        if chunk_text.strip() and word_count > 0:
            output_chunks.append(chunk)
        
        idx += 1

    return output_chunks 