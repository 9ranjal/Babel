"""
Template registry for structured Excel data processing.
Provides intelligent templates for different file types to generate clean, coherent text.
Based on comprehensive semantic analysis of 82 Excel files.
"""

from typing import Dict, Callable, Optional, List, Tuple
import re

# Global tracking for discarded rows
DISCARDED_ROWS = []

def log_discarded_row(filename: str, row: Dict, reason: str) -> None:
    """Log discarded rows for QA audit trail."""
    DISCARDED_ROWS.append({
        "filename": filename,
        "row_data": row,
        "reason": reason,
        "timestamp": "2025-01-05"  # Would use datetime.now() in production
    })

def get_discarded_rows() -> List[Dict]:
    """Get all discarded rows for QA analysis."""
    return DISCARDED_ROWS.copy()

def clear_discarded_rows() -> None:
    """Clear the discarded rows list."""
    DISCARDED_ROWS.clear()

def save_discarded_rows_report(output_path: str = None) -> str:
    """
    Save discarded rows report for QA analysis.
    
    Args:
        output_path: Optional path to save the report
        
    Returns:
        Path where report was saved
    """
    import json
    import os
    from datetime import datetime
    
    if not DISCARDED_ROWS:
        return "No discarded rows to report"
    
    # 🔧 FIXED: Handle empty output_path and provide fallback
    if output_path is None or output_path == "":
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        output_path = f"data/qa/discarded_rows_{timestamp}.json"
    
    # 🔧 FIXED: Ensure directory exists with proper error handling
    directory = os.path.dirname(output_path)
    if directory:
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception as e:
            # Fallback to current directory if path creation fails
            output_path = f"discarded_rows_{timestamp}.json"
    
    # 📊 ENHANCED: Add explainability layer to the report
    enhanced_discarded_rows = []
    for row in DISCARDED_ROWS:
        enhanced_row = row.copy()
        
        # Add explainability metadata
        row_data = row.get("row_data", {})
        enhanced_row["explainability"] = {
            "empty_field_count": sum(1 for v in row_data.values() if not v or str(v).strip().lower() in ["", "nan", "none", "-"]),
            "total_fields": len(row_data),
            "word_count": len(str(row.get("row_data", "")).split()),
            "has_key_fields": any(field.lower() in ["name", "title", "detail", "act", "scheme"] for field in row_data.keys())
        }
        enhanced_discarded_rows.append(enhanced_row)
    
    # Group by reason for analysis
    reason_counts = {}
    for row in DISCARDED_ROWS:
        reason = row["reason"]
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
    
    report = {
        "summary": {
            "total_discarded": len(DISCARDED_ROWS),
            "reason_breakdown": reason_counts,
            "generated_at": datetime.now().isoformat()
        },
        "discarded_rows": enhanced_discarded_rows
    }
    
    try:
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        return output_path
    except Exception as e:
        # Final fallback to current directory
        fallback_path = f"discarded_rows_{timestamp}.json"
        with open(fallback_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        return fallback_path

def is_semantically_valid_sentence(text: str) -> Tuple[bool, str]:
    """
    Validate if generated sentence is semantically meaningful.
    
    Returns:
        Tuple of (is_valid, reason)
    """
    if not text or not text.strip():
        return False, "Empty or null text"
    
    text = text.strip()
    words = text.split()
    
    # 🔍 ENHANCED: Contextual length-based filtering
    # Instead of hard 7-word minimum, apply contextual rules
    if len(words) < 7:
        # Check if it's a factually solid sentence with strong noun-verb-object framing
        has_proper_noun = any(word[0].isupper() for word in words if len(word) > 2)
        has_verb = any(word.lower() in ['was', 'is', 'were', 'are', 'has', 'have', 'had', 'passed', 'established', 'created', 'formed'] for word in words)
        has_object = len(words) >= 4  # At least 4 words suggests some object
        
        if has_proper_noun and has_verb and has_object:
            # Allow short sentences with strong SVO framing
            pass
        else:
            return False, f"Too short ({len(words)} words, minimum 7) and lacks proper noun/verb structure"
    
    # 🔍 IMPROVED: Check for missing subject (sentences starting with verbs)
    subject_verb_patterns = [
        r"^\s*(was|is|were|are|has|have|had)\s+",  # Starts with verb without subject
        r"^\s*(published|launched|established|founded|created|formed)\s+",  # Starts with past participle
    ]
    for pattern in subject_verb_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False, f"Missing subject - starts with verb: {pattern}"
    
    # 🔍 IMPROVED: Check for incomplete sentences (missing main clause)
    if re.search(r"^\s*was\s+\w+\s+by\s+\w+\s+and\s+\w+$", text, re.IGNORECASE):
        return False, "Incomplete sentence - missing main clause after 'and'"
    
    # 🔍 NEW: Check for fragmented or incoherent multi-sentence chunks
    if looks_fragmented(text):
        return False, "Fragmented or incoherent multi-sentence structure"
    
    # 🔍 NEW: Check for missing subject-verb-object structure
    if lacks_subject_verb_object(text):
        return False, "Missing proper subject-verb-object structure"
    
    # Check for placeholder patterns
    placeholder_patterns = [
        r"\bwas\s+\w+\s+in\s+\w+\s+by\s+\w+\s+to\s+\w+\s+for\b",  # "was Established in to and is Headquartered in"
        r"\bwas\s+Published\s+in\s+by\s+\w+\s+and\s+on\b",  # "was Published in by G.V. Krishna Rao and on"
        r"\bThe\s+was\s+Launched\s+in\s+by\s+to\s+for\b",  # "The was Launched in by to for"
        r"\bRuled\s+the\s+\w+\s+From\s+and\s+is\s+for\b",  # "Ruled the Mughal Empire From and is for"
        r"\bwas\s+\w+\s+in\s+\w+\s+to\s+\w+\s+and\s+is\s+in\b",  # Generic verb chain
        r"\b-\s*-\s*-\s*-\b",  # Dashes only
        r"\b\w+\s+was\s+\w+\s+who\s+\w+\s+as\s+\.\.\b",  # Incomplete action phrase
    ]
    
    for pattern in placeholder_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False, f"Contains placeholder pattern: {pattern}"
    
    # Check for excessive empty fields (too many "to", "and", "in" without content)
    empty_field_indicators = ["to", "and", "in", "by", "for", "with", "of"]
    empty_count = sum(1 for word in words if word.lower() in empty_field_indicators)
    if empty_count > len(words) * 0.4:  # More than 40% are empty field indicators
        return False, f"Too many empty field indicators ({empty_count}/{len(words)})"
    
    # Check for repeated filler phrases
    filler_phrases = [
        "was established in", "was launched in", "was published in",
        "was founded in", "was created in", "was formed in"
    ]
    text_lower = text.lower()
    filler_count = sum(1 for phrase in filler_phrases if phrase in text_lower)
    if filler_count > 2:
        return False, f"Too many filler phrases ({filler_count})"
    
    # 🔍 IMPROVED: Check for incomplete sentences (ends with prepositions or conjunctions)
    if text.rstrip().endswith((" in", " to", " by", " for", " with", " of", " and", " or")):
        return False, "Incomplete sentence ending with preposition/conjunction"
    
    # Check for verb chains without subjects/objects
    verb_chains = [
        r"\bwas\s+\w+\s+in\s+\w+\s+to\s+\w+\s+for\b",
        r"\bwas\s+\w+\s+by\s+\w+\s+to\s+\w+\s+in\b"
    ]
    for pattern in verb_chains:
        if re.search(pattern, text, re.IGNORECASE):
            return False, "Verb chain without proper subject/object"
    
    # 🔍 FINAL: Hardened cross-check for actor-object semantic agreement
    # If subject is a known organization or act → reject "was a social reformer" scaffolds
    organization_act_patterns = [
        r"(\w+\s+Association|\w+\s+Society|\w+\s+Samaj|\w+\s+Act|\w+\s+Regulation|\w+\s+Bill|\w+\s+Code|\w+\s+Policy)\s+was\s+a\s+Social\s+Reformer",
        r"(\w+\s+Committee|\w+\s+Commission|\w+\s+Board)\s+was\s+a\s+Social\s+Reformer",
        r"(\w+\s+Organization|\w+\s+Institution|\w+\s+Foundation)\s+was\s+a\s+Social\s+Reformer",
        r"(\w+\s+Prevention\s+Act|\w+\s+Restraint\s+Act|\w+\s+Amendment\s+Act|\w+\s+Prohibition\s+Act)\s+was\s+a\s+Social\s+Reformer",
        r"(\w+\s+Act,\s+\d{4})\s+was\s+a\s+Social\s+Reformer",  # "Act, 1870 was a Social Reformer"
        r"(\w+\s+Regulation\s+\w+)\s+was\s+a\s+Social\s+Reformer",  # "Regulation XVII was a Social Reformer"
        r"(Regulation\s+[IVX]+)\s+was\s+a\s+Social\s+Reformer",  # "Regulation XVII was a Social Reformer" (Roman numerals)
        r"(Regulation\s+\w+)\s+was\s+a\s+Social\s+Reformer"  # "Regulation XVII was a Social Reformer" (any regulation)
    ]
    
    for pattern in organization_act_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False, f"Organization/Act misclassified as reformer: {pattern}"
    
    # 🔍 NEW: Check for semantic richness (meaningful entities/concepts)
    meaningful_entities = count_meaningful_entities(text)
    if meaningful_entities < 2:
        return False, f"Insufficient meaningful entities ({meaningful_entities}/2 required)"
    
    # 🔍 NEW: Check for overly generic sentences
    if is_overly_generic(text):
        return False, "Overly generic sentence - lacks specific information"
    
    # 🔍 NEW: Check for abstract stub overuse
    if has_too_many_abstract_stubs(text):
        return False, "Too many abstract stubs without concrete information"
    
    return True, "Valid sentence"

def looks_fragmented(text: str) -> bool:
    """
    Check if text looks fragmented or incoherent across multiple sentences.
    
    Returns:
        True if text appears fragmented
    """
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) < 2:
        return False  # Single sentence, not fragmented
    
    # Check for sentence fragments (too short)
    # More lenient for template outputs - allow short but meaningful sentences
    short_sentences = []
    for s in sentences:
        words = s.split()
        if len(words) < 4:
            # Check if it's a meaningful short sentence (has proper noun or specific data)
            has_proper_noun = any(word[0].isupper() for word in words if len(word) > 2)
            has_specific_data = any(word.replace('.', '').replace(',', '').replace('%', '').isdigit() for word in words)
            has_meaningful_content = any(word.lower() not in ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'] for word in words)
            
            if not (has_proper_noun or has_specific_data or has_meaningful_content):
                short_sentences.append(s)
    
    if len(short_sentences) > 0:
        return True
    
    # Check for unclear referents (sentences starting with "It", "This", "That" without context)
    unclear_referents = 0
    for sentence in sentences[1:]:  # Skip first sentence
        if re.match(r'^\s*(It|This|That|They|These|Those)\s+', sentence, re.IGNORECASE):
            unclear_referents += 1
    
    if unclear_referents > 0:
        return True
    
    # Check for disconnected sentence patterns
    disconnected_patterns = [
        r"was\s+\w+\s+in\s+\d+\.\s+It\s+has",  # "was Launched in 2013. It has 3 Components"
        r"was\s+established\.\s+\w+\s+\w+",    # "The Committee was established. Examine environmental concerns"
        r"is\s+for\s+\w+\.\s+\w+\s+-\s+\w+",   # "It is for Women Upliftment. Women - Remarriage"
    ]
    
    for pattern in disconnected_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    # 🔍 FINAL: Smart fragment detection - allow coherent multi-sentence chunks
    fragment_indicators = [
        r'^\s*(was|is|were|are|has|have|had)\s+',
        r'^\s*(launched|established|implemented|created|formed)\s+',
        r'^\s*(examine|review|study|analyze)\s+',
        r'^\s*(chaired|headed|led)\s+by\s+',
        r'^\s*(and|or|but)\s+'
    ]
    
    # Check if all sentences have proper SVO structure
    all_have_svo = True
    all_start_with_proper_nouns = True
    shared_subject = None
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        words = sentence.split()
        
        # Check if sentence starts with proper noun (capitalized)
        if words and not words[0][0].isupper():
            all_start_with_proper_nouns = False
        
        # Check for basic SVO structure (has subject, verb, and object)
        has_subject = any(word[0].isupper() for word in words if len(word) > 2)
        has_verb = any(word.lower() in ['was', 'is', 'were', 'are', 'has', 'have', 'had', 'examined', 'published', 'established'] for word in words)
        has_object = len(words) >= 4  # At least 4 words suggests some object
        
        if not (has_subject and has_verb and has_object):
            all_have_svo = False
        
        # Track shared subject (first proper noun)
        if not shared_subject and words and words[0][0].isupper():
            shared_subject = words[0]
    
    # If all sentences have SVO and start with proper nouns, they're likely coherent
    if all_have_svo and all_start_with_proper_nouns:
        return False  # Not fragmented
    
    # Check for consecutive fragments only if coherence criteria aren't met
    consecutive_fragments = 0
    max_consecutive = 0
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        
        # Check if sentence is a fragment
        is_fragment = any(re.search(pattern, sentence_lower) for pattern in fragment_indicators)
        
        # Additional checks for very short sentences (only if they start with problematic patterns)
        if len(sentence.split()) < 4 and any(re.search(pattern, sentence_lower) for pattern in fragment_indicators):
            is_fragment = True
        
        if is_fragment:
            consecutive_fragments += 1
            max_consecutive = max(max_consecutive, consecutive_fragments)
        else:
            consecutive_fragments = 0
    
    # 🔍 FINAL: Three consecutive sentence fragments with no subject = discard
    if max_consecutive >= 3:
        return True
    
    return False

def lacks_subject_verb_object(text: str) -> bool:
    """
    Check if text lacks proper subject-verb-object structure.
    
    Returns:
        True if SVO structure is missing
    """
    text_lower = text.lower()
    
    # Check for sentences that start with generic phrases without clear subjects
    generic_starts = [
        r"^\s*it\s+is\s+for\s+\w+",  # "It is for Women Upliftment"
        r"^\s*it\s+has\s+\w+",       # "It has 3 Components"
        r"^\s*it\s+was\s+\w+",       # "It was established"
        r"^\s*this\s+is\s+for\s+\w+", # "This is for..."
        r"^\s*that\s+is\s+for\s+\w+", # "That is for..."
    ]
    
    for pattern in generic_starts:
        if re.search(pattern, text_lower):
            return True
    
    # Check for sentences with only abstract nouns and generic phrases
    abstract_nouns = ["upliftment", "empowerment", "development", "improvement", "enhancement", "support"]
    abstract_count = sum(1 for word in text_lower.split() if word in abstract_nouns)
    
    if abstract_count > 1 and len(text.split()) < 10:
        return True
    
    return False

def has_too_many_abstract_stubs(text: str) -> bool:
    """
    Check if text has too many abstract stubs without concrete information.
    
    Returns:
        True if too many abstract stubs
    """
    text_lower = text.lower()
    
    # Abstract stub patterns
    abstract_patterns = [
        r"it\s+is\s+for\s+\w+",           # "It is for Women Upliftment"
        r"this\s+is\s+for\s+\w+",         # "This is for..."
        r"that\s+is\s+for\s+\w+",         # "That is for..."
        r"covered\s+under:\s+\w+",        # "Covered under: BMG"
        r"includes:\s+\w+",               # "Includes: pensions, maternity"
        r"consists\s+of:\s+\w+",          # "Consists of:..."
    ]
    
    stub_count = sum(1 for pattern in abstract_patterns if re.search(pattern, text_lower))
    
    if stub_count > 0 and len(text.split()) < 8:
        return True
    
    return False

def count_meaningful_entities(text: str) -> int:
    """
    Count meaningful entities/concepts in text.
    
    Returns:
        Number of meaningful entities found
    """
    # Remove common function words
    function_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "was", "were", "are", "has", "have", "had"}
    
    words = text.split()
    meaningful_words = [w for w in words if w.lower() not in function_words and len(w) > 2]
    
    # Count capitalized words (likely proper nouns)
    capitalized_count = sum(1 for w in words if w[0].isupper() and len(w) > 2)
    
    # Count words with numbers (dates, statistics)
    number_count = sum(1 for w in words if any(c.isdigit() for c in w))
    
    return len(meaningful_words) + capitalized_count + number_count

