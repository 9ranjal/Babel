"""
Domain classification for UPSC chunks.
Automatically classifies chunks into domains like Polity, Economy, Environment, etc.
"""

from typing import Dict, List, Optional
import json
from pathlib import Path

class DomainClassifier:
    """
    Classifies chunks into UPSC domains based on multiple indicators.
    """
    
    def __init__(self):
        self.domain_rules = self._load_domain_rules()
        self.topic_domain_mapping = self._load_topic_domain_mapping()
    
    def _load_domain_rules(self) -> Dict[str, Dict]:
        """Load domain classification rules."""
        return {
            "Polity": {
                "keywords": ["constitution", "parliament", "government", "election", "democracy", "rights", "amendment"],
                "entities": ["GOVT", "ORG", "LAW"],
                "semantic_types": ["definition", "timeline", "process"]
            },
            "Economy": {
                "keywords": ["gdp", "inflation", "budget", "fiscal", "monetary", "trade", "banking", "finance"],
                "entities": ["ORG", "MONEY", "PERCENT"],
                "semantic_types": ["definition", "data", "analysis"]
            },
            "Environment": {
                "keywords": ["climate", "pollution", "conservation", "biodiversity", "forest", "wildlife", "sustainability"],
                "entities": ["GPE", "ORG"],
                "semantic_types": ["definition", "issue", "solution"]
            },
            "Geography": {
                "keywords": ["river", "mountain", "climate", "soil", "agriculture", "region", "state"],
                "entities": ["GPE", "LOC"],
                "semantic_types": ["definition", "description", "location"]
            },
            "History": {
                "keywords": ["ancient", "medieval", "modern", "independence", "freedom", "movement", "dynasty"],
                "entities": ["PERSON", "DATE", "EVENT"],
                "semantic_types": ["timeline", "event", "biography"]
            },
            "Science": {
                "keywords": ["technology", "innovation", "research", "discovery", "experiment", "theory"],
                "entities": ["ORG", "PERSON"],
                "semantic_types": ["definition", "process", "discovery"]
            },
            "International Relations": {
                "keywords": ["diplomacy", "treaty", "alliance", "conflict", "peace", "united nations", "bilateral"],
                "entities": ["GPE", "ORG", "PERSON"],
                "semantic_types": ["event", "agreement", "policy"]
            }
        }
    
    def _load_topic_domain_mapping(self) -> Dict[str, str]:
        """Load direct topic to domain mapping."""
        return {
            "Polity": "Polity",
            "Constitution": "Polity",
            "Governance": "Polity",
            "Economy": "Economy",
            "Economics": "Economy",
            "Finance": "Economy",
            "Environment": "Environment",
            "Ecology": "Environment",
            "Geography": "Geography",
            "History": "History",
            "Science": "Science",
            "Technology": "Science",
            "International": "International Relations",
            "Diplomacy": "International Relations"
        }
    
    def classify_domain(self, chunk: Dict) -> List[str]:
        """
        Classify chunk into domains based on multiple indicators.
        
        Args:
            chunk: Chunk dictionary with metadata
            
        Returns:
            List of domain tags
        """
        domains = []
        
        # Method 1: Direct topic mapping
        topic_domains = self._topic_based_classification(chunk)
        domains.extend(topic_domains)
        
        # Method 2: Entity-based classification
        entity_domains = self._entity_based_classification(chunk)
        domains.extend(entity_domains)
        
        # Method 3: Semantic type classification
        semantic_domains = self._semantic_type_classification(chunk)
        domains.extend(semantic_domains)
        
        # Method 4: Keyword-based classification
        keyword_domains = self._keyword_based_classification(chunk)
        domains.extend(keyword_domains)
        
        # Remove duplicates and return
        return list(set(domains))
    
    def _topic_based_classification(self, chunk: Dict) -> List[str]:
        """Classify based on topic hierarchy."""
        domains = []
        
        # Check topic field
        topic = chunk.get("topic", "")
        if topic in self.topic_domain_mapping:
            domains.append(self.topic_domain_mapping[topic])
        
        # Check subtopics
        for i in range(1, 6):
            subtopic = chunk.get(f"subtopic{i}", "")
            if subtopic in self.topic_domain_mapping:
                domains.append(self.topic_domain_mapping[subtopic])
        
        return domains
    
    def _entity_based_classification(self, chunk: Dict) -> List[str]:
        """Classify based on entity mix."""
        domains = []
        
        # Get entity counts
        entity_counts = chunk.get("entity_counts", {})
        if not entity_counts:
            return domains
        
        # Analyze entity patterns
        for domain, rules in self.domain_rules.items():
            domain_entities = rules.get("entities", [])
            entity_score = 0
            
            for entity_type in domain_entities:
                if entity_type in entity_counts:
                    entity_score += entity_counts[entity_type]
            
            # If significant entity presence, add domain
            if entity_score >= 2:
                domains.append(domain)
        
        return domains
    
    def _semantic_type_classification(self, chunk: Dict) -> List[str]:
        """Classify based on semantic type."""
        domains = []
        
        semantic_type = chunk.get("semantic_type", {})
        if not semantic_type:
            return domains
        
        primary_type = semantic_type.get("primary", "")
        
        # Map semantic types to domains
        for domain, rules in self.domain_rules.items():
            domain_semantic_types = rules.get("semantic_types", [])
            if primary_type in domain_semantic_types:
                domains.append(domain)
        
        return domains
    
    def _keyword_based_classification(self, chunk: Dict) -> List[str]:
        """Classify based on keyword presence in text."""
        domains = []
        
        chunk_text = chunk.get("chunk_text", "")
        if chunk_text is None:
            chunk_text = ""
        chunk_text = chunk_text.lower()
        if not chunk_text:
            return domains
        
        # Check keyword patterns
        for domain, rules in self.domain_rules.items():
            domain_keywords = rules.get("keywords", [])
            keyword_score = 0
            
            for keyword in domain_keywords:
                if keyword.lower() in chunk_text:
                    keyword_score += 1
            
            # If multiple keywords present, add domain
            if keyword_score >= 2:
                domains.append(domain)
        
        return domains
    
    def get_domain_confidence(self, chunk: Dict, domain: str) -> float:
        """
        Get confidence score for a specific domain classification.
        
        Args:
            chunk: Chunk dictionary
            domain: Domain to check
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        if domain not in self.domain_rules:
            return 0.0
        
        rules = self.domain_rules[domain]
        total_score = 0
        max_score = 0
        
        # Topic-based score
        topic_score = 0
        topic = chunk.get("topic", "")
        if topic == domain:
            topic_score = 1.0
        max_score += 1
        total_score += topic_score
        
        # Entity-based score
        entity_counts = chunk.get("entity_counts", {})
        entity_score = 0
        domain_entities = rules.get("entities", [])
        for entity_type in domain_entities:
            if entity_type in entity_counts:
                entity_score += min(entity_counts[entity_type] / 5.0, 1.0)
        max_score += len(domain_entities)
        total_score += entity_score
        
        # Keyword-based score
        chunk_text = chunk.get("chunk_text", "")
        if chunk_text is None:
            chunk_text = ""
        chunk_text = chunk_text.lower()
        keyword_score = 0
        domain_keywords = rules.get("keywords", [])
        for keyword in domain_keywords:
            if keyword.lower() in chunk_text:
                keyword_score += 1
        max_score += len(domain_keywords)
        total_score += keyword_score
        
        return total_score / max_score if max_score > 0 else 0.0 