import unicodedata
import re
from datetime import datetime

def clean_mnemonic_patterns(text: str) -> str:
    """
    Remove mnemonic patterns and artifacts from text.
    
    Args:
        text: Input text to clean
        
    Returns:
        Cleaned text with mnemonic patterns removed
    """
    if not text:
        return text
    
    # Common mnemonic patterns
    patterns = [
        r"=/=",  # Equivalence markers
        r"\brd\b",  # "rd" abbreviation
        r"NB:",  # Nota bene
        r"^\W+",  # Leading non-word characters
        r"\(W\)",  # (W) markers
        r"\bCAPS\b",  # CAPS markers
        r"->",  # Arrow markers
        r"@@",  # Double at symbols
        r"include:",  # Include markers
        r"eg\.",  # Example markers
        r"i\.e\.",  # Id est markers
        r"🧠",  # Brain emoji
        r"💡",  # Lightbulb emoji
        r"==>",  # Implication arrows
        r"=/=",  # Equivalence arrows
        r"~",  # Tilde markers
        r"->",  # Arrow markers
        r"@@",  # Double at symbols
    ]
    
    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    
    return text.strip()

def remove_generic_tags(text: str) -> str:
    """
    Remove generic tags and meaningless terms from text.
    
    Args:
        text: Input text to clean
        
    Returns:
        Cleaned text with generic tags removed
    """
    if not text:
        return text
    
    # Generic tags to remove
    generic_tags = [
        "Person General",
        "Thing",
        "Type", 
        "Topic",
        "Source",
        "Theme",
        "General",
        "Include",
        "Known",
        "Focused",
        "Truth",
        "Person",
        "Thing",
        "Type",
        "Topic",
        "Source",
        "Theme",
        "General",
        "Include",
        "Known",
        "Focused",
        "Truth"
    ]
    
    for tag in generic_tags:
        text = text.replace(tag, "")
    
    return text.strip()

def normalize_text(text: str) -> str:
    """
    Normalize text by fixing common formatting issues.
    
    Args:
        text: Input text to normalize
        
    Returns:
        Normalized text
    """
    if not text:
        return text
    
    # Fix multiple spaces
    text = re.sub(r"\s+", " ", text)
    
    # Fix multiple periods
    text = text.replace(". .", ".").replace("..", ".")
    
    # Fix multiple commas
    text = re.sub(r",\s*,", ",", text)
    
    # Fix spacing around punctuation
    text = re.sub(r"\s+([.,!?])", r"\1", text)
    
    # Fix spacing after punctuation
    text = re.sub(r"([.,!?])\s*([A-Z])", r"\1 \2", text)
    
    return text.strip()

def is_tautological_or_broken(text: str) -> bool:
    """
    Check if text is tautological, broken, or of poor quality.
    
    Args:
        text: Text to evaluate
        
    Returns:
        True if text should be discarded
    """
    if not text:
        return True
    
    text_lower = text.lower()
    
    # Too short
    if len(text.split()) < 3:
        return True
    
    # Known junk patterns
    junk_patterns = [
        "akshay kumar",
        "true",
        "none",
        "nan",
        "n/a",
        "not applicable",
        "tbd",
        "to be determined"
    ]
    
    for pattern in junk_patterns:
        if pattern in text_lower:
            return True
    
    # Tautological patterns (question contains answer)
    if re.search(r"who is ([^?]+)\?", text_lower):
        person_name = re.search(r"who is ([^?]+)\?", text_lower).group(1).strip()
        if person_name in text_lower.replace(f"who is {person_name}?", ""):
            return True
    
    # Entity echo patterns
    if re.search(r"([A-Z][a-z]+ [A-Z][a-z]+) is \1", text_lower):
        return True
    
    # Check for completely empty or meaningless content
    if text.strip() in ["", ".", "..", "..."]:
        return True
    
    return False