def is_overly_generic(text: str) -> bool:
    """
    Check if sentence is overly generic and lacks specific information.
    
    Returns:
        True if sentence is too generic
    """
    text_lower = text.lower()
    
    # Generic patterns that lack specific information
    generic_patterns = [
        r"the\s+\w+\s+was\s+passed",  # "The Act was passed"
        r"the\s+\w+\s+was\s+established",  # "The committee was established"
        r"the\s+\w+\s+was\s+created",  # "The scheme was created"
        r"the\s+\w+\s+was\s+formed",  # "The organization was formed"
        r"the\s+\w+\s+was\s+founded",  # "The institution was founded"
    ]
    
    for pattern in generic_patterns:
        if re.search(pattern, text_lower):
            # Check if it has additional meaningful information
            meaningful_info = count_meaningful_entities(text)
            if meaningful_info < 3:  # Less than 3 meaningful entities
                return True
    
    return False

def has_sufficient_fields(row: Dict, min_fields: int = 2) -> Tuple[bool, str]:
    """
    Check if row has sufficient meaningful fields for templating.
    
    Args:
        row: Dictionary containing row data
        min_fields: Minimum number of non-empty fields required
        
    Returns:
        Tuple of (has_sufficient, reason)
    """
    # Count non-empty fields (excluding common empty values)
    empty_values = {"", "nan", "none", "-", "n/a", "null", "undefined"}
    non_empty_fields = []
    
    for key, value in row.items():
        if value and str(value).strip().lower() not in empty_values:
            non_empty_fields.append(key)
    
    if len(non_empty_fields) < min_fields:
        return False, f"Insufficient fields ({len(non_empty_fields)}/{min_fields} required)"
    
    # 🔍 UPGRADED: Check for semantic anchors (required for meaningful output)
    # Updated to include actual Excel field names
    semantic_anchors = {
        "person": ["name", "reformer", "leader", "chairperson", "author", "founder", "emperor", "ruler", "detail", "commentary"],
        "entity": ["scheme", "act", "committee", "organization", "institution", "dynasty", "empire", "statistic", "sector"],
        "event": ["battle", "war", "movement", "rebellion", "treaty", "convention", "data", "commentary"],
        "location": ["state", "region", "country", "city", "river", "mountain", "site", "climatic type", "countries"],
        "concept": ["term", "definition", "concept", "principle", "doctrine", "topic", "details"]
    }
    
    # Check if we have at least one semantic anchor from each category
    anchor_categories_present = []
    for category, fields in semantic_anchors.items():
        has_anchor = any(field.lower() in [k.lower() for k in non_empty_fields] for field in fields)
        anchor_categories_present.append(has_anchor)
    
    # 🔍 ENHANCED: More lenient anchor requirements for high-quality content
    # Require at least 1 different type of semantic anchors
    if sum(anchor_categories_present) < 1:
        return False, f"Insufficient semantic anchors ({sum(anchor_categories_present)}/1 required categories)"
    
    # 🔍 NEW: Check for specific field combinations that indicate quality data
    # Updated to include actual Excel field names
    quality_indicators = [
        # Person + Action/Context
        (["name", "reformer", "detail"], ["achievement", "contribution", "focus", "commentary"]),
        (["emperor", "ruler"], ["period", "reign", "achievements"]),
        # Entity + Purpose/Context
        (["scheme", "act", "statistic"], ["objective", "purpose", "target", "sector", "data"]),
        (["committee", "organization"], ["purpose", "objective", "chairperson"]),
        # Event + Details
        (["battle", "war"], ["year", "period", "outcome"]),
        (["treaty", "convention"], ["year", "parties", "purpose"]),
        # Location + Characteristics
        (["state", "region", "climatic type"], ["features", "characteristics", "climate", "countries", "details"]),
        (["river", "mountain"], ["source", "destination", "height"]),
        # Concept + Definition
        (["term"], ["definition", "topic", "details"])
    ]
    
    has_quality_combo = False
    for primary_fields, secondary_fields in quality_indicators:
        has_primary = any(field.lower() in [k.lower() for k in non_empty_fields] for field in primary_fields)
        has_secondary = any(field.lower() in [k.lower() for k in non_empty_fields] for field in secondary_fields)
        if has_primary and has_secondary:
            has_quality_combo = True
            break
    
    # 🔍 ENHANCED: More lenient quality field requirements
    # If we have sufficient semantic anchors, allow some flexibility in quality combinations
    if not has_quality_combo and sum(anchor_categories_present) < 2:
        return False, "No quality field combination present (primary + secondary fields)"
    
    return True, f"Sufficient semantic anchors and quality fields ({len(non_empty_fields)} present)"

