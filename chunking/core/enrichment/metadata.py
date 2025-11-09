from pathlib import Path
from ..processing.text_cleaner import slugify
from typing import Optional, List, Dict, Tuple
import os

def extract_metadata_from_filename(filename: str, file_type: str = "markdown", sheet_name: str = None) -> Dict[str, str]:
    """
    Extract metadata from filename for both Excel and Markdown files.
    Enhanced with hierarchical path parsing for better subtopic extraction.
    
    Args:
        filename: The filename to extract metadata from
        file_type: Either "markdown" or "excel"
        sheet_name: Optional sheet name for Excel files
    
    Returns:
        Dictionary with topic, subtopic1-5, author fields
    """
    base = os.path.basename(filename)
    
    if file_type == "excel":
        # Enhanced Excel metadata extraction with sheet names
        metadata = extract_excel_metadata(filename, sheet_name)
        return metadata
    else:
        # For markdown files, parse as TOPIC_AUTHOR_SUBTOPICPHRASE
        parts = base[:-3].split('_')  # remove .md
        if len(parts) >= 3:
            topic = parts[0]
            author = parts[1].replace('-', ' ').replace('.', ' ').title()
            # Join everything after author as a single phrase
            subtopic_raw = '_'.join(parts[2:])
            subtopic_clean = clean_subtopic_text(subtopic_raw)
            # Only split if a rare, explicit multi-subtopic pattern is detected
            multi_split_patterns = [
                ('centre parliament', ['Centre', 'Parliament']),
                ('union state', ['Union', 'State']),
                ('union state relations', ['Union State Relations']),
                # Add more explicit patterns as needed
            ]
            subtopic_lower = subtopic_clean.lower()
            found_split = False
            for pattern, split_list in multi_split_patterns:
                if pattern in subtopic_lower:
                    # Assign each part to subtopic fields
                    metadata = {
                        "topic": topic,
                        "subtopic1": split_list[0],
                        "subtopic2": split_list[1] if len(split_list) > 1 else "",
                        "subtopic3": split_list[2] if len(split_list) > 2 else "",
                        "subtopic4": split_list[3] if len(split_list) > 3 else "",
                        "subtopic5": split_list[4] if len(split_list) > 4 else "",
                        "author": author
                    }
                    found_split = True
                    break
            if not found_split:
                # Known multi-word concepts to preserve as a single phrase
                multi_word_concepts = [
                    'specialised agencies', 'specialized agencies', 'climate change conventions',
                    'medieval india', 'ancient civilization', 'freedom struggle', 'union state relations',
                    'world trade organization', 'international organizations', 'international organisations',
                    'united nations', 'air pollution', 'water pollution', 'soil pollution',
                    'environmental protection', 'biodiversity conservation', 'wildlife protection',
                    'forest conservation', 'marine conservation', 'coastal management',
                    'disaster management', 'climate change', 'global warming', 'ozone depletion',
                    'sustainable development', 'renewable energy', 'nuclear energy',
                    'economic reforms', 'financial inclusion', 'digital india',
                    'make in india', 'startup india', 'skill india', 'swachh bharat',
                    'ayushman bharat', 'pm kisan', 'pm fasal bima yojana',
                    'directive principles', 'fundamental rights', 'constitutional rights',
                    'parliamentary democracy', 'federal structure', 'judicial review',
                    'public administration', 'civil services', 'local government',
                    'urban development', 'rural development', 'agricultural reforms',
                    'industrial policy', 'foreign policy', 'defense policy',
                    'social welfare', 'health care', 'education policy',
                    'science technology', 'space technology', 'information technology',
                    'telecommunications', 'transport infrastructure', 'energy security',
                    'food security', 'water security', 'national security',
                    'border management', 'coastal security', 'cyber security',
                    'internal security', 'external security', 'strategic autonomy',
                    'regional cooperation', 'bilateral relations', 'multilateral forums',
                    'trade agreements', 'investment treaties', 'economic diplomacy',
                    'cultural diplomacy', 'soft power', 'hard power',
                    'smart power', 'comprehensive power', 'national interest',
                    'public interest', 'social justice', 'economic justice',
                    'environmental justice', 'climate justice', 'gender justice',
                    'tribal rights', 'minority rights', 'human rights',
                    'civil liberties', 'political rights', 'economic rights',
                    'social rights', 'cultural rights', 'environmental rights'
                ]
                def normalize_phrase(s):
                    return s.replace(' ', '').lower()
                subtopic_norm = normalize_phrase(subtopic_clean)
                for concept in multi_word_concepts:
                    if normalize_phrase(concept) == subtopic_norm:
                        metadata = {
                            "topic": topic,
                            "subtopic1": concept.title(),
                            "subtopic2": "",
                            "subtopic3": "",
                            "subtopic4": "",
                            "subtopic5": "",
                            "author": author
                        }
                        break
                else:
                    # Default: assign the cleaned phrase, title-cased, to subtopic1
                    metadata = {
                        "topic": topic,
                        "subtopic1": subtopic_clean.title(),
                        "subtopic2": "",
                        "subtopic3": "",
                        "subtopic4": "",
                        "subtopic5": "",
                        "author": author
                    }
        elif len(parts) == 2:
            topic = parts[0]
            author = parts[1].replace('-', ' ').replace('.', ' ').title()
            metadata = {
                "topic": topic,
                "subtopic1": "",
                "subtopic2": "",
                "subtopic3": "",
                "subtopic4": "",
                "subtopic5": "",
                "author": author
            }
        else:
            topic = parts[0] if parts else "Unknown"
            metadata = {
                "topic": topic,
                "subtopic1": "",
                "subtopic2": "",
                "subtopic3": "",
                "subtopic4": "",
                "subtopic5": "",
                "author": None
            }
        return metadata

