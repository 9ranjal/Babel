"""
Pre-emption Rights clause skill
"""
from typing import Dict, Any
from .base_skill import BaseSkill
from ...models.schemas import NegotiationContext, TermProposal


class PreemptionSkill(BaseSkill):
    """Handles pre-emption rights negotiation"""
    
    def __init__(self, supabase_client):
        super().__init__("preemption_rights", supabase_client)
    
    def propose_company(self, context: NegotiationContext) -> TermProposal:
        """
        Company may want to limit to next round only for cap-table control
        """
        guidance = self.get_guidance(context)
        
        # Company perspective: grant pre-emption but limit scope
        value = {
            "enabled": True,
            "expiry_next_round_only": True  # Limit to next round
        }
        
        # Fetch supporting snippets
        snippets = self.fetch_snippets(context, perspectives=['founder', 'balance'])
        snippet_ids = [s.id for s in snippets]
        
        rationale = self.build_rationale("company", value, context, snippets)
        
        return TermProposal(
            clause_key=self.clause_key,
            value=value,
            rationale=rationale,
            snippet_ids=snippet_ids
        )
    
    def propose_investor(self, context: NegotiationContext) -> TermProposal:
        """
        Investor prefers ongoing pre-emption to protect against dilution
        """
        guidance = self.get_guidance(context)
        
        # Investor perspective: ongoing pre-emption is market standard
        value = {
            "enabled": True,
            "expiry_next_round_only": False  # Ongoing rights
        }
        
        # Fetch supporting snippets
        snippets = self.fetch_snippets(context, perspectives=['investor', 'detail'])
        snippet_ids = [s.id for s in snippets]
        
        rationale = self.build_rationale("investor", value, context, snippets)
        
        return TermProposal(
            clause_key=self.clause_key,
            value=value,
            rationale=rationale,
            snippet_ids=snippet_ids
        )