def calculate_chunk_validation_score(text: str, row: Dict) -> Tuple[float, str]:
    """
    Calculate a validation score for chunk quality (0-1) with reason code.
    
    Args:
        text: Generated text
        row: Original row data
        
    Returns:
        Tuple of (score, reason_code)
    """
    if not text or not text.strip():
        return 0.0
    
    score = 1.0
    deductions = []
    
    # Base score starts at 1.0, deductions reduce it
    
    # 🔍 FINAL: Refined length penalty - more lenient for short factual sentences
    word_count = len(text.split())
    if word_count < 5:
        score -= 0.3
        deductions.append("very_short_length")
    elif word_count < 7:
        # Check if it's a short but factual sentence
        has_proper_noun = any(word[0].isupper() for word in text.split() if len(word) > 2)
        has_verb = any(word.lower() in ['was', 'is', 'were', 'are', 'has', 'have', 'had', 'passed', 'established', 'created'] for word in text.split())
        if has_proper_noun and has_verb:
            score -= 0.1  # Minimal penalty for short factual sentences
            deductions.append("short_but_factual")
        else:
            score -= 0.2
            deductions.append("short_length")
    elif word_count > 50:
        score -= 0.1
        deductions.append("very_long")
    
    # Fragment penalty
    if looks_fragmented(text):
        score -= 0.4
        deductions.append("fragmented")
    
    # SVO structure penalty
    if lacks_subject_verb_object(text):
        score -= 0.3
        deductions.append("lacks_svo")
    
    # Abstract stub penalty
    if has_too_many_abstract_stubs(text):
        score -= 0.2
        deductions.append("abstract_stubs")
    
    # Generic content penalty
    if is_overly_generic(text):
        score -= 0.2
        deductions.append("overly_generic")
    
    # Entity richness bonus/penalty
    entity_count = count_meaningful_entities(text)
    if entity_count >= 3:
        score += 0.1  # Bonus for rich content
    elif entity_count < 2:
        score -= 0.2
        deductions.append("insufficient_entities")
    
    # Field sufficiency bonus/penalty
    has_fields, _ = has_sufficient_fields(row)
    if not has_fields:
        score -= 0.3
        deductions.append("insufficient_fields")
    
    # Organization/Act misclassification penalty
    organization_act_patterns = [
        r"(\w+\s+Association|\w+\s+Society|\w+\s+Samaj|\w+\s+Act|\w+\s+Regulation|\w+\s+Bill)\s+was\s+a\s+Social\s+Reformer",
        r"(\w+\s+Committee|\w+\s+Commission|\w+\s+Board)\s+was\s+a\s+Social\s+Reformer",
        r"(\w+\s+Organization|\w+\s+Institution|\w+\s+Foundation)\s+was\s+a\s+Social\s+Reformer"
    ]
    
    for pattern in organization_act_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            score -= 0.4
            deductions.append("misclassification")
            break
    
    # Junk suffix penalty
    junk_patterns = [
        r"\s+Women\s+-\s+\w+\s*$",
        r"\s+Reform\s+-\s+\w+\s*$",
        r"\s+etc\.\s*$",
        r"\s+and\s+others\s*$"
    ]
    
    for pattern in junk_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            score -= 0.1
            deductions.append("junk_suffix")
            break
    
    # Ensure score is between 0 and 1
    score = max(0.0, min(1.0, score))
    
    # 🔍 FINAL: Determine reason code based on primary issues
    if score >= 0.85:
        reason_code = "production_ready"
    elif score >= 0.65:
        reason_code = "review_needed"
    else:
        # Determine specific reason for low score
        if "misclassification" in deductions:
            reason_code = "reformer_template_misapplied_to_act"
        elif "fragmented" in deductions:
            reason_code = "fragmented_multi_sentence"
        elif "lacks_svo" in deductions:
            reason_code = "missing_subject_verb_object"
        elif "insufficient_fields" in deductions:
            reason_code = "insufficient_semantic_anchors"
        elif "short_but_factual" in deductions:
            reason_code = "short_but_factual_sentence"
        else:
            reason_code = "multiple_quality_issues"
    
    return score, reason_code

