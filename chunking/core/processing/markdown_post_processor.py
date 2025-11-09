"""
Markdown-specific post-processor for chunk text enhancement.
Extends the base post-processor with Markdown-specific functionality.
"""

import re
from typing import Dict, List, Tuple, Optional
from .base_post_processor import BaseChunkPostProcessor

class MarkdownPostProcessor(BaseChunkPostProcessor):
    """
    Markdown-specific post-processor that handles:
    1. Markdown-specific glossary terms
    2. Academic/academic entity expansion
    3. Context-dead chunk detection
    4. Semantic type classification
    5. Quality assessment
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the Markdown post-processor.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
    
    def _get_glossary_map(self) -> Dict[str, str]:
        """Get Markdown-specific glossary mappings (disabled)."""
        return {}
    
    def _get_entity_map(self) -> Dict[str, str]:
        """Get Markdown-specific entity mappings."""
        return {
            # Academic institutions
            "IIT": "Indian Institute of Technology",
            "IISc": "Indian Institute of Science",
            "TIFR": "Tata Institute of Fundamental Research",
            "CSIR": "Council of Scientific and Industrial Research",
            "ICAR": "Indian Council of Agricultural Research",
            
            # Government bodies
            "CAG": "Comptroller and Auditor General",
            "CEC": "Chief Election Commissioner",
            "CIC": "Chief Information Commissioner",
            "NHRC": "National Human Rights Commission",
            "NCW": "National Commission for Women",
            
            # International organizations
            "UN": "United Nations",
            "UNESCO": "United Nations Educational, Scientific and Cultural Organization",
            "WHO": "World Health Organization",
            "IMF": "International Monetary Fund",
            "WTO": "World Trade Organization",
            "FAO": "Food and Agriculture Organization",
            "ILO": "International Labour Organization",
            
            # Indian constitutional bodies
            "UPSC": "Union Public Service Commission",
            "SPSC": "State Public Service Commission",
            "JPSC": "Joint Public Service Commission",
            "Election Commission": "Election Commission of India",
            "Finance Commission": "Finance Commission of India",
        }

    def process(self, text: str, metadata: Optional[Dict] = None, context: Optional[Dict] = None):
        """Override to be lenient with non-string inputs for markdown.

        Coerces None/non-string inputs to a safe string before delegating to base.
        """
        if not isinstance(text, str):
            text = "" if text is None else str(text)
        return super().process(text, metadata, context)
    
    def _pre_process(self, text: str, context: Optional[Dict] = None) -> str:
        """
        Pre-process Markdown text.
        
        Args:
            text: Text to pre-process
            context: Additional context
            
        Returns:
            Pre-processed text
        """
        # Allow non-string/None input gracefully here (tests expect leniency for markdown processor)
        if not isinstance(text, str):
            text = "" if text is None else str(text)

        # Remove Markdown formatting comprehensively
        import re
        
        # Headers (multiline) - allow leading spaces
        text = re.sub(r'(?m)^\s*#{1,6}\s+', '', text)
        
        # Blockquotes (multiline) - allow leading spaces
        text = re.sub(r'(?m)^\s*>\s*', '', text)
        
        # Fenced code blocks: keep content, drop fences (allow optional language label)
        text = re.sub(r'```+[A-Za-z0-9_\-]*\s*\n([\s\S]*?)\n```+', r'\1', text)
        
        # Inline code: collapse stray backticks and remove code fences
        text = re.sub(r'`([^`]+)`', r'\1', text)
        # Remove any stray backticks
        text = text.replace('`', '')
        
        # Images: ![alt](src) -> alt
        text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
        
        # Links: [text](url) -> text
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        # Reference-style inline links: [text][ref] -> text
        text = re.sub(r'\[([^\]]+)\]\[[^\]]+\]', r'\1', text)
        
        # Reference-style link definitions: remove entire definition lines
        text = re.sub(r'(?m)^\s*\[[^\]]+\]:\s+\S+.*$', '', text)
        
        # Emphasis/strong/underscore markers
        text = text.replace('***', '').replace('**', '').replace('*', '')
        text = text.replace('__', '').replace('_', '')
        
        # Pandoc class markers like {.underline}
        text = re.sub(r'\{\.[^}]+\}', '', text)
        
        # Tables: remove pipe characters used for tables
        text = text.replace('|', ' ')
        
        # Clean leftover markdown artifacts
        text = re.sub(r'\s+', ' ', text.strip())
        
        return text
    
    def _post_process(self, text: str, context: Optional[Dict] = None) -> str:
        """
        Post-process Markdown text.
        
        Args:
            text: Text to post-process
            context: Additional context
            
        Returns:
            Post-processed text
        """
        # Ensure proper sentence ending
        if text and not text.endswith(('.', '!', '?')):
            text += '.'
        
        # Remove excessive punctuation
        import re
        text = re.sub(r'\.+', '.', text)
        text = re.sub(r'!\s*!', '!', text)
        text = re.sub(r'\?\s*\?', '?', text)
        
        return text
    
    def _assess_quality(self, text: str, metadata: Optional[Dict] = None, context: Optional[Dict] = None) -> Dict:
        """
        Assess Markdown chunk quality with specific criteria.
        
        Args:
            text: Text to assess
            metadata: Chunk metadata
            context: Additional context
            
        Returns:
            Quality metrics dictionary
        """
        # Get base quality assessment
        quality_metrics = super()._assess_quality(text, metadata, context)
        
        # Markdown-specific quality checks
        word_count = len(text.split())
        
        # Academic content indicators
        academic_terms = ["research", "study", "analysis", "methodology", "theory", "empirical", "data", "findings"]
        academic_score = sum(1 for term in academic_terms if term.lower() in text.lower()) / len(academic_terms)
        
        # Citation indicators
        citation_patterns = [r'\(\d{4}\)', r'\[.*?\]', r'et al\.', r'ibid\.', r'op\. cit\.']
        citation_count = sum(1 for pattern in citation_patterns if re.search(pattern, text))
        
        # Update quality metrics
        quality_metrics.update({
            "academic_score": academic_score,
            "citation_count": citation_count,
            "is_academic_content": academic_score > 0.3,
            "has_citations": citation_count > 0
        })
        
        # Adjust chunk quality based on academic indicators
        if academic_score > 0.5 and citation_count > 0:
            quality_metrics["chunk_quality"] = "high"
        elif academic_score > 0.3 or citation_count > 0:
            quality_metrics["chunk_quality"] = "medium"
        
        return quality_metrics

def process_markdown_text(text: str, metadata: Optional[Dict] = None, context: Optional[Dict] = None) -> Tuple[str, Dict]:
    """
    Convenience function to process Markdown text.
    
    Args:
        text: Raw Markdown text
        metadata: Chunk metadata for context
        context: Additional context
        
    Returns:
        Tuple of (processed_text, metadata)
    """
    processor = MarkdownPostProcessor()
    return processor.process(text, metadata, context)
