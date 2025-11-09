import hashlib
import re
from ..processing.text_cleaner import normalize_chunk_text
from .metadata import generate_concept_tags, map_ner_to_domain_tags
from ..analysis.semantics import classify_semantic_type_hierarchical
from ..analysis.scoring import calculate_entity_density, calculate_retrieval_score
from .excel_rewriter import rewrite_list_chunk
from .embedding import get_embedding
import numpy as np

# Retrieval score threshold constants
EXCEL_RETRIEVAL_THRESHOLD = 0.2
MARKDOWN_RETRIEVAL_THRESHOLD = 0.3

def extract_retrieval_keywords(chunk: dict) -> list:
    """Extract MINIMAL retrieval keywords - only critical abbreviations and codes.
    
    OPTIMIZATION: Reduced 80% - modern embeddings handle semantic similarity.
    Focus only on exact-match terms that embeddings might miss.
    """
    keywords = set()
    
    # Extract only critical abbreviations and codes  
    text = chunk.get("chunk_text", "")
    
    # Critical patterns: abbreviations, codes, acts, years
    critical_patterns = [
        r'\b[A-Z]{2,5}\b',  # Abbreviations: GDP, SEZ, UPSC, etc.
        r'\b\d{4}\b',       # Years: 1991, 2000, etc.
        r'\w+\s+Act\b',     # Acts: Sarfaesi Act, etc.
        r'\bArticle\s+\d+', # Constitutional articles
        r'\bSection\s+\d+'  # Legal sections
    ]
    
    for pattern in critical_patterns:
        matches = re.findall(pattern, text)
        keywords.update([m.lower() for m in matches])
    
    # Add only entity abbreviations (not full names - embeddings handle those)
    entity_texts = chunk.get("entities", {}).get("entity_texts", {})
    for entity_list in entity_texts.values():
        for entity in entity_list:
            # Only add if it's an abbreviation (all caps, 2-5 chars)
            if entity and entity.isupper() and 2 <= len(entity) <= 5:
                keywords.add(entity.lower())
    
    # Filter for only the most critical terms
    keywords = {kw for kw in keywords if len(kw) >= 2}
    
    # DRASTICALLY reduced: max 5 keywords (was 20)
    return list(keywords)[:5]

def detect_and_resolve_references(chunk, all_chunks_in_doc):
    """Detect reference phrases and resolve to section headings/chunk_ids using regex and embedding similarity."""
    text = chunk.get("chunk_text", "")
    references = []
    
    # Early return if no other chunks to compare against
    if not all_chunks_in_doc:
        return references
    
    # Regex patterns for common references
    patterns = [
        r'see (above|below|section [\w\d]+|table [\w\d]+|figure [\w\d]+)',
        r'as discussed (above|earlier|in [\w\d\s]+)',
        r'(refer to|see also) ([\w\d\s]+)',
        r'(table|figure) ([\w\d]+)',
    ]
    found_refs = []
    for pat in patterns:
        for match in re.findall(pat, text, re.IGNORECASE):
            # Flatten match tuple to string
            if isinstance(match, tuple):
                ref_text = " ".join([str(m) for m in match if m])
            else:
                ref_text = match
            found_refs.append(ref_text.strip())
    
    # Pre-filter chunks with valid headings and embeddings
    valid_chunks = [
        (other_chunk.get("section_heading", ""), other_chunk.get("embedding", None), other_chunk.get("chunk_id", ""))
        for other_chunk in all_chunks_in_doc
        if other_chunk.get("section_heading") and other_chunk.get("embedding") is not None
    ]
    
    # Try to resolve each reference to a heading/chunk
    for ref in found_refs:
        best_match = None
        best_score = 0.0
        
        # Only compute embedding if we have valid chunks to compare against
        if valid_chunks:
            ref_emb = get_embedding(ref)
            
            for heading, heading_emb, chunk_id in valid_chunks:
                # Cosine similarity
                sim = np.dot(ref_emb, heading_emb) / (np.linalg.norm(ref_emb) * np.linalg.norm(heading_emb) + 1e-8)
                if sim > best_score:
                    best_score = sim
                    best_match = {
                        "matched_heading": heading,
                        "matched_chunk_id": chunk_id,
                        "similarity": float(sim)
                    }
        
        references.append({
            "ref_text": ref,
            "best_match": best_match
        })
    
    return references