def clean_special_artifacts(text: str) -> str:
    if not text:
        return text
    # Unicode normalization
    text = unicodedata.normalize('NFKC', text)
    # Degree symbol
    text = text.replace('°', ' degree')
    # Bullets
    text = text.replace('•', '-')
    # En dash, em dash
    text = text.replace('–', '-').replace('—', '-')
    # Smart quotes
    text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    # Ellipsis
    text = text.replace('…', '...')
    # Remove other non-ASCII except basic punctuation
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def normalize_chunk_text(text: str) -> str:
    """
    Comprehensive text normalization for chunks.
    Removes markdown formatting, collapses whitespace, and flattens to single line.
    """
    if not text:
        return text
    
    # Clean special unicode/symbol artifacts first
    text = clean_special_artifacts(text)
    
    # Fix Excel-specific formatting issues first
    text = fix_excel_formatting_issues(text)
    
    # Fix common compound words and typos
    text = fix_common_compounds(text)
    
    # Fix double-escaped backslashes first
    text = fix_double_escaped_backslashes(text)
    
    # Remove {.underline} artifacts
    text = re.sub(r'\{\.underline\}', '', text)
    
    # Remove underline_ artifacts from IDs and paths
    text = re.sub(r'underline_', '', text)
    
    # Remove other markdown formatting artifacts
    text = re.sub(r'\{[^}]*\}', '', text)  # Remove any remaining {...} patterns
    
    # Clean up markdown headers
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)  # Remove # headers
    
    # Clean up markdown emphasis
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Remove **bold**
    text = re.sub(r'\*([^*]+)\*', r'\1', text)      # Remove *italic*
    text = re.sub(r'__([^_]+)__', r'\1', text)      # Remove __bold__
    text = re.sub(r'_([^_]+)_', r'\1', text)        # Remove _italic_
    
    # Clean up markdown links
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # [text](url) -> text
    
    # Clean up markdown code
    text = re.sub(r'`([^`]+)`', r'\1', text)        # Remove `code`
    text = re.sub(r'```[^`]*```', '', text)         # Remove code blocks
    
    # Clean up HTML-like tags
    text = re.sub(r'<[^>]+>', '', text)             # Remove HTML tags
    
    # Clean up bullets and blockquotes
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)  # bullets
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)          # blockquotes
    
    # Clean up extra whitespace and flatten
    text = re.sub(r'\n{2,}', '\n', text)                          # collapse multiple newlines
    text = text.replace('\n', ' ')                                 # flatten to single line
    text = re.sub(r'\s+', ' ', text)                               # collapse whitespace
    text = text.strip()
    
    return text

def normalize_chunk_text_enhanced(text: str, preserve_original: bool = True) -> dict:
    """
    Enhanced text normalization with metadata tracking.
    
    Args:
        text: Text to normalize
        preserve_original: Whether to preserve original text in output
        
    Returns:
        dict with cleaned text and metadata
    """
    if not text:
        return {
            "original_text": text if preserve_original else None,
            "cleaned_text": text,
            "cleaning_metadata": {
                "original_length": 0,
                "cleaned_length": 0,
                "changes_made": False,
                "cleaned_at": datetime.now().isoformat()
            }
        }
    
    original = text
    cleaned = normalize_chunk_text(text)
    
    return {
        "original_text": original if preserve_original else None,
        "cleaned_text": cleaned,
        "cleaning_metadata": {
            "original_length": len(original),
            "cleaned_length": len(cleaned),
            "changes_made": original != cleaned,
            "cleaned_at": datetime.now().isoformat()
        }
    }