def validate_template_output(text: str, row: Dict, filename: str) -> Tuple[bool, str]:
    """
    Comprehensive validation of template output.
    
    Args:
        text: Generated text from template
        row: Original row data
        filename: Source filename
        
    Returns:
        Tuple of (is_valid, reason)
    """
    # 🔍 NEW: Post-template cleanup and normalization
    text = normalize_template_output(text)
    
    # Check semantic validity
    is_semantic, semantic_reason = is_semantically_valid_sentence(text)
    if not is_semantic:
        return False, f"Semantic validation failed: {semantic_reason}"
    
    # Check field sufficiency
    has_fields, field_reason = has_sufficient_fields(row)
    if not has_fields:
        return False, f"Field validation failed: {field_reason}"
    
    # Additional quality checks
    words = text.split()
    
    # Check for balanced content (not too many prepositions/conjunctions)
    function_words = ["the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"]
    function_word_count = sum(1 for word in words if word.lower() in function_words)
    if function_word_count > len(words) * 0.6:
        return False, f"Too many function words ({function_word_count}/{len(words)})"
    
    # Check for meaningful content (at least 3 content words)
    content_words = [w for w in words if w.lower() not in function_words and len(w) > 2]
    if len(content_words) < 3:
        return False, f"Insufficient content words ({len(content_words)}/3 required)"
    
    # 🔍 FINAL: Calculate validation score with reason code
    validation_score, reason_code = calculate_chunk_validation_score(text, row)
    
    # Reject if score is too low
    if validation_score < 0.65:
        return False, f"Validation score too low: {validation_score:.2f} (reason: {reason_code})"
    
    return True, f"Template output is valid (score: {validation_score:.2f}, reason: {reason_code})"

def normalize_template_output(text: str) -> str:
    """
    Normalize and clean template output to improve quality.
    
    Args:
        text: Raw template output
        
    Returns:
        Cleaned and normalized text
    """
    if not text:
        return text
    
    # 🔍 NEW: Strip mnemonic residue and acronyms
    text = strip_mnemonic_residue(text)
    
    # 🔍 NEW: Collapse broken phrases into coherent sentences
    text = collapse_broken_phrases(text)
    
    # 🔍 NEW: Clean junk suffixes and fragmented metadata
    text = clean_junk_suffixes(text)
    
    # 🔍 NEW: Repair broken sentence pairs
    text = repair_broken_sentence_pairs(text)
    
    # Clean up extra whitespace and punctuation
    text = re.sub(r'\s+', ' ', text.strip())
    text = re.sub(r'\.+', '.', text)
    text = re.sub(r'\s+\.', '.', text)
    
    return text.strip()

def strip_mnemonic_residue(text: str) -> str:
    """
    Remove mnemonic residue and unexplained acronyms.
    
    Args:
        text: Text to clean
        
    Returns:
        Text with mnemonic residue removed
    """
    if not text:
        return text
    
    # Remove common mnemonic patterns
    mnemonic_patterns = [
        r"covered\s+under:\s+[A-Z]{2,}",  # "Covered under: BMG"
        r"includes:\s+[A-Z]{2,}",         # "Includes: BMG"
        r"consists\s+of:\s+[A-Z]{2,}",    # "Consists of: BMG"
        r"under\s+[A-Z]{2,}\s+scheme",    # "Under BMG scheme"
        r"part\s+of\s+[A-Z]{2,}",         # "Part of BMG"
    ]
    
    for pattern in mnemonic_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    
    # Remove standalone acronyms without explanation
    text = re.sub(r'\b[A-Z]{2,}\b(?:\s*[.,])?', "", text)
    
    return text.strip()

def collapse_broken_phrases(text: str) -> str:
    """
    Attempt to collapse broken phrases into coherent sentences.
    
    Args:
        text: Text with potentially broken phrases
        
    Returns:
        Text with improved coherence
    """
    if not text:
        return text
    
    # 🔍 ENHANCED: Try to fix common broken patterns
    fixes = [
        # Fix "was Launched in 2013. It has 3 Components. Implemented by MoEFCC"
        (r"was\s+Launched\s+in\s+(\d+)\.\s+It\s+has\s+(\d+)\s+Components\.\s+Implemented\s+by\s+(\w+)",
         r"The scheme was launched in \1 and has \2 components, implemented by \3"),
        
        # Fix "The Committee was established. Examine environmental concerns. Chaired by M.S. Swaminathan"
        (r"The\s+(\w+)\s+was\s+established\.\s+(\w+\s+\w+)\.\s+Chaired\s+by\s+([^.]+)",
         r"The \1 chaired by \3 was established to \2"),
        
        # Fix "It is for Women Upliftment. Women - Remarriage"
        (r"It\s+is\s+for\s+(\w+)\s+(\w+)\.\s+(\w+)\s+-\s+(\w+)",
         r"The scheme focuses on \1 \2, specifically \3 \4"),
        
        # 🔍 NEW: Fix "The Widow Remarriage Association was a Social Reformer who Vishnu Shastri Pandit"
        (r"The\s+(\w+\s+\w+\s+Association)\s+was\s+a\s+Social\s+Reformer\s+who\s+([^.]+)",
         r"The \1 was founded by \2"),
        
        # 🔍 NEW: Fix "The Female Infanticide Prevention Act, 1870 was a Social Reformer who Mandated Birth registration"
        (r"The\s+(\w+\s+\w+\s+Prevention\s+Act[^.]*)\s+was\s+a\s+Social\s+Reformer\s+who\s+([^.]+)",
         r"The \1 was passed to \2"),
        
        # 🔍 NEW: Fix "The Criminal Law (Amendment) Act, 2013 was passed after the Nirbhaya case"
        (r"The\s+(\w+\s+Law\s+\(Amendment\)\s+Act[^.]*)\s+was\s+passed\s+after\s+([^.]+)",
         r"The \1 was passed in response to \2"),
        
        # 🔍 NEW: Fix "Regulation XVII declared Sati illegal in Bengal under William Bentinck"
        (r"(\w+\s+X{1,3}I{0,3})\s+declared\s+([^.]+)",
         r"\1 was passed to declare \2"),
    ]
    
    for pattern, replacement in fixes:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text

def repair_broken_sentence_pairs(text: str) -> str:
    """
    Repair broken sentence pairs by joining short fragments with appropriate connectors.
    
    Args:
        text: Text that may contain broken sentence pairs
        
    Returns:
        Repaired text with better sentence flow
    """
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) < 2:
        return text
    
    repaired_sentences = []
    i = 0
    
    while i < len(sentences):
        current = sentences[i]
        next_sentence = sentences[i + 1] if i + 1 < len(sentences) else None
        
        # Check if current sentence is short and next sentence is also short
        if (len(current.split()) < 4 and next_sentence and len(next_sentence.split()) < 4):
            # Check if they can be joined with a comma or connector
            current_lower = current.lower()
            next_lower = next_sentence.lower()
            
            # If both have named entities or specific data, join them
            has_named_entity = any(word[0].isupper() for word in current.split() if len(word) > 2)
            has_specific_data = any(word.replace('.', '').replace(',', '').replace('%', '').isdigit() for word in current.split())
            next_has_named_entity = any(word[0].isupper() for word in next_sentence.split() if len(word) > 2)
            next_has_specific_data = any(word.replace('.', '').replace(',', '').replace('%', '').isdigit() for word in next_sentence.split())
            
            if (has_named_entity or has_specific_data) and (next_has_named_entity or next_has_specific_data):
                # Join with comma
                repaired_sentences.append(f"{current}, {next_sentence}")
                i += 2  # Skip next sentence since we merged it
            else:
                repaired_sentences.append(current)
                i += 1
        else:
            repaired_sentences.append(current)
            i += 1
    
    return ". ".join(repaired_sentences) + "." if repaired_sentences else text

