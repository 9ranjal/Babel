#!/usr/bin/env python3
"""
Abstract base class for chunk processors.
Defines the interface that all chunk processors must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path


class ChunkProcessor(ABC):
    """
    Abstract base class for chunk processors.
    
    All chunk processors must implement the process method to handle
    specific file types and return a list of chunks.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the processor with optional configuration.
        
        Args:
            config: Configuration dictionary for the processor
        """
        self.config = config or {}
        self.processor_name = self.__class__.__name__
    
    @abstractmethod
    def process(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Process a file and return a list of chunks.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            List of chunk dictionaries
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError(f"{self.processor_name} must implement process()")
    
    @abstractmethod
    def can_process(self, file_path: str) -> bool:
        """
        Check if this processor can handle the given file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the processor can handle this file type
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError(f"{self.processor_name} must implement can_process()")
    
    def get_processor_info(self) -> Dict[str, Any]:
        """
        Get information about this processor.
        
        Returns:
            Dictionary with processor information
        """
        return {
            "name": self.processor_name,
            "config": self.config,
            "description": self.__doc__ or "No description available"
        }
    
    def validate_file(self, file_path: str) -> bool:
        """
        Validate that the file exists and is readable.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if the file is valid
        """
        path = Path(file_path)
        return path.exists() and path.is_file() and path.stat().st_size > 0
    
    def pre_process(self, file_path: str) -> Dict[str, Any]:
        """
        Pre-process the file to extract basic information.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with pre-processing information
        """
        path = Path(file_path)
        return {
            "file_path": str(file_path),
            "file_name": path.name,
            "file_size": path.stat().st_size,
            "file_extension": path.suffix.lower(),
            "processor_name": self.processor_name
        }
    
    def post_process(self, chunks: List[Dict[str, Any]], file_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Post-process chunks after creation.
        
        Args:
            chunks: List of chunks to post-process
            file_info: Information about the source file
            
        Returns:
            Post-processed chunks
        """
        # Note: Post-processing is disabled to maintain schema compatibility
        # File information is already available in source_chunk and source_id fields
        return chunks 