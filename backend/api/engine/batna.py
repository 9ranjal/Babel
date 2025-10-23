"""
BATNA computation: leverage, weights, and clause bands
"""
from typing import Dict, Any, Tuple, List
from ..models.schemas import ClauseGuidance, MarketBenchmark, PersonaResponse


class BatnaEngine:
    """Computes leverage, weights, and BATNA bands for personas"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    def compute_leverage(self, persona: PersonaResponse) -> float:
        """Compute leverage score based on persona attributes"""
        attrs = persona.attrs
        leverage = 0.5  # Base
        
        if persona.kind == "company":
            # Company leverage factors
            if attrs.get("repeat_founder_any"):
                leverage += 0.2
            if attrs.get("alt_offers", 0) > 0:
                leverage += 0.15
            if attrs.get("runway_months", 0) > 6:
                leverage += 0.1
            if attrs.get("runway_months", 0) < 4:
                leverage -= 0.2
        else:
            # Investor leverage factors
            if attrs.get("marquee"):
                leverage += 0.2
            if attrs.get("ownership_target_pct", 0) > 0.15:
                leverage += 0.1
            if attrs.get("diligence_speed") == "accelerated":
                leverage -= 0.1
        
        return max(0.0, min(1.0, leverage))
    
    def compute_weights(self, persona: PersonaResponse) -> Dict[str, float]:
        """Compute clause weights based on persona attributes"""
        attrs = persona.attrs
        weights = {"exclusivity": 0.5, "vesting": 0.5, "pro_rata_rights": 0.3}
        
        if persona.kind == "company":
            # Founder weight adjustments
            if attrs.get("runway_months", 0) < 6 or attrs.get("diligence_speed") == "accelerated":
                weights["exclusivity"] = 0.8
        else:
            # Investor weight adjustments
            if attrs.get("marquee"):
                weights["pro_rata_rights"] = 0.8
        
        return weights
    
    def compute_batna_bands(
        self, 
        clause_key: str, 
        guidance: ClauseGuidance, 
        market: MarketBenchmark,
        persona: PersonaResponse
    ) -> Tuple[float, float, float, float]:
        """
        Compute BATNA bands for a clause
        
        Returns: (default_low, default_high, walk_away_min, walk_away_max)
        """
        # Default band from guidance
        default_low = guidance.default_low or market.p25 or 0
        default_high = guidance.default_high or market.p75 or 100
        
        # Walk-away bounds from guidance
        walk_away_min = guidance.min_val or default_low * 0.5
        walk_away_max = guidance.max_val or default_high * 1.5
        
        # Adjust based on leverage
        leverage = persona.leverage_score or 0.5
        range_size = default_high - default_low
        
        if persona.kind == "company":
            # Company wants lower values (shorter exclusivity, less vesting)
            if clause_key == "exclusivity":
                # Lower leverage = accept longer exclusivity
                adjustment = (1 - leverage) * range_size * 0.2
                default_low += adjustment
                default_high += adjustment
            elif clause_key == "vesting":
                # Lower leverage = accept longer vesting
                adjustment = (1 - leverage) * range_size * 0.1
                default_low += adjustment
                default_high += adjustment
        else:
            # Investor wants higher values (longer exclusivity, more vesting)
            if clause_key == "exclusivity":
                # Higher leverage = demand longer exclusivity
                adjustment = leverage * range_size * 0.2
                default_low -= adjustment
                default_high -= adjustment
            elif clause_key == "vesting":
                # Higher leverage = demand longer vesting
                adjustment = leverage * range_size * 0.1
                default_low -= adjustment
                default_high -= adjustment
        
        return default_low, default_high, walk_away_min, walk_away_max
    
    def get_persona_batna_value(self, clause_key: str, persona: PersonaResponse) -> Dict[str, Any]:
        """Get persona's ideal value for a clause"""
        batna = persona.batna or {}
        return batna.get(clause_key, {})
    
    def compute_anchor_investor(self, investor_personas: List[PersonaResponse]) -> PersonaResponse:
        """Choose anchor investor for multi-investor sessions"""
        if not investor_personas:
            raise ValueError("No investor personas provided")
        
        # First try: marquee investors
        marquee_investors = [p for p in investor_personas if p.attrs.get("marquee")]
        if marquee_investors:
            return marquee_investors[0]
        
        # Second try: highest ownership target
        ownership_sorted = sorted(
            investor_personas, 
            key=lambda p: p.attrs.get("ownership_target_pct", 0), 
            reverse=True
        )
        return ownership_sorted[0]
    
    def aggregate_investor_utilities(
        self, 
        investor_personas: List[PersonaResponse], 
        terms: Dict[str, Dict[str, Any]]
    ) -> float:
        """Aggregate utilities from multiple investors"""
        if not investor_personas:
            return 0.0
        
        # Weight by ownership target or equal weights
        total_weight = 0.0
        weighted_utility = 0.0
        
        for persona in investor_personas:
            weight = persona.attrs.get("ownership_target_pct", 1.0)
            if weight <= 0:
                weight = 1.0  # Equal weight if no target specified
            
            # Simple utility calculation (distance from BATNA)
            utility = self._calculate_simple_utility(persona, terms)
            
            weighted_utility += weight * utility
            total_weight += weight
        
        return weighted_utility / total_weight if total_weight > 0 else 0.0
    
    def _calculate_simple_utility(self, persona: PersonaResponse, terms: Dict[str, Dict[str, Any]]) -> float:
        """Simple utility calculation for a persona"""
        total_utility = 0.0
        total_weight = 0.0
        
        weights = persona.weights or {}
        batna = persona.batna or {}
        
        for clause_key, term_value in terms.items():
            weight = weights.get(clause_key, 0.5)
            batna_value = batna.get(clause_key, {})
            
            # Calculate utility based on distance from BATNA
            utility = self._clause_utility(clause_key, term_value, batna_value)
            
            total_utility += weight * utility
            total_weight += weight
        
        return total_utility / total_weight if total_weight > 0 else 0.5
    
    def _clause_utility(self, clause_key: str, actual: Dict[str, Any], batna: Dict[str, Any]) -> float:
        """Calculate utility for a single clause"""
        if not batna:
            return 0.5  # Neutral if no BATNA
        
        # For numeric values, calculate distance
        if clause_key == "exclusivity":
            actual_days = actual.get("period_days", 0)
            batna_days = batna.get("period_days", 0)
            if batna_days > 0:
                distance = abs(actual_days - batna_days) / batna_days
                return max(0.0, 1.0 - distance)
        
        elif clause_key == "vesting":
            actual_months = actual.get("vesting_months", 0)
            batna_months = batna.get("vesting_months", 0)
            if batna_months > 0:
                distance = abs(actual_months - batna_months) / batna_months
                return max(0.0, 1.0 - distance)
        
        # For boolean values, exact match
        return 1.0 if actual == batna else 0.3