def normalize_chunk_comprehensive(chunk: dict, preserve_original: bool = False) -> dict:
    """
    Comprehensive chunk normalization that consolidates all cleaning logic.
    This replaces the redundant final normalizer functionality.
    
    Args:
        chunk: Chunk dictionary to normalize
        preserve_original: Whether to preserve original text
        
    Returns:
        Normalized chunk with cleaning metadata
    """
    from datetime import datetime
    from ..schema import ensure_field_integrity, has_required_fields, get_missing_fields
    
    normalized_chunk = chunk.copy()
    
    # 1. Enhanced text cleaning with metadata tracking
    if "chunk_text" in normalized_chunk:
        original_text = normalized_chunk["chunk_text"]
        result = normalize_chunk_text_enhanced(original_text, preserve_original)
        
        normalized_chunk["chunk_text"] = result["cleaned_text"]
        normalized_chunk["original_word_count"] = normalized_chunk.get("chunk_word_count", 0)
        normalized_chunk["chunk_word_count"] = len(result["cleaned_text"].split())
        normalized_chunk["cleaning_metadata"] = result["cleaning_metadata"]
    
    # 2. Field integrity validation
    normalized_chunk = ensure_field_integrity(normalized_chunk)
    
    # Validate semantic_type structure
    if not isinstance(normalized_chunk.get("semantic_type"), dict):
        normalized_chunk["semantic_type"] = {"primary": "other"}
    elif "primary" not in normalized_chunk["semantic_type"]:
        normalized_chunk["semantic_type"]["primary"] = "other"
    
    # 3. Enhanced fact-likeness tagging (consolidated from final normalizer)
    semantic_type = normalized_chunk.get("semantic_type", {}).get("primary", "")
    text = normalized_chunk.get("chunk_text", "").lower()
    
    # Enhanced fact-likeness detection
    fact_indicators = [
        semantic_type in ["definition", "fact", "statistic", "concept"],
        any(word in text for word in ["is defined as", "refers to", "consists of", "includes"]),
        normalized_chunk.get("entity_density", 0) > 0.02,  # High entity density
        len(normalized_chunk.get("primary_entities", [])) > 2,  # Multiple entities
        any(word in text for word in ["is a", "are", "refers to", "means", "consists of"]),
        normalized_chunk.get("chunk_type") == "excel" and normalized_chunk.get("rewritten_flag") is True
    ]
    
    normalized_chunk["is_fact_like"] = any(fact_indicators)
    normalized_chunk["fact_likeness_score"] = sum(fact_indicators) / len(fact_indicators)
    
    # Add fact-likeness metadata
    normalized_chunk["fact_likeness_indicators"] = {
        "semantic_type_fact": semantic_type in ["definition", "fact", "statistic", "concept"],
        "has_definition_phrases": any(word in text for word in ["is defined as", "refers to", "consists of", "includes"]),
        "high_entity_density": normalized_chunk.get("entity_density", 0) > 0.02,
        "multiple_entities": len(normalized_chunk.get("primary_entities", [])) > 2,
        "has_fact_phrases": any(word in text for word in ["is a", "are", "refers to", "means", "consists of"]),
        "is_rewritten_excel": normalized_chunk.get("chunk_type") == "excel" and normalized_chunk.get("rewritten_flag") is True
    }
    
    # 4. Add normalization metadata
    normalized_chunk["normalized"] = True
    normalized_chunk["normalized_at"] = datetime.now().isoformat()
    normalized_chunk["last_enriched_at"] = datetime.now().isoformat()
    normalized_chunk["normalization"] = {
        "normalized_at": datetime.now().isoformat(),
        "cleaned_by": "text_cleaner.py",
        "has_required_fields": has_required_fields(normalized_chunk),
        "fact_likeness_score": normalized_chunk.get("fact_likeness_score", 0),
        "is_fact_like": normalized_chunk.get("is_fact_like", False),
        "validation_enabled": True
    }
    
    return normalized_chunk

def normalize_chunks_batch(chunks: list, preserve_original: bool = False) -> dict:
    """
    Normalize a batch of chunks with comprehensive cleaning.
    
    Args:
        chunks: List of chunks to normalize
        preserve_original: Whether to preserve original text
        
    Returns:
        dict with normalized chunks and statistics
    """
    from datetime import datetime
    
    normalized_chunks = []
    stats = {
        "normalized_count": 0,
        "skipped_count": 0,
        "error_count": 0,
        "errors": []
    }
    
    for chunk in chunks:
        try:
            if chunk.get("normalized") is True:
                stats["skipped_count"] += 1
                normalized_chunks.append(chunk)
                continue
            
            normalized_chunk = normalize_chunk_comprehensive(chunk, preserve_original)
            normalized_chunks.append(normalized_chunk)
            stats["normalized_count"] += 1
            
        except Exception as e:
            stats["error_count"] += 1
            stats["errors"].append(f"Error normalizing chunk {chunk.get('chunk_id', 'unknown')}: {str(e)}")
            # Keep original chunk if normalization fails
            normalized_chunks.append(chunk)
    
    return {
        "chunks": normalized_chunks,
        "stats": stats
    }