def extract_meaningful_subtopic(filename: str, topic: str = "", author: str = "") -> str:
    """
    Extract meaningful subtopic from filename by removing redundant information.
    
    Args:
        filename: The filename to extract subtopic from
        topic: The topic (to avoid redundancy)
        author: The author (to avoid redundancy)
        
    Returns:
        Clean subtopic string
    """
    if not filename:
        return ""
    
    # Convert to lowercase for comparison
    filename_lower = filename.lower()
    topic_lower = topic.lower()
    author_lower = author.lower()
    
    # Remove topic if it appears in filename
    if topic and topic_lower in filename_lower:
        filename = filename.replace(topic, "").replace(topic_lower, "")
    
    # Remove author if it appears in filename (handle variations)
    if author:
        # Handle space-separated author names
        author_parts = author.split()
        for part in author_parts:
            if part.lower() in filename_lower:
                filename = filename.replace(part, "").replace(part.lower(), "")
        # Also try the full author name
        if author_lower in filename_lower:
            filename = filename.replace(author, "").replace(author_lower, "")
    
    # Remove common prefixes and suffixes
    prefixes_to_remove = [
        "economy_", "economic_", "polity_", "constitution_", "history_",
        "geography_", "environment_", "science_", "technology_"
    ]
    
    suffixes_to_remove = [
        "_2025", "_2024", "_2023", "_2022", "_2021", "_2020",
        "_2019", "_2018", "_2017", "_2016", "_2015"
    ]
    
    # Remove prefixes
    for prefix in prefixes_to_remove:
        if filename_lower.startswith(prefix.lower()):
            filename = filename[len(prefix):]
            break
    
    # Remove suffixes
    for suffix in suffixes_to_remove:
        if filename_lower.endswith(suffix.lower()):
            filename = filename[:-len(suffix)]
            break
    
    # Special handling for ECONOMIC SURVEY patterns
    if "economic survey" in filename_lower:
        import re
        # Remove "ECONOMIC SURVEY" and year patterns
        filename = re.sub(r'economic\s*survey\s*\d{4}', '', filename, flags=re.IGNORECASE)
        filename = re.sub(r'economic\s*survey', '', filename, flags=re.IGNORECASE)
    
    # Clean up underscores and extra spaces
    filename = filename.replace("_", " ").strip()
    
    # Remove duplicate words
    words = filename.split()
    unique_words = []
    for word in words:
        if word.lower() not in [w.lower() for w in unique_words]:
            unique_words.append(word)
    
    result = " ".join(unique_words)
    
    # If result is empty or too short, return original cleaned filename
    if len(result.strip()) < 3:
        return filename.replace("_", " ").strip()
    
    return result

