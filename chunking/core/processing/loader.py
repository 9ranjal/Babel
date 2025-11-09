# chunking/loader.py
# File loading and discovery logic

import os
from pathlib import Path
from typing import List, Tuple

def find_markdown_files(input_dir: str) -> List[Path]:
    """Recursively find all markdown files."""
    return sorted(Path(input_dir).rglob("*.md"))

def read_markdown_file(path: Path) -> str:
    """Read and return content of a markdown file."""
    return path.read_text(encoding="utf-8")

def extract_topic_from_path(md_path: Path) -> str:
    """Extract top-level topic based on furnace/ path structure."""
    try:
        parts = md_path.parts
        idx = parts.index("furnace")
        return parts[idx + 1] if idx + 1 < len(parts) else "Unknown"
    except ValueError:
        return "Unknown"

def find_excel_files(input_dir: str) -> List[Path]:
    """Recursively find all Excel files (.xlsx)."""
    return sorted(Path(input_dir).rglob("*.xlsx")) 