def fix_excel_formatting_issues(text: str) -> str:
    """
    Fix Excel-specific formatting issues like bullet-dash combos and underscore leakage.
    """
    if not text:
        return text
    
    # 1. Fix bullet-dash combo artifacts FIRST
    # Pattern: "• – Implementing Ministry – Budget – Timeline"
    text = re.sub(r'•\s*–\s*', '• ', text)  # Remove dash after bullet
    
    # 2. Fix leading dashes at start of text
    text = re.sub(r'^\s*–\s*', '', text)  # Remove leading dash at start of text
    
    # 3. Fix underscore leakage from Excel headers/sheet names
    # Pattern: "Literature_ Monuments include..."
    text = re.sub(r'([A-Za-z])_\s*([A-Za-z])', r'\1 \2', text)  # Replace underscore with space
    text = re.sub(r'([A-Za-z])_([A-Za-z])', r'\1 \2', text)  # Replace underscore with space (no space after)
    
    # 4. Fix multiple dashes and formatting artifacts
    text = re.sub(r'––', '–', text)  # Replace double dash with single
    text = re.sub(r'•\s*•', '•', text)  # Replace double bullets with single
    
    # 5. Fix structured item dashes (convert to colons) - BEFORE sentence boundary fixes
    # Pattern: "Implementing Ministry – Budget – Timeline"
    # Look for patterns where dash is followed by capitalized words
    text = re.sub(r'\s+–\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', r': \1', text)
    
    # 6. Fix sentence boundary dashes (more specific)
    # Pattern: "Sentence ends – New sentence starts"
    text = re.sub(r'([a-z])\s*–\s*([A-Z][a-z])', r'\1. \2', text)  # Fix sentence boundaries
    text = re.sub(r'([.!?])\s*–\s*([A-Z][a-z])', r'\1 \2', text)  # Fix sentence boundaries with punctuation
    
    # 7. Fix remaining mid-sentence dashes (but not structured items)
    # Pattern: "Some text – To Address this issue"
    # Only convert to period if it's a single word, not a structured list
    text = re.sub(r'\s+–\s+([A-Z][a-z]+)(?!\s+[A-Z])', r'. \1', text)  # Replace mid-sentence dash with period
    
    return text

def fix_common_compounds(text: str) -> str:
    """Fix common compound words and typos using intelligent rules."""
    if not text:
        return text
    
    # First, handle specific known cases that need special treatment
    specific_fixes = [
        ("LaxmikantCentre", "Laxmikant Centre"),
        ("laxmikantcentre", "Laxmikant Centre"),
        ("LAXMIKANTCENTRE", "Laxmikant Centre"),
        ("DELHISULTANATE", "Delhi Sultanate"),
        ("delhisultanate", "Delhi Sultanate"),
        ("FREEDOMANDPARTITION", "Freedom and Partition"),
        ("freedomandpartition", "Freedom and Partition"),
    ]
    
    for wrong, correct in specific_fixes:
        text = text.replace(wrong, correct)
    
    # Apply intelligent compound word splitting rules
    text = apply_compound_word_rules(text)
    
    return text

