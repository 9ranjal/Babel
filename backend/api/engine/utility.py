"""
Utility Calculation: Score proposals based on persona preferences
"""
from typing import Dict, Any
from ..models.schemas import NegotiationContext, PersonaResponse


class UtilityEngine:
    """Calculate utility scores for proposals based on persona preferences"""
    
    def __init__(self):
        pass
    
    def calculate_utility(
        self,
        persona: PersonaResponse,
        terms: Dict[str, Dict[str, Any]],
        context: NegotiationContext
    ) -> float:
        """
        Calculate utility score for a set of terms from persona's perspective
        
        Uses persona weights and BATNA to score how good the deal is.
        Returns: float between 0-100 (higher is better for the persona)
        """
        if not persona.weights:
            # If no weights, use uniform weighting
            return 50.0
        
        total_utility = 0.0
        total_weight = 0.0
        
        for clause_key, term_value in terms.items():
            weight = persona.weights.get(clause_key, 1.0)
            total_weight += weight
            
            # Calculate per-clause utility
            clause_utility = self._calculate_clause_utility(
                clause_key, 
                term_value, 
                persona, 
                context
            )
            
            total_utility += weight * clause_utility
        
        if total_weight == 0:
            return 50.0
        
        return total_utility / total_weight
    
    def _calculate_clause_utility(
        self,
        clause_key: str,
        term_value: Dict[str, Any],
        persona: PersonaResponse,
        context: NegotiationContext
    ) -> float:
        """
        Calculate utility for a single clause value
        
        Returns: 0-100 score
        """
        # Get persona's BATNA (ideal value) for this clause
        batna = persona.batna.get(clause_key) if persona.batna else None
        
        if not batna:
            # No preference, neutral utility
            return 50.0
        
        guidance = context.guidance.get(clause_key)
        
        # For numeric values, calculate distance from BATNA
        if guidance and guidance.units in ['days', 'pct', 'number']:
            # Extract numeric value (assume first param is the main one)
            actual_val = list(term_value.values())[0] if term_value else None
            batna_val = list(batna.values())[0] if batna else None
            
            if actual_val is not None and batna_val is not None:
                # Get bounds for normalization
                min_val = guidance.min_val or 0
                max_val = guidance.max_val or 100
                range_val = max_val - min_val
                
                if range_val > 0:
                    # Distance from BATNA as fraction of range
                    distance = abs(actual_val - batna_val) / range_val
                    
                    # Convert to utility (closer = better)
                    # 0 distance = 100 utility, max distance = 0 utility
                    utility = max(0, 100 * (1 - distance))
                    return utility
        
        # For boolean/enum values, exact match = 100, else 0
        if term_value == batna:
            return 100.0
        else:
            return 30.0  # Partial credit for having the clause
    
    def calculate_nash_product(
        self,
        company_utility: float,
        investor_utility: float
    ) -> float:
        """
        Calculate Nash product for a proposal
        
        Used by solver to find balanced solutions
        """
        return company_utility * investor_utility
    
    def get_utilities(
        self,
        terms: Dict[str, Dict[str, Any]],
        context: NegotiationContext
    ) -> Dict[str, float]:
        """
        Calculate utilities for both parties
        
        Returns: {"company": x, "investor": y}
        """
        company_util = self.calculate_utility(
            context.company_persona,
            terms,
            context
        )
        
        investor_util = self.calculate_utility(
            context.investor_persona,
            terms,
            context
        )
        
        return {
            "company": company_util,
            "investor": investor_util
        }

