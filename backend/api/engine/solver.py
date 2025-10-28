"""
Solver: Nash-lite compromise between company and investor proposals
"""
from typing import Dict, Any, Optional
from ..models.schemas import NegotiationContext, TermProposal
from .utility import UtilityEngine
from .policy import PolicyEngine


class NegotiationSolver:
    """Finds balanced compromise between proposals"""
    
    def __init__(self, supabase_client):
        self.utility_engine = UtilityEngine()
        self.policy_engine = PolicyEngine(supabase_client)
    
    def solve(
        self,
        company_proposals: Dict[str, TermProposal],
        investor_proposals: Dict[str, TermProposal],
        context: NegotiationContext
    ) -> Dict[str, Dict[str, Any]]:
        """
        Find compromise solution between company and investor proposals
        
        Uses leverage-weighted Nash bargaining approach:
        - Higher leverage = more weight to that party's proposal
        - Clamps to policy bounds
        - Returns final term values
        """
        final_terms = {}
        
        # Get leverage scores (default to 0.5 if not set)
        company_leverage = context.company_persona.leverage_score or 0.5
        investor_leverage = context.investor_persona.leverage_score or 0.5
        
        # Normalize leverage to sum to 1
        total_leverage = company_leverage + investor_leverage
        company_weight = company_leverage / total_leverage if total_leverage > 0 else 0.5
        investor_weight = investor_leverage / total_leverage if total_leverage > 0 else 0.5
        
        # Get all clause keys
        all_clauses = set(company_proposals.keys()) | set(investor_proposals.keys())
        
        for clause_key in all_clauses:
            company_prop = company_proposals.get(clause_key)
            investor_prop = investor_proposals.get(clause_key)
            
            # Check for pinned/overridden terms
            existing_term = context.existing_terms.get(clause_key)
            if existing_term and existing_term.pinned_by:
                # Use pinned value
                final_terms[clause_key] = existing_term.value
                continue
            
            # Check for user overrides
            if clause_key in context.user_overrides:
                final_terms[clause_key] = context.user_overrides[clause_key]
                continue
            
            # If only one party has a proposal, use it (clamped)
            if not company_prop:
                final_terms[clause_key] = self._clamp_term(
                    clause_key, 
                    investor_prop.value, 
                    context
                )
                continue
            
            if not investor_prop:
                final_terms[clause_key] = self._clamp_term(
                    clause_key, 
                    company_prop.value, 
                    context
                )
                continue
            
            # Both parties have proposals - find compromise
            compromise = self._find_compromise(
                clause_key,
                company_prop.value,
                investor_prop.value,
                company_weight,
                investor_weight,
                context
            )
            
            final_terms[clause_key] = self._clamp_term(clause_key, compromise, context)
        
        return final_terms
    
    def _find_compromise(
        self,
        clause_key: str,
        company_value: Dict[str, Any],
        investor_value: Dict[str, Any],
        company_weight: float,
        investor_weight: float,
        context: NegotiationContext
    ) -> Dict[str, Any]:
        """
        Find weighted compromise between two values
        """
        guidance = context.guidance.get(clause_key)
        
        # For numeric values, do weighted average
        if guidance and guidance.units in ['days', 'pct', 'number']:
            result = {}
            
            # Average each parameter
            all_params = set(company_value.keys()) | set(investor_value.keys())
            
            for param_key in all_params:
                c_val = company_value.get(param_key)
                i_val = investor_value.get(param_key)
                
                if isinstance(c_val, (int, float)) and isinstance(i_val, (int, float)):
                    # Weighted average
                    avg_val = (company_weight * c_val) + (investor_weight * i_val)
                    
                    # Round to int if both inputs were ints
                    if isinstance(c_val, int) and isinstance(i_val, int):
                        avg_val = round(avg_val)
                    
                    result[param_key] = avg_val
                else:
                    # Non-numeric, favor higher leverage party
                    result[param_key] = c_val if company_weight > investor_weight else i_val
            
            return result
        
        # For boolean/enum values, favor higher leverage party
        if company_weight > investor_weight:
            return company_value
        else:
            return investor_value
    
    def _clamp_term(
        self,
        clause_key: str,
        value: Dict[str, Any],
        context: NegotiationContext
    ) -> Dict[str, Any]:
        """
        Clamp term value to policy bounds
        """
        result = {}
        
        for param_key, param_value in value.items():
            if isinstance(param_value, (int, float)):
                # Get bounds for this parameter
                # For simplicity, use clause-level bounds
                min_val, max_val = self.policy_engine.get_bounds(clause_key, context)
                
                clamped = param_value
                if min_val is not None and clamped < min_val:
                    clamped = min_val
                if max_val is not None and clamped > max_val:
                    clamped = max_val
                
                result[param_key] = clamped
            else:
                result[param_key] = param_value
        
        return result


