"""
Base post-processor class for chunk text enhancement.
Provides common functionality that can be extended for different file types.
"""

import re
from typing import Dict, List, Tuple, Optional, Any
from abc import ABC, abstractmethod

class BaseChunkPostProcessor(ABC):
    """
    Base class for chunk post-processing with common functionality.
    
    Handles:
    1. Glossary term injection
    2. Acronym/entity expansion
    3. Context-dead chunk detection
    4. Semantic type classification
    5. Quality assessment
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the base post-processor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Common glossary mappings (can be overridden by subclasses)
        self.glossary_map = self._get_glossary_map()
        
        # Common entity mappings (can be overridden by subclasses)
        self.entity_map = self._get_entity_map()
        
        # Quality thresholds
        self.min_confidence = self.config.get("min_confidence", 0.7)
        self.min_word_count = self.config.get("min_word_count", 3)
        self.max_word_count = self.config.get("max_word_count", 500)
    
    @abstractmethod
    def _get_glossary_map(self) -> Dict[str, str]:
        """Get glossary mappings for this processor type."""
        return {}
    
    @abstractmethod
    def _get_entity_map(self) -> Dict[str, str]:
        """Get entity mappings for this processor type."""
        return {}
    
    def process(self, text: str, metadata: Optional[Dict] = None, context: Optional[Dict] = None) -> Tuple[str, Dict]:
        """
        Process chunk text through the complete post-processing pipeline.
        
        Args:
            text: Raw chunk text
            metadata: Chunk metadata for context
            context: Additional context (file info, row data, etc.)
            
        Returns:
            Tuple of (processed_text, processing_metadata)
        """
        # Strict type handling at base level; subclasses may override for leniency
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        if not text.strip():
            return "", self._create_empty_metadata()
        
        # Track processing steps (optional)
        from ..config import INCLUDE_PROCESSING_STEPS
        processing_steps = [] if INCLUDE_PROCESSING_STEPS else None
        
        # 1. Pre-processing (subclass-specific)
        processed_text = self._pre_process(text, context)
        if processing_steps is not None:
            processing_steps.append("pre_process")
        
        # 2. Inject glossary definitions (DISABLED - causes chunk bloat and poor embeddings)
        # processed_text, glossary_hits = self._inject_glossary(processed_text)
        # Skip injection, keep tracking for analysis only
        # processing_steps.append("glossary_injection")
        
        # 3. Normalize entities and acronyms
        processed_text, entities_expanded = self._normalize_entities(processed_text or "")
        if processing_steps is not None:
            processing_steps.append("entity_normalization")
        
        # 4. Post-processing (subclass-specific)
        processed_text = self._post_process(processed_text or "", context)
        if processing_steps is not None:
            processing_steps.append("post_process")
        
        # 5. Classify semantic type
        semantic_classification = self._classify_chunk_pattern(processed_text)
        semantic_type = semantic_classification["semantic_type"]
        semantic_reasoning = semantic_classification["reasoning"]
        semantic_confidence = semantic_classification["confidence"]
        if processing_steps is not None:
            processing_steps.append("semantic_classification")
        
        # 6. Assess quality and detect context-dead chunks
        quality_metrics = self._assess_quality(processed_text, metadata, context)
        if processing_steps is not None:
            processing_steps.append("quality_assessment")
        
        # 7. Build comprehensive metadata using schema
        from ..schema import create_chunk_from_template, update_chunk_field
        
        # Create base chunk with schema
        processing_metadata = create_chunk_from_template()
        
        # Update with processing results
        processing_metadata = update_chunk_field(processing_metadata, "semantic_type.primary", semantic_type)
        processing_metadata = update_chunk_field(processing_metadata, "semantic_type.reasoning", semantic_reasoning)
        processing_metadata = update_chunk_field(processing_metadata, "semantic_type.confidence", semantic_confidence)
        processing_metadata = update_chunk_field(processing_metadata, "semantic_type.secondary_tags", semantic_classification.get("secondary_tags", []))
        processing_metadata = update_chunk_field(processing_metadata, "semantic_type.question_affinity", semantic_classification.get("question_affinity", []))
        if processing_steps is not None:
            processing_metadata = update_chunk_field(processing_metadata, "qa_metadata.processing_steps", processing_steps)
        # DISABLED: Glossary miss detection produces nonsensical matches (e.g. environmental terms for political content)
        # processing_metadata = update_chunk_field(processing_metadata, "qa_metadata.glossary_misses", self._find_glossary_misses(processed_text))
        processing_metadata = update_chunk_field(processing_metadata, "qa_metadata.entities_expanded", entities_expanded)
        processing_metadata = update_chunk_field(processing_metadata, "qa_metadata.confidence_score", quality_metrics.get("confidence_score", 0.5))
        processing_metadata = update_chunk_field(processing_metadata, "qa_metadata.quality_score", quality_metrics.get("quality_score", 0.5))
        processing_metadata = update_chunk_field(processing_metadata, "qa_metadata.chunk_quality", quality_metrics.get("chunk_quality", "medium"))
        processing_metadata = update_chunk_field(processing_metadata, "qa_metadata.is_context_dead", quality_metrics.get("is_context_dead", False))
        processing_metadata = update_chunk_field(processing_metadata, "qa_metadata.original_length", len(text))
        processing_metadata = update_chunk_field(processing_metadata, "qa_metadata.processed_length", len(processed_text))
        
        # Add quality metrics
        for key, value in quality_metrics.items():
            if key in ["word_count", "is_complete_sentence", "has_numeric_stat", "primary_entity", "omit_flag", "show_skip_reasons", "quality_flags"]:
                processing_metadata = update_chunk_field(processing_metadata, f"qa_metadata.{key}", value)
        
        return processed_text, processing_metadata
    
    def _pre_process(self, text: str, context: Optional[Dict] = None) -> str:
        """
        Pre-process text (subclass-specific).
        
        Args:
            text: Text to pre-process
            context: Additional context
            
        Returns:
            Pre-processed text
        """
        # Base implementation - just clean whitespace
        return re.sub(r'\s+', ' ', text.strip())
    
    def _post_process(self, text: str, context: Optional[Dict] = None) -> str:
        """
        Post-process text (subclass-specific).
        
        Args:
            text: Text to post-process
            context: Additional context
            
        Returns:
            Post-processed text
        """
        # Base implementation - ensure proper sentence ending
        if text and not text.endswith(('.', '!', '?')):
            text += '.'
        return text
    
    def _inject_glossary(self, text: str) -> Tuple[str, List[Dict]]:
        """
        Inject glossary definitions into text with enhanced matching.
        
        Args:
            text: Text to process
            
        Returns:
            Tuple of (processed_text, glossary_hits)
        """
        glossary_hits = []
        
        for term, definition in self.glossary_map.items():
            # Enhanced glossary matching with multi-term and plural support
            hits = self._find_glossary_matches(text, term)
            
            for hit in hits:
                # Only inject if definition isn't already present
                if definition.lower() not in text.lower():
                    # Use inline rephrasing instead of appending
                    replacement = f"{hit['matched_term']} (refers to {definition.lower()})"
                    text = text.replace(hit['matched_term'], replacement)
                    
                    glossary_hits.append({
                        "term": term,
                        "definition": definition,
                        "replacement": replacement,
                        "matched_term": hit['matched_term'],
                        "match_type": hit['match_type']
                    })
        
        return text, glossary_hits
    
    def _find_glossary_matches(self, text: str, term: str) -> List[Dict[str, Any]]:
        """
        Find all matches for a glossary term including variations.
        
        Args:
            text: Text to search
            term: Glossary term to find
            
        Returns:
            List of match dictionaries
        """
        matches = []
        
        # Direct match
        if term in text:
            matches.append({
                "matched_term": term,
                "match_type": "exact"
            })
        
        # Case-insensitive match
        if term.lower() in text.lower() and term not in text:
            # Find the actual case in text
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            for match in pattern.finditer(text):
                matches.append({
                    "matched_term": match.group(),
                    "match_type": "case_insensitive"
                })
        
        # Plural forms
        plural_forms = self._get_plural_forms(term)
        for plural in plural_forms:
            if plural in text:
                matches.append({
                    "matched_term": plural,
                    "match_type": "plural"
                })
        
        # Multi-term matches (e.g., "GDP, RBI, and FDI")
        multi_term_matches = self._find_multi_term_matches(text, term)
        matches.extend(multi_term_matches)
        
        return matches
    
    def _get_plural_forms(self, term: str) -> List[str]:
        """
        Generate plural forms of a term.
        
        Args:
            term: Singular term
            
        Returns:
            List of plural forms
        """
        plurals = []
        
        # Simple plural rules
        if term.endswith('y'):
            plurals.append(term[:-1] + 'ies')  # policy -> policies
        elif term.endswith('s'):
            plurals.append(term + 'es')  # class -> classes
        else:
            plurals.append(term + 's')  # default
        
        # Special cases
        special_plurals = {
            "GDP": "GDPs",
            "RBI": "RBIs", 
            "FDI": "FDIs",
            "IMF": "IMFs",
            "WTO": "WTOs",
            "UNESCO": "UNESCOs",
            "WHO": "WHOs"
        }
        
        if term in special_plurals:
            plurals.append(special_plurals[term])
        
        return plurals
    
    def _find_multi_term_matches(self, text: str, term: str) -> List[Dict[str, Any]]:
        """
        Find multi-term matches (e.g., "GDP, RBI, and FDI").
        
        Args:
            text: Text to search
            term: Term to find in multi-term context
            
        Returns:
            List of multi-term matches
        """
        matches = []
        
        # Pattern for multi-term lists
        patterns = [
            r'(\w+),\s*(\w+),\s*and\s*(\w+)',  # A, B, and C
            r'(\w+)\s+and\s+(\w+)',  # A and B
            r'(\w+),\s*(\w+)',  # A, B
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                terms_in_match = match.groups()
                if term in terms_in_match:
                    matches.append({
                        "matched_term": match.group(),
                        "match_type": "multi_term",
                        "terms": terms_in_match
                    })
        
        return matches
    
    def _normalize_entities(self, text: str) -> Tuple[str, List[str]]:
        """
        Expand acronyms and normalize entities.
        
        Args:
            text: Text to process
            
        Returns:
            Tuple of (processed_text, expanded_entities)
        """
        expanded_entities = []
        
        for acronym, full_name in self.entity_map.items():
            # Replace standalone acronyms (with word boundaries)
            pattern = r'\b' + re.escape(acronym) + r'\b'
            if re.search(pattern, text):
                text = re.sub(pattern, full_name, text)
                expanded_entities.append(f"{acronym} → {full_name}")
        
        return text, expanded_entities
    
    def _find_glossary_misses(self, text: str) -> List[Dict[str, Any]]:
        """
        Find terms that might be glossary terms but aren't mapped.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of dictionaries with missed term details
        """
        # Simple heuristic: capitalized terms that might be concepts
        potential_terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        # Filter out common words and already mapped terms
        common_words = {"India", "The", "This", "That", "These", "Those", "First", "Second", "Third"}
        mapped_terms = set(self.glossary_map.keys())
        
        missed_terms = []
        for term in potential_terms:
            if (term not in common_words and 
                term not in mapped_terms and 
                len(term) > 3):
                
                # Check if term appears to be a concept (multiple words, technical-looking)
                is_likely_concept = (
                    len(term.split()) > 1 or  # Multi-word terms
                    any(word in term.lower() for word in ["system", "theory", "method", "process", "analysis"]) or
                    term.endswith(("ism", "tion", "ment", "ness", "ity"))
                )
                
                missed_terms.append({
                    "term": term,
                    "length": len(term),
                    "word_count": len(term.split()),
                    "is_likely_concept": is_likely_concept,
                    "glossary_consulted": list(self.glossary_map.keys())[:5],  # Show first 5 terms for context
                    "fallback_attempted": False  # Could be enhanced with fuzzy matching
                })
        
        return missed_terms
    
    def _classify_chunk_pattern(self, text: str) -> Dict[str, Any]:
        """
        Classify chunk into semantic type with reasoning.
        
        Args:
            text: Text to classify
            
        Returns:
            Dictionary with semantic_type and reasoning
        """
        text_lower = text.lower()
        reasoning = []
        
        # Strong definition patterns with reasoning
        definition_patterns = [
            (r'\b(\w+)\s+is\s+(?:a|an)\s+(\w+)', "X is a Y pattern"),
            (r'\b(\w+)\s+means\s+', "means pattern"),
            (r'\b(\w+)\s+refers\s+to\s+', "refers to pattern"),
            (r'\b(\w+)\s+is\s+defined\s+as\s+', "defined as pattern"),
            (r'\b(\w+)\s+is\s+known\s+as\s+', "known as pattern"),
            (r'\bconcept\s+of\s+(\w+)', "concept of pattern"),
            (r'\b(\w+)\s+denotes\s+', "denotes pattern"),
            (r'\b(\w+)\s+signifies\s+', "signifies pattern")
        ]
        
        for pattern, reason in definition_patterns:
            if re.search(pattern, text_lower):
                reasoning.append(reason)
                return {
                    "semantic_type": "definition",
                    "reasoning": reasoning,
                    "confidence": 0.9
                }
        
        # Statistical data with specific patterns
        if re.search(r'\d+\.?\d*\s*%', text):
            reasoning.append("percentage pattern")
            return {
                "semantic_type": "statistical",
                "reasoning": reasoning,
                "confidence": 0.95
            }
        
        if re.search(r'\d+\s*(million|billion|thousand)', text):
            reasoning.append("large number pattern")
            return {
                "semantic_type": "statistical",
                "reasoning": reasoning,
                "confidence": 0.9
            }
        
        # Historical events with stronger patterns
        historical_patterns = [
            (r'\b(\w+)\s+was\s+founded\s+in\s+', "founded in pattern"),
            (r'\b(\w+)\s+was\s+established\s+in\s+', "established in pattern"),
            (r'\b(\w+)\s+was\s+created\s+in\s+', "created in pattern"),
            (r'\b(\w+)\s+was\s+introduced\s+in\s+', "introduced in pattern"),
            (r'\b(\w+)\s+started\s+in\s+', "started in pattern"),
            (r'\b(\w+)\s+emerged\s+in\s+', "emerged in pattern")
        ]
        
        for pattern, reason in historical_patterns:
            if re.search(pattern, text_lower):
                reasoning.append(reason)
                return {
                    "semantic_type": "historical_event",
                    "reasoning": reasoning,
                    "confidence": 0.85
                }
        
        # Person descriptions with stronger patterns
        person_patterns = [
            (r'\b(\w+)\s+was\s+a\s+(\w+)', "was a pattern"),
            (r'\b(\w+)\s+is\s+a\s+(\w+)', "is a pattern"),
            (r'\b(\w+)\s+reformer', "reformer pattern"),
            (r'\b(\w+)\s+leader', "leader pattern"),
            (r'\b(\w+)\s+activist', "activist pattern"),
            (r'\b(\w+)\s+pioneer', "pioneer pattern"),
            (r'\b(\w+)\s+scholar', "scholar pattern"),
            (r'\b(\w+)\s+philosopher', "philosopher pattern")
        ]
        
        for pattern, reason in person_patterns:
            if re.search(pattern, text_lower):
                reasoning.append(reason)
                return {
                    "semantic_type": "person",
                    "reasoning": reasoning,
                    "confidence": 0.8
                }
        
        # Geographic information with stronger patterns
        geo_patterns = [
            (r'\b(\w+)\s+is\s+located\s+', "located pattern"),
            (r'\bclimate\s+of\s+(\w+)', "climate pattern"),
            (r'\bgeography\s+of\s+(\w+)', "geography pattern"),
            (r'\b(\w+)\s+region', "region pattern"),
            (r'\b(\w+)\s+area', "area pattern"),
            (r'\b(\w+)\s+river', "river pattern"),
            (r'\b(\w+)\s+mountain', "mountain pattern")
        ]
        
        for pattern, reason in geo_patterns:
            if re.search(pattern, text_lower):
                reasoning.append(reason)
                return {
                    "semantic_type": "geographic",
                    "reasoning": reasoning,
                    "confidence": 0.8
                }
        
        # Legal/Policy with stronger patterns
        legal_patterns = [
            (r'\b(\w+)\s+act', "act pattern"),
            (r'\b(\w+)\s+law', "law pattern"),
            (r'\b(\w+)\s+policy', "policy pattern"),
            (r'\b(\w+)\s+scheme', "scheme pattern"),
            (r'\b(\w+)\s+program', "program pattern"),
            (r'\b(\w+)\s+regulation', "regulation pattern"),
            (r'\b(\w+)\s+amendment', "amendment pattern")
        ]
        
        for pattern, reason in legal_patterns:
            if re.search(pattern, text_lower):
                reasoning.append(reason)
                return {
                    "semantic_type": "legal_policy",
                    "reasoning": reasoning,
                    "confidence": 0.8
                }
        
        # Comparisons with stronger patterns
        comparison_patterns = [
            (r'\bcompared\s+to\s+', "compared to pattern"),
            (r'\bunlike\s+', "unlike pattern"),
            (r'\bdifferent\s+from\s+', "different from pattern"),
            (r'\bsimilar\s+to\s+', "similar to pattern"),
            (r'\b(\w+)\s+vs\s+(\w+)', "vs pattern"),
            (r'\b(\w+)\s+versus\s+(\w+)', "versus pattern")
        ]
        
        for pattern, reason in comparison_patterns:
            if re.search(pattern, text_lower):
                reasoning.append(reason)
                return {
                    "semantic_type": "comparison",
                    "reasoning": reasoning,
                    "confidence": 0.85
                }
        
        # Causes/Effects with stronger patterns
        causal_patterns = [
            (r'\bbecause\s+', "because pattern"),
            (r'\bdue\s+to\s+', "due to pattern"),
            (r'\bleads\s+to\s+', "leads to pattern"),
            (r'\bresults\s+in\s+', "results in pattern"),
            (r'\bcauses\s+', "causes pattern"),
            (r'\b(\w+)\s+leads\s+to\s+(\w+)', "leads to pattern"),
            (r'\b(\w+)\s+results\s+in\s+(\w+)', "results in pattern")
        ]
        
        for pattern, reason in causal_patterns:
            if re.search(pattern, text_lower):
                reasoning.append(reason)
                return {
                    "semantic_type": "causal",
                    "reasoning": reasoning,
                    "confidence": 0.8
                }
        
        # Default case
        reasoning.append("no specific pattern detected")
        
        # Determine secondary tags and question affinity
        secondary_tags = self._determine_secondary_tags(text_lower)
        question_affinity = self._determine_question_affinity(text_lower)
        
        return {
            "semantic_type": "general",
            "reasoning": reasoning,
            "confidence": 0.3,
            "secondary_tags": secondary_tags,
            "question_affinity": question_affinity
        }
    
    def _determine_secondary_tags(self, text_lower: str) -> List[str]:
        """
        Determine secondary semantic tags for the chunk.
        
        Args:
            text_lower: Lowercase text to analyze
            
        Returns:
            List of secondary tags
        """
        secondary_tags = []
        
        # Descriptive content
        if any(word in text_lower for word in ["describes", "characterized by", "features", "consists of"]):
            secondary_tags.append("descriptive")
        
        # Analytical content
        if any(word in text_lower for word in ["analysis", "examines", "investigates", "studies"]):
            secondary_tags.append("analytical")
        
        # Comparative content
        if any(word in text_lower for word in ["compared", "versus", "difference", "similar"]):
            secondary_tags.append("comparative")
        
        # Temporal content
        if any(word in text_lower for word in ["during", "period", "era", "century", "decade"]):
            secondary_tags.append("temporal")
        
        # Spatial content
        if any(word in text_lower for word in ["located", "region", "area", "geographic", "spatial"]):
            secondary_tags.append("spatial")
        
        # Causal content
        if any(word in text_lower for word in ["causes", "leads to", "results in", "because"]):
            secondary_tags.append("causal")
        
        return secondary_tags
    
    def _determine_question_affinity(self, text_lower: str) -> List[str]:
        """
        Determine what types of questions this chunk can answer.
        
        Args:
            text_lower: Lowercase text to analyze
            
        Returns:
            List of question types this chunk can answer
        """
        question_types = []
        
        # Factoid questions (what, who, when, where)
        if any(word in text_lower for word in ["is", "was", "are", "were", "has", "had"]):
            question_types.append("factoid")
        
        # Definition questions
        if any(word in text_lower for word in ["means", "refers to", "defined as", "is known as"]):
            question_types.append("definition")
        
        # Trend questions
        if any(word in text_lower for word in ["increased", "decreased", "grew", "declined", "trend"]):
            question_types.append("trend")
        
        # Comparison questions
        if any(word in text_lower for word in ["compared", "versus", "difference", "similar"]):
            question_types.append("comparison")
        
        # Process questions
        if any(word in text_lower for word in ["process", "steps", "procedure", "method"]):
            question_types.append("process")
        
        # Cause-effect questions
        if any(word in text_lower for word in ["causes", "leads to", "results in", "because"]):
            question_types.append("cause_effect")
        
        return question_types
    
    def _assess_quality(self, text: str, metadata: Optional[Dict] = None, context: Optional[Dict] = None) -> Dict:
        """
        Assess chunk quality and detect context-dead chunks.
        
        Args:
            text: Text to assess
            metadata: Chunk metadata
            context: Additional context
            
        Returns:
            Quality metrics dictionary
        """
        word_count = len(text.split())
        
        # Base quality assessment
        quality_metrics = {
            "word_count": word_count,
            "is_context_dead": False,
            "chunk_quality": "medium",
            "confidence_score": 0.5,
            "quality_score": 0.5,  # Composite quality score
            "quality_flags": []
        }
        
        # Initialize quality score components
        length_score = 0.0
        content_score = 0.0
        structure_score = 0.0
        entity_score = 0.0
        
        # 1. Length Assessment (0-1 score)
        if word_count >= 10 and word_count <= 50:
            length_score = 1.0
        elif word_count >= 5 and word_count <= 100:
            length_score = 0.8
        elif word_count < 5:
            length_score = 0.3
            quality_metrics["quality_flags"].append("too_short")
        else:
            length_score = 0.6
            quality_metrics["quality_flags"].append("too_long")
        
        # 2. Content Assessment (0-1 score)
        # Check for meaningful content
        if re.search(r'\b[a-zA-Z]{3,}\b', text):
            content_score = 1.0
        else:
            content_score = 0.0
            quality_metrics["quality_flags"].append("no_meaningful_content")
        
        # Check for numeric-only content
        if re.match(r'^[\d\s\.]+$', text.strip()):
            content_score = 0.2
            quality_metrics["quality_flags"].append("numeric_only")
        
        # 3. Structure Assessment (0-1 score)
        # Check for complete sentences
        if text and text.strip().endswith(('.', '!', '?')) and text[0].isupper():
            structure_score = 1.0
        elif text and text.strip().endswith(('.', '!', '?')):
            structure_score = 0.8
        elif text and text[0].isupper():
            structure_score = 0.7
        else:
            structure_score = 0.5
            quality_metrics["quality_flags"].append("fragment_detected")
        
        # 4. Entity Assessment (0-1 score)
        # Check for named entities (basic heuristic)
        entity_patterns = [
            r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Proper nouns
            r'\b[A-Z]{2,}\b',  # Acronyms
            r'\b\d{4}\b',  # Years
            r'\b\d+\.?\d*\b'  # Numbers
        ]
        entity_count = sum(1 for pattern in entity_patterns if re.search(pattern, text))
        entity_score = min(entity_count * 0.2, 1.0)
        
        # Only flag as "no_entities" if it's a longer text that should have entities
        if entity_count == 0 and word_count > 8:
            quality_metrics["quality_flags"].append("no_entities")
        
        # 5. Calculate Composite Quality Score
        quality_metrics["quality_score"] = (
            length_score * 0.25 +
            content_score * 0.3 +
            structure_score * 0.25 +
            entity_score * 0.2
        )
        
        # 6. Context-dead detection
        if word_count < self.min_word_count or content_score < 0.5:
            quality_metrics["is_context_dead"] = True
        
        # 7. Determine categorical quality
        if quality_metrics["quality_score"] >= 0.8:
            quality_metrics["chunk_quality"] = "high"
        elif quality_metrics["quality_score"] >= 0.5:
            quality_metrics["chunk_quality"] = "medium"
        else:
            quality_metrics["chunk_quality"] = "low"
            quality_metrics["quality_flags"].append("low_quality_score")
        
        # 8. Confidence score (can be overridden by subclasses)
        if metadata and "source_confidence_score" in metadata:
            quality_metrics["confidence_score"] = metadata["source_confidence_score"]
        
        # 9. Add confidence-based flags (only if confidence is explicitly low)
        if metadata and "source_confidence_score" in metadata:
            if metadata["source_confidence_score"] < 0.7:
                quality_metrics["quality_flags"].append("low_confidence")
        
        # 10. Ensure quality flags are clear and ranked by severity
        # Sort flags by severity (most severe first)
        flag_severity = {
            "no_meaningful_content": 1,
            "numeric_only": 2,
            "too_short": 3,
            "fragment_detected": 4,
            "no_entities": 5,
            "low_confidence": 6,
            "glossary_miss": 7,
            "too_long": 8,
            "low_quality_score": 9
        }
        
        # Sort flags by severity
        quality_metrics["quality_flags"] = sorted(
            quality_metrics["quality_flags"],
            key=lambda flag: flag_severity.get(flag, 10)  # Default severity 10 for unknown flags
        )
        
        # 11. Set chunk_quality to low if multiple severe flags
        severe_flags = ["no_meaningful_content", "numeric_only", "too_short", "fragment_detected"]
        if any(flag in quality_metrics["quality_flags"] for flag in severe_flags):
            quality_metrics["chunk_quality"] = "low"
            quality_metrics["quality_score"] = max(0.0, quality_metrics["quality_score"] - 0.2)
        
        return quality_metrics
    
    def _create_empty_metadata(self) -> Dict:
        """Create empty metadata for empty text."""
        return {
            "qa_metadata": {
                "confidence_score": 0.0,
                "quality_score": 0.0,
                "chunk_quality": "low",
                "is_context_dead": True,
                "is_complete_sentence": False,
                "has_numeric_stat": False,
                "primary_entity": None,
                "omit_flag": True,
                "show_skip_reasons": ["empty_text"],
                "quality_flags": ["empty_text"],
                "entities_expanded": [],
                "processing_steps": ["empty_text"],
                "original_length": 0,
                "processed_length": 0,
            },
            "semantic_type": {
                "primary": "empty",
                "secondary_tags": [],
                "domain": None,
                "cognitive_level": "none",
                "question_type_affinity": [],
                "reasoning": "Empty text provided",
                "confidence": 0.0
            }
        }