def clean_subtopic_text(subtopic: str) -> str:
    """
    Clean up subtopic text by removing common artifacts and normalizing.
    
    Args:
        subtopic: Raw subtopic text from filename
        
    Returns:
        Cleaned subtopic text
    """
    if not subtopic:
        return ""
    
    # Remove common artifacts
    cleaned = subtopic
    
    # Remove common suffixes/artifacts
    artifacts_to_remove = [
        "UNDERLINE",
        "MARKDOWN",
        "MD",
        "TXT",
        "PDF"
    ]
    
    for artifact in artifacts_to_remove:
        cleaned = cleaned.replace(artifact, "")
    
    # Clean up special characters and formatting
    cleaned = cleaned.replace('_', ' ')
    cleaned = cleaned.replace('-', ' ')
    cleaned = cleaned.replace('.', ' ')
    
    # Remove extra whitespace
    cleaned = ' '.join(cleaned.split())
    
    return cleaned.strip()

def split_compound_subtopic(subtopic: str) -> list:
    """
    Split compound subtopics into meaningful parts.
    
    Examples:
    - "SPECIALISEDAGENCIES" -> ["Specialized", "Agencies"]
    - "CLIMATE CHANGE CONVENTIONS" -> ["Climate Change Conventions"]
    - "LAXMIKANTCENTRE PARLIAMENT" -> ["Centre", "Parliament"]
    """
    if not subtopic:
        return []
    
    # Convert to lowercase for comparison
    subtopic_lower = subtopic.lower()
    
    # Handle patterns that should NOT be split (keep as single concepts)
    phrases_to_keep_together = [
        "climate change conventions",
        "climate change",
        "specialized agencies",
        "specialised agencies",
        "international organizations",
        "united nations",
        "world trade organization",
        "advent of europeans",
        "freedom struggle",
        "national movement", 
        "economic survey",
        "ancient civilization",
        "medieval period",
        "modern history",
        "colonial rule",
        "independence movement",
        "partition of india",
        "gandhi era",
        "nehru era",
        "planning commission",
        "green revolution",
        "economic reforms",
        "liberalization privatization globalization",
        "digital india",
        "make in india",
        "startup india",
        "skill india",
        "swachh bharat",
        "beti bachao beti padhao",
        "pradhan mantri jan dhan yojana",
        "pradhan mantri fasal bima yojana",
        "pradhan mantri kisan samman nidhi",
        "ayushman bharat",
        "pm kisan",
        "pm fasal bima yojana",
        "pm jan dhan yojana",
        "directive principles",
        "fundamental rights",
        "constitutional directive principles",
        "constitutional fundamental rights"
    ]
    
    # Check for phrases that should stay together FIRST
    for phrase in phrases_to_keep_together:
        if phrase in subtopic_lower:
            return [phrase.title()]
    
    # Handle specific compound patterns that need special splitting
    compound_patterns = [
        # Laxmikant patterns
        ("laxmikantcentre", "Centre"),
        ("laxmikant centre", "Centre"),
        ("laxmikantcentre parliament", "Centre Parliament"),
        ("laxmikant centre parliament", "Centre Parliament"),
        
        # Specialized/Specialised patterns
        ("specialisedagencies", "Specialized Agencies"),
        ("specializedagencies", "Specialized Agencies"),
        
        # Ancient patterns
        ("ancient civilization", "Ancient Civilization"),
        ("ancient dynasties", "Ancient Dynasties"),
        
        # Other common patterns
        ("economic survey", "Economic Survey"),
        ("national movement", "National Movement"),
        ("freedom struggle", "Freedom Struggle"),
    ]
    
    # Check for specific patterns
    for pattern, replacement in compound_patterns:
        if pattern in subtopic_lower:
            # Replace the pattern and split the result
            cleaned = subtopic_lower.replace(pattern, replacement.lower())
            parts = [part.strip().title() for part in cleaned.split() if part.strip()]
            return parts
    
    # General splitting for all-caps or mixed-case compound words
    if subtopic.isupper() or (subtopic != subtopic.lower() and subtopic != subtopic.upper()):
        # Split on common boundaries
        import re
        # Split on camelCase, UPPERCASE, or word boundaries
        parts = re.split(r'(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|\s+', subtopic)
        parts = [part.strip().title() for part in parts if part.strip()]
        return parts
    
    # Simple space-based splitting
    return [part.strip().title() for part in subtopic.split() if part.strip()]

