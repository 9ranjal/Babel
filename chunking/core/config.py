"""
Centralized configuration for the chunking pipeline.
All constants, paths, thresholds, and model names are defined here.
"""

import os
from pathlib import Path

# ─── Environment Variables ───
def get_env_path(key: str, default: str) -> str:
    """Get path from environment variable or use default."""
    return os.getenv(key, default)

# ─── Base Paths ───
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# ─── Input Paths ───
FURNACE_INPUT_DIR = get_env_path("FURNACE_INPUT_DIR", "/Users/pranjalsingh/Desktop/alchemy-bot (feeder data)/furnace")
EXCEL_INPUT_DIR = get_env_path("EXCEL_INPUT_DIR", "/Users/pranjalsingh/Desktop/alchemy-bot (feeder data)/output_excels")

# ─── Output Paths ───
CHUNK_OUTPUT_DIR = DATA_DIR / "chunks"
MARKDOWN_OUTPUT_DIR = CHUNK_OUTPUT_DIR / "markdown"
EXCEL_OUTPUT_DIR = CHUNK_OUTPUT_DIR / "excel"
FINAL_OUTPUT_DIR = CHUNK_OUTPUT_DIR / "final"

# ─── Checkpoint and Temporary Paths ───
CHECKPOINT_PATH = DATA_DIR / "checkpoints"
TEMP_PATH = DATA_DIR / "temp"

# ─── QA and Analysis Paths ───
QA_DIR = DATA_DIR / "qa"
QA_MARKDOWN_DIR = QA_DIR / "markdown"
QA_EXCEL_DIR = QA_DIR / "excel"
QA_MASTER_DIR = QA_DIR / "master"

# ─── Optional Metadata Toggles ───
# Control verbose debug metadata in chunks (reduces JSON bloat when disabled)
INCLUDE_PROCESSING_STEPS = os.getenv("INCLUDE_PROCESSING_STEPS", "true").lower() in {"1", "true", "yes"}

# ─── Metadata Paths ───
EXCEL_META_PATH = DATA_DIR / "excel_metadata.json"

# ─── Embedding Configuration ───
EMBEDDING_MODEL = "bge-large-en-v1.5"
EMBEDDING_DIM = 1024
EMBEDDING_NORMALIZE = True

# ─── Embedding Storage Configuration ───
SAVE_VECTORS_IN_JSON = False  # Set to True for development, False for production
COMPRESS_JSON_FILES = True    # Enable gzip compression for JSON files
EMBEDDING_COMPRESSION_LEVEL = 6  # gzip compression level (1-9, higher = smaller but slower)
VALIDATE_EMBEDDINGS = True    # Validate embedding format and dimensions

# ─── NLP Configuration ───
SPACY_MODEL = get_env_path("SPACY_MODEL", "en_core_web_trf")
BATCH_SIZE = 8  # Reduced for better memory management
N_PROCESS = 1   # macOS safe - avoid fork issues
MAX_MEMORY_CHUNKS = 1000

# ─── Chunking Thresholds ───
MARKDOWN_MAX_WORDS = 500
MARKDOWN_MIN_WORDS = 15
MARKDOWN_SHORT_THRESHOLD = 15

EXCEL_MAX_WORDS = 200
EXCEL_MIN_WORDS = 8
EXCEL_SHORT_THRESHOLD = 8

MERGE_MAX_WORDS = 150
CHUNK_SIZE = 100
OVERLAP_RATIO = 0.3

# ─── Quality and Scoring Thresholds ───
MARKDOWN_RETRIEVAL_THRESHOLD = 0.3
EXCEL_RETRIEVAL_THRESHOLD = 0.2
MIN_RETRIEVAL_SCORE = 0.3
ENTITY_DENSITY_THRESHOLD = 0.01

# ─── Supabase Configuration ───
SUPABASE_URL = "https://oycvxbembwatvvpppnfw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im95Y3Z4YmVtYndhdHZ2cHBwbmZ3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTAwMzE1NCwiZXhwIjoyMDY2NTc5MTU0fQ.p-LqSBWFsBplDVDsh_RJ8W9yXMs-qyMihLycAluD50I"

# ─── File Patterns ───
MARKDOWN_FILE_PATTERN = "*.md"
EXCEL_FILE_PATTERN = "*.xlsx"
CHUNK_FILE_PATTERN = "*_chunks_*.json"
FINAL_CHUNK_PATTERN = "final_chunks*.json"

