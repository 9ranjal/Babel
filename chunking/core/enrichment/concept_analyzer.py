"""
Concept tag extraction for UPSC chunks.
Extracts concept tags using multiple methods including TF-IDF, UPSC concept matching, etc.
"""

from typing import Dict, List, Optional, Set
import re
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
import json
from pathlib import Path

class ConceptAnalyzer:
    """
    Extracts concept tags from chunks using multiple methods.
    """
    
    def __init__(self):
        self.upsc_concepts = self._load_upsc_concepts()
        self.tfidf_vectorizer = None
        self.corpus_vocabulary = set()
    
    def _load_upsc_concepts(self) -> Dict[str, Set[str]]:
        """Load HIERARCHICAL UPSC concept taxonomy for better RAG organization."""
        # OPTIMIZED: Hierarchical structure for better concept clustering
        concepts = {
            # POLITY DOMAIN
            "polity.constitutional": {
                "constitution", "fundamental rights", "directive principles", "amendment",
                "constitutional development", "judicial review", "separation of powers"
            },
            "polity.governance": {
                "parliament", "democracy", "federalism", "election commission", 
                "political parties", "local government", "panchayati raj", "bureaucracy"
            },
            
            # ECONOMY DOMAIN  
            "economy.macroeconomic": {
                "gdp", "inflation", "fiscal policy", "monetary policy", "budget",
                "balance of payments", "economic indicators", "growth"
            },
            "economy.sectors": {
                "banking", "finance", "taxation", "agriculture", "industry", 
                "services", "foreign direct investment", "trade"
            },
            "economy.reforms": {
                "liberalization", "privatization", "globalization", "subsidies",
                "economic reforms", "new economic policy"
            },
            
            # ENVIRONMENT DOMAIN
            "environment.conservation": {
                "biodiversity", "conservation", "wildlife protection", "forest conservation",
                "ecosystem", "sustainability", "environmental protection"
            },
            "environment.climate": {
                "climate change", "carbon footprint", "renewable energy", 
                "global warming", "climate policy", "environmental impact"
            },
            "environment.pollution": {
                "pollution", "air pollution", "water pollution", "waste management",
                "environmental degradation", "pollution control"
            },
            
            # GEOGRAPHY DOMAIN
            "geography.physical": {
                "physical geography", "climate", "vegetation", "soil", "minerals",
                "water resources", "landforms", "natural resources"
            },
            "geography.human": {
                "human geography", "population", "urbanization", "migration",
                "settlements", "transportation", "regional planning"
            },
            
            # HISTORY DOMAIN
            "history.ancient": {
                "ancient history", "ancient civilization", "archaeology", 
                "cultural heritage", "art and architecture", "ancient india"
            },
            "history.medieval": {
                "medieval history", "mughal empire", "sultanate period",
                "medieval architecture", "medieval society"
            },
            "history.modern": {
                "modern history", "independence movement", "freedom struggle",
                "british rule", "social reform movements", "nationalist movement"
            },
            
            # SCIENCE & TECHNOLOGY DOMAIN
            "science.technology": {
                "information technology", "biotechnology", "nanotechnology", "space technology",
                "nuclear technology", "artificial intelligence", "robotics", "cybersecurity"
            },
            "science.digital": {
                "digital india", "e-governance", "digital transformation", "fintech",
                "blockchain", "internet of things", "big data"
            },
            
            # INTERNATIONAL RELATIONS DOMAIN
            "international.diplomacy": {
                "diplomacy", "foreign policy", "bilateral relations", "multilateral forums",
                "united nations", "regional cooperation", "climate diplomacy"
            },
            "international.security": {
                "security", "terrorism", "defense", "nuclear policy", "border management",
                "internal security", "cybersecurity"
            }
        }
        return concepts
    
    def extract_concept_tags(self, chunk: Dict, corpus_context: Optional[List[str]] = None) -> List[str]:
        """
        Extract concept tags from chunk using multiple methods.
        
        Args:
            chunk: Chunk dictionary
            corpus_context: Optional list of chunk texts for corpus analysis
            
        Returns:
            List of concept tags
        """
        concepts = set()
        
        chunk_text = chunk.get("chunk_text", "")
        if not chunk_text:
            return list(concepts)
        
        # Method 1: UPSC concept matching
        upsc_concepts = self._upsc_concept_matching(chunk_text)
        concepts.update(upsc_concepts)
        
        # Method 2: TF-IDF extraction (if corpus available)
        if corpus_context:
            tfidf_concepts = self._tfidf_extraction(chunk_text, corpus_context)
            concepts.update(tfidf_concepts)
        
        # Method 3: Topic hierarchy extraction
        topic_concepts = self._topic_hierarchy_extraction(chunk)
        concepts.update(topic_concepts)
        
        # Method 4: Entity-based concepts
        entity_concepts = self._entity_based_extraction(chunk)
        concepts.update(entity_concepts)
        
        # Method 5: Keyword extraction
        keyword_concepts = self._keyword_extraction(chunk_text)
        concepts.update(keyword_concepts)
        
        return list(concepts)
    
    def _upsc_concept_matching(self, text: str) -> Set[str]:
        """Match text against HIERARCHICAL UPSC concept taxonomy."""
        concepts = set()
        text_lower = text.lower()
        
        # Match against hierarchical concept structure
        for hierarchy_key, concept_set in self.upsc_concepts.items():
            matches = 0
            matched_concepts = []
            
            for concept in concept_set:
                # Check for exact phrase match
                if concept.lower() in text_lower:
                    matched_concepts.append(concept)
                    matches += 1
            
            # If we have matches, add the hierarchical tag
            if matches > 0:
                concepts.add(hierarchy_key)  # e.g., "polity.constitutional"
                
                # Also add specific concepts for detailed tagging
                concepts.update(matched_concepts[:3])  # Limit to top 3 specific matches
        
        return concepts
    
    def _tfidf_extraction(self, text: str, corpus: List[str]) -> Set[str]:
        """Extract concepts using TF-IDF analysis."""
        concepts = set()
        
        try:
            # Initialize TF-IDF vectorizer if not done
            if self.tfidf_vectorizer is None:
                self.tfidf_vectorizer = TfidfVectorizer(
                    max_features=1000,
                    stop_words='english',
                    ngram_range=(1, 3),
                    min_df=2,
                    max_df=0.8
                )
                # Fit on corpus
                self.tfidf_vectorizer.fit(corpus)
                self.corpus_vocabulary = set(self.tfidf_vectorizer.get_feature_names_out())
            
            # Transform the text
            text_vector = self.tfidf_vectorizer.transform([text])
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            
            # Get top features
            top_indices = text_vector.toarray()[0].argsort()[-10:][::-1]  # Top 10
            
            for idx in top_indices:
                if text_vector[0, idx] > 0.1:  # Threshold
                    feature = feature_names[idx]
                    # Only add if it's a meaningful concept
                    if len(feature) > 3 and not feature.isdigit():
                        concepts.add(feature)
        
        except Exception as e:
            # Fallback to simple keyword extraction
            pass
        
        return concepts
    
    def _topic_hierarchy_extraction(self, chunk: Dict) -> Set[str]:
        """Extract concepts from topic hierarchy."""
        concepts = set()
        
        # Add topic and subtopics as concepts
        topic = chunk.get("topic", "")
        if topic:
            concepts.add(topic.lower())
        
        for i in range(1, 6):
            subtopic = chunk.get(f"subtopic{i}", "")
            if subtopic:
                concepts.add(subtopic.lower())
        
        return concepts
    
    def _entity_based_extraction(self, chunk: Dict) -> Set[str]:
        """
        Extract high-level themes from entities.
        Focuses on conceptual categories, not specific entity names.
        """
        concepts = set()
        
        # Extract conceptual themes from entity types, not specific names
        person_entities = chunk.get("entities", {}).get("person_entities", [])
        if person_entities:
            concepts.add("personality")  # High-level theme
        
        entity_data = chunk.get("entities", {})
        org_entities = entity_data.get("org_entities", [])
        if org_entities:
            concepts.add("institutional")  # High-level theme
        
        gpe_entities = entity_data.get("gpe_entities", [])
        if gpe_entities:
            concepts.add("geographic")  # High-level theme
        
        # Add domain-specific themes based on entity patterns
        if len(person_entities) > 2:
            concepts.add("biographical")
        
        if len(org_entities) > 2:
            concepts.add("organizational")
        
        if len(gpe_entities) > 2:
            concepts.add("spatial")
        
        return concepts
    
    def _keyword_extraction(self, text: str) -> Set[str]:
        """
        Extract high-level conceptual themes from text.
        Focuses on thematic concepts, not specific keywords.
        """
        concepts = set()
        
        # Define high-level conceptual themes
        theme_patterns = {
            "celestial": ["star", "galaxy", "planet", "moon", "sun", "space", "astronomical", "cosmic"],
            "geographic": ["mountain", "river", "ocean", "continent", "region", "territory", "landscape"],
            "temporal": ["ancient", "medieval", "modern", "historical", "contemporary", "timeline"],
            "quantitative": ["statistical", "numerical", "measurement", "calculation", "percentage"],
            "institutional": ["government", "organization", "institution", "bureaucracy", "administration"],
            "economic": ["financial", "monetary", "fiscal", "economic", "commercial", "trade"],
            "environmental": ["ecological", "environmental", "conservation", "sustainability", "biodiversity"],
            "social": ["societal", "community", "cultural", "demographic", "population"],
            "technological": ["technological", "innovation", "digital", "automation", "artificial"],
            "political": ["political", "governance", "democracy", "authority", "leadership"]
        }
        
        text_lower = text.lower()
        
        # Match themes based on keyword presence
        for theme, keywords in theme_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                concepts.add(theme)
        
        return concepts
    
    def get_concept_confidence(self, chunk: Dict, concept: str) -> float:
        """
        Get confidence score for a specific concept.
        
        Args:
            chunk: Chunk dictionary
            concept: Concept to check
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        chunk_text = chunk.get("chunk_text", "").lower()
        concept_lower = concept.lower()
        
        # Check exact match
        if concept_lower in chunk_text:
            return 1.0
        
        # Check partial match
        if concept_lower.replace(" ", "") in chunk_text.replace(" ", ""):
            return 0.8
        
        # Check word-level match
        concept_words = concept_lower.split()
        chunk_words = set(chunk_text.split())
        matches = sum(1 for word in concept_words if word in chunk_words)
        
        if len(concept_words) > 0:
            return matches / len(concept_words)
        
        return 0.0 