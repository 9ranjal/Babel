"""
Excel-specific post-processor that combines text polishing and post-processing.
This module handles Excel-specific text enhancement that's not needed for markdown.
"""

import re
from typing import Dict, List, Tuple, Optional
from .text_polisher import TextPolisher
from .base_post_processor import BaseChunkPostProcessor

class ExcelPostProcessor(BaseChunkPostProcessor):
    """
    Excel-specific post-processor that handles:
    1. Text polishing with T5 transformer
    2. Glossary term injection
    3. Acronym/entity expansion
    4. Context-dead chunk detection
    5. Semantic type classification
    """
    
    def __init__(self, use_large_for_low_confidence: bool = True, config: Optional[Dict] = None, 
                 enable_text_polishing: bool = True, model_name: str = "google/flan-t5-base", 
                 batch_size: int = 8):
        """
        Initialize the Excel post-processor.
        
        Args:
            use_large_for_low_confidence: Whether to use large T5 model for low confidence chunks
            config: Configuration dictionary
            enable_text_polishing: Whether to enable T5 text polishing (disable for speed)
            model_name: T5 model name for text polishing
            batch_size: Batch size for T5 processing
        """
        # Initialize text polisher only if enabled
        self.enable_text_polishing = enable_text_polishing
        if enable_text_polishing:
            self.text_polisher = TextPolisher(
                model_name=model_name,
                use_large_for_low_confidence=use_large_for_low_confidence,
                batch_size=batch_size
            )
        else:
            self.text_polisher = None
        
        # Initialize base class
        super().__init__(config)
    
    def _get_glossary_map(self) -> Dict[str, str]:
        """Get Excel-specific glossary mappings.
        
        DISABLED: Glossary system deprecated to prevent chunk bloat and embedding noise.
        Modern RAG systems work better with clean, original content.
        """
        return {
            # DISABLED: Hardcoded glossary terms (like biotic, abiotic, CWA, MMT) removed 
            # to prevent cross-domain pollution and improve embedding quality.
            # Use query-time glossary lookup instead.
        }
    
    def _get_entity_map(self) -> Dict[str, str]:
        """Get Excel-specific entity mappings."""
        return {
            "DK": "Dhondo Keshav Karve",
            "AIWC": "All India Women's Conference",
            "Phule": "Jyotirao Phule",
            "Gandhi": "Mahatma Gandhi",
            "Nehru": "Jawaharlal Nehru",
            "Patel": "Sardar Vallabhbhai Patel",
            "Bose": "Subhas Chandra Bose",
            "Tilak": "Bal Gangadhar Tilak",
            "Gokhale": "Gopal Krishna Gokhale",
            "Naoroji": "Dadabhai Naoroji",
            "Ranade": "Mahadev Govind Ranade",
            "Agarkar": "Gopal Ganesh Agarkar",
            "Malabari": "Behramji Malabari",
            "Vidyasagar": "Ishwar Chandra Vidyasagar",
            "Dayanand": "Swami Dayanand Saraswati",
            "Vivekananda": "Swami Vivekananda",
            "Ramakrishna": "Sri Ramakrishna Paramahamsa",
            "Aurobindo": "Sri Aurobindo",
            "Tagore": "Rabindranath Tagore",
            "Iqbal": "Muhammad Iqbal",
            # Add more as needed
        }
    
    def process(self, text: str, row_data: Optional[Dict] = None, filename: Optional[str] = None) -> Tuple[str, Dict]:
        """
        Process Excel text through the complete post-processing pipeline.
        
        Args:
            text: Raw text from Excel template
            row_data: Original row data for context
            filename: Source filename for context
            
        Returns:
            Tuple of (processed_text, metadata)
        """
        if not text or not text.strip():
            return text, self._create_empty_metadata()
        
        # 1. Text Polishing (Grammar and fluency) - Excel-specific
        if self.enable_text_polishing and self.text_polisher:
            polished_text, confidence = self.text_polisher.polish_chunk(text)
        else:
            polished_text, confidence = text, 0.75  # Skip polishing, use default confidence
        
        # 2. Apply structured templates for dense data - Excel-specific
        structured_text = self._apply_structured_template(polished_text)
        
        # 3. Use base class processing pipeline
        context = {
            "row_data": row_data,
            "filename": filename,
            "confidence": confidence
        }
        
        metadata = {
            "source_confidence_score": confidence
        }
        
        processed_text, processing_metadata = super().process(structured_text, metadata, context)
        
        # 4. Add Excel-specific metadata using schema
        from ..schema import update_chunk_field
        
        row_completeness = self._assess_row_completeness(row_data) if row_data else 0.0
        processing_metadata = update_chunk_field(processing_metadata, "excel_metadata.row_data_completeness", row_completeness)
        processing_metadata = update_chunk_field(processing_metadata, "excel_metadata.template_success", True)
        processing_metadata = update_chunk_field(processing_metadata, "excel_metadata.source_confidence", "medium")  # Will be refined later
        processing_metadata = update_chunk_field(processing_metadata, "excel_metadata.source_confidence_score", confidence)
        
        # Add source metadata
        if filename:
            processing_metadata = update_chunk_field(processing_metadata, "source_metadata.file_path", filename)
        
        return processed_text, processing_metadata
    
    def _apply_structured_template(self, text: str) -> str:
        """
        Apply rule-based sentence templates for dense data.
        
        Args:
            text: Text to process
            
        Returns:
            Text with structured templates applied
        """
        # Handle percentage references
        text = re.sub(r'(\d+\.?\d*)\s*%\s*rain', r'\1% rainfall', text)
        
        # Handle temperature references
        text = re.sub(r'(\d+\.?\d*)\s*degree', r'\1 degrees Celsius', text)
        
        return text
    
    def _assess_row_completeness(self, row_data: Dict) -> float:
        """
        Assess the completeness of row data.
        
        Args:
            row_data: Row data dictionary
            
        Returns:
            Completeness score (0.0-1.0)
        """
        if not row_data:
            return 0.0
        
        total_fields = len(row_data)
        non_empty_fields = sum(1 for v in row_data.values() 
                              if v and str(v).strip().lower() not in ["", "nan", "none", "-"])
        
        return non_empty_fields / total_fields if total_fields > 0 else 0.0

