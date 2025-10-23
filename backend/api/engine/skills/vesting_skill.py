"""
Vesting clause skill
"""
from typing import Dict, Any
from .base_skill import BaseSkill
from ...models.schemas import NegotiationContext, TermProposal


class VestingSkill(BaseSkill):
    """Handles founder vesting negotiation"""
    
    def __init__(self, supabase_client):
        super().__init__("vesting", supabase_client)
    
    def propose_company(self, context: NegotiationContext) -> TermProposal:
        """
        Company/founders prefer shorter vesting or no cliff
        """
        guidance = self.get_guidance(context)
        market = self.get_market_data(context)
        
        # Default to market median or 36 months
        vesting_months = 36
        cliff_months = 0  # Founders prefer no cliff
        
        if market and market.p25:
            vesting_months = int(market.p25)
        elif guidance and guidance.default_low:
            vesting_months = int(guidance.default_low)
        
        value = {
            "vesting_months": vesting_months,
            "cliff_months": cliff_months
        }
        
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
        Investor prefers standard 4-year vesting with 1-year cliff
        """
        guidance = self.get_guidance(context)
        market = self.get_market_data(context)
        
        # Default to market p75 or 48 months
        vesting_months = 48
        cliff_months = 12  # Standard 1-year cliff
        
        if market and market.p75:
            vesting_months = int(market.p75)
        elif guidance and guidance.default_high:
            vesting_months = int(guidance.default_high)
        
        value = {
            "vesting_months": vesting_months,
            "cliff_months": cliff_months
        }
        
        snippets = self.fetch_snippets(context, perspectives=['investor', 'detail'])
        snippet_ids = [s.id for s in snippets]
        
        rationale = self.build_rationale("investor", value, context, snippets)
        
        return TermProposal(
            clause_key=self.clause_key,
            value=value,
            rationale=rationale,
            snippet_ids=snippet_ids
        )

