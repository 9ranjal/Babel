"""
Policy Engine: Hard constraints and bounds enforcement
"""
from typing import Dict, Any, Optional, Tuple
from ..models.schemas import ClauseGuidance, NegotiationContext


class PolicyEngine:
    """Enforces hard constraints on clause values"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    def get_bounds(
        self, 
        clause_key: str, 
        context: NegotiationContext
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Get min/max bounds for a clause from guidance or library constraints
        
        Returns: (min_val, max_val)
        """
        # First try clause_guidance
        guidance = context.guidance.get(clause_key)
        if guidance and guidance.min_val is not None:
            return (guidance.min_val, guidance.max_val)
        
        # Fallback to clause_library constraints
        result = self.supabase.table("clause_library").select("constraints").eq(
            "clause_key", clause_key
        ).execute()
        
        if result.data and len(result.data) > 0:
            constraints = result.data[0].get("constraints", {})
            min_constraint = constraints.get("min", {})
            max_constraint = constraints.get("max", {})
            
            # Try to extract numeric bounds (first key in min/max dicts)
            min_val = None
            max_val = None
            if min_constraint:
                min_val = list(min_constraint.values())[0] if min_constraint else None
            if max_constraint:
                max_val = list(max_constraint.values())[0] if max_constraint else None
            
            return (min_val, max_val)
        
        return (None, None)
    
    def clamp_value(
        self, 
        clause_key: str, 
        value: Any, 
        context: NegotiationContext
    ) -> Any:
        """
        Clamp a numeric value to policy bounds
        
        For non-numeric values (booleans, enums), returns as-is
        """
        if not isinstance(value, (int, float)):
            return value
        
        min_val, max_val = self.get_bounds(clause_key, context)
        
        if min_val is not None and value < min_val:
            return min_val
        if max_val is not None and value > max_val:
            return max_val
        
        return value
    
    def validate_term(
        self, 
        clause_key: str, 
        value: Dict[str, Any], 
        context: NegotiationContext
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a term against policy constraints
        
        Returns: (is_valid, error_message)
        """
        guidance = context.guidance.get(clause_key)
        
        # Check bounds for each parameter in the value
        for param_key, param_value in value.items():
            if isinstance(param_value, (int, float)):
                min_val, max_val = self.get_bounds(clause_key, context)
                
                if min_val is not None and param_value < min_val:
                    return (False, f"{param_key} ({param_value}) below minimum ({min_val})")
                if max_val is not None and param_value > max_val:
                    return (False, f"{param_key} ({param_value}) above maximum ({max_val})")
        
        # TODO: Add enum validation, required field checks, etc.
        
        return (True, None)
    
    def is_non_negotiable(
        self, 
        clause_key: str, 
        party: str,  # "investor" or "company"
        context: NegotiationContext
    ) -> bool:
        """
        Check if a clause is non-negotiable for a given party
        """
        result = self.supabase.table("clause_library").select("constraints").eq(
            "clause_key", clause_key
        ).execute()
        
        if result.data and len(result.data) > 0:
            constraints = result.data[0].get("constraints", {})
            flag_key = f"non_negotiable_for_{party}"
            return constraints.get(flag_key, False)
        
        return False

