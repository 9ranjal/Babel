"""
Base skill interface for clause-specific negotiation logic
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple
from ...models.schemas import NegotiationContext, TermProposal, EmbeddedSnippet


class BaseSkill(ABC):
    """Base class for clause-specific negotiation skills"""
    
    def __init__(self, clause_key: str, supabase_client):
        self.clause_key = clause_key
        self.supabase = supabase_client
    
    @abstractmethod
    def propose_company(self, context: NegotiationContext) -> TermProposal:
        """Generate company's proposal for this clause"""
        pass
    
    @abstractmethod
    def propose_investor(self, context: NegotiationContext) -> TermProposal:
        """Generate investor's proposal for this clause"""
        pass
    
    def fetch_snippets(
        self, 
        context: NegotiationContext,
        perspectives: List[str] = None,
        limit: int = 3
    ) -> List[EmbeddedSnippet]:
        """
        Fetch relevant snippets for this clause
        
        Args:
            context: Negotiation context
            perspectives: List of perspectives to fetch (detail, founder, investor, etc.)
            limit: Max snippets to return
        """
        if perspectives is None:
            perspectives = ['detail', 'founder', 'investor', 'balance']
        
        query = self.supabase.table("embedded_snippets").select("*").eq(
            "clause_key", self.clause_key
        ).in_("perspective", perspectives).eq(
            "stage", context.stage
        ).eq(
            "region", context.region
        ).limit(limit)
        
        result = query.execute()
        
        snippets = []
        if result.data:
            for row in result.data:
                snippets.append(EmbeddedSnippet(**row))
        
        return snippets
    
    def get_guidance(self, context: NegotiationContext):
        """Helper to get guidance for this clause from context"""
        return context.guidance.get(self.clause_key)
    
    def get_market_data(self, context: NegotiationContext):
        """Helper to get market data for this clause from context"""
        return context.market_data.get(self.clause_key)
    
    def build_rationale(
        self, 
        party: str,
        value: Dict[str, Any],
        context: NegotiationContext,
        snippets: List[EmbeddedSnippet]
    ) -> str:
        """
        Build a rationale string explaining the proposal
        
        Args:
            party: "company" or "investor"
            value: Proposed value
            context: Negotiation context
            snippets: Supporting snippets
        """
        guidance = self.get_guidance(context)
        
        if not guidance:
            return f"{party.title()} proposes: {value}"
        
        # Extract relevant POV
        if party == "company":
            pov = guidance.founder_pov_md or guidance.detail_md
        else:
            pov = guidance.investor_pov_md or guidance.detail_md
        
        # Build rationale
        parts = [f"{party.title()}'s proposal: {self._format_value(value)}"]
        
        if pov:
            parts.append(f"Rationale: {pov}")
        
        if guidance.batna_base:
            parts.append(f"Market baseline: {guidance.batna_base}")
        
        return " | ".join(parts)
    
    def _format_value(self, value: Dict[str, Any]) -> str:
        """Format value dict for display"""
        if len(value) == 1:
            return str(list(value.values())[0])
        return str(value)