def clean_junk_suffixes(text: str) -> str:
    """
    Remove junk suffixes and fragmented metadata from text.
    
    Args:
        text: Text to clean
        
    Returns:
        Text with junk suffixes removed
    """
    if not text:
        return text
    
    # 🔍 ENHANCED: Expandable blacklist of suffix patterns
    junk_patterns = [
        r"\s+Women\s+-\s+Sati\s*$",           # "Women - Sati"
        r"\s+Women\s+-\s+Remarriage\s*$",      # "Women - Remarriage"
        r"\s+Women\s+-\s+Education\s*$",       # "Women - Education"
        r"\s+Women\s+-\s+\w+\s*$",             # "Women - anything"
        r"\s+Reform\s+-\s+\w+\s*$",            # "Reform - anything"
        r"\s+Topic\s+-\s+\w+\s*$",             # "Topic - anything"
        r"\s+Subject\s+-\s+\w+\s*$",           # "Subject - anything"
        r"\s+Category\s+-\s+\w+\s*$",          # "Category - anything"
        r"\s+Type\s+-\s+\w+\s*$",              # "Type - anything"
        r"\s+-\s+\w+\s*$",                     # Generic "- something" at end
        r"\s+etc\.\s*$",                       # "etc." at end
        r"\s+and\s+others\s*$",                # "and others" at end
        r"\s+See\s+more\s*$",                  # "See more"
        r"\s+General\s*$",                     # "General"
        r"\s+\.\s+\w+\s+-\s+\w+\s*$",         # ". Category - Subcategory"
        r"\s+\.\s+\w+\s*$",                    # ". Single word"
        r"\s*\([^)]*\)\s*$",                   # "(additional info)"
        r"\s*\[[^\]]*\]\s*$",                  # "[metadata]"
        r"\s*Note:\s*\w*\s*$",                 # "Note: something"
        r"\s*Ref:\s*\w*\s*$",                  # "Ref: something"
    ]
    
    for pattern in junk_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    
    # Clean up any resulting double periods or spaces
    text = re.sub(r'\.\s*\.', '.', text)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def is_probably_reformer_row(row: Dict) -> bool:
    """Check if row likely contains a person reformer, not an act/institution."""
    name = row.get("Reformer", "") or row.get("Name", "") or row.get("Detail", "") or ""
    name_lower = name.lower()
    
    # 🔍 ENHANCED: Must contain known reformer names
    reformer_names = ["rao", "roy", "karve", "phule", "periyar", "gandhi", "naicker", "guru", "vidyasagar", "malabari", "telang", "deshmukh", "pandit", "swaminathan"]
    has_reformer_name = any(title in name_lower for title in reformer_names)
    
    # 🔍 ENHANCED: Must NOT contain legal/institutional terms
    legal_terms = ["act", "bill", "regulation", "association", "society", "samaj", "committee", "commission", "prevention", "amendment"]
    has_legal_terms = any(term in name_lower for term in legal_terms)
    
    # 🔍 NEW: Check for organization patterns that should NOT be treated as reformers
    org_patterns = [
        r"\w+\s+association",
        r"\w+\s+society", 
        r"\w+\s+samaj",
        r"\w+\s+committee",
        r"\w+\s+commission",
        r"\w+\s+act",
        r"\w+\s+regulation",
        r"\w+\s+bill"
    ]
    
    has_org_pattern = any(re.search(pattern, name_lower) for pattern in org_patterns)
    
    # 🔍 NEW: Check for specific problematic cases
    problematic_cases = [
        "widow remarriage association",
        "female infanticide prevention act",
        "criminal law amendment act",
        "regulation xvii"
    ]
    
    is_problematic = any(case in name_lower for case in problematic_cases)
    
    return has_reformer_name and not has_legal_terms and not has_org_pattern and not is_problematic

def is_probably_legal_act_row(row: Dict) -> bool:
    """Check if row likely contains a legal act/law, not a person."""
    name = row.get("Act", "") or row.get("Name", "") or row.get("Title", "") or row.get("Detail", "") or ""
    name_lower = name.lower()
    
    # 🔍 ENHANCED: Legal terms that indicate acts/laws
    legal_terms = ["act", "bill", "regulation", "law", "legislation", "statute", "amendment", "prevention"]
    
    # 🔍 NEW: Specific legal act patterns
    legal_patterns = [
        r"\w+\s+act",
        r"\w+\s+regulation",
        r"\w+\s+bill",
        r"\w+\s+amendment",
        r"\w+\s+prevention",
        r"criminal\s+law",
        r"civil\s+law"
    ]
    
    has_legal_term = any(term in name_lower for term in legal_terms)
    has_legal_pattern = any(re.search(pattern, name_lower) for pattern in legal_patterns)
    
    # 🔍 NEW: Check for specific known legal acts
    known_acts = [
        "female infanticide prevention act",
        "criminal law amendment act",
        "regulation xvii",
        "widow remarriage act",
        "sati prevention act"
    ]
    
    is_known_act = any(act in name_lower for act in known_acts)
    
    return has_legal_term or has_legal_pattern or is_known_act

