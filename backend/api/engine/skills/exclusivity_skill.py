"""
Exclusivity clause skill
"""
from typing import Dict, Any
from .base_skill import BaseSkill
from ...models.schemas import NegotiationContext, TermProposal


class ExclusivitySkill(BaseSkill):
    """Handles exclusivity period negotiation"""
    
    def __init__(self, supabase_client):
        super().__init__("exclusivity", supabase_client)
    
    def propose_company(self, context: NegotiationContext) -> TermProposal:
        """
        Company prefers shorter exclusivity (~30 days) to preserve flexibility
        """
        guidance = self.get_guidance(context)
        
        # Company aims for lower end or below market baseline
        if guidance and guidance.default_low is not None:
            # Aim for ~2/3 of the low default (e.g., 45 -> 30)
            period_days = int(guidance.default_low * 0.67)
            
            # Clamp to bounds
            if guidance.min_val is not None:
                period_days = max(int(guidance.min_val), period_days)
        else:
            # Fallback to conservative 30 days
            period_days = 30
        
        value = {"period_days": period_days}
        
        # Fetch supporting snippets
        snippets = self.fetch_snippets(context, perspectives=['founder', 'detail'])
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
        Investor prefers longer exclusivity (45-60 days) for diligence
        """
        guidance = self.get_guidance(context)
        
        # Investor aims for high end of market baseline
        if guidance and guidance.default_high is not None:
            period_days = int(guidance.default_high)
            
            # Clamp to bounds
            if guidance.max_val is not None:
                period_days = min(int(guidance.max_val), period_days)
        else:
            # Fallback to 60 days
            period_days = 60
        
        value = {"period_days": period_days}
        
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