def apply_compound_word_rules(text: str) -> str:
    """Apply intelligent rules to split compound words."""
    if not text:
        return text
    
    # Rule 1: Split camelCase words (e.g., "NationalMovement" -> "National Movement")
    import re
    
    # Handle camelCase patterns
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    
    # Rule 1.5: Handle specific compound words that need special treatment
    # Handle words that start with "Non" followed by a capital letter
    text = re.sub(r'Non([A-Z])', r'Non \1', text)
    
    # Handle words that end with "world" but are compound
    text = re.sub(r'([A-Z][a-z]+)world', r'\1 World', text)
    
    # Handle words that contain "Adalat" (Hindi/Urdu word)
    text = re.sub(r'([A-Z][a-z]+)adalat', r'\1 Adalat', text)
    
    # Handle words that end with "india" but are compound
    text = re.sub(r'([A-Z][a-z]+)india', r'\1 India', text)
    
    # Handle words that end with "governance" but are compound
    text = re.sub(r'([A-Z][a-z]+)governance', r'\1 Governance', text)
    
    # Rule 2: Split ALL_CAPS words into proper case
    # First, identify words that are all caps and likely compound words
    words = text.split()
    processed_words = []
    
    for word in words:
        # Skip if it's already properly spaced or contains special characters
        if ' ' in word or not word.isalpha():
            processed_words.append(word)
            continue
            
        # Handle ALL_CAPS words
        if word.isupper() and len(word) > 3:
            # Split on common patterns
            if 'AND' in word:
                # Handle cases like "FREEDOMANDPARTITION" -> "Freedom and Partition"
                parts = word.split('AND')
                if len(parts) == 2:
                    processed_word = f"{parts[0].title()} and {parts[1].title()}"
                else:
                    processed_word = word.title()
            elif 'OF' in word:
                # Handle cases like "ADVENTOFEUROPEANS" -> "Advent of Europeans"
                parts = word.split('OF')
                if len(parts) == 2:
                    processed_word = f"{parts[0].title()} of {parts[1].title()}"
                else:
                    processed_word = word.title()
            elif 'THE' in word:
                # Handle cases like "ADVENTOFTHEEUROPEANS" -> "Advent of the Europeans"
                parts = word.split('THE')
                if len(parts) == 2:
                    processed_word = f"{parts[0].title()} the {parts[1].title()}"
                else:
                    processed_word = word.title()
            else:
                # For other ALL_CAPS words, try to split on common boundaries
                # Look for patterns where a consonant is followed by a vowel
                processed_word = word.title()
        else:
            processed_word = word
            
        processed_words.append(processed_word)
    
    # Rule 3: Apply title case to remaining words that look like they should be capitalized
    final_words = []
    for word in processed_words:
        # If it's a single word that's all lowercase but looks like it should be title case
        if word.islower() and len(word) > 3 and word.isalpha():
            # Check if it looks like a proper noun or important term
            if any(char.isupper() for char in word):
                # Already has some caps, leave as is
                final_words.append(word)
            else:
                # Apply title case
                final_words.append(word.title())
        else:
            final_words.append(word)
    
    return ' '.join(final_words)

def fix_double_escaped_backslashes(text: str) -> str:
    """Fix double-escaped backslashes in text."""
    if not text:
        return text
    
    # Fix common escaped characters that should be unescaped
    text = text.replace('\\$', '$')  # \$ -> $
    text = text.replace("\\'", "'")  # \' -> '
    text = text.replace('\\"', '"')  # \" -> "
    text = text.replace('\\n', '\n')  # \n -> newline
    text = text.replace('\\t', '\t')  # \t -> tab
    
    # Replace any remaining double backslashes with single backslashes
    text = text.replace('\\\\', '\\')
    
    return text

def slugify(text: str) -> str:
    text = text.lower().strip().replace(' ', '_')
    text = re.sub(r'[^a-z0-9_]', '', text)
    return text

def strip_stub_prefixes(text: str) -> str:
    """Remove stub-like sentence prefixes that indicate incomplete content."""
    if not text:
        return text
    
    # Remove common stub prefixes
    stub_patterns = [
        r"^(shows|includes|miscellaneous|examples?)[:\s]",
        r"^(reformers include:?)",
        r"^(items include:?)",
        r"^(features include:?)",
        r"^(components include:?)"
    ]
    
    for pattern in stub_patterns:
        text = re.sub(pattern, "", text.strip(), flags=re.IGNORECASE)
    
    return text.strip()
def strip_intro_prefixes(text: str) -> str:
    """Remove intro prefixes that indicate incomplete content."""
    if not text:
        return text
    
    # Remove common intro prefixes
    intro_patterns = [
        r"^(reformers include[:\-]?)\s*",
        r"^(items include[:\-]?)\s*", 
        r"^(features include[:\-]?)\s*",
        r"^(components include[:\-]?)\s*",
        r"^(examples include[:\-]?)\s*",
        r"^(includes[:\-]?)\s*"
    ]
    
    for pattern in intro_patterns:
        text = re.sub(pattern, "", text.strip(), flags=re.IGNORECASE)
    
    return text.strip()