def extract_hierarchical_metadata(filepath: str) -> Dict[str, str]:
    """
    Extract hierarchical metadata from filepath structure.
    
    Example: Polity/Laxmikant/CONSTITUTIONAL/Directive_Principles/Part_IV.md
    Returns: topic=Polity, author=Laxmikant, subtopic1=CONSTITUTIONAL, etc.
    """
    path_parts = Path(filepath).parts
    
    # Skip if path is too short
    if len(path_parts) < 2:
        return {}
    
    metadata = {
        "topic": "",
        "subtopic1": "",
        "subtopic2": "",
        "subtopic3": "",
        "subtopic4": "",
        "subtopic5": "",
        "author": ""
    }
    
    # Map path depth to metadata fields
    # Example: ['data', 'furnace', 'Polity', 'Laxmikant', 'CONSTITUTIONAL', 'Directive_Principles', 'Part_IV.md']
    
    # Skip common prefix directories and full path prefixes
    start_idx = 0
    skip_patterns = [
        'data', 'furnace', 'output_excels', 'chunks',
        'Users', 'pranjalsingh', 'Desktop', 'alchemy-bot (feeder data)',
        'alchemy-bot', 'feeder data'
    ]
    
    # Handle the full path structure
    for i, part in enumerate(path_parts):
        # Skip root and system path components
        if part in ['/', 'Users', 'pranjalsingh', 'Desktop']:
            start_idx = i + 1
            continue
        # Skip project-specific paths
        if part in ['data', 'furnace', 'output_excels', 'chunks']:
            start_idx = i + 1
            continue
        # Skip the full project folder name (handle trailing spaces)
        if 'alchemy-bot' in part or 'feeder data' in part:
            start_idx = i + 1
            continue
        # Once we find the first meaningful part, stop
        break
    
    relevant_parts = path_parts[start_idx:]
    
    if len(relevant_parts) >= 1:
        metadata["topic"] = relevant_parts[0]
    
    # For the second part, check if it looks like an author or a folder
    if len(relevant_parts) >= 2:
        second_part = relevant_parts[1]
        # If it contains parentheses or looks like a year/folder, treat as subtopic
        if '(' in second_part or second_part.isupper() or any(char.isdigit() for char in second_part):
            metadata["subtopic1"] = second_part
        else:
            metadata["author"] = second_part
    
    # Map remaining parts to subtopics
    start_subtopic_idx = 2 if metadata.get("author") else 1
    subtopic_parts = []
    
    for i, part in enumerate(relevant_parts[start_subtopic_idx:], 1):
        if i <= 5:  # Limit to subtopic1-5
            # Clean up filename extension
            clean_part = part.replace('.md', '').replace('.xlsx', '')
            
            # Intelligently extract meaningful subtopic from filename
            meaningful_subtopic = extract_meaningful_subtopic(clean_part, metadata.get("topic", ""), metadata.get("author", ""))
            
            # Split compound subtopics
            if meaningful_subtopic:
                split_parts = split_compound_subtopic(meaningful_subtopic)
                subtopic_parts.extend(split_parts)
    
    # Assign split parts to subtopic fields
    for i, part in enumerate(subtopic_parts[:5], 1):
        metadata[f"subtopic{i}"] = part
    
    return metadata

