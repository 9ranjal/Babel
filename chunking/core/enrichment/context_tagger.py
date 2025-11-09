#!/usr/bin/env python3
"""
Context Tagging Module
Generates semantic context tags for chunks based on content analysis.
"""

import re
from typing import Dict, Any, List, Set
from ..config import ENTITY_TYPE_GROUPS

def generate_context_tags(chunk: Dict[str, Any]) -> List[str]:
    """
    Generate context tags for a chunk based on content analysis.
    
    Args:
        chunk: Chunk dictionary with text and metadata
        
    Returns:
        List of context tags
    """
    tags = set()  # Use set to avoid duplicates
    
    chunk_text = chunk.get("chunk_text", "").lower() if chunk.get("chunk_text") else ""
    semantic_type = chunk.get("semantic_type", {})
    primary_type = semantic_type.get("primary", "") if isinstance(semantic_type, dict) else ""
    section_heading = chunk.get("section_heading", "").lower() if chunk.get("section_heading") else ""
    
    # Combine text sources for analysis
    analysis_text = f"{chunk_text} {section_heading}"
    
    # 1. Cause and Effect Patterns
    if any(pattern in analysis_text for pattern in [
        "causes of", "caused by", "due to", "because of", "as a result",
        "leads to", "results in", "consequently", "therefore", "thus"
    ]):
        tags.add("cause")
    
    # 2. Example Patterns
    if any(pattern in analysis_text for pattern in [
        "examples of", "for example", "such as", "including", "like",
        "e.g.", "for instance", "specifically", "notably"
    ]):
        tags.add("example")
    
    # 3. Comparison Patterns
    if any(pattern in analysis_text for pattern in [
        "difference between", "compared to", "versus", "vs", "unlike",
        "similar to", "in contrast", "on the other hand", "however",
        "while", "whereas", "although", "but"
    ]):
        tags.add("comparison")
    
    # 4. Statistical Patterns
    if any(pattern in analysis_text for pattern in [
        "%", "percent", "percentage", "gdp", "growth rate", "statistics",
        "data shows", "according to data", "survey", "study found",
        "research indicates", "figures show", "numbers indicate"
    ]):
        tags.add("statistical")
    
    # 5. Timeline Patterns
    if any(pattern in analysis_text for pattern in [
        "timeline", "chronology", "sequence", "order of events",
        "first", "second", "third", "finally", "initially",
        "subsequently", "afterwards", "before", "during", "while"
    ]):
        tags.add("timeline")
    
    # 6. Scheme/Policy Patterns
    if any(pattern in analysis_text for pattern in [
        "scheme", "policy", "program", "initiative", "plan",
        "government scheme", "central scheme", "state scheme",
        "ministry of", "department of", "authority", "commission"
    ]):
        tags.add("scheme")
    
    # 7. Definition Patterns
    if any(pattern in analysis_text for pattern in [
        "definition", "defined as", "means", "refers to", "is known as",
        "called", "termed", "concept of", "principle of", "theory of"
    ]):
        tags.add("definition")
    
    # 8. Process/Procedure Patterns
    if any(pattern in analysis_text for pattern in [
        "process", "procedure", "steps", "method", "technique",
        "how to", "procedure for", "process of", "methodology",
        "approach", "strategy", "mechanism"
    ]):
        tags.add("process")
    
    # 9. Location/Geography Patterns
    if any(pattern in analysis_text for pattern in [
        "located in", "situated in", "found in", "geography of",
        "region", "area", "zone", "district", "state", "country",
        "continent", "ocean", "river", "mountain", "valley"
    ]):
        tags.add("geographic")
    
    # 10. Historical Patterns
    if any(pattern in analysis_text for pattern in [
        "history", "historical", "ancient", "medieval", "modern",
        "era", "period", "dynasty", "empire", "kingdom", "rule",
        "reign", "century", "decade", "year", "bce", "ce", "ad"
    ]):
        tags.add("historical")
    
    # 11. Legal/Constitutional Patterns
    if any(pattern in analysis_text for pattern in [
        "constitution", "constitutional", "article", "amendment",
        "act", "law", "legislation", "bill", "ordinance", "rule",
        "regulation", "judgment", "court", "supreme court", "high court"
    ]):
        tags.add("legal")
    
    # 12. Economic Patterns
    if any(pattern in analysis_text for pattern in [
        "economy", "economic", "finance", "financial", "budget",
        "fiscal", "monetary", "inflation", "deflation", "recession",
        "growth", "development", "investment", "trade", "commerce"
    ]):
        tags.add("economic")
    
    # 13. Environmental Patterns
    if any(pattern in analysis_text for pattern in [
        "environment", "environmental", "climate", "pollution",
        "conservation", "biodiversity", "ecosystem", "sustainable",
        "green", "renewable", "energy", "forest", "wildlife"
    ]):
        tags.add("environmental")
    
    # 14. Scientific/Technical Patterns
    if any(pattern in analysis_text for pattern in [
        "science", "scientific", "technology", "technical", "research",
        "study", "experiment", "discovery", "innovation", "development",
        "laboratory", "scientist", "engineer", "analysis", "theory"
    ]):
        tags.add("scientific")
    
    # 15. Social/Cultural Patterns
    if any(pattern in analysis_text for pattern in [
        "society", "social", "culture", "cultural", "tradition",
        "custom", "religion", "religious", "festival", "celebration",
        "community", "people", "population", "demographics"
    ]):
        tags.add("social")
    
    # 16. Political Patterns
    if any(pattern in analysis_text for pattern in [
        "politics", "political", "government", "administration",
        "democracy", "election", "vote", "parliament", "legislature",
        "executive", "judiciary", "bureaucracy", "ministry"
    ]):
        tags.add("political")
    
    # 17. Health/Medical Patterns
    if any(pattern in analysis_text for pattern in [
        "health", "medical", "disease", "treatment", "medicine",
        "hospital", "doctor", "patient", "symptom", "diagnosis",
        "vaccine", "immunization", "public health"
    ]):
        tags.add("health")
    
    # 18. Education Patterns
    if any(pattern in analysis_text for pattern in [
        "education", "educational", "school", "university", "college",
        "student", "teacher", "curriculum", "syllabus", "examination",
        "learning", "teaching", "academic", "scholarship"
    ]):
        tags.add("education")
    
    # 19. Infrastructure Patterns
    if any(pattern in analysis_text for pattern in [
        "infrastructure", "road", "highway", "railway", "airport",
        "port", "bridge", "dam", "power plant", "telecommunication",
        "internet", "digital", "connectivity", "transport"
    ]):
        tags.add("infrastructure")
    
    # 20. Agriculture Patterns
    if any(pattern in analysis_text for pattern in [
        "agriculture", "farming", "crop", "farmer", "irrigation",
        "fertilizer", "pesticide", "harvest", "yield", "production",
        "food security", "rural", "village", "land"
    ]):
        tags.add("agriculture")
    
    # Semantic type based tags
    if primary_type:
        semantic_tags = {
            "timeline": "timeline",
            "comparison": "comparison", 
            "definition": "definition",
            "factual": "factual",
            "quote_or_source": "quote",
            "constitutional_principle": "legal",
            "fundamental_rights": "legal",
            "directive_principles": "legal",
            "federal_structure": "political",
            "parliamentary_system": "political",
            "legislative_process": "political",
            "state_legislature": "political",
            "supreme_court": "legal",
            "high_court": "legal",
            "judicial_review": "legal",
            "electoral_system": "political",
            "election_commission": "political",
            "panchayati_raj": "political",
            "urban_governance": "political",
            "decentralization": "political",
            "indus_valley": "historical",
            "vedic_period": "historical",
            "mauryan_empire": "historical",
            "gupta_empire": "historical",
            "ancient_civilization": "historical",
            "delhi_sultanate": "historical",
            "mughal_empire": "historical",
            "medieval_kingdoms": "historical",
            "british_rule": "historical",
            "freedom_struggle": "historical",
            "gandhi_era": "historical",
            "partition_independence": "historical",
            "nehru_era": "historical",
            "republic_era": "historical",
            "planning_era": "economic",
            "green_revolution": "agriculture",
            "economic_reforms": "economic",
            "art_architecture": "cultural",
            "literature_culture": "cultural",
            "music_dance": "cultural",
            "human_anatomy": "health",
            "medical_diagnosis": "health",
            "medical_treatment": "health",
            "genetics_biotechnology": "scientific",
            "cancer_oncology": "health",
            "ecosystem_ecology": "environmental",
            "biodiversity_conservation": "environmental",
            "pollution_environmental": "environmental",
            "climate_atmospheric": "environmental",
            "information_technology": "scientific",
            "renewable_energy": "environmental",
            "space_technology": "scientific",
            "biotechnology": "scientific",
            "scientific_research": "scientific",
            "innovation_technology": "scientific",
            "quantum_physics": "scientific",
            "nanotechnology": "scientific",
            "gdp_growth": "economic",
            "inflation_monetary": "economic",
            "fiscal_policy": "economic",
            "employment_labor": "economic",
            "banking_sector": "economic",
            "capital_markets": "economic",
            "insurance_sector": "economic",
            "digital_finance": "economic",
            "international_trade": "economic",
            "current_account": "economic",
            "trade_policy": "economic",
            "agricultural_production": "agriculture",
            "agricultural_policy": "agriculture",
            "rural_development": "agriculture",
            "manufacturing_sector": "economic",
            "service_sector": "economic",
            "infrastructure_development": "infrastructure",
            "landforms_terrain": "geographic",
            "water_bodies": "geographic",
            "coastal_marine": "geographic",
            "climatic_zones": "geographic",
            "population_demography": "social",
            "settlement_patterns": "geographic",
            "migration_mobility": "social",
            "resource_distribution": "economic",
            "agricultural_geography": "agriculture",
            "industrial_geography": "economic",
            "indian_geography": "geographic",
            "world_geography": "geographic",
            "air_pollution": "environmental",
            "water_pollution": "environmental",
            "soil_pollution": "environmental",
            "noise_pollution": "environmental",
            "endangered_species": "environmental",
            "ecosystem_protection": "environmental",
            "climate_change_impact": "environmental",
            "greenhouse_emissions": "environmental",
            "climate_policy": "environmental",
            "sustainable_practices": "environmental",
            "green_technology": "environmental",
            "environmental_law": "environmental",
            "environmental_assessment": "environmental",
            "government_schemes": "scheme",
            "policy_announcements": "political",
            "budget_announcements": "economic",
            "recent_developments": "current_affairs",
            "new_launches": "current_affairs",
            "year_specific": "current_affairs",
            "diplomatic_relations": "political",
            "international_agreements": "political",
            "foreign_policy": "political",
            "global_affairs": "current_affairs",
            "bilateral_relations": "political",
            "multilateral_cooperation": "political",
            "regional_cooperation": "political",
            "neighborhood_policy": "political"
        }
        
        if primary_type in semantic_tags:
            tags.add(semantic_tags[primary_type])
    
    # Entity-based tags
    entity_counts = chunk.get("entity_counts", {})
    
    # Geographic entities
    geographic_entities = sum(entity_counts.get(ent_type, 0) for ent_type in ["GPE", "LOC", "FAC"])
    if geographic_entities > 0:
        tags.add("geographic")
    
    # Statistical entities
    statistical_entities = sum(entity_counts.get(ent_type, 0) for ent_type in ["NUMBER", "PERCENT", "MONEY", "QUANTITY", "CARDINAL", "ORDINAL"])
    if statistical_entities > 0:
        tags.add("statistical")
    
    # Temporal entities
    temporal_entities = sum(entity_counts.get(ent_type, 0) for ent_type in ["DATE", "TIME"])
    if temporal_entities > 0:
        tags.add("timeline")
    
    # Legal entities
    legal_entities = entity_counts.get("LAW", 0)
    if legal_entities > 0:
        tags.add("legal")
    
    # Organizational entities
    org_entities = entity_counts.get("ORG", 0)
    if org_entities > 0:
        tags.add("organizational")
    
    # Personal entities
    person_entities = entity_counts.get("PERSON", 0)
    if person_entities > 0:
        tags.add("personal")
    
    return sorted(list(tags))  # Convert back to sorted list

def get_context_tag_descriptions() -> Dict[str, str]:
    """Get descriptions for all possible context tags."""
    return {
        "cause": "Cause and effect relationships",
        "example": "Examples and illustrations", 
        "comparison": "Comparisons and contrasts",
        "statistical": "Statistical data and numbers",
        "timeline": "Chronological sequences and dates",
        "scheme": "Government schemes and programs",
        "definition": "Definitions and explanations",
        "process": "Processes and procedures",
        "geographic": "Geographic and location information",
        "historical": "Historical events and periods",
        "legal": "Legal and constitutional content",
        "economic": "Economic and financial content",
        "environmental": "Environmental and ecological content",
        "scientific": "Scientific and technical content",
        "social": "Social and cultural content",
        "political": "Political and governance content",
        "health": "Health and medical content",
        "education": "Educational content",
        "infrastructure": "Infrastructure and development",
        "agriculture": "Agricultural content",
        "organizational": "Organizations and institutions",
        "personal": "People and personalities",
        "quote": "Quotes and references",
        "factual": "Factual information",
        "current_affairs": "Current events and developments",
        "cultural": "Cultural and artistic content"
    } 