# Global processor instance to avoid re-creating models
_global_excel_processor = None

def get_excel_processor(enable_text_polishing: bool = None) -> ExcelPostProcessor:
    """
    Get or create a global Excel processor instance.
    
    Args:
        enable_text_polishing: Whether to enable T5 text polishing (None = use config default)
    
    Returns:
        ExcelPostProcessor instance
    """
    global _global_excel_processor
    if _global_excel_processor is None:
        # Import here to avoid circular imports
        from ..config import (
            ENABLE_EXCEL_TEXT_POLISHING, USE_LARGE_T5_MODEL, 
            T5_BATCH_SIZE
        )
        
        if enable_text_polishing is None:
            enable_text_polishing = ENABLE_EXCEL_TEXT_POLISHING
            
        _global_excel_processor = ExcelPostProcessor(
            use_large_for_low_confidence=USE_LARGE_T5_MODEL,
            enable_text_polishing=enable_text_polishing,
            model_name="google/flan-t5-base",  # Keep original T5 base model
            batch_size=T5_BATCH_SIZE
        )
    return _global_excel_processor

def process_excel_text(text: str, row_data: Optional[Dict] = None, filename: Optional[str] = None) -> Tuple[str, Dict]:
    """
    Convenience function to process Excel text using a shared processor instance.
    
    Args:
        text: Raw text from Excel template
        row_data: Original row data for context
        filename: Source filename for context
        
    Returns:
        Tuple of (processed_text, metadata)
    """
    processor = get_excel_processor()
    return processor.process(text, row_data, filename)
