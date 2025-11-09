from ..processing.text_cleaner import normalize_chunk_text, slugify
from typing import List

def classify_semantic_type_hierarchical(chunk: dict) -> dict:
    domain = classify_upsc_domain(chunk)
    cognitive_level = classify_cognitive_level(chunk)
    if not domain:
        domain = "General"
    if not cognitive_level:
        cognitive_level = "comprehension"
    result = {
        "primary": get_primary_type(chunk),
        "secondary": get_secondary_types(chunk),
        "domain": domain,
        "cognitive_level": cognitive_level,
        "question_type_affinity": predict_question_types(chunk)
    }
    patterns = detect_upsc_patterns(chunk)
    if patterns:
        result["patterns"] = patterns
    return result

def get_primary_type(chunk: dict) -> str:
    import re
    raw_text = chunk.get("chunk_text", "")
    text = raw_text.lower()  # Text is already normalized in enrichment step
    word_count = chunk.get("chunk_word_count", 0)
    
    # Get metadata for override logic
    concept_tags = chunk.get("concept_tags", [])
    entity_texts = chunk.get("entity_texts", {})
    topic = chunk.get("topic", "").lower()
    subtopic1 = chunk.get("subtopic1", "").lower()
    
    # 🔧 ENHANCED: Critical UPSC term overrides (highest priority)
    # Ramsar sites and wetlands
    if "ramsar" in text or "wetland" in text or "ramsar site" in text:
        return "biodiversity_conservation"
    
    # Submarine and underwater features
    if any(term in text for term in ["submarine canyon", "submarine canyons", "underwater valley", "underwater valleys", "continental shelf", "continental slope", "abyssal plain"]):
        return "landforms_terrain"
    
    # Oceanic and marine features
    if any(term in text for term in ["oceanic", "marine", "submarine", "underwater", "deep sea", "ocean floor"]):
        return "landforms_terrain"
    
    # Quote/Source detection (keep existing logic)
    if re.search(r"\b(as per|according to|states that|mentioned in|as stated by|report says|committee observed)\b", text):
        return "quote_or_source"
    if re.search(r"\b(as per|according to|states that|mentioned in|as stated by|report says|committee observed)\b", raw_text.lower()):
        return "quote_or_source"
    
    # Definition detection (keep existing logic)
    if re.search(r"\b(means|refers to|defined as|is known as|called|termed as|concept of|principle of)\b", text):
        return "definition"
    if re.search(r"\b(means|refers to|defined as|is known as|called|termed as|concept of|principle of)\b", raw_text.lower()):
        return "definition"
    
    # Timeline detection (keep existing logic)
    if len(chunk.get("date_entities", [])) >= 2:
        return "timeline"
    
    # Comparison detection (keep existing logic)
    if any(p in text for p in ["compared to", "whereas", "in contrast", "versus", "difference between", "both", "respectively", "unlike", "distinction", "on the other hand", "while", "but"]):
        return "comparison"
    
    # 🔧 ENHANCED: Scoring-based semantic classification
    # Normalize text for better keyword matching
    normalized_text = re.sub(r'\W+', ' ', text)
    
    # Define category keywords with scoring weights
    CATEGORY_KEYWORDS = {
        # Environment & Conservation
        "biodiversity_conservation": ["ramsar", "wetland", "national park", "biosphere", "protected area", "flora", "fauna", "wildlife", "conservation", "endangered", "species", "habitat", "ecosystem", "biodiversity", "reserve", "sanctuary"],
        "pollution_environmental": ["pollution", "contamination", "environmental", "air pollution", "water pollution", "soil pollution", "noise pollution", "pollutant", "contaminant", "emission", "waste"],
        "climate_atmospheric": ["climate", "atmosphere", "weather", "temperature", "rainfall", "monsoon", "climatic", "climate change", "global warming", "greenhouse", "atmospheric", "meteorological"],
        
        # Geography & Landforms
        "landforms_terrain": ["landform", "terrain", "topography", "mountain", "hill", "peak", "valley", "plain", "plateau", "desert", "canyon", "underwater valleys", "continental shelf", "continental slope", "submarine", "oceanic", "marine", "geological", "geomorphological"],
        "water_bodies": ["river", "lake", "ocean", "sea", "stream", "pond", "water body", "water resource", "drainage", "watershed", "aquifer", "groundwater", "surface water"],
        "coastal_marine": ["coast", "coastal", "marine", "island", "peninsula", "bay", "gulf", "strait", "submarine", "beach", "shore", "littoral"],
        
        # Technology (with more specific keywords)
        "information_technology": ["internet", "software", "hardware", "programming", "coding", "algorithm", "data", "digital", "cyber", "web site", "artificial intelligence", "machine learning", "computer", "app", "database", "cybersecurity", "blockchain", "cloud computing"],
        "space_technology": ["space", "satellite", "rocket", "spacecraft", "orbit", "astronaut", "space technology", "space science", "space exploration", "launch vehicle", "remote sensing"],
        "renewable_energy": ["renewable energy", "solar", "wind", "hydro", "geothermal", "biomass", "clean energy", "green energy", "sustainable energy", "photovoltaic", "turbine"],
        
        # Polity & Governance
        "constitutional_principle": ["constitution", "constitutional", "basic structure", "fundamental rights", "directive principles", "federalism", "secularism", "democracy", "rule of law", "constitutional amendment", "constitutional provision"],
        "judicial_review": ["judicial review", "article 13", "article 32", "basic structure", "supreme court", "high court", "writ", "habeas corpus", "judicial activism", "public interest litigation"],
        "parliamentary_system": ["parliament", "lok sabha", "rajya sabha", "speaker", "parliamentary", "bicameral", "legislative", "parliamentary procedure", "question hour", "zero hour"],
        
        # History
        "ancient_civilization": ["ancient", "ancient india", "ancient civilization", "ancient culture", "ancient period", "indus valley", "harappan", "vedic", "mauryan", "gupta", "ancient dynasty"],
        "mughal_empire": ["mughal", "mughal empire", "mughal dynasty", "babur", "akbar", "aurangzeb", "mughal period", "mughal architecture", "mughal administration"],
        "british_rule": ["british", "colonial", "colonial rule", "british rule", "east india company", "crown rule", "colonial administration", "british raj"],
        
        # Economy
        "gdp_growth": ["gdp", "gross domestic product", "economic growth", "economic development", "economic expansion", "economic performance", "economic indicator"],
        "inflation_monetary": ["inflation", "monetary", "monetary policy", "inflation rate", "price level", "consumer price index", "reserve bank", "monetary authority"],
        "banking_sector": ["banking", "bank", "commercial bank", "public sector bank", "private sector bank", "banking sector", "financial institution", "credit", "loan"],
        
        # Current Affairs
        "government_schemes": ["scheme", "program", "initiative", "mission", "campaign", "yojana", "abhiyan", "government scheme", "welfare scheme", "development program"],
        "policy_announcements": ["policy", "announcement", "decision", "reform", "measure", "step", "government policy", "policy framework"],
    }
    
    # Calculate scores for each category
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in normalized_text)
        scores[category] = score
    
    # Pick the category with highest score
    if scores:
        best_category, best_score = max(scores.items(), key=lambda x: x[1])
        
        # 🔧 ENHANCED OVERRIDE LOGIC: Prevent domain-inconsistent labels
        if best_score > 0:
            # Override IT classification if strong environmental/geographic signals exist
            if best_category == "information_technology":
                # Check for environmental/geographic metadata
                env_geo_tags = ["environment", "ecology", "geography", "geographic", "environmental", "physical", "oceanic", "marine"]
                if any(tag.lower() in env_geo_tags for tag in concept_tags):
                    return "biodiversity_conservation"
                
                # Check for specific environmental keywords that should override IT
                env_keywords = ["ramsar", "wetland", "national park", "biosphere", "flora", "fauna", "wildlife", "conservation", "habitat", "ecosystem", "submarine", "underwater", "continental shelf", "continental slope", "oceanic", "marine", "geological"]
                if any(kw in normalized_text for kw in env_keywords):
                    return "biodiversity_conservation"
                
                # Check topic/subtopic for geographic/environmental context
                geo_topics = ["geography", "environment", "ecology", "oceans", "physical", "geological"]
                if topic in geo_topics or subtopic1 in geo_topics:
                    return "landforms_terrain"
            
            # 🔧 ENHANCED: Topic-based overrides
            if topic == "geography" and best_category == "information_technology":
                return "landforms_terrain"
            
            if topic == "environment" and best_category == "information_technology":
                return "biodiversity_conservation"
            
            return best_category
    
    # Fallback checks (keep existing logic)
    if chunk.get("is_fact_like") and word_count < 30:
        return "factual"
    
    # Biographical check
    BIO_KEYWORDS = ["born", "died", "biography", "life of", "contribution of"]
    FALSE_PERSONS = {"earth", "sun", "moon", "mars", "venus", "jupiter", "saturn", "uranus", "neptune", "pluto"}
    person_entities = [str(p).strip().lower() for p in chunk.get("person_entities", [])]
    if (
        any(b in text for b in BIO_KEYWORDS) or
        (
            person_entities and
            word_count < 100 and
            any(p not in FALSE_PERSONS for p in person_entities)
        )
    ):
        return "biographical"
    
    # Procedural check
    if text.startswith("steps") or "how to" in text or "process of" in text or "steps involved" in text or "procedure for" in text:
        return "procedural"
    
    # Analytical check
    if any(a in text for a in ["analysis", "criticism", "debate", "however", "nevertheless"]):
        return "analytical"
    
    # Final factual check
    if word_count <= 40 and chunk.get("entity_density", 0) > 0.15:
        return "factual"
    
    return "other"