# Template functions for different Excel file types based on semantic analysis
TEMPLATES: Dict[str, Callable[[Dict], str]] = {
    # --- PERSON BIOGRAPHY (1 file) ---
    "reformers": lambda r: f"{r.get('Detail', '')} was a social reformer who believed in {r.get('Commentary', '').lower().rstrip('.')}. ({r.get('Detail 2', '')})",
    
    # --- ECONOMIC STATISTICS (3 files) ---
    "economy": lambda r: f"{r.get('Statistic', r.get('Name', ''))} in the {r.get('Sector', 'economy')} sector demonstrates {r.get('Data', r.get('Value', ''))}. This represents {r.get('Commentary', r.get('Note', ''))}",
    "trends": lambda r: f"The trend in {r.get('Indicator', r.get('Name', ''))} indicates {r.get('Data', r.get('Value', ''))} during {r.get('Period', r.get('Year', ''))}. This suggests {r.get('Commentary', r.get('Note', ''))}",
    
    # --- GLOSSARY DEFINITIONS (2 files) ---
    "glossary": lambda r: f"{r.get('Term', r.get('Name', ''))} is defined as {r.get('Definition', r.get('Description', ''))}. This concept is significant for {r.get('Significance', r.get('Note', ''))}",
    
    # --- GEOGRAPHIC DATA (23 files) ---
    "climate": lambda r: f"The climate in {r.get('Region', r.get('State', ''))} is characterized by {r.get('Type', r.get('Climate', ''))} with {r.get('Features', r.get('Characteristics', ''))}",
    "rivers": lambda r: f"The {r.get('River', r.get('Name', ''))} originates from {r.get('Source', '')} and flows through {r.get('States', r.get('Region', ''))} into the {r.get('Outflow', r.get('Destination', ''))}",
    "landforms": lambda r: f"{r.get('Landform', r.get('Name', ''))} is found in {r.get('Region', r.get('Location', ''))} and formed due to {r.get('Formation', r.get('Process', ''))}",
    "borders": lambda r: f"The border between {r.get('Country1', r.get('From', ''))} and {r.get('Country2', r.get('To', ''))} is defined by {r.get('Boundary', r.get('Type', ''))}",
    "petroleum": lambda r: f"{r.get('Field', r.get('Name', ''))} petroleum field in {r.get('State', r.get('Location', ''))} has reserves of {r.get('Reserves', r.get('Quantity', ''))} and is operated by {r.get('Operator', r.get('Company', ''))}",
    "coal": lambda r: f"{r.get('Mine', r.get('Name', ''))} coal mine in {r.get('State', r.get('Location', ''))} produces {r.get('Production', r.get('Quantity', ''))} and is owned by {r.get('Owner', r.get('Company', ''))}",
    "rocks": lambda r: f"{r.get('Rock', r.get('Name', ''))} rocks in {r.get('Location', r.get('Region', ''))} are composed of {r.get('Composition', r.get('Minerals', ''))} and are used for {r.get('Use', r.get('Purpose', ''))}",
    "land_use": lambda r: f"{r.get('Category', r.get('Type', ''))} covers {r.get('Area (MH)', r.get('Area', ''))} million hectares ({r.get('Percentage', '').replace('%', '')}%) of India's total land area",
    "himalayas": lambda r: f"The {r.get('Range', r.get('Name', ''))} in the Himalayas extends from {r.get('From', r.get('Start', ''))} to {r.get('To', r.get('End', ''))} with peaks reaching {r.get('Height', r.get('Elevation', ''))}",
    "passes": lambda r: f"{r.get('Pass', r.get('Name', ''))} connects {r.get('From', r.get('Start', ''))} and {r.get('To', r.get('End', ''))} in the {r.get('Range', r.get('Mountain', ''))} range",
    "gsi_sites": lambda r: f"{r.get('Site', r.get('Name', ''))} in {r.get('State', r.get('Location', ''))} is a {r.get('Type', r.get('Category', ''))} site known for {r.get('Significance', r.get('Features', ''))}",
    "international": lambda r: f"{r.get('Country', r.get('Name', ''))} has {r.get('Feature', r.get('Characteristic', ''))} with {r.get('Details', r.get('Description', ''))}",
    
    # --- ART & CULTURE (4 files) ---
    "art_culture": lambda r: f"{r.get('Artwork', r.get('Name', ''))} was created during {r.get('Period', r.get('Era', ''))} and represents {r.get('Style', r.get('Type', ''))}. It is located at {r.get('Location', r.get('Site', ''))}",
    "heritage_sites": lambda r: f"{r.get('Site', r.get('Name', ''))} in {r.get('State', r.get('Location', ''))} is a {r.get('Type', r.get('Category', ''))} heritage site known for {r.get('Significance', r.get('Features', ''))}",
    "unesco": lambda r: f"{r.get('Site', r.get('Name', ''))} in {r.get('State', r.get('Location', ''))} is a UNESCO World Heritage site designated in {r.get('Year', r.get('Date', ''))} for {r.get('Criteria', r.get('Significance', ''))}",
    "publications_art": lambda r: f"{r.get('Publication', r.get('Name', ''))} was published in {r.get('Year', r.get('Date', ''))} by {r.get('Author', r.get('Creator', ''))} and focuses on {r.get('Subject', r.get('Topic', ''))}",
    
    # --- GOVERNMENT SCHEMES (6 files) ---
    "schemes": lambda r: f"The {r.get('Scheme', r.get('Name', ''))} was launched in {r.get('Year', r.get('Launch Year', ''))} by {r.get('Ministry', r.get('Department', ''))} to {r.get('Objective', r.get('Purpose', ''))} for {r.get('Target Group', r.get('Beneficiaries', ''))}",
    "schemes_ii": lambda r: f"The {r.get('Scheme', r.get('Name', ''))} aims to {r.get('Objective', r.get('Goal', ''))} through {r.get('Implementation', r.get('Method', ''))} with a budget of {r.get('Budget', r.get('Allocation', ''))}",
    "reports": lambda r: f"The {r.get('Report', r.get('Name', ''))} was published in {r.get('Year', r.get('Date', ''))} by {r.get('Commission', r.get('Organization', ''))} and contains {r.get('Content', r.get('Findings', ''))}",
    "ir": lambda r: f"{r.get('Organization', r.get('Name', ''))} was established in {r.get('Year', r.get('Founded', ''))} to {r.get('Purpose', r.get('Objective', ''))} and is headquartered in {r.get('Location', r.get('Headquarters', ''))}",
    
    # --- LEGAL ACTS (1 file) ---
    "charter_acts": lambda r: f"The {r.get('Act', r.get('Name', ''))} was passed in {r.get('Year', r.get('Date', ''))} to {r.get('Purpose', r.get('Objective', ''))}. Key provisions include {r.get('Provisions', r.get('Features', ''))}",
    
    # --- TRIBAL COMMUNITIES (1 file) ---
    "tribes": lambda r: f"The {r.get('Tribe', r.get('Name', ''))} community is found in {r.get('Region', r.get('Location', ''))} and is known for {r.get('Characteristics', r.get('Features', ''))}. They practice {r.get('Practices', r.get('Customs', ''))}",
    
    # --- LITERARY SOURCES (1 file) ---
    "literature_monuments": lambda r: f"{r.get('Text', r.get('Name', ''))} was written by {r.get('Author', r.get('Creator', ''))} during {r.get('Period', r.get('Era', ''))}. It is significant for {r.get('Significance', r.get('Importance', ''))}",
    
    # --- SOCIAL MOVEMENTS (1 file) ---
    "national_movement": lambda r: f"The {r.get('Movement', r.get('Event', ''))} emerged in {r.get('Period', r.get('Year', ''))} under {r.get('Leader', r.get('Organizer', ''))} to {r.get('Objective', r.get('Goal', ''))}. Key events include {r.get('Events', r.get('Activities', ''))}",
    
    # --- COMMITTEES & COMMISSIONS (1 file) ---
    "committees": lambda r: f"The {r.get('Committee', r.get('Name', ''))} was established in {r.get('Year', r.get('Date', ''))} under {r.get('Chairperson', r.get('Chair', ''))} to {r.get('Purpose', r.get('Objective', ''))}. Key recommendations include {r.get('Recommendations', r.get('Findings', ''))}",
    
    # --- INTERNATIONAL AGREEMENTS (1 file) ---
    "conventions": lambda r: f"The {r.get('Convention', r.get('Name', ''))} was signed in {r.get('Year', r.get('Date', ''))} between {r.get('Parties', r.get('Countries', ''))} to {r.get('Purpose', r.get('Objective', ''))}. It is headquartered in {r.get('Location', r.get('Secretariat', ''))}",
    
    # --- ANCIENT HISTORY (Multiple files) ---
    "dynasties": lambda r: f"The {r.get('Dynasty', r.get('Name', ''))} dynasty ruled from {r.get('Period', r.get('Time', ''))} with its capital at {r.get('Capital', r.get('Seat', ''))}. It was known for {r.get('Achievements', r.get('Significance', ''))}",
    "buddhism_jainism": lambda r: f"{r.get('Religion', r.get('Name', ''))} was founded by {r.get('Founder', r.get('Prophet', ''))} in {r.get('Period', r.get('Era', ''))} and teaches {r.get('Teachings', r.get('Philosophy', ''))}",
    "ashokan_edicts": lambda r: f"The {r.get('Edict', r.get('Name', ''))} edict was inscribed in {r.get('Location', r.get('Site', ''))} during {r.get('Period', r.get('Era', ''))} and contains {r.get('Content', r.get('Message', ''))}",
    "literary_sources": lambda r: f"{r.get('Source', r.get('Name', ''))} was written in {r.get('Language', r.get('Script', ''))} during {r.get('Period', r.get('Era', ''))} and provides information about {r.get('Content', r.get('Subject', ''))}",
    "tribes_ancient": lambda r: f"The {r.get('Tribe', r.get('Name', ''))} tribe inhabited {r.get('Region', r.get('Location', ''))} during {r.get('Period', r.get('Era', ''))} and practiced {r.get('Practices', r.get('Customs', ''))}",
    
    # --- MEDIEVAL HISTORY (Multiple files) ---
    "medieval_dynasties": lambda r: f"The {r.get('Dynasty', r.get('Name', ''))} dynasty ruled from {r.get('Period', r.get('Time', ''))} and was known for {r.get('Achievements', r.get('Significance', ''))}",
    "mughals": lambda r: f"{r.get('Emperor', r.get('Ruler', ''))} ruled the Mughal Empire from {r.get('Period', r.get('Reign', ''))} and is known for {r.get('Achievements', r.get('Contributions', ''))}",
    "struggle": lambda r: f"The {r.get('Struggle', r.get('Event', ''))} took place in {r.get('Period', r.get('Year', ''))} between {r.get('Parties', r.get('Sides', ''))} and resulted in {r.get('Outcome', r.get('Result', ''))}",
    "decline_mughals": lambda r: f"The decline of the Mughal Empire began in {r.get('Period', r.get('Era', ''))} due to {r.get('Reasons', r.get('Factors', ''))} and led to {r.get('Consequences', r.get('Results', ''))}",
    
    # --- COLONIAL HISTORY (Multiple files) ---
    "british_administration": lambda r: f"The {r.get('Administration', r.get('System', ''))} was established in {r.get('Year', r.get('Period', ''))} to {r.get('Purpose', r.get('Objective', ''))} and included {r.get('Features', r.get('Components', ''))}",
    "advent_europeans": lambda r: f"{r.get('European', r.get('Country', ''))} arrived in India in {r.get('Year', r.get('Period', ''))} and established {r.get('Establishment', r.get('Presence', ''))} for {r.get('Purpose', r.get('Objective', ''))}",
    "rising_resentment": lambda r: f"Resentment against {r.get('Target', r.get('Subject', ''))} grew in {r.get('Period', r.get('Era', ''))} due to {r.get('Reasons', r.get('Factors', ''))} and manifested in {r.get('Manifestations', r.get('Forms', ''))}",
    "publications": lambda r: f"{r.get('Publication', r.get('Name', ''))} was published in {r.get('Year', r.get('Date', ''))} by {r.get('Author', r.get('Publisher', ''))} and focused on {r.get('Subject', r.get('Topic', ''))}",
    
    # --- POLITY (Multiple files) ---
    "constitution": lambda r: f"Article {r.get('Article', r.get('Number', ''))} of the Constitution provides for {r.get('Provision', r.get('Content', ''))} under {r.get('Part', r.get('Section', ''))}",
    "amendments": lambda r: f"The {r.get('Amendment', r.get('Number', ''))} amendment changed {r.get('Focus', r.get('Subject', ''))} in {r.get('Year', r.get('Date', ''))} to {r.get('Purpose', r.get('Objective', ''))}",
    "schedules": lambda r: f"The {r.get('Schedule', r.get('Number', ''))} of the Constitution relates to {r.get('Subject', r.get('Content', ''))} and includes {r.get('Details', r.get('Items', ''))}",
    "constituent_assembly": lambda r: f"{r.get('Member', r.get('Name', ''))} from {r.get('Region', r.get('State', ''))} was {r.get('Role', r.get('Position', ''))} in the Constituent Assembly and contributed to {r.get('Contributions', r.get('Work', ''))}",
    "citizenship": lambda r: f"Citizenship under {r.get('Category', r.get('Type', ''))} is granted to {r.get('Eligibility', r.get('Criteria', ''))} through {r.get('Process', r.get('Method', ''))}",
    
    # --- ENVIRONMENT (Multiple files) ---
    "flora_fauna": lambda r: f"{r.get('Species', r.get('Name', ''))} is a {r.get('Type', r.get('Category', ''))} species found in {r.get('Region', r.get('Location', ''))} and is listed as {r.get('Status', r.get('IUCN Status', ''))}",
    "pollutants": lambda r: f"{r.get('Pollutant', r.get('Name', ''))} is a {r.get('Type', r.get('Category', ''))} pollutant that {r.get('Effects', r.get('Impact', ''))} and is regulated by {r.get('Regulation', r.get('Standard', ''))}",
    "biodiversity": lambda r: f"{r.get('Site', r.get('Name', ''))} in {r.get('State', r.get('Location', ''))} is a biodiversity heritage site known for {r.get('Significance', r.get('Features', ''))}",
    "environment": lambda r: f"{r.get('Species', r.get('Name', ''))} is a {r.get('Type', r.get('Category', ''))} species found in {r.get('Region', r.get('Location', ''))} and is listed as {r.get('Status', r.get('IUCN Status', ''))}",
    
    # --- TRANSPORT (Multiple files) ---
    "road_networks": lambda r: f"The {r.get('Road', r.get('Name', ''))} connects {r.get('From', r.get('Start', ''))} to {r.get('To', r.get('End', ''))} and is important for {r.get('Significance', r.get('Purpose', ''))}",
    "ports": lambda r: f"{r.get('Port', r.get('Name', ''))} in {r.get('State', r.get('Location', ''))} is a {r.get('Type', r.get('Category', ''))} port that handles {r.get('Cargo', r.get('Traffic', ''))}",
    
    # --- DEFAULT ---
    "default": lambda r: ". ".join([str(v) for v in r.values() if str(v).strip() and str(v).strip().lower() not in ["nan", "none", "-"]]),
}

