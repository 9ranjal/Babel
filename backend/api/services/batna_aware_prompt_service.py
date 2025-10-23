"""
BATNA-Aware Prompt Service
Enhanced prompts that integrate with BATNA engine data for intelligent responses
"""
from typing import Dict, Any, List, Optional
from uuid import UUID
from ..services.prompt_service import prompt_service
from ..engine.batna import BatnaEngine
from ..engine.utility import UtilityEngine
from ..models.schemas import PersonaResponse, NegotiationContext


class BatnaAwarePromptService:
    """Enhanced prompt service that integrates BATNA data for intelligent responses"""
    
    def __init__(self, supabase_client):
        self.base_prompt_service = prompt_service
        self.batna_engine = BatnaEngine(supabase_client)
        self.utility_engine = UtilityEngine()
    
    def get_batna_enhanced_prompt(
        self, 
        intent: str, 
        clause_key: str,
        transaction_id: UUID,
        personas: List[Dict[str, Any]],
        user_message: str = "",
        **kwargs
    ) -> str:
        """Get BATNA-enhanced prompt with real negotiation data"""
        
        # Get base prompt with proper parameters
        prompt_kwargs = {
            'clause_key': clause_key,
            'user_message': user_message,
            **kwargs
        }
        base_prompt = self.base_prompt_service.get_intent_prompt(intent, **prompt_kwargs)
        
        # Add BATNA context
        batna_context = self._build_batna_context(clause_key, personas, transaction_id)
        
        return f"{base_prompt}\n\n{BATNA_CONTEXT_HEADER}\n{batna_context}"
    
    def _build_batna_context(
        self, 
        clause_key: str, 
        personas: List[Dict[str, Any]], 
        transaction_id: UUID
    ) -> str:
        """Build BATNA-aware context for prompts"""
        
        context_parts = []
        
        # Add persona leverage analysis
        leverage_analysis = self._analyze_leverage(personas)
        if leverage_analysis:
            context_parts.append(f"**LEVERAGE ANALYSIS:**\n{leverage_analysis}")
        
        # Add BATNA bands for the specific clause
        batna_bands = self._get_clause_batna_bands(clause_key, personas)
        if batna_bands:
            context_parts.append(f"**BATNA BANDS FOR {clause_key.upper()}:**\n{batna_bands}")
        
        # Add negotiation positioning
        positioning = self._get_negotiation_positioning(personas)
        if positioning:
            context_parts.append(f"**NEGOTIATION POSITIONING:**\n{positioning}")
        
        # Add market context
        market_context = self._get_market_context(clause_key)
        if market_context:
            context_parts.append(f"**MARKET CONTEXT:**\n{market_context}")
        
        return "\n\n".join(context_parts)
    
    def _analyze_leverage(self, personas: List[Dict[str, Any]]) -> str:
        """Analyze leverage distribution among personas"""
        if not personas:
            return "No personas available for leverage analysis."
        
        leverage_analysis = []
        
        for persona_data in personas:
            persona = persona_data.get('personas', {})
            leverage = persona.get('leverage_score', 0.5)
            kind = persona.get('kind', 'unknown')
            label = persona_data.get('label', 'Unnamed')
            
            leverage_level = "High" if leverage > 0.7 else "Medium" if leverage > 0.4 else "Low"
            
            leverage_analysis.append(
                f"- **{label}** ({kind}): {leverage_level} leverage ({leverage:.2f})"
            )
        
        # Add leverage-based negotiation advice
        company_personas = [p for p in personas if p.get('personas', {}).get('kind') == 'company']
        investor_personas = [p for p in personas if p.get('personas', {}).get('kind') == 'investor']
        
        if company_personas and investor_personas:
            company_leverage = company_personas[0].get('personas', {}).get('leverage_score', 0.5)
            investor_leverage = investor_personas[0].get('personas', {}).get('leverage_score', 0.5)
            
            if company_leverage > investor_leverage + 0.2:
                leverage_analysis.append("\n**NEGOTIATION ADVICE:** Company has significant leverage advantage. Can push for founder-friendly terms.")
            elif investor_leverage > company_leverage + 0.2:
                leverage_analysis.append("\n**NEGOTIATION ADVICE:** Investor has leverage advantage. Company should focus on protecting key interests.")
            else:
                leverage_analysis.append("\n**NEGOTIATION ADVICE:** Balanced leverage. Focus on win-win solutions and trade-offs.")
        
        return "\n".join(leverage_analysis)
    
    def _get_clause_batna_bands(self, clause_key: str, personas: List[Dict[str, Any]]) -> str:
        """Get BATNA bands for a specific clause"""
        if not personas:
            return "No BATNA data available."
        
        batna_info = []
        
        for persona_data in personas:
            persona = persona_data.get('personas', {})
            batna = persona.get('batna', {})
            weights = persona.get('weights', {})
            label = persona_data.get('label', 'Unnamed')
            kind = persona.get('kind', 'unknown')
            
            clause_batna = batna.get(clause_key, {})
            clause_weight = weights.get(clause_key, 0.0)
            
            if clause_batna:
                batna_info.append(f"- **{label}** ({kind}): BATNA = {clause_batna}, Weight = {clause_weight:.2f}")
            else:
                batna_info.append(f"- **{label}** ({kind}): No BATNA data for {clause_key}")
        
        return "\n".join(batna_info)
    
    def _get_negotiation_positioning(self, personas: List[Dict[str, Any]]) -> str:
        """Get negotiation positioning advice based on personas"""
        if not personas:
            return "No positioning data available."
        
        positioning = []
        
        # Analyze company positioning
        company_personas = [p for p in personas if p.get('personas', {}).get('kind') == 'company']
        if company_personas:
            company = company_personas[0].get('personas', {})
            attrs = company.get('attrs', {})
            
            positioning.append("**COMPANY POSITIONING:**")
            
            if attrs.get('repeat_founder_any'):
                positioning.append("- Repeat founder: Strong negotiating position")
            if attrs.get('alt_offers', 0) > 0:
                positioning.append(f"- Alternative offers: {attrs.get('alt_offers')} options available")
            if attrs.get('runway_months', 0) < 6:
                positioning.append("- Short runway: Time pressure may limit options")
            if attrs.get('diligence_speed') == 'accelerated':
                positioning.append("- Accelerated process: May need to compromise on terms")
        
        # Analyze investor positioning
        investor_personas = [p for p in personas if p.get('personas', {}).get('kind') == 'investor']
        if investor_personas:
            investor = investor_personas[0].get('personas', {})
            attrs = investor.get('attrs', {})
            
            positioning.append("\n**INVESTOR POSITIONING:**")
            
            if attrs.get('marquee'):
                positioning.append("- Marquee investor: Strong market position")
            if attrs.get('ownership_target_pct', 0) > 0.15:
                positioning.append(f"- High ownership target: {attrs.get('ownership_target_pct', 0)*100:.1f}% - may demand more control")
            if attrs.get('diligence_speed') == 'accelerated':
                positioning.append("- Accelerated diligence: May be willing to compromise for speed")
        
        return "\n".join(positioning)
    
    def _get_market_context(self, clause_key: str) -> str:
        """Get market context for a specific clause"""
        # This would integrate with market benchmarks
        market_contexts = {
            "exclusivity": "Market standard: 30-90 days. Shorter periods favor founders, longer periods favor investors.",
            "vesting": "Market standard: 4-year vesting with 1-year cliff. Accelerated vesting on change of control is common.",
            "liquidation_preference": "Market standard: 1x non-participating preferred. Participating preferred is less founder-friendly.",
            "anti_dilution": "Market standard: Weighted average anti-dilution. Full ratchet is very investor-friendly.",
            "board_composition": "Market standard: 3-5 person board with founder control in early stages, investor control in later stages."
        }
        
        return market_contexts.get(clause_key, f"Market context for {clause_key} not available.")
    
    def get_negotiation_strategy_prompt(
        self, 
        clause_key: str, 
        transaction_id: UUID,
        personas: List[Dict[str, Any]]
    ) -> str:
        """Get BATNA-aware negotiation strategy prompt"""
        
        base_prompt = self.base_prompt_service.get_intent_prompt(
            "simulate_trade",
            clause_key=clause_key,
            user_message="Provide negotiation strategy based on current BATNA data"
        )
        
        batna_context = self._build_batna_context(clause_key, personas, transaction_id)
        
        strategy_prompt = f"""
{base_prompt}

{BATNA_CONTEXT_HEADER}
{batna_context}

**STRATEGY REQUIREMENTS:**
Based on the BATNA data above, provide specific negotiation strategy including:
1. **Optimal Ask**: What should each party ask for based on their leverage and BATNA?
2. **Trade Opportunities**: What can be traded between parties?
3. **Risk Assessment**: What are the risks of each position?
4. **Timing Strategy**: When should each party make their moves?
5. **Fallback Positions**: What are acceptable alternatives if primary goals aren't met?

Be specific about numbers, percentages, and concrete terms based on the actual BATNA data.
"""
        
        return strategy_prompt


# Constants
BATNA_CONTEXT_HEADER = """
**BATNA-AWARE CONTEXT:**
The following data is computed from actual persona attributes, leverage scores, and negotiation weights. Use this data to provide specific, data-driven advice rather than generic guidance.
"""


# Global instance
def get_batna_aware_prompt_service(supabase_client):
    """Get BATNA-aware prompt service instance"""
    return BatnaAwarePromptService(supabase_client)