def get_secondary_types(chunk: dict) -> list:
    text = chunk.get("chunk_text", "").lower()
    tags = []
    if len(chunk.get("date_entities", [])) >= 2:
        tags.append("timeline")
    if any(marker in text for marker in ["as per", "according to", "states that", "mentioned in"]):
        tags.append("quote_or_source")
    if chunk.get("chunk_type") == "excel" and chunk.get("has_number") and chunk.get("chunk_word_count", 0) <= 15:
        tags.append("numerical_stat")
    if any(k in text for k in ["tribe", "species", "biosphere", "origin", "pass", "festival", "dance", "art form", "classical", "traditional", "folk"]):
        tags.append("map_pairing")
    if any(a in text for a in ["analysis", "criticism", "debate", "however", "nevertheless"]):
        tags.append("analytical")
    if chunk.get("person_entities") and len(chunk.get("person_entities")) > 1 and chunk.get("chunk_word_count", 0) < 100:
        tags.append("biographical")
    if any(l in text for l in ["act", "amendment", "bill", "ordinance", "legislation", "law"]):
        tags.append("legislative")
    return tags

def classify_upsc_domain(chunk: dict) -> str:
    tags = chunk.get("concept_tags", [])
    tags_slug = [slugify(t) for t in tags]
    topic = tags[0] if tags else ""
    subtopic = tags[1] if len(tags) > 1 else ""
    domain_map = {
        "History": ["Ancient", "Medieval", "Modern", "Culture"],
        "Geography": ["Physical", "Human", "Environmental", "Economic"],
        "Polity": ["Constitutional", "Institutional", "Governance"],
        "Economy": ["Macro", "Micro", "Developmental", "Sectoral"],
    }
    for subject, subs in domain_map.items():
        if slugify(subject) in tags_slug:
            for sub in subs:
                if slugify(sub) in tags_slug:
                    return f"{subject}.{sub}"
            return f"{subject}.General"
    text = chunk.get("chunk_text", "").lower()
    if "constitution" in text or "article" in text:
        return "Polity.Constitutional"
    if "river" in text or "mountain" in text:
        return "Geography.Physical"
    if "gdp" in text or "inflation" in text:
        return "Economy.Macro"
    return "General"