def clean_sheet_name(sheet_name: str) -> str:
    """
    Clean sheet names by removing underscores and normalizing formatting.
    """
    if not sheet_name:
        return ""
    
    # Remove underscores and replace with spaces
    cleaned = sheet_name.replace('_', ' ')
    
    # Remove common Excel artifacts
    cleaned = cleaned.replace('Sheet1', '').replace('Sheet2', '').replace('Sheet3', '')
    cleaned = cleaned.replace('Worksheet1', '').replace('Worksheet2', '')
    
    # Clean up extra whitespace
    cleaned = ' '.join(cleaned.split())
    
    return cleaned

def extract_excel_metadata(filename: str, sheet_name: str = None) -> Dict[str, str]:
    """
    Extract enhanced metadata from Excel files, including sheet names.
    
    Args:
        filename: Excel file path
        sheet_name: Optional sheet name
        
    Returns:
        Dictionary with topic, subtopic1-5, author fields
    """
    base = os.path.basename(filename)
    
    # Primary: Use filename-based extraction (most Excel files follow this pattern)
    if "__" in base:
        topic, subtopic1 = base.split("__", 1)
        topic = topic.strip()
        subtopic1 = os.path.splitext(subtopic1)[0].strip()
        # Clean up subtopic text (remove extra underscores, artifacts)
        subtopic1 = clean_subtopic_text(subtopic1)
    else:
        topic = os.path.splitext(base)[0]
        subtopic1 = ""
    
    # Enhance with sheet name if available (but skip generic sheet names like "Sheet1")
    subtopic2 = ""
    if sheet_name:
        cleaned_sheet_name = clean_sheet_name(sheet_name)
        if cleaned_sheet_name and cleaned_sheet_name.lower() not in ["sheet1", "sheet2", "sheet3", "worksheet1", "worksheet2"]:
            if not subtopic1:
                subtopic1 = extract_meaningful_subtopic(cleaned_sheet_name)
            else:
                # Add sheet name as subtopic2
                subtopic2 = extract_meaningful_subtopic(cleaned_sheet_name)
    
    return {
        "topic": topic,
        "subtopic1": subtopic1,
        "subtopic2": subtopic2,
        "subtopic3": "",
        "subtopic4": "",
        "subtopic5": "",
        "author": "Excel"
    }

def extract_author_from_filename(filename: str, topic: Optional[str]=None) -> Optional[str]:
    base = Path(filename).name
    parts = base[:-3].split('_')  # remove .md
    if len(parts) >= 3:
        author = parts[1].replace('-', ' ').replace('.', ' ').title()
        if topic and author.replace(' ', '').lower() == (topic or '').replace(' ', '').lower():
            return None
        return author
    return None

def build_chunk_id(topic: str, author: Optional[str], section_stack: List[str], chunk_idx: int, chunk_type: str = "markdown", additional_info: str = "") -> str:
    """
    Build a consistent chunk ID for both Excel and Markdown chunks.
    
    Args:
        topic: The main topic
        author: The author (optional)
        section_stack: List of section names
        chunk_idx: Chunk index
        chunk_type: Either "markdown" or "excel"
        additional_info: Additional info like row number for Excel
    
    Returns:
        Consistent chunk ID string
    """
    parts = [slugify(topic)]
    
    if author:
        parts.append(slugify(author))
    
    # Add section information
    for section in section_stack:
        if section:
            parts.append(slugify(section))
    
    # Add chunk type identifier
    parts.append(chunk_type)
    
    # Add additional info (e.g., row number for Excel)
    if additional_info:
        parts.append(slugify(additional_info))
    
    # Add chunk index
    parts.append(f"{chunk_idx:03d}")
    
    return '_'.join(parts)

def generate_concept_tags(chunk: dict) -> list:
    """Generate concept tags from topic/subtopic fields in chunk metadata."""
    return [chunk.get(f, "") for f in ["topic", "subtopic1", "subtopic2", "subtopic3", "subtopic4", "subtopic5"] if chunk.get(f, "")]

def map_ner_to_domain_tags(chunk: dict) -> list:
    """Map NER entity fields to human-usable domain tags."""
    from ..config import DOMAIN_TAG_MAPPING
    
    tags = []
    for field, tag in DOMAIN_TAG_MAPPING.items():
        if chunk.get(field) and isinstance(chunk[field], list) and len(chunk[field]) > 0:
            tags.append(tag)
    return tags 