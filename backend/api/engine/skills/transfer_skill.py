"""
Transfer restrictions clause skill (placeholder)
"""
from typing import Dict, Any
from .base_skill import BaseSkill
from ...models.schemas import NegotiationContext, TermProposal


class TransferSkill(BaseSkill):
    """Handles share transfer restrictions negotiation"""
    
    def __init__(self, supabase_client):
        super().__init__("transfer_restrictions", supabase_client)
    
    def propose_company(self, context: NegotiationContext) -> TermProposal:
        """
        Company may prefer more flexibility in transfers
        """
        # Placeholder - assumes a boolean restriction field
        value = {"restrictions_enabled": True}
        
        snippets = self.fetch_snippets(context, perspectives=['founder', 'detail'])
        snippet_ids = [s.id for s in snippets]
        
        rationale = "Company proposes standard transfer restrictions"
        
        return TermProposal(
            clause_key=self.clause_key,
            value=value,
            rationale=rationale,
            snippet_ids=snippet_ids
        )
    
    def propose_investor(self, context: NegotiationContext) -> TermProposal:
        """
        Investor prefers strict transfer restrictions
        """
        value = {"restrictions_enabled": True}
        
        snippets = self.fetch_snippets(context, perspectives=['investor', 'detail'])
        snippet_ids = [s.id for s in snippets]
        
        rationale = "Investor proposes standard transfer restrictions"
        
        return TermProposal(
            clause_key=self.clause_key,
            value=value,
            rationale=rationale,
            snippet_ids=snippet_ids
        )