def classify_cognitive_level(chunk: dict) -> str:
    text = chunk.get("chunk_text", "").lower()
    if any(k in text for k in ["founded in", "capital of", "born in", "established in"]):
        return "recall"
    if any(k in text for k in ["means", "refers to", "defined as", "is known as"]):
        return "comprehension"
    if any(k in text for k in ["factors", "reasons", "components", "causes", "analysis", "explain"]):
        return "analysis"
    if any(k in text for k in ["suggest", "recommend", "propose", "design"]):
        return "synthesis"
    if any(k in text for k in ["evaluate", "assess", "judge", "critique"]):
        return "evaluation"
    if any(k in text for k in ["apply", "use", "demonstrate", "implement"]):
        return "application"
    return "comprehension"

def predict_question_types(chunk: dict) -> list:
    types = []
    text = chunk.get("chunk_text", "").lower()
    if chunk.get("chunk_word_count", 0) < 30 and chunk.get("entity_density", 0) > 0.15:
        types.append("prelims_factual")
    if any(k in text for k in ["compared to", "respectively"]):
        types.append("prelims_comparison")
    if get_primary_type(chunk) == "procedural" or classify_upsc_domain(chunk) == "Polity.Governance":
        types.append("mains_governance")
    if "current" in text or "recent" in text:
        types.append("mains_current_relevance")
    return types

def detect_upsc_patterns(chunk: dict) -> list:
    text = chunk.get("chunk_text", "").lower()
    patterns = []
    if any(k in text for k in ["except", "not", "which of the following"]):
        patterns.append("exception_pattern")
    if any(k in text for k in ["because:", "statement 1", "statement 2"]):
        patterns.append("statement_reason")
    if any(k in text for k in ["not true", "incorrect", "false"]):
        patterns.append("negative_questioning")
    if all(k in text for k in ["both", "all"]) or "respectively" in text:
        patterns.append("multiple_correct")
    return patterns 