def determine_source_confidence(text: str, row: Dict, filename: str, template_success: bool) -> str:
    """
    Determine source confidence based on text quality and template success.
    
    Args:
        text: Generated text
        row: Original row data
        filename: Source filename
        template_success: Whether template was successfully applied
        
    Returns:
        Confidence level: "high", "medium", or "low"
    """
    # Markdown files are always high confidence
    if filename.endswith('.md'):
        return "high"
    
    # Excel files with successful template and good validation
    if template_success:
        # Check if text looks fragmented
        if looks_fragmented(text):
            return "medium"
        else:
            return "high"
    
    # Excel files with fallback template or fragment detected
    return "low"

def apply_template(filename: str, row: Dict) -> Optional[str]:
    """
    Apply appropriate template based on filename and row data with comprehensive validation.
    
    Args:
        filename: Name of the Excel file
        row: Dictionary containing row data with headers as keys
        
    Returns:
        Structured text string or None if no template matches or validation fails
    """
    filename_lower = filename.lower()
    
    # ✅ STEP 1: Pre-validation - Check if row has sufficient fields
    has_fields, field_reason = has_sufficient_fields(row, min_fields=2)
    if not has_fields:
        log_discarded_row(filename, row, f"Pre-validation failed: {field_reason}")
        return None
    
    # ✅ STEP 2: Check if row is already sentence-like (skip templating)
    text = ". ".join([str(v) for v in row.values() if isinstance(v, str) and str(v).strip()])
    if text.count(".") >= 2 and len(text.split()) > 12:
        # Validate the sentence-like text too
        is_valid, reason = validate_template_output(text, row, filename)
        if is_valid:
            return text.strip()
        else:
            log_discarded_row(filename, row, f"Sentence-like validation failed: {reason}")
            return None
    
    # ✅ STEP 3: Smart type guards for specific templates
    if "reformer" in filename_lower and is_probably_reformer_row(row):
        try:
            result = TEMPLATES["reformers"](row)
            if result and result.strip():
                is_valid, reason = validate_template_output(result, row, filename)
                if is_valid:
                    return result.strip()
                else:
                    log_discarded_row(filename, row, f"Reformer template validation failed: {reason}")
                    return None
        except Exception as e:
            log_discarded_row(filename, row, f"Reformer template error: {e}")
            return None
    
    if "act" in filename_lower or "legal" in filename_lower:
        if is_probably_legal_act_row(row):
            try:
                result = TEMPLATES["charter_acts"](row)
                if result and result.strip():
                    is_valid, reason = validate_template_output(result, row, filename)
                    if is_valid:
                        return result.strip()
                    else:
                        log_discarded_row(filename, row, f"Legal act template validation failed: {reason}")
                        return None
            except Exception as e:
                log_discarded_row(filename, row, f"Legal act template error: {e}")
                return None
    
    # ✅ STEP 4: Try to match filename patterns to templates (with validation)
    for template_key in TEMPLATES:
        if template_key in filename_lower:
            # Skip reformers template if not a reformer row
            if template_key == "reformers" and not is_probably_reformer_row(row):
                continue
            # Skip legal acts template if not a legal act row
            if template_key == "charter_acts" and not is_probably_legal_act_row(row):
                continue
                
            try:
                template_func = TEMPLATES[template_key]
                result = template_func(row)
                
                if result and result.strip():
                    is_valid, reason = validate_template_output(result, row, filename)
                    if is_valid:
                        return result.strip()
                    else:
                        log_discarded_row(filename, row, f"{template_key} template validation failed: {reason}")
                        return None
            except Exception as e:
                log_discarded_row(filename, row, f"{template_key} template error: {e}")
                continue
    
    # ✅ STEP 5: Enhanced fallback with validation
    headers = list(row.keys())
    header_text = " ".join(headers).lower()
    
    # Pattern matching for common Excel structures
    fallback_templates = [
        (["scheme", "program", "initiative"], _apply_generic_scheme_template),
        (["dynasty", "king", "ruler", "empire"], _apply_generic_dynasty_template),
        (["reformer", "leader", "personality"], _apply_generic_person_template),
        (["act", "law", "legislation"], _apply_generic_act_template),
        (["battle", "war", "conflict"], _apply_generic_battle_template),
        (["land", "geography", "area", "forest", "agriculture"], _apply_generic_geography_template),
        (["economy", "statistic", "data", "sector"], _apply_generic_economy_template),
        (["river", "mountain", "climate", "pass"], _apply_generic_geography_template),
        (["committee", "commission", "report"], _apply_generic_committee_template),
        (["convention", "treaty", "agreement"], _apply_generic_convention_template),
        (["species", "flora", "fauna", "biodiversity"], _apply_generic_environment_template),
    ]
    
    for keywords, template_func in fallback_templates:
        if any(word in header_text for word in keywords):
            try:
                result = template_func(row)
                if result and result.strip():
                    is_valid, reason = validate_template_output(result, row, filename)
                    if is_valid:
                        return result.strip()
                    else:
                        log_discarded_row(filename, row, f"Fallback template validation failed: {reason}")
                        return None
            except Exception as e:
                log_discarded_row(filename, row, f"Fallback template error: {e}")
                continue
    
    # ✅ STEP 6: Final fallback to default template with validation
    try:
        text = TEMPLATES["default"](row)
        if text and text.strip():
            is_valid, reason = validate_template_output(text, row, filename)
            if is_valid:
                return text.strip()
            else:
                log_discarded_row(filename, row, f"Default template validation failed: {reason}")
                return None
        else:
            log_discarded_row(filename, row, "Default template returned empty text")
            return None
    except Exception as e:
        log_discarded_row(filename, row, f"Default template error: {e}")
        return None

def _apply_generic_scheme_template(row: Dict) -> str:
    """Generic template for scheme/program type data."""
    name = row.get('Name') or row.get('Scheme') or row.get('Program') or 'scheme'
    year = row.get('Year') or row.get('Launch Year') or ''
    ministry = row.get('Ministry') or row.get('Department') or ''
    objective = row.get('Objective') or row.get('Purpose') or row.get('Aim') or ''
    target = row.get('Target') or row.get('Beneficiaries') or row.get('Target Group') or ''
    
    parts = []
    if name:
        parts.append(f"The {name}")
    if year:
        parts.append(f"launched in {year}")
    if ministry:
        parts.append(f"by {ministry}")
    if objective:
        parts.append(f"aims to {objective}")
    if target:
        parts.append(f"for {target}")
    
    return ". ".join(parts) + "." if parts else None