# ─── Protected Semantic Types ───
PROTECTED_TYPES = [
    "constitutional_principle", "definition", "factual",
    # Polity - Deep
    "fundamental_rights", "directive_principles", "federal_structure", "parliamentary_system", 
    "legislative_process", "state_legislature", "presidential_system", "prime_ministerial", 
    "bureaucracy", "state_executive", "supreme_court", "high_court", "judicial_review", 
    "lower_judiciary", "electoral_system", "election_commission", "electoral_process", 
    "panchayati_raj", "urban_governance", "decentralization",
    # History - Deep
    "indus_valley", "vedic_period", "mauryan_empire", "gupta_empire", "ancient_civilization", 
    "delhi_sultanate", "mughal_empire", "medieval_kingdoms", "british_rule", "freedom_struggle", 
    "gandhi_era", "partition_independence", "nehru_era", "republic_era", "planning_era", 
    "green_revolution", "economic_reforms", "art_architecture", "literature_culture", "music_dance",
    # Science & Technology - Deep
    "human_anatomy", "medical_diagnosis", "medical_treatment", "genetics_biotechnology", 
    "cancer_oncology", "ecosystem_ecology", "biodiversity_conservation", "pollution_environmental", 
    "climate_atmospheric", "information_technology", "renewable_energy", "space_technology", 
    "biotechnology", "scientific_research", "innovation_technology", "quantum_physics", "nanotechnology",
    # Economy - Deep
    "gdp_growth", "inflation_monetary", "fiscal_policy", "employment_labor", "banking_sector", 
    "capital_markets", "insurance_sector", "digital_finance", "international_trade", "current_account", 
    "trade_policy", "agricultural_production", "agricultural_policy", "rural_development", 
    "manufacturing_sector", "service_sector", "infrastructure_development",
    # Geography - Deep
    "landforms_terrain", "water_bodies", "coastal_marine", "climatic_zones", "population_demography", 
    "settlement_patterns", "migration_mobility", "resource_distribution", "agricultural_geography", 
    "industrial_geography", "indian_geography", "world_geography",
    # Environment - Deep
    "air_pollution", "water_pollution", "soil_pollution", "noise_pollution", "biodiversity_conservation", 
    "endangered_species", "ecosystem_protection", "climate_change_impact", "greenhouse_emissions", 
    "climate_policy", "renewable_energy", "sustainable_practices", "green_technology", 
    "environmental_law", "environmental_assessment",
    # Current Affairs - Deep
    "government_schemes", "policy_announcements", "budget_announcements", "recent_developments", 
    "new_launches", "year_specific", "diplomatic_relations", "international_agreements", 
    "foreign_policy", "global_affairs", "bilateral_relations", "multilateral_cooperation", 
    "regional_cooperation", "neighborhood_policy"
]

# ─── Entity Types ───
# Expanded per user request to include additional spaCy entity types used in the corpus
ENTITY_TYPES = [
    # HIGH-VALUE ENTITIES (optimized for RAG)
    "PERSON",   # Essential for biographical queries
    "ORG",      # Government, institutions
    "GPE",      # Countries, states, cities  
    "DATE",     # Historical events, timelines
    "MONEY",    # Economic data
    "PERCENT",  # Statistics, economic indicators
    "LAW",      # Acts, constitutional articles
    "EVENT",    # Historical events, movements

    # Additional entities now included
    "LOC",          # Non-political locations (e.g., seas, basins, regions)
    "CARDINAL",     # Cardinal numbers (counts, enumerations)
    "QUANTITY",     # Measurements and numeric quantities
    # Remaining standard spaCy types now included
    "NORP",         # Nationalities, religious/political groups
    "FAC",          # Facilities (buildings, airports, highways, bridges)
    "PRODUCT",      # Objects, vehicles, foods, etc. (not services)
    "WORK_OF_ART",  # Titles of books, songs, etc.
    "LANGUAGE",     # Any named language
    "TIME",         # Times smaller than a day
    "ORDINAL",      # First, second, etc.
]

# ─── Entity Type Groupings for UPSC Context (optimized) ───
ENTITY_TYPE_GROUPS = {
    "geographic": ["GPE"],
    "statistical": ["PERCENT", "MONEY"],
    "temporal": ["DATE"],
    "organizational": ["ORG"],
    "personal": ["PERSON"],
    "legal": ["LAW"],
    "events": ["EVENT"],
}

# ─── Domain Tags Mapping (optimized) ───
DOMAIN_TAG_MAPPING = {
    # HIGH-VALUE ENTITY MAPPINGS
    "person_entities": "Person",        # Essential for biographical queries
    "org_entities": "Organization",     # Government, institutions
    "gpe_entities": "Geography",        # Countries, states, cities
    "date_entities": "Date",            # Historical events, timelines
    "money_entities": "Monetary",       # Economic data
    "percent_entities": "Percentage",   # Statistics, economic indicators
    "law_entities": "Legal",            # Acts, constitutional articles
    "event_entities": "Event",          # Historical events, movements
}

# ─── Stop Words ───
STOP_WORDS = {
    'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
    'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
    'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must', 'shall'
}

# ─── Validation ───
REQUIRED_CHUNK_FIELDS = [
    "chunk_id", "chunk_text", "chunk_word_count", "topic", "author"
]

# ─── File Extensions ───
MARKDOWN_EXTENSIONS = [".md", ".markdown"]
EXCEL_EXTENSIONS = [".xlsx", ".xls"]
JSON_EXTENSIONS = [".json"]

# ─── Timestamp Format ───
TIMESTAMP_FORMAT = "%Y%m%d_%H%M"

# ─── Retry Configuration ───
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
REQUEST_TIMEOUT = 30  # seconds

# ─── Batch Processing ───
UPLOAD_BATCH_SIZE = 100
PROCESSING_BATCH_SIZE = 1000

# ─── QA Configuration ───
SAMPLE_SIZE = 30
CSV_EXPORT_LIMIT = 50
METRICS_HISTORY_RETENTION = 10  # number of historical metric files to keep

# ─── Performance Configuration ───
ENABLE_EXCEL_TEXT_POLISHING = True  # Set to True for better quality, False for speed
EXCEL_BATCH_SIZE = 100  # Process Excel rows in batches
USE_LARGE_T5_MODEL = False  # Set to False for faster processing

# ─── Text Polishing Configuration ───
T5_BATCH_SIZE = 8  # Batch size for T5 processing (8-16 recommended)
ENABLE_HEURISTIC_SKIP = True  # Skip polishing for already clean sentences
HEURISTIC_SKIP_MIN_WORDS = 30  # Skip polishing for sentences with 30+ words

# ─── Early Row Skipping Configuration ───
ENABLE_EARLY_ROW_SKIP = True  # Skip processing low-value rows early
MIN_NON_EMPTY_FIELDS = 2  # Minimum non-empty fields required (reduced from 3)
MAX_NUMERIC_RATIO = 0.9  # Skip rows with >90% numeric values (was 70%)
MIN_TEXT_FIELD_LENGTH = 5  # Minimum length for text fields (reduced from 10) 