"""
Parallel glossary processing utilities for improved performance.
"""

import re
import time
from typing import Dict, List, Tuple, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import threading

class ParallelGlossaryProcessor:
    """
    Thread-safe parallel glossary processor for high-performance term expansion.
    """
    
    def __init__(self, glossary_map: Dict[str, str], max_workers: int = 4):
        """
        Initialize parallel glossary processor.
        
        Args:
            glossary_map: Dictionary mapping terms to definitions
            max_workers: Maximum number of worker threads
        """
        self.glossary_map = glossary_map
        self.max_workers = max_workers
        self.lock = threading.Lock()
        
        # Pre-compile regex patterns for better performance
        self._compile_patterns()
        
        # Statistics
        self.stats = {
            "processed_chunks": 0,
            "total_matches": 0,
            "total_time": 0.0
        }
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for all glossary terms."""
        self.term_patterns = {}
        
        for term in self.glossary_map.keys():
            # Create case-insensitive word boundary pattern
            pattern = rf'\b{re.escape(term)}\b'
            try:
                self.term_patterns[term] = re.compile(pattern, re.IGNORECASE)
            except re.error:
                # Skip terms that can't be compiled as regex
                continue
    
    def process_batch(self, texts: List[str], enable_injection: bool = False) -> List[Tuple[str, Dict]]:
        """
        Process a batch of texts for glossary matching in parallel.
        
        Args:
            texts: List of texts to process
            enable_injection: Whether to inject definitions into text (slow)
            
        Returns:
            List of (processed_text, metadata) tuples
        """
        start_time = time.time()
        
        if not texts:
            return []
        
        # Process in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit tasks
            future_to_index = {
                executor.submit(self._process_single_text, text, enable_injection): i
                for i, text in enumerate(texts)
            }
            
            # Collect results in order
            results = [None] * len(texts)
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    results[index] = future.result()
                except Exception as e:
                    # Handle errors gracefully
                    logger.warning(f"Error processing glossary for text {index}: {e}")
                    results[index] = (texts[index], {})  # Return empty metadata
        
        # Update statistics
        total_processed = len(texts)
        
        # Log progress
        logger.info(f"✅ Parallel processing complete: {total_processed} texts processed")
        
        return results
    
    def _process_single_text(self, text: str, enable_injection: bool) -> Tuple[str, Dict]:
        """
        Process a single text (glossary processing disabled).
        
        Args:
            text: Text to process
            enable_injection: Whether to inject definitions (ignored)
            
        Returns:
            Tuple of (processed_text, metadata)
        """
        if not text or not text.strip():
            return text, {}
        
        # Glossary processing disabled - return original text with empty metadata
        return text, {}
    
    def get_statistics(self) -> Dict:
        """Get processing statistics."""
        with self.lock:
            stats = self.stats.copy()
            
        if stats["processed_chunks"] > 0 and stats["total_time"] > 0:
            stats["avg_chunks_per_second"] = stats["processed_chunks"] / stats["total_time"]
        else:
            stats["avg_chunks_per_second"] = 0
        
        return stats

class FastAcronymExpander:
    """
    High-performance acronym expansion using precompiled patterns.
    """
    
    def __init__(self, acronym_map: Dict[str, str]):
        """
        Initialize acronym expander.
        
        Args:
            acronym_map: Dictionary mapping acronyms to full forms
        """
        self.acronym_map = acronym_map
        self._compile_acronym_patterns()
    
    def _compile_acronym_patterns(self):
        """Compile regex patterns for acronym matching."""
        self.acronym_patterns = {}
        
        # Sort by length (longer first) to avoid partial matches
        sorted_acronyms = sorted(self.acronym_map.keys(), key=len, reverse=True)
        
        for acronym in sorted_acronyms:
            # Match whole word acronyms
            pattern = rf'\b{re.escape(acronym)}\b'
            try:
                self.acronym_patterns[acronym] = re.compile(pattern)
            except re.error:
                continue
    
    @lru_cache(maxsize=1000)
    def expand_text(self, text: str) -> Tuple[str, List[str]]:
        """
        Expand acronyms in text with caching for repeated patterns.
        
        Args:
            text: Text to process
            
        Returns:
            Tuple of (expanded_text, list_of_expansions)
        """
        if not text:
            return text, []
        
        expanded_text = text
        expansions = []
        
        for acronym, full_form in self.acronym_map.items():
            pattern = self.acronym_patterns.get(acronym)
            if not pattern:
                continue
            
            if pattern.search(expanded_text):
                # Replace first occurrence with full form
                replacement = f"{acronym} ({full_form})"
                expanded_text = pattern.sub(replacement, expanded_text, count=1)
                expansions.append(f"{acronym} → {full_form}")
        
        return expanded_text, expansions

# Factory function for easy integration
def create_parallel_glossary_processor(glossary_map: Dict[str, str], 
                                     max_workers: int = 4) -> ParallelGlossaryProcessor:
    """
    Create a parallel glossary processor with optimal settings.
    
    Args:
        glossary_map: Glossary terms and definitions
        max_workers: Number of worker threads
        
    Returns:
        Configured ParallelGlossaryProcessor
    """
    return ParallelGlossaryProcessor(glossary_map, max_workers)

def create_fast_acronym_expander(acronym_map: Dict[str, str]) -> FastAcronymExpander:
    """
    Create a fast acronym expander.
    
    Args:
        acronym_map: Acronym mappings
        
    Returns:
        Configured FastAcronymExpander
    """
    return FastAcronymExpander(acronym_map)