def _apply_generic_dynasty_template(row: Dict) -> str:
    """Generic template for dynasty/empire type data."""
    dynasty = row.get('Dynasty') or row.get('Empire') or row.get('Kingdom') or 'dynasty'
    capital = row.get('Capital') or row.get('Seat') or ''
    region = row.get('Region') or row.get('Territory') or ''
    ruler = row.get('Ruler') or row.get('King') or row.get('Emperor') or ''
    period = row.get('Period') or row.get('Time') or row.get('Reign') or ''
    notes = row.get('Notes') or row.get('Significance') or row.get('Achievements') or ''
    
    parts = []
    if dynasty:
        parts.append(f"The {dynasty}")
    if capital and region:
        parts.append(f"with its capital at {capital} in {region}")
    elif capital:
        parts.append(f"with its capital at {capital}")
    elif region:
        parts.append(f"in {region}")
    if ruler and period:
        parts.append(f"was led by {ruler} during {period}")
    elif ruler:
        parts.append(f"was led by {ruler}")
    if notes:
        parts.append(f"It is known for {notes}")
    
    return ". ".join(parts) + "." if parts else None

def _apply_generic_person_template(row: Dict) -> str:
    """Generic template for person/reformer type data."""
    person = row.get('Person') or row.get('Reformer') or row.get('Leader') or row.get('Name') or 'reformer'
    period = row.get('Period') or row.get('Time') or row.get('Era') or ''
    contributions = row.get('Contributions') or row.get('Work') or row.get('Achievements') or row.get('Role') or ''
    significance = row.get('Significance') or row.get('Impact') or row.get('Legacy') or ''
    
    parts = []
    if person:
        parts.append(f"{person}")
    if period:
        parts.append(f"was active during {period}")
    if contributions:
        parts.append(f"and {contributions}")
    if significance:
        parts.append(f"His/her significance includes {significance}")
    
    return ". ".join(parts) + "." if parts else None

def _apply_generic_act_template(row: Dict) -> str:
    """Generic template for act/law type data."""
    act = row.get('Act') or row.get('Law') or row.get('Legislation') or 'act'
    year = row.get('Year') or row.get('Passed') or ''
    purpose = row.get('Purpose') or row.get('Objective') or row.get('Aim') or ''
    provisions = row.get('Provisions') or row.get('Features') or row.get('Key Points') or ''
    
    parts = []
    if act:
        parts.append(f"The {act}")
    if year:
        parts.append(f"was passed in {year}")
    if purpose:
        parts.append(f"to {purpose}")
    if provisions:
        parts.append(f"Key provisions include {provisions}")
    
    return ". ".join(parts) + "." if parts else None

def _apply_generic_geography_template(row: Dict) -> str:
    """Generic template for geography/land use type data."""
    # Try to extract meaningful information from the row
    category = None
    area = None
    percentage = None
    
    # Look for category/name in various possible columns
    for key in row.keys():
        if any(word in key.lower() for word in ["category", "name", "type", "land", "area"]) and not any(word in key.lower() for word in ["area (mh)", "area(mh)"]):
            if row[key] and str(row[key]).strip():
                category = str(row[key]).strip()
                break
    
    # Look for area/quantity in various possible columns
    for key in row.keys():
        if any(word in key.lower() for word in ["area (mh)", "area(mh)", "mh", "hectares", "quantity"]):
            if row[key] and str(row[key]).strip():
                area = str(row[key]).strip()
                break
    
    # Look for percentage in various possible columns
    for key in row.keys():
        if any(word in key.lower() for word in ["percentage", "percent", "%"]) and not any(word in key.lower() for word in ["area (mh)", "area(mh)"]):
            if row[key] and str(row[key]).strip():
                percentage = str(row[key]).strip()
                break
    
    parts = []
    if category:
        parts.append(f"{category}")
    if area:
        parts.append(f"covers {area} million hectares")
    if percentage:
        parts.append(f"({percentage} of total)")
    
    if parts:
        return " ".join(parts) + " of India's land area."
    
    return None

def _apply_generic_economy_template(row: Dict) -> str:
    """Generic template for economy/statistics type data."""
    statistic = None
    sector = None
    data = None
    commentary = None
    
    # Look for statistic name
    for key in row.keys():
        if any(word in key.lower() for word in ["statistic", "name", "indicator", "metric"]):
            if row[key] and str(row[key]).strip():
                statistic = str(row[key]).strip()
                break
    
    # Look for sector
    for key in row.keys():
        if any(word in key.lower() for word in ["sector", "category", "type"]):
            if row[key] and str(row[key]).strip():
                sector = str(row[key]).strip()
                break
    
    # Look for data value
    for key in row.keys():
        if any(word in key.lower() for word in ["data", "value", "amount", "quantity"]):
            if row[key] and str(row[key]).strip():
                data = str(row[key]).strip()
                break
    
    # Look for commentary
    for key in row.keys():
        if any(word in key.lower() for word in ["commentary", "note", "description", "detail"]):
            if row[key] and str(row[key]).strip():
                commentary = str(row[key]).strip()
                break
    
    parts = []
    if statistic:
        parts.append(f"{statistic}")
    if sector:
        parts.append(f"in the {sector} sector")
    if data:
        parts.append(f"shows {data}")
    if commentary:
        parts.append(f"({commentary})")
    
    if parts:
        return " ".join(parts) + "."
    
    return None

def _apply_generic_battle_template(row: Dict) -> str:
    """Generic template for battle/war type data."""
    battle = row.get('Battle') or row.get('War') or row.get('Conflict') or 'battle'
    year = row.get('Year') or row.get('Date') or ''
    parties = row.get('Parties') or row.get('Sides') or row.get('Combatants') or ''
    location = row.get('Location') or row.get('Place') or ''
    outcome = row.get('Outcome') or row.get('Result') or row.get('Consequence') or ''
    
    parts = []
    if battle:
        parts.append(f"The {battle}")
    if year:
        parts.append(f"took place in {year}")
    if parties:
        parts.append(f"between {parties}")
    if location:
        parts.append(f"at {location}")
    if outcome:
        parts.append(f"Outcome: {outcome}")
    
    return ". ".join(parts) + "." if parts else None

def _apply_generic_committee_template(row: Dict) -> str:
    """Generic template for committee/commission type data."""
    committee = row.get('Committee') or row.get('Commission') or row.get('Name') or 'committee'
    year = row.get('Year') or row.get('Established') or ''
    chairperson = row.get('Chairperson') or row.get('Chair') or row.get('Head') or ''
    purpose = row.get('Purpose') or row.get('Objective') or row.get('Aim') or ''
    recommendations = row.get('Recommendations') or row.get('Findings') or row.get('Report') or ''
    
    parts = []
    if committee:
        parts.append(f"The {committee}")
    if year:
        parts.append(f"was established in {year}")
    if chairperson:
        parts.append(f"under {chairperson}")
    if purpose:
        parts.append(f"to {purpose}")
    if recommendations:
        parts.append(f"Key recommendations include {recommendations}")
    
    return ". ".join(parts) + "." if parts else None

def _apply_generic_convention_template(row: Dict) -> str:
    """Generic template for convention/treaty type data."""
    convention = row.get('Convention') or row.get('Treaty') or row.get('Agreement') or 'convention'
    year = row.get('Year') or row.get('Signed') or ''
    parties = row.get('Parties') or row.get('Countries') or row.get('Signatories') or ''
    purpose = row.get('Purpose') or row.get('Objective') or row.get('Aim') or ''
    location = row.get('Location') or row.get('Secretariat') or row.get('Headquarters') or ''
    
    parts = []
    if convention:
        parts.append(f"The {convention}")
    if year:
        parts.append(f"was signed in {year}")
    if parties:
        parts.append(f"between {parties}")
    if purpose:
        parts.append(f"to {purpose}")
    if location:
        parts.append(f"It is headquartered in {location}")
    
    return ". ".join(parts) + "." if parts else None

def _apply_generic_environment_template(row: Dict) -> str:
    """Generic template for environment/biodiversity type data."""
    species = row.get('Species') or row.get('Name') or row.get('Organism') or 'species'
    type_category = row.get('Type') or row.get('Category') or row.get('Classification') or ''
    region = row.get('Region') or row.get('Location') or row.get('Habitat') or ''
    status = row.get('Status') or row.get('IUCN Status') or row.get('Conservation Status') or ''
    significance = row.get('Significance') or row.get('Importance') or row.get('Features') or ''
    
    parts = []
    if species:
        parts.append(f"{species}")
    if type_category:
        parts.append(f"is a {type_category} species")
    if region:
        parts.append(f"found in {region}")
    if status:
        parts.append(f"and is listed as {status}")
    if significance:
        parts.append(f"It is significant for {significance}")
    
    return ". ".join(parts) + "." if parts else None 