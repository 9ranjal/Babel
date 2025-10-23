"""
Retriever for embedded snippets and guidance citations
"""
from typing import List, Optional, Dict, Any
from ..models.schemas import EmbeddedSnippet


class GuidanceRetriever:
    """Retrieves guidance snippets for citations"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    def get_snippets_by_ids(self, snippet_ids: List[int]) -> List[EmbeddedSnippet]:
        """
        Fetch snippets by their IDs
        
        Args:
            snippet_ids: List of snippet IDs to fetch
            
        Returns:
            List of EmbeddedSnippet objects
        """
        if not snippet_ids:
            return []
        
        result = self.supabase.table("embedded_snippets").select("*").in_(
            "id", snippet_ids
        ).execute()
        
        snippets = []
        if result.data:
            for row in result.data:
                snippets.append(EmbeddedSnippet(**row))
        
        return snippets
    
    def get_snippets_for_clause(
        self,
        clause_key: str,
        stage: str,
        region: str,
        perspectives: Optional[List[str]] = None,
        limit: int = 5
    ) -> List[EmbeddedSnippet]:
        """
        Fetch snippets for a specific clause/stage/region
        
        Args:
            clause_key: Clause identifier
            stage: Funding stage (seed, series-a, etc.)
            region: Geographic region (IN, US, etc.)
            perspectives: Filter by perspective (detail, founder, investor, balance)
            limit: Max number of snippets to return
            
        Returns:
            List of EmbeddedSnippet objects
        """
        query = self.supabase.table("embedded_snippets").select("*").eq(
            "clause_key", clause_key
        ).eq(
            "stage", stage
        ).eq(
            "region", region
        )
        
        if perspectives:
            query = query.in_("perspective", perspectives)
        
        query = query.limit(limit)
        
        result = query.execute()
        
        snippets = []
        if result.data:
            for row in result.data:
                snippets.append(EmbeddedSnippet(**row))
        
        return snippets
    
    def semantic_search(
        self,
        query_text: str,
        clause_key: Optional[str] = None,
        stage: Optional[str] = None,
        region: Optional[str] = None,
        limit: int = 5
    ) -> List[EmbeddedSnippet]:
        """
        Semantic search over snippets using embeddings
        
        TODO: Implement once embeddings are populated
        For now, returns keyword-based results
        
        Args:
            query_text: Search query
            clause_key: Optional filter by clause
            stage: Optional filter by stage
            region: Optional filter by region
            limit: Max results
            
        Returns:
            List of relevant snippets
        """
        # For now, do simple text search
        # TODO: Replace with vector similarity search
        query = self.supabase.table("embedded_snippets").select("*")
        
        if clause_key:
            query = query.eq("clause_key", clause_key)
        if stage:
            query = query.eq("stage", stage)
        if region:
            query = query.eq("region", region)
        
        # Text search in content
        query = query.ilike("content", f"%{query_text}%")
        query = query.limit(limit)
        
        result = query.execute()
        
        snippets = []
        if result.data:
            for row in result.data:
                snippets.append(EmbeddedSnippet(**row))
        
        return snippets
    
    def get_all_cited_snippets(
        self,
        snippet_id_map: Dict[str, List[int]]
    ) -> Dict[str, List[EmbeddedSnippet]]:
        """
        Fetch all snippets referenced in a negotiation round
        
        Args:
            snippet_id_map: Dict[clause_key -> List[snippet_ids]]
            
        Returns:
            Dict[clause_key -> List[EmbeddedSnippet]]
        """
        # Collect all unique snippet IDs
        all_ids = set()
        for ids in snippet_id_map.values():
            all_ids.update(ids)
        
        if not all_ids:
            return {}
        
        # Fetch all snippets
        snippets = self.get_snippets_by_ids(list(all_ids))
        
        # Index by ID
        snippet_by_id = {s.id: s for s in snippets}
        
        # Build result map
        result = {}
        for clause_key, ids in snippet_id_map.items():
            result[clause_key] = [snippet_by_id[id] for id in ids if id in snippet_by_id]
        
        return result

