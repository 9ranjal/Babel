"""
Text Polisher using T5 Transformer for sentence completion and grammar correction.
"""

import re
import time
from typing import Dict, List, Tuple, Optional
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import logging

logger = logging.getLogger(__name__)

class TextPolisher:
    """
    Polishes chunk text using T5 transformer for better sentence structure and grammar.
    Supports both individual and batch processing for optimal performance.
    """
    
    def __init__(self, model_name: str = "google/flan-t5-base", use_large_for_low_confidence: bool = True, batch_size: int = 8):
        """
        Initialize the text polisher with T5 model.
        
        Args:
            model_name: T5 model to use for text polishing
            use_large_for_low_confidence: Whether to use large model for low confidence chunks
            batch_size: Batch size for batch processing (8-16 recommended)
        """
        self.model_name = model_name
        self.use_large_for_low_confidence = use_large_for_low_confidence
        self.batch_size = batch_size
        self.large_polisher = None
        
        try:
            self.polisher = pipeline(
                "text2text-generation", 
                model=model_name,
                max_length=150,  # Increased for base model
                do_sample=False
            )
            logger.info(f"✅ Text polisher initialized with {model_name} (batch_size={batch_size})")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize T5 polisher: {e}")
            self.polisher = None
    
    def polish_sentence(self, text: str) -> str:
        """
        Polish a single sentence to make it grammatically correct and complete.
        
        Args:
            text: Raw chunk text to polish
            
        Returns:
            Polished sentence
        """
        if not text or not self.polisher:
            return text
        
        try:
            # Clean up common issues first
            cleaned_text = self._pre_clean(text)
            
            # Check for broken patterns that need deeper rewriting
            if self._needs_deeper_rewrite(cleaned_text):
                return self._deep_rewrite(cleaned_text)
            
            # Create polishing prompt with input sanitization
            sanitized_text = self._sanitize_for_prompt(cleaned_text)
            prompt = f"Convert to a grammatically correct and complete sentence: {sanitized_text}"
            
            # Generate polished text
            result = self.polisher(prompt, max_length=150, do_sample=False)
            polished = result[0]['generated_text'].strip()
            
            # Post-clean the result
            final_text = self._post_clean(polished)
            
            logger.debug(f"Polished: '{text}' → '{final_text}'")
            return final_text
            
        except Exception as e:
            logger.warning(f"⚠️ Text polishing failed for '{text}': {e}")
            return text
    
    def _pre_clean(self, text: str) -> str:
        """
        Pre-clean text before polishing.
        
        Args:
            text: Raw text
            
        Returns:
            Pre-cleaned text
        """
        # Remove trailing punctuation artifacts
        text = re.sub(r'\.\.\s*$', '.', text)
        text = re.sub(r'\(\s*\)\s*$', '', text)
        text = re.sub(r'\.\s*\.\s*$', '.', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Fix common abbreviations
        text = re.sub(r'\bFY(\d+)\b', r'FY \1', text)
        text = re.sub(r'\bQ(\d+)\b', r'Q\1', text)
        
        # Fix repeated periods in titles or abbreviations
        text = re.sub(r'\b([A-Z])\.\s*([A-Z])\.', r'\1. \2.', text)  # e.g., U.S. → U.S.
        
        return text
    
    def _post_clean(self, text: str) -> str:
        """
        Post-clean polished text.
        
        Args:
            text: Polished text
            
        Returns:
            Post-cleaned text
        """
        # Ensure proper sentence ending
        if text and not text.endswith(('.', '!', '?')):
            text += '.'
        
        # Remove double punctuation
        text = re.sub(r'\.+', '.', text)
        text = re.sub(r'!\s*!', '!', text)
        text = re.sub(r'\?\s*\?', '?', text)
        
        # Fix spacing around punctuation
        text = re.sub(r'\s+([.!?])', r'\1', text)
        
        # Normalize quotes
        text = text.replace(""", "\"").replace(""", "\"")
        text = text.replace("'", "'").replace("'", "'")
        
        return text.strip()
    
    def _sanitize_for_prompt(self, text: str) -> str:
        """
        Sanitize text for safe prompt injection.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text safe for prompt injection
        """
        # Escape newlines and quotes
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = text.replace('"', '\\"').replace("'", "\\'")
        
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        # Limit length to prevent prompt overflow
        if len(text) > 800:  # Increased for base model
            text = text[:800] + "..."
        
        return text.strip()
    
    def estimate_confidence(self, original: str, polished: str) -> float:
        """
        Estimate confidence score based on polishing quality.
        
        Args:
            original: Original text
            polished: Polished text
            
        Returns:
            Confidence score (0.0-1.0)
        """
        if not original or not polished:
            return 0.5
        
        # Calculate similarity (simple Levenshtein-based)
        similarity = self._calculate_similarity(original, polished)
        
        # Check for improvements
        improvements = self._count_improvements(original, polished)
        
        # Check for entity preservation
        entity_penalty = self._check_entity_preservation(original, polished)
        
        # Check for length sanity
        length_penalty = self._check_length_sanity(original, polished)
        
        # Base confidence on similarity and improvements, with penalties
        confidence = min(0.9, similarity + (improvements * 0.1) - entity_penalty - length_penalty)
        
        return max(0.1, confidence)
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0.0-1.0)
        """
        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.5
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.5
    
    def _count_improvements(self, original: str, polished: str) -> int:
        """
        Count improvements in polished text.
        
        Args:
            original: Original text
            polished: Polished text
            
        Returns:
            Number of improvements
        """
        improvements = 0
        
        # Check for proper sentence ending
        if not original.endswith(('.', '!', '?')) and polished.endswith(('.', '!', '?')):
            improvements += 1
        
        # Check for proper capitalization
        if polished and polished[0].isupper():
            improvements += 1
        
        # Check for verb presence
        if any(word in polished.lower() for word in ['is', 'are', 'was', 'were', 'has', 'have', 'had', 'does', 'did', 'will', 'can', 'should']):
            improvements += 1
        
        # Check for reduced artifacts
        if original.count('..') > polished.count('..'):
            improvements += 1
        
        if original.count('()') > polished.count('()'):
            improvements += 1
        
        return improvements
    
    def _check_entity_preservation(self, original: str, polished: str) -> float:
        """
        Check if named entities are preserved in polished text.
        
        Args:
            original: Original text
            polished: Polished text
            
        Returns:
            Penalty score (0.0-0.3) for entity loss
        """
        # Extract potential named entities (words starting with capital letters)
        original_entities = set(word for word in original.split() 
                              if word[0].isupper() and len(word) > 2)
        polished_entities = set(word for word in polished.split() 
                              if word[0].isupper() and len(word) > 2)
        
        # Check for entity loss
        lost_entities = original_entities - polished_entities
        
        # Penalty based on percentage of entities lost
        if original_entities:
            loss_ratio = len(lost_entities) / len(original_entities)
            return min(0.3, loss_ratio * 0.3)  # Max 0.3 penalty
        
        return 0.0
    
    def _check_length_sanity(self, original: str, polished: str) -> float:
        """
        Check if polished text maintains reasonable length.
        
        Args:
            original: Original text
            polished: Polished text
            
        Returns:
            Penalty score (0.0-0.2) for length issues
        """
        original_words = len(original.split())
        polished_words = len(polished.split())
        
        if original_words == 0:
            return 0.0
        
        # Check if polished is too short (less than 50% of original)
        if polished_words < 0.5 * original_words:
            return 0.2  # Significant penalty for truncation
        
        # Check if polished is too long (more than 200% of original)
        if polished_words > 2.0 * original_words:
            return 0.1  # Minor penalty for over-expansion
        
        return 0.0
    
    def _needs_deeper_rewrite(self, text: str) -> bool:
        """
        Check if text needs deeper rewriting due to broken patterns.
        
        Args:
            text: Text to check
            
        Returns:
            True if deeper rewriting is needed
        """
        text_lower = text.lower()
        
        # Broken patterns that indicate deeper issues
        broken_patterns = [
            "believed in advocate",
            "believed in on",
            "believed in championed",
            "believed in fought",
            "believed in led",
            "believed in used",
            "believed in promoted",
            "believed in worked",
            "believed in established",
            "believed in founded",
            "believed in created",
            "believed in developed",
            "believed in introduced",
            "believed in implemented",
            "believed in advocated",
            "believed in supported",
            "believed in focused",
            "believed in emphasized",
            "believed in stressed",
            "believed in highlighted"
        ]
        
        return any(pattern in text_lower for pattern in broken_patterns)
    
    def _deep_rewrite(self, text: str) -> str:
        """
        Perform deeper rewriting for broken patterns.
        
        Args:
            text: Text to rewrite
            
        Returns:
            Deeply rewritten text
        """
        try:
            # Create a more specific rewrite prompt
            sanitized_text = self._sanitize_for_prompt(text)
            prompt = f"Rewrite this sentence clearly and grammatically, fixing any awkward phrasing: {sanitized_text}"
            
            # Generate rewritten text
            result = self.polisher(prompt, max_length=200, do_sample=False)  # Longer for complex rewrites
            rewritten = result[0]['generated_text'].strip()
            
            # Post-clean the result
            final_text = self._post_clean(rewritten)
            
            logger.debug(f"Deep rewrite: '{text}' → '{final_text}'")
            return final_text
            
        except Exception as e:
            logger.warning(f"⚠️ Deep rewrite failed for '{text}': {e}")
            return text
    
    def polish_chunk(self, text: str) -> Tuple[str, float]:
        """
        Polish a chunk of text and return with confidence score.
        
        Args:
            text: Text to polish
            
        Returns:
            Tuple of (polished_text, confidence_score)
        """
        start_time = time.time()
        
        polished = self.polish_sentence(text)
        confidence = self.estimate_confidence(text, polished)
        
        # If confidence is low and large model is enabled, try again with large model
        if (confidence <= 0.88 and self.use_large_for_low_confidence and 
            self._should_use_large_model(text)):
            polished = self._polish_with_large_model(text)
            confidence = self.estimate_confidence(text, polished)
        
        duration = time.time() - start_time
        if duration > 1.0:  # Log slow polishing operations
            logger.debug(f"⚠️ Slow text polishing: {duration:.2f}s for {len(text)} chars")
        
        return polished, confidence
    
    def polish_batch(self, texts: List[str], enable_heuristic_skip: bool = True) -> List[Tuple[str, float]]:
        """
        Polish a batch of texts for improved performance.
        
        Args:
            texts: List of texts to polish
            enable_heuristic_skip: Whether to skip texts that are already clean
            
        Returns:
            List of (polished_text, confidence_score) tuples
        """
        if not texts or not self.polisher:
            return [(text, 0.75) for text in texts]
        
        start_time = time.time()
        results = []
        
        # Group texts by whether they need processing
        to_process = []
        to_skip = []
        
        for i, text in enumerate(texts):
            if enable_heuristic_skip and self._is_clean_sentence(text):
                to_skip.append((i, text, 0.85))  # High confidence for clean sentences
            else:
                to_process.append((i, text))
        
        logger.debug(f"📦 Batch processing: {len(to_process)} to polish, {len(to_skip)} skipped")
        
        # Process texts that need polishing in batches
        processed_results = {}
        
        if to_process:
            # Split into smaller batches for T5 processing
            for batch_start in range(0, len(to_process), self.batch_size):
                batch_end = min(batch_start + self.batch_size, len(to_process))
                batch_items = to_process[batch_start:batch_end]
                
                # Extract texts and create prompts
                batch_texts = [item[1] for item in batch_items]
                batch_prompts = []
                
                for text in batch_texts:
                    cleaned_text = self._pre_clean(text)
                    sanitized_text = self._sanitize_for_prompt(cleaned_text)
                    
                    if self._needs_deeper_rewrite(cleaned_text):
                        prompt = f"Rewrite this sentence clearly and grammatically, fixing any awkward phrasing: {sanitized_text}"
                    else:
                        prompt = f"Convert to a grammatically correct and complete sentence: {sanitized_text}"
                    
                    batch_prompts.append(prompt)
                
                # Process batch through T5
                try:
                    batch_results = self.polisher(batch_prompts, max_length=150, do_sample=False, batch_size=len(batch_prompts))
                    
                    # Process results
                    for (orig_idx, orig_text), result in zip(batch_items, batch_results):
                        polished = self._post_clean(result['generated_text'].strip())
                        confidence = self.estimate_confidence(orig_text, polished)
                        processed_results[orig_idx] = (polished, confidence)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Batch polishing failed: {e}")
                    # Fallback to individual processing
                    for orig_idx, orig_text in batch_items:
                        try:
                            polished = self.polish_sentence(orig_text)
                            confidence = self.estimate_confidence(orig_text, polished)
                            processed_results[orig_idx] = (polished, confidence)
                        except:
                            processed_results[orig_idx] = (orig_text, 0.5)
        
        # Combine results in original order
        final_results = [None] * len(texts)
        
        # Add skipped results
        for orig_idx, text, confidence in to_skip:
            final_results[orig_idx] = (text, confidence)
        
        # Add processed results
        for orig_idx, (polished, confidence) in processed_results.items():
            final_results[orig_idx] = (polished, confidence)
        
        duration = time.time() - start_time
        throughput = len(texts) / duration if duration > 0 else 0
        
        logger.debug(f"📊 Batch polishing complete: {len(texts)} texts in {duration:.2f}s ({throughput:.1f} texts/sec)")
        
        return final_results
    
    def _is_clean_sentence(self, text: str) -> bool:
        """
        Heuristic to determine if a sentence is already clean and doesn't need polishing.
        
        Args:
            text: Text to check
            
        Returns:
            True if text appears clean and grammatical
        """
        if not text or len(text.strip()) < 10:
            return False
        
        text = text.strip()
        
        # Check for good sentence structure
        has_good_ending = text.endswith(('.', '!', '?'))
        has_good_start = text[0].isupper()
        has_verb = any(word in text.lower() for word in [
            'is', 'are', 'was', 'were', 'has', 'have', 'had', 'does', 'did', 
            'will', 'can', 'should', 'would', 'could', 'established', 'created',
            'developed', 'implemented', 'founded', 'led', 'advocated', 'promoted'
        ])
        
        # Check for problematic patterns
        has_broken_patterns = any(pattern in text.lower() for pattern in [
            'believed in advocate', 'believed in on', 'believed in fought',
            '..', '()', 'shows that', 'includes that', 'examples that'
        ])
        
        # Word count check (sentences with 30+ words are usually complete)
        word_count = len(text.split())
        is_substantial = word_count >= 30
        
        # Must be substantial OR have good structure without broken patterns
        is_clean = (is_substantial or (has_good_ending and has_good_start and has_verb)) and not has_broken_patterns
        
        if is_clean:
            logger.debug(f"✅ Skipping clean sentence: {text[:50]}...")
        
        return is_clean
    
    def _should_use_large_model(self, text: str) -> bool:
        """
        Determine if text should use large model for better processing.
        
        Args:
            text: Text to analyze
            
        Returns:
            True if large model should be used
        """
        # Use large model for complex content
        text_lower = text.lower()
        
        # Geography/climate content (often complex)
        if any(word in text_lower for word in ['climate', 'geography', 'savanna', 'tropical', 'temperature', 'rainfall']):
            return True
        
        # Long unstructured lists
        if len(text.split()) > 50:
            return True
        
        # Stat-heavy content
        if text.count('%') > 2 or text.count('degree') > 2:
            return True
        
        return False
    
    def _polish_with_large_model(self, text: str) -> str:
        """
        Polish text using the large T5 model for better quality.
        
        Args:
            text: Text to polish
            
        Returns:
            Polished text from large model
        """
        try:
            # Lazy load large model
            if self.large_polisher is None:
                self.large_polisher = pipeline(
                    "text2text-generation",
                    model="google/flan-t5-large",
                    max_length=200,
                    do_sample=False
                )
                logger.info("✅ Large T5 model loaded for complex content")
            
            # Clean and sanitize
            cleaned_text = self._pre_clean(text)
            sanitized_text = self._sanitize_for_prompt(cleaned_text)
            
            # Use more specific prompt for large model
            prompt = f"Rewrite this text clearly and grammatically, improving flow and coherence: {sanitized_text}"
            
            # Generate with large model
            result = self.large_polisher(prompt, max_length=200, do_sample=False)
            polished = result[0]['generated_text'].strip()
            
            # Post-clean
            final_text = self._post_clean(polished)
            
            logger.debug(f"Large model polish: '{text}' → '{final_text}'")
            return final_text
            
        except Exception as e:
            logger.warning(f"⚠️ Large model polishing failed for '{text}': {e}")
            return text

def polish_chunk_text(text: str, polisher: Optional[TextPolisher] = None) -> Tuple[str, float]:
    """
    Polish chunk text and return confidence score.
    
    Args:
        text: Text to polish
        polisher: TextPolisher instance (will create if None)
        
    Returns:
        Tuple of (polished_text, confidence_score)
    """
    if not polisher:
        polisher = TextPolisher()
    
    return polisher.polish_chunk(text)
