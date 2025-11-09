#!/usr/bin/env python3
"""
Plugin system for chunking processors.

This package provides a plugin-based architecture for processing different
file types into chunks. Each plugin implements the ChunkProcessor interface
and can be automatically discovered and used by the PluginManager.
"""

from .base import ChunkProcessor
from .manager import PluginManager, plugin_manager
from .markdown import MarkdownProcessor
from .excel import ExcelProcessor

__all__ = [
    'ChunkProcessor',
    'PluginManager', 
    'plugin_manager',
    'MarkdownProcessor',
    'ExcelProcessor'
]

# Version information
__version__ = "1.0.0" 