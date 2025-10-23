"""
Context Service
Handles transaction context and persona management for copilot
"""
from typing import Dict, Any, List, Optional
from uuid import UUID
from ..services.supabase import get_supabase_client


class ContextService:
    """Service for managing transaction context and personas"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    async def load_transaction_personas(self, transaction_id: UUID) -> List[Dict[str, Any]]:
        """Load personas linked to a transaction"""
        try:
            result = self.supabase.table("transaction_personas").select("*, personas(*)").eq("transaction_id", str(transaction_id)).execute()
            return result.data
        except Exception as e:
            print(f"Error loading transaction personas: {e}")
            return []
    
    async def get_transaction_context(self, transaction_id: UUID) -> Dict[str, Any]:
        """Get comprehensive transaction context"""
        try:
            # Load transaction details
            tx_result = self.supabase.table("transactions").select("*").eq("id", str(transaction_id)).execute()
            transaction = tx_result.data[0] if tx_result.data else None
            
            # Load personas
            personas = await self.load_transaction_personas(transaction_id)
            
            # Load negotiation sessions if any
            sessions_result = self.supabase.table("negotiation_sessions").select("*").eq("transaction_id", str(transaction_id)).execute()
            sessions = sessions_result.data
            
            return {
                "transaction": transaction,
                "personas": personas,
                "sessions": sessions,
                "persona_count": len(personas),
                "has_company": any(p.get("kind") == "company" for p in personas),
                "has_investors": any(p.get("kind") == "investor" for p in personas)
            }
            
        except Exception as e:
            print(f"Error loading transaction context: {e}")
            return {
                "transaction": None,
                "personas": [],
                "sessions": [],
                "persona_count": 0,
                "has_company": False,
                "has_investors": False
            }
    
    async def get_persona_leverage(self, persona_id: UUID) -> Dict[str, Any]:
        """Get leverage information for a persona"""
        try:
            result = self.supabase.table("personas").select("leverage, weights, batna").eq("id", str(persona_id)).execute()
            persona = result.data[0] if result.data else None
            
            if persona:
                return {
                    "leverage": persona.get("leverage", 0.5),
                    "weights": persona.get("weights", {}),
                    "batna": persona.get("batna", {})
                }
            return {"leverage": 0.5, "weights": {}, "batna": {}}
            
        except Exception as e:
            print(f"Error loading persona leverage: {e}")
            return {"leverage": 0.5, "weights": {}, "batna": {}}
    
    def build_context_summary(self, context: Dict[str, Any]) -> str:
        """Build a human-readable context summary"""
        transaction = context.get("transaction", {})
        personas = context.get("personas", [])
        
        summary = f"Transaction: {transaction.get('name', 'Unnamed')}\n"
        summary += f"Personas: {context.get('persona_count', 0)} total\n"
        
        if context.get("has_company"):
            company_personas = [p for p in personas if p.get("kind") == "company"]
            summary += f"Company: {len(company_personas)} persona(s)\n"
        
        if context.get("has_investors"):
            investor_personas = [p for p in personas if p.get("kind") == "investor"]
            summary += f"Investors: {len(investor_personas)} persona(s)\n"
        
        if context.get("sessions"):
            summary += f"Active Sessions: {len(context.get('sessions', []))}\n"
        
        return summary


# Service instance
context_service = ContextService()
