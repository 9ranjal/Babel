"""
Versioning utilities for chunk files to avoid overwriting with each run.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

def get_next_version_number(output_dir: str, base_filename: str) -> int:
    """Get the next version number for a file in the directory."""
    existing_files = []
    for file in os.listdir(output_dir):
        if file.startswith(base_filename) and file.endswith('.json'):
            # Extract version number from filename like "notes_chunks_v1_20241224_1430.json"
            parts = file.replace('.json', '').split('_')
            if len(parts) >= 3 and parts[-2].startswith('v'):
                try:
                    version = int(parts[-2][1:])  # Remove 'v' and convert to int
                    existing_files.append(version)
                except ValueError:
                    continue
    
    return max(existing_files, default=0) + 1

def generate_versioned_filename(base_filename: str, output_dir: str, include_timestamp: bool = True) -> str:
    """Generate a versioned filename that won't overwrite existing files."""
    version = get_next_version_number(output_dir, base_filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    
    if include_timestamp:
        return f"{base_filename}_v{version}_{timestamp}.json"
    else:
        return f"{base_filename}_v{version}.json"

def save_versioned_chunks(chunks: List[Dict], output_dir: str, base_filename: str, 
                         create_symlink: bool = True, symlink_name: Optional[str] = None) -> str:
    """
    Save chunks with versioning and optionally create a symlink.
    
    Args:
        chunks: List of chunk dictionaries
        output_dir: Directory to save the file
        base_filename: Base filename (e.g., "notes_chunks")
        create_symlink: Whether to create a symlink to the latest version
        symlink_name: Name for the symlink (defaults to base_filename + ".json")
    
    Returns:
        Path to the saved file
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate versioned filename
    filename = generate_versioned_filename(base_filename, output_dir)
    output_path = os.path.join(output_dir, filename)
    
    # Save chunks
    with open(output_path, "w") as f:
        json.dump(chunks, f, indent=2)
    
    # Create symlink if requested
    if create_symlink:
        if symlink_name is None:
            symlink_name = f"{base_filename}.json"
        
        symlink_path = os.path.join(output_dir, symlink_name)
        
        # Remove existing symlink if it exists
        if os.path.islink(symlink_path) or os.path.exists(symlink_path):
            os.remove(symlink_path)
        
        # Create new symlink
        os.symlink(os.path.abspath(output_path), symlink_path)
    
    return output_path

def get_latest_versioned_file(output_dir: str, base_filename: str) -> Optional[str]:
    """Get the path to the latest versioned file."""
    if not os.path.exists(output_dir):
        return None
    
    latest_file = None
    latest_version = -1
    
    for file in os.listdir(output_dir):
        if file.startswith(base_filename) and file.endswith('.json'):
            parts = file.replace('.json', '').split('_')
            if len(parts) >= 2 and parts[-2].startswith('v'):
                try:
                    version = int(parts[-2][1:])
                    if version > latest_version:
                        latest_version = version
                        latest_file = file
                except ValueError:
                    continue
    
    if latest_file:
        return os.path.join(output_dir, latest_file)
    return None

def load_latest_versioned_chunks(output_dir: str, base_filename: str) -> List[Dict]:
    """Load the latest versioned chunks file."""
    latest_file = get_latest_versioned_file(output_dir, base_filename)
    if not latest_file:
        return []
    
    with open(latest_file, 'r') as f:
        return json.load(f) 