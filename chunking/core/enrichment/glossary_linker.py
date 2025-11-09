"""
Glossary Linker for mapping chunk text to glossary terms.
"""

import re
from typing import Dict, List, Set, Optional
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)

class GlossaryLinker:
    """
    Links chunk text to glossary terms using fuzzy matching.
    """
    
    def __init__(self, glossary_terms: Optional[Dict[str, str]] = None):
        """
        Initialize glossary linker.
        
        Args:
            glossary_terms: Dictionary of term -> definition mappings
        """
        self.glossary_terms = glossary_terms or {}
        self._build_term_index()
        logger.info(f"✅ Glossary linker initialized with {len(self.glossary_terms)} terms")
    
    def _build_term_index(self):
        """Build index for efficient term matching."""
        self.term_index = {}
        for term, definition in self.glossary_terms.items():
            # Store normalized term
            normalized = term.lower().strip()
            self.term_index[normalized] = {
                'original': term,
                'definition': definition
            }
    
    def map_to_glossary_terms(self, chunk_text: str, threshold: float = 0.8) -> List[str]:
        """
        Map chunk text to glossary terms using fuzzy matching.
        
        Args:
            chunk_text: Text to analyze
            threshold: Similarity threshold for matching
            
        Returns:
            List of matched glossary terms
        """
        if not chunk_text or not self.glossary_terms:
            return []
        
        matches = []
        chunk_lower = chunk_text.lower()
        
        for term, term_data in self.term_index.items():
            # Check for exact substring match first
            if term in chunk_lower:
                matches.append(term_data['original'])
                continue
            
            # Check for word boundary matches
            if self._word_boundary_match(term, chunk_lower):
                matches.append(term_data['original'])
                continue
            
            # Fuzzy matching for similar terms
            similarity = self._calculate_similarity(term, chunk_lower)
            if similarity >= threshold:
                matches.append(term_data['original'])
        
        # Remove duplicates while preserving order
        unique_matches = []
        seen = set()
        for match in matches:
            if match not in seen:
                unique_matches.append(match)
                seen.add(match)
        
        logger.debug(f"Found {len(unique_matches)} glossary matches in: '{chunk_text[:50]}...'")
        return unique_matches
    
    def _word_boundary_match(self, term: str, text: str) -> bool:
        """
        Check for word boundary matches.
        
        Args:
            term: Term to match
            text: Text to search in
            
        Returns:
            True if term is found with word boundaries
        """
        # Split term into words
        term_words = term.split()
        if len(term_words) == 1:
            # Single word - check for word boundaries
            pattern = r'\b' + re.escape(term) + r'\b'
            return bool(re.search(pattern, text))
        else:
            # Multi-word term - check if all words are present
            return all(word in text for word in term_words)
    
    def _calculate_similarity(self, term: str, text: str) -> float:
        """
        Calculate similarity between term and text.
        
        Args:
            term: Term to match
            text: Text to search in
            
        Returns:
            Similarity score (0.0-1.0)
        """
        # Use SequenceMatcher for similarity
        return SequenceMatcher(None, term, text).ratio()
    
    def get_glossary_matches(self, chunk_text: str) -> List[Dict[str, str]]:
        """
        Get detailed glossary matches with definitions.
        
        Args:
            chunk_text: Text to analyze
            
        Returns:
            List of dictionaries with term and definition
        """
        matched_terms = self.map_to_glossary_terms(chunk_text)
        matches = []
        
        for term in matched_terms:
            # Find the definition
            for normalized_term, term_data in self.term_index.items():
                if term_data['original'] == term:
                    matches.append({
                        'term': term,
                        'definition': term_data['definition'],
                        'source': 'glossary_linker'
                    })
                    break
        
        return matches

def create_glossary_from_chunks(chunks: List[Dict]) -> Dict[str, str]:
    """
    Create a glossary from existing chunks that contain definitions.
    
    Args:
        chunks: List of chunk dictionaries
        
    Returns:
        Dictionary of term -> definition mappings
    """
    glossary = {}
    
    for chunk in chunks:
        text = chunk.get('chunk_text', '')
        
        # Look for definition patterns
        if 'is defined as' in text.lower() or 'refers to' in text.lower():
            # Extract term and definition
            term_def = extract_term_definition(text)
            if term_def:
                term, definition = term_def
                glossary[term] = definition
    
    logger.info(f"✅ Created glossary with {len(glossary)} terms from chunks")
    return glossary

def extract_term_definition(text: str) -> Optional[tuple]:
    """
    Extract term and definition from text.
    
    Args:
        text: Text containing definition
        
    Returns:
        Tuple of (term, definition) or None
    """
    # Common definition patterns
    patterns = [
        r'^([^.]*?)\s+is\s+defined\s+as\s+(.+?)(?:\.|$)',
        r'^([^.]*?)\s+refers\s+to\s+(.+?)(?:\.|$)',
        r'^([^.]*?)\s+means\s+(.+?)(?:\.|$)',
        r'^([^.]*?)\s*:\s*(.+?)(?:\.|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            term = match.group(1).strip()
            definition = match.group(2).strip()
            
            # Clean up the term and definition
            term = re.sub(r'^[^a-zA-Z]*', '', term)  # Remove leading non-letters
            term = re.sub(r'[^a-zA-Z]*$', '', term)  # Remove trailing non-letters
            
            if term and definition and len(term) > 2:
                return (term, definition)
    
    return None

def map_chunk_to_glossary(chunk_text: str, glossary_terms: Dict[str, str]) -> List[str]:
    """
    Map a single chunk to glossary terms.
    
    Args:
        chunk_text: Text to analyze
        glossary_terms: Dictionary of term -> definition mappings
        
    Returns:
        List of matched glossary terms
    """
    linker = GlossaryLinker(glossary_terms)
    return linker.map_to_glossary_terms(chunk_text)

