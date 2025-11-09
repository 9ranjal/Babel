import re
from typing import List, Tuple, Optional, Dict
import spacy

def parse_markdown_sections(md_lines: List[str]) -> List[Tuple[str, str]]:
    """
    Parse markdown into sections using header markers and Pandoc underline markers.
    - Detects lines starting with '#', allowing leading whitespace
    - Also treats lines with '{.underline}' as section titles
    - Aggregates subsequent lines as section content until next title
    """
    sections: List[Tuple[str, str]] = []
    current_title: str = "Untitled"
    current_content: List[str] = []

    header_re = re.compile(r"^\s*#{1,6}\s*(.+?)\s*$")

    for i, raw_line in enumerate(md_lines):
        line = raw_line.rstrip("\n")
        stripped = line.strip()
        if not stripped:
            continue

        m = header_re.match(line)
        is_underline_heading = ("{.underline}" in line)

        if m or is_underline_heading:
            # Flush previous section
            if current_content:
                sections.append((current_title, "\n".join(current_content)))
                current_content = []
            # Set new title from header text or the whole line (underline case)
            current_title = m.group(1) if m else stripped
        else:
            current_content.append(stripped)

    # Flush tail
    if current_content:
        sections.append((current_title, "\n".join(current_content)))

    # Ensure minimal content and valid titles
    final_sections: List[Tuple[str, str]] = []
    for title, content in sections:
        if title and content and len(content.strip()) > 5:
            final_sections.append((title, content))

    return final_sections

def extract_document_structure(sections: List[Tuple[str, str]]) -> Dict[str, str]:
    """
    Extract document structure from parsed sections.
    
    Args:
        sections: List of (title, content) tuples from parse_markdown_sections
        
    Returns:
        Dictionary with document_title, section_id, section_heading
    """
    structure = {
        "document_title": "",
        "section_id": "",
        "section_heading": ""
    }
    
    if not sections:
        return structure
    
    # First section title becomes document title
    first_title, _ = sections[0]
    if first_title and first_title != "Untitled":
        structure["document_title"] = first_title
    
    # Generate section_id from document title
    if structure["document_title"]:
        structure["section_id"] = slugify(structure["document_title"])
    
    # Section heading is the current section title
    if sections:
        current_title, _ = sections[0]
        structure["section_heading"] = current_title
    
    return structure

def slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug.
    
    Args:
        text: Text to convert
        
    Returns:
        URL-friendly slug
    """
    import re
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')

def is_fact_like(text: str) -> bool:
    """
    Determine if a chunk of text is fact-like based on linguistic patterns.
    
    Args:
        text: The text to analyze
        
    Returns:
        bool: True if the text appears to be factual, False otherwise
    """
    # Convert to lowercase for pattern matching
    text_lower = text.lower()
    
    # Fact-like indicators
    fact_indicators = [
        r'\d{4}',  # Years
        r'\d+%',   # Percentages
        r'\d+\.\d+',  # Decimal numbers
        r'according to',
        r'research shows',
        r'studies indicate',
        r'data shows',
        r'statistics show',
        r'found that',
        r'discovered',
        r'identified',
        r'measured',
        r'calculated',
        r'estimated',
        r'approximately',
        r'about',
        r'nearly',
        r'roughly'
    ]
    
    # Opinion-like indicators
    opinion_indicators = [
        r'i think',
        r'i believe',
        r'in my opinion',
        r'it seems',
        r'it appears',
        r'probably',
        r'maybe',
        r'perhaps',
        r'possibly',
        r'could be',
        r'might be',
        r'should be',
        r'ought to',
        r'better',
        r'worse',
        r'good',
        r'bad',
        r'excellent',
        r'terrible'
    ]
    
    # Count matches
    fact_count = sum(1 for pattern in fact_indicators if re.search(pattern, text_lower))
    opinion_count = sum(1 for pattern in opinion_indicators if re.search(pattern, text_lower))
    
    # Determine if fact-like based on ratio
    total_indicators = fact_count + opinion_count
    if total_indicators == 0:
        # If no clear indicators, check for other fact-like patterns
        has_numbers = bool(re.search(r'\d+', text))
        has_dates = bool(re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', text))
        has_names = bool(re.search(r'[A-Z][a-z]+ [A-Z][a-z]+', text))
        return has_numbers or has_dates or has_names
    
    fact_ratio = fact_count / total_indicators
    return fact_ratio >= 0.6  # Threshold for fact-like content 