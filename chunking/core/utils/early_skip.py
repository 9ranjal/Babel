"""
Early row skipping utilities for performance optimization.
"""

import re
from typing import Dict, Tuple, List
from ..config import (
    ENABLE_EARLY_ROW_SKIP, MIN_NON_EMPTY_FIELDS, 
    MAX_NUMERIC_RATIO, MIN_TEXT_FIELD_LENGTH
)

def should_skip_row(row_data: Dict, filename: str = "") -> Tuple[bool, str]:
    """
    Determine if a row should be skipped early to save processing time.
    
    Args:
        row_data: Dictionary of row field values
        filename: Source filename for context
        
    Returns:
        Tuple of (should_skip, reason)
    """
    if not ENABLE_EARLY_ROW_SKIP or not row_data:
        return False, ""
    
    # Count non-empty fields
    non_empty_values = []
    for value in row_data.values():
        if value and str(value).strip().lower() not in ["", "nan", "none", "-", "null"]:
            non_empty_values.append(str(value).strip())
    
    # Skip if too few non-empty fields
    if len(non_empty_values) < MIN_NON_EMPTY_FIELDS:
        return True, f"insufficient_data ({len(non_empty_values)} fields)"
    
    # Check for numeric-heavy rows
    numeric_count = 0
    text_fields = 0
    has_substantial_text = False
    
    for value in non_empty_values:
        # Check if primarily numeric
        if _is_primarily_numeric(value):
            numeric_count += 1
        else:
            text_fields += 1
            # Check for substantial text content
            if len(value) >= MIN_TEXT_FIELD_LENGTH and _has_meaningful_text(value):
                has_substantial_text = True
    
    # Skip if too many numeric fields and no substantial text
    total_fields = len(non_empty_values)
    numeric_ratio = numeric_count / total_fields if total_fields > 0 else 0
    
    if numeric_ratio > MAX_NUMERIC_RATIO and not has_substantial_text:
        return True, f"numeric_heavy ({numeric_ratio:.1%} numeric, no substantial text)"
    
    # Check for low-value content patterns
    combined_text = " ".join(non_empty_values).lower()
    
    # Skip rows with only metadata/structural content
    if _is_metadata_only(combined_text):
        return True, "metadata_only"
    
    # Skip rows with broken/incomplete content
    if _is_broken_content(combined_text):
        return True, "broken_content"
    
    return False, "keep"

def _is_primarily_numeric(value: str) -> bool:
    """Check if a value is primarily numeric."""
    if not value:
        return False
    
    # Remove common numeric formatting
    cleaned = re.sub(r'[,\s%$₹]', '', value)
    
    # Check if mostly digits, decimals, or common numeric patterns
    numeric_chars = sum(1 for c in cleaned if c.isdigit() or c in '.-')
    total_chars = len(cleaned)
    
    return total_chars > 0 and (numeric_chars / total_chars) > 0.7

def _has_meaningful_text(value: str) -> bool:
    """Check if text content is meaningful (not just codes/numbers)."""
    if not value or len(value) < MIN_TEXT_FIELD_LENGTH:
        return False
    
    # Look for indicators of meaningful text
    has_spaces = ' ' in value
    has_lowercase = any(c.islower() for c in value)
    has_articles = any(word in value.lower().split() for word in ['the', 'a', 'an', 'of', 'in', 'for', 'and', 'or'])
    word_count = len(value.split())
    
    return (has_spaces and has_lowercase and word_count >= 3) or has_articles

def _is_metadata_only(text: str) -> bool:
    """Check if content is only metadata/structural information."""
    metadata_patterns = [
        r'^(chapter|section|unit|part)\s+\d+$',
        r'^(page|pg)\s+\d+$',
        r'^(table|figure|fig)\s+\d+',
        r'^(source|ref|reference):\s*$',
        r'^(note|notes?):\s*$',
        r'^(see|refer|check)\s+(chapter|section|page)',
        r'^(continued|cont\.?|contd\.?)$',
        r'^(total|sum|average|avg)$'
    ]
    
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in metadata_patterns)

def _is_broken_content(text: str) -> bool:
    """Check if content appears broken or malformed - CONSERVATIVE approach."""
    # MUCH more conservative patterns - only catch truly broken content
    broken_patterns = [
        r'\.{5,}',  # Five or more dots (not 3+)
        r'\({3,}|\){3,}',  # Three or more parentheses (not 2+)
        r'[A-Z]{15,}',  # Very long all-caps sequences (not 10+) 
        r'^[^a-zA-Z]*$',  # No alphabetic characters at all
        r'^\s*[-_=+*]{5,}\s*$',  # Long lines of special characters (not 3+)
        r'^(test|debug|error|null|undefined|nan)$'  # Obviously broken placeholders
    ]
    
    # Check for excessive repetition (more conservative)
    words = text.split()
    if len(words) > 10:  # Only check longer texts
        unique_words = set(words)
        repetition_ratio = len(words) / len(unique_words)
        if repetition_ratio > 5:  # More repetition required (was 3)
            return True
    
    # Only flag as broken if it matches patterns AND is very short with no meaning
    has_broken_pattern = any(re.search(pattern, text, re.IGNORECASE) for pattern in broken_patterns)
    is_meaningless = len(text.strip()) < 10 and not any(c.isalpha() for c in text)
    
    return has_broken_pattern or is_meaningless

def analyze_skip_effectiveness(processed_rows: List[Dict], skipped_rows: List[Dict]) -> Dict:
    """
    Analyze the effectiveness of row skipping for performance tuning.
    
    Args:
        processed_rows: List of rows that were processed
        skipped_rows: List of rows that were skipped
        
    Returns:
        Dictionary with skip analysis metrics
    """
    total_rows = len(processed_rows) + len(skipped_rows)
    skip_rate = len(skipped_rows) / total_rows if total_rows > 0 else 0
    
    # Analyze skip reasons
    skip_reasons = {}
    for row in skipped_rows:
        reason = row.get('skip_reason', 'unknown')
        skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
    
    # Estimate time saved (rough calculation)
    # Assume each skipped row saves ~500ms of processing time
    estimated_time_saved = len(skipped_rows) * 0.5  # seconds
    
    analysis = {
        "total_rows": total_rows,
        "processed_rows": len(processed_rows),
        "skipped_rows": len(skipped_rows),
        "skip_rate": skip_rate,
        "estimated_time_saved_seconds": estimated_time_saved,
        "skip_reasons": skip_reasons,
        "efficiency_gain": f"{skip_rate:.1%} reduction in processing load"
    }
    
    return analysis
