#!/usr/bin/env python3
"""
Plugin manager for chunking processors.
Handles plugin registration, discovery, and orchestration.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Type
import importlib
import inspect

from .base import ChunkProcessor


class PluginManager:
    """
    Plugin manager for chunking processors.
    
    Manages the registration, discovery, and execution of chunk processors.
    """
    
    def __init__(self):
        """Initialize the plugin manager."""
        self.processors: Dict[str, Type[ChunkProcessor]] = {}
        self.instances: Dict[str, ChunkProcessor] = {}
        self.config: Dict[str, Any] = {}
    
    def register_processor(self, processor_class: Type[ChunkProcessor], name: Optional[str] = None) -> None:
        """
        Register a processor class.
        
        Args:
            processor_class: The processor class to register
            name: Optional name for the processor (defaults to class name)
        """
        if not issubclass(processor_class, ChunkProcessor):
            raise ValueError(f"Processor must inherit from ChunkProcessor: {processor_class}")
        
        processor_name = name or processor_class.__name__
        self.processors[processor_name] = processor_class
        print(f"✅ Registered processor: {processor_name}")
    
    def get_processor(self, name: str, config: Optional[Dict[str, Any]] = None) -> ChunkProcessor:
        """
        Get a processor instance.
        
        Args:
            name: Name of the processor
            config: Configuration for the processor
            
        Returns:
            Processor instance
            
        Raises:
            KeyError: If processor not found
        """
        if name not in self.processors:
            raise KeyError(f"Processor not found: {name}")
        
        # Create instance if not exists
        if name not in self.instances:
            processor_config = {**self.config.get(name, {}), **(config or {})}
            self.instances[name] = self.processors[name](processor_config)
        
        return self.instances[name]
    
    def get_processor_for_file(self, file_path: str, config: Optional[Dict[str, Any]] = None) -> Optional[ChunkProcessor]:
        """
        Get the appropriate processor for a file.
        
        Args:
            file_path: Path to the file
            config: Configuration for the processor
            
        Returns:
            Processor instance or None if no suitable processor found
        """
        for name, processor_class in self.processors.items():
            processor = self.get_processor(name, config)
            if processor.can_process(file_path):
                return processor
        
        return None
    
    def process_file(self, file_path: str, config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Process a file using the appropriate processor.
        
        Args:
            file_path: Path to the file to process
            config: Configuration for the processor
            
        Returns:
            List of chunks
            
        Raises:
            ValueError: If no suitable processor found
        """
        processor = self.get_processor_for_file(file_path, config)
        if not processor:
            raise ValueError(f"No processor found for file: {file_path}")
        
        return processor.process(file_path)
    
    def process_directory(self, directory_path: str, config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Process all files in a directory.
        
        Args:
            directory_path: Path to the directory
            config: Configuration for processors
            
        Returns:
            List of all chunks from all files
        """
        directory = Path(directory_path)
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Invalid directory: {directory_path}")
        
        all_chunks = []
        processed_files = 0
        failed_files = 0
        
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                try:
                    chunks = self.process_file(str(file_path), config)
                    all_chunks.extend(chunks)
                    processed_files += 1
                    print(f"✅ Processed {file_path.name}: {len(chunks)} chunks")
                except Exception as e:
                    failed_files += 1
                    print(f"❌ Failed to process {file_path.name}: {e}")
        
        print(f"\n📊 Processing complete:")
        print(f"   Files processed: {processed_files}")
        print(f"   Files failed: {failed_files}")
        print(f"   Total chunks: {len(all_chunks)}")
        
        return all_chunks
    
    def list_processors(self) -> List[Dict[str, Any]]:
        """
        List all registered processors.
        
        Returns:
            List of processor information dictionaries
        """
        processor_info = []
        
        for name, processor_class in self.processors.items():
            info = {
                "name": name,
                "class": processor_class.__name__,
                "description": processor_class.__doc__ or "No description",
                "module": processor_class.__module__
            }
            
            # Get instance info if available
            if name in self.instances:
                instance_info = self.instances[name].get_processor_info()
                info.update(instance_info)
            
            processor_info.append(info)
        
        return processor_info
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """
        Set global configuration for processors.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
    
    def auto_discover_processors(self, plugin_dir: Optional[str] = None) -> None:
        """
        Auto-discover processors in the plugins directory.
        
        Args:
            plugin_dir: Directory to search for plugins (defaults to current directory)
        """
        if plugin_dir is None:
            plugin_dir = os.path.dirname(os.path.abspath(__file__))
        
        plugin_path = Path(plugin_dir)
        
        for file_path in plugin_path.glob("*.py"):
            if file_path.name.startswith("__"):
                continue
            
            module_name = f"chunking.plugins.{file_path.stem}"
            
            try:
                module = importlib.import_module(module_name)
                
                # Find processor classes in the module
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, ChunkProcessor) and 
                        obj != ChunkProcessor):
                        self.register_processor(obj)
                        
            except Exception as e:
                print(f"⚠️  Failed to load plugin {file_path.name}: {e}")


# Global plugin manager instance
plugin_manager = PluginManager()

# Auto-discover processors
plugin_manager.auto_discover_processors() 