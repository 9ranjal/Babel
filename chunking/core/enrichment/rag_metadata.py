"""
RAG Metadata Enhancement for chunks.
"""

import re
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

def enhance_rag_metadata(chunk: Dict) -> Dict:
    """
    Enhance chunk with RAG-ready metadata.
    
    Args:
        chunk: Chunk dictionary to enhance
        
    Returns:
        Enhanced chunk with RAG metadata
    """
    text = chunk.get('chunk_text', '')
    if not text:
        return chunk
    
    # Analyze text for RAG metadata
    is_complete = _is_complete_sentence(text)
    has_numeric = _has_numeric_statistics(text)
    primary_entity = _extract_primary_entity(text)
    retrieval_score = _calculate_retrieval_score(chunk, text)
    
    # Ensure nested retrieval_metadata exists
    rm = chunk.get('retrieval_metadata') or {}
    rm['retrieval_score'] = retrieval_score
    # Derive compact retrieval keywords (≤5)
    try:
        from .enhancer import extract_retrieval_keywords
        kws = extract_retrieval_keywords(chunk)
    except Exception:
        kws = []
    rm['retrieval_keywords'] = (kws or [])[:5]
    if primary_entity:
        rm['primary_entity'] = primary_entity
    chunk['retrieval_metadata'] = rm

    # Lightweight QA hints at top-level for backward compatibility
    chunk['is_complete_sentence'] = is_complete
    chunk['has_numeric_stat'] = has_numeric
    
    return chunk

def _is_complete_sentence(text: str) -> bool:
    """
    Check if text is a complete sentence.
    
    Args:
        text: Text to analyze
        
    Returns:
        True if text appears to be a complete sentence
    """
    # Basic sentence completeness checks
    if not text:
        return False
    
    # Should start with capital letter
    if not text[0].isupper():
        return False
    
    # Should end with sentence-ending punctuation
    if not text.rstrip().endswith(('.', '!', '?')):
        return False
    
    # Should have a verb (basic check)
    words = text.lower().split()
    verbs = ['is', 'are', 'was', 'were', 'has', 'have', 'had', 'does', 'did', 'will', 'can', 'should', 'would', 'could', 'may', 'might']
    has_verb = any(verb in words for verb in verbs)
    
    # Should have reasonable length
    reasonable_length = 3 <= len(words) <= 200
    
    return has_verb and reasonable_length

def _has_numeric_statistics(text: str) -> bool:
    """
    Check if text contains numerical statistics.
    
    Args:
        text: Text to analyze
        
    Returns:
        True if text contains numerical data
    """
    # Look for percentage signs
    if '%' in text:
        return True
    
    # Look for numbers followed by units
    number_patterns = [
        r'\d+\.?\d*\s*(million|billion|trillion|thousand|hundred)',
        r'\d+\.?\d*\s*(percent|%|degree|°|inch|cm|km|miles)',
        r'\d+\.?\d*\s*(FY\d+|Q\d+)',  # Fiscal year, quarter
        r'\d{4}',  # Years
        r'\d+\.?\d*\s*(tonnes?|kg|grams?)',  # Weight units
    ]
    
    for pattern in number_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False

def _extract_primary_entity(text: str) -> Optional[str]:
    """
    Extract the primary entity from text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Primary entity name or None
    """
    # Look for named entities (words starting with capital letters)
    words = text.split()
    entities = []
    
    for word in words:
        # Clean the word
        clean_word = re.sub(r'[^\w]', '', word)
        if len(clean_word) > 2 and clean_word[0].isupper():
            entities.append(clean_word)
    
    if not entities:
        return None
    
    # Return the first significant entity
    # Prioritize person names, places, organizations
    for entity in entities:
        if entity.lower() not in ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'into', 'during', 'including', 'until', 'against', 'among', 'throughout', 'despite', 'towards', 'upon', 'concerning', 'about', 'like', 'through', 'over', 'before', 'between', 'after', 'since', 'without', 'under', 'within', 'along', 'following', 'across', 'behind', 'beyond', 'toward', 'up', 'out', 'down', 'off', 'above', 'near', 'except', 'below', 'beneath', 'beside', 'beyond', 'inside', 'outside', 'onto', 'upon', 'underneath', 'alongside', 'amid', 'amongst', 'around', 'before', 'behind', 'below', 'beneath', 'beside', 'between', 'beyond', 'inside', 'outside', 'throughout', 'underneath', 'within', 'without']:
            return entity
    
    return entities[0] if entities else None

def _calculate_retrieval_score(chunk: Dict, text: str) -> float:
    """
    Calculate retrieval score for RAG.
    
    Args:
        chunk: Chunk dictionary
        text: Chunk text
        
    Returns:
        Retrieval score (0.0-1.0)
    """
    score = 0.5  # Base score
    
    # Boost for complete sentences
    if _is_complete_sentence(text):
        score += 0.2
    
    # Boost for having numeric statistics
    if _has_numeric_statistics(text):
        score += 0.1
    
    # Boost for having a primary entity
    if _extract_primary_entity(text):
        score += 0.1
    
    # Boost for source confidence
    source_confidence = chunk.get('source_confidence_score', 0.5)
    score += source_confidence * 0.1
    
    # Boost for chunk quality
    chunk_quality = chunk.get('chunk_quality', 'ok')
    if chunk_quality == 'good':
        score += 0.1
    elif chunk_quality == 'poor':
        score -= 0.1
    
    # Penalty for very short or very long chunks
    word_count = len(text.split())
    if word_count < 5:
        score -= 0.1
    elif word_count > 100:
        score -= 0.05
    
    return max(0.0, min(1.0, score))

def enhance_chunks_batch(chunks: List[Dict]) -> List[Dict]:
    """
    Enhance a batch of chunks with RAG metadata.
    
    Args:
        chunks: List of chunk dictionaries
        
    Returns:
        List of enhanced chunks
    """
    enhanced_chunks = []
    
    for chunk in chunks:
        try:
            enhanced_chunk = enhance_rag_metadata(chunk)
            enhanced_chunks.append(enhanced_chunk)
        except Exception as e:
            logger.warning(f"⚠️ Failed to enhance chunk {chunk.get('chunk_id', 'unknown')}: {e}")
            enhanced_chunks.append(chunk)  # Keep original if enhancement fails
    
    logger.info(f"✅ Enhanced {len(enhanced_chunks)} chunks with RAG metadata")
    return enhanced_chunks