def process_chunk_for_rag(chunk: dict, all_chunks_in_doc=None) -> dict:
    chunk = rewrite_list_chunk(chunk)
    chunk["chunk_text"] = normalize_chunk_text(chunk.get("chunk_text", ""))
    # REMOVED: Replaced by hierarchical concept tagging in enhancer.py ConceptAnalyzer
    # chunk["concept_tags"] = generate_concept_tags(chunk)
    chunk["domain_tags"] = map_ner_to_domain_tags(chunk)
    chunk["semantic_type"] = classify_semantic_type_hierarchical(chunk)
    if chunk.get("semantic_type") is None:
        chunk["semantic_type"] = {"primary": "other"}
    chunk["entity_density"] = calculate_entity_density(chunk)
    # Store retrieval score in nested structure (matches enhancer.py pattern)
    retrieval_score = calculate_retrieval_score(chunk)
    if "retrieval_metadata" not in chunk:
        chunk["retrieval_metadata"] = {}
    chunk["retrieval_metadata"]["retrieval_score"] = retrieval_score
    chunk["primary_entities"] = extract_primary_entities(chunk)
    chunk["retrieval_keywords"] = extract_retrieval_keywords(chunk)
    chunk["embedding"] = get_embedding(chunk["chunk_text"])
    # 🔧 NEW: Add cross-reference resolution for markdown
    if all_chunks_in_doc is not None and chunk.get("chunk_type") == "markdown":
        chunk["references"] = detect_and_resolve_references(chunk, all_chunks_in_doc)
    else:
        chunk["references"] = []
    norm_text = chunk["chunk_text"]
    chunk["chunk_hash"] = hashlib.sha256(norm_text.encode("utf-8")).hexdigest()
    # Protected semantic types that should never be omitted
    PROTECTED_TYPES = [
        "constitutional_principle", "definition", "factual",
        # Polity - Deep
        "fundamental_rights", "directive_principles", "federal_structure", "parliamentary_system", "legislative_process", "state_legislature", "presidential_system", "prime_ministerial", "bureaucracy", "state_executive", "supreme_court", "high_court", "judicial_review", "lower_judiciary", "electoral_system", "election_commission", "electoral_process", "panchayati_raj", "urban_governance", "decentralization",
        # History - Deep
        "indus_valley", "vedic_period", "mauryan_empire", "gupta_empire", "ancient_civilization", "delhi_sultanate", "mughal_empire", "medieval_kingdoms", "british_rule", "freedom_struggle", "gandhi_era", "partition_independence", "nehru_era", "republic_era", "planning_era", "green_revolution", "economic_reforms", "art_architecture", "literature_culture", "music_dance",
        # Science & Technology - Deep
        "human_anatomy", "medical_diagnosis", "medical_treatment", "genetics_biotechnology", "cancer_oncology", "ecosystem_ecology", "biodiversity_conservation", "pollution_environmental", "climate_atmospheric", "information_technology", "renewable_energy", "space_technology", "biotechnology", "scientific_research", "innovation_technology", "quantum_physics", "nanotechnology",
        # Economy - Deep
        "gdp_growth", "inflation_monetary", "fiscal_policy", "employment_labor", "banking_sector", "capital_markets", "insurance_sector", "digital_finance", "international_trade", "current_account", "trade_policy", "agricultural_production", "agricultural_policy", "rural_development", "manufacturing_sector", "service_sector", "infrastructure_development",
        # Geography - Deep
        "landforms_terrain", "water_bodies", "coastal_marine", "climatic_zones", "population_demography", "settlement_patterns", "migration_mobility", "resource_distribution", "agricultural_geography", "industrial_geography", "indian_geography", "world_geography",
        # Environment - Deep
        "air_pollution", "water_pollution", "soil_pollution", "noise_pollution", "biodiversity_conservation", "endangered_species", "ecosystem_protection", "climate_change_impact", "greenhouse_emissions", "climate_policy", "renewable_energy", "sustainable_practices", "green_technology", "environmental_law", "environmental_assessment",
        # Current Affairs - Deep
        "government_schemes", "policy_announcements", "budget_announcements", "recent_developments", "new_launches", "year_specific", "diplomatic_relations", "international_agreements", "foreign_policy", "global_affairs", "bilateral_relations", "multilateral_cooperation", "regional_cooperation", "neighborhood_policy"
    ]
    
    # Different omit logic for Excel vs Markdown chunks
    chunk_type = chunk.get("chunk_type", "markdown")
    semantic_type = chunk.get("semantic_type", {})
    primary_type = semantic_type.get("primary") if isinstance(semantic_type, dict) else semantic_type
    
    if primary_type in PROTECTED_TYPES:
        chunk["omit_flag"] = False
    elif chunk_type == "excel":
        # Excel chunks need lower retrieval score threshold
        retrieval_score = chunk.get("retrieval_metadata", {}).get("retrieval_score", 0)
        if retrieval_score < EXCEL_RETRIEVAL_THRESHOLD and primary_type not in ["elimination_hook", "numerical_stat"]:
            chunk["omit_flag"] = True
    else:
        # Markdown chunks - original threshold
        retrieval_score = chunk.get("retrieval_metadata", {}).get("retrieval_score", 0)
        if retrieval_score < MARKDOWN_RETRIEVAL_THRESHOLD and primary_type not in ["elimination_hook", "numerical_stat"]:
            chunk["omit_flag"] = True
    
    return chunk

def extract_primary_entities(chunk: dict) -> list:
    """Extract primary entities for the chunk."""
    entities = []
    
    # Access entities from nested structure
    entity_data = chunk.get("entities", {})
    
    # Add person entities
    entities.extend(entity_data.get("person_entities", []))
    
    # Add organization entities
    entities.extend(entity_data.get("org_entities", []))
    
    # Add geographic entities
    entities.extend(entity_data.get("gpe_entities", []))
    
    # Add law entities
    entities.extend(entity_data.get("law_entities", []))
    
    # Limit to top 5 most important entities
    return entities[:5]

def should_merge_chunks(chunk1: dict, chunk2: dict) -> bool:
    chunk_type1 = chunk1.get("chunk_type", "markdown")
    chunk_type2 = chunk2.get("chunk_type", "markdown")
    
    # Excel chunks are discrete by design - never merge them
    if chunk_type1 == "excel" or chunk_type2 == "excel":
        return False
    
    # Only merge markdown chunks
    if (
        chunk1.get("chunk_word_count", 0) < 50 and
        chunk2.get("chunk_word_count", 0) < 50 and
        chunk1.get("topic") == chunk2.get("topic") and
        chunk1.get("subtopic1") == chunk2.get("subtopic1")
    ):
        total = chunk1["chunk_word_count"] + chunk2["chunk_word_count"]
        return total <= 300
    
    return False 