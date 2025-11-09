def calculate_entity_density(chunk: dict) -> float:
    """Compute entity density from nested entities structure (v2 schema)."""
    entities = chunk.get("entities", {}) if isinstance(chunk.get("entities"), dict) else {}
    total_entities = 0
    for e in ["person", "org", "gpe", "date", "law"]:
        total_entities += len(entities.get(f"{e}_entities", []) or [])
    wc = chunk.get("chunk_word_count", 0) or 0
    if wc <= 0:
        return 0.0
    return total_entities / wc

def calculate_retrieval_score(chunk: dict) -> float:
    score = 0.0
    wc = chunk.get("chunk_word_count", 0)
    ed = chunk.get("entity_density", 0)
    chunk_type = chunk.get("chunk_type", "markdown")
    
    # Different scoring for Excel vs Markdown chunks
    if chunk_type == "excel":
        # Excel chunks are naturally short - more lenient scoring
        if 10 <= wc <= 100:  # Excel chunks are typically 10-100 words
            score += 0.3
        elif 5 <= wc <= 150:  # Allow even shorter Excel chunks
            score += 0.15
        # Lower entity density threshold for Excel
        if 2 <= ed * 100 <= 15:
            score += 0.25
    else:
        # Markdown chunks - original scoring
        if 100 <= wc <= 300:
            score += 0.3
        elif 20 <= wc <= 350:
            score += 0.15
        if 5 <= ed * 100 <= 20:
            score += 0.25
    
    semantic_type = chunk.get("semantic_type", {})
    primary_type = None
    if isinstance(semantic_type, dict):
        primary_type = semantic_type.get("primary") or semantic_type.get("primary_type") or None
    else:
        primary_type = semantic_type
    # High-value semantic types that get bonus points
    HIGH_VALUE_TYPES = [
        "factual", "definition", "constitutional_principle", "elimination_hook",
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
    
    if primary_type in HIGH_VALUE_TYPES:
        score += 0.2
    
    # Enhanced richness scoring
    try:
        score += calculate_chunk_richness_score(chunk)
    except Exception:
        pass
    
    if not chunk.get("omit_flag") and chunk.get("chunk_quality") == "ok":
        score += 0.15
    if len(chunk.get("concept_tags", [])) >= 2:
        score += 0.1
    return min(score, 1.0)

def calculate_chunk_richness_score(chunk: dict) -> float:
    """Calculate additional richness score based on content quality."""
    score = 0.0
    text = chunk.get("chunk_text", "")
    chunk_type = chunk.get("chunk_type", "markdown")
    
    # Multi-sentence coherence bonus
    sentences = text.split('.')
    if len(sentences) > 1:
        score += 0.1
    
    # Verb richness bonus (penalize listicle chunks without verbs)
    import re
    verbs = re.findall(r'\b(is|are|was|were|has|have|had|do|does|did|can|could|will|would|should|may|might)\b', text.lower())
    if verbs:
        score += 0.05
    
    # Multi-entity bonus
    entity_types = 0
    for ent_type in ["person_entities", "org_entities", "gpe_entities", "date_entities", "law_entities"]:
        if chunk.get(ent_type):
            entity_types += 1
    if entity_types >= 2:
        score += 0.05
    
    # Penalize pure listicle chunks (Excel-specific)
    if chunk_type == "excel":
        if "," in text and not any(kw in text.lower() for kw in ["is", "are", "was", "were", "has", "have", "had"]):
            score -= 0.1  # Penalty for pure lists without verbs
    
    return score 