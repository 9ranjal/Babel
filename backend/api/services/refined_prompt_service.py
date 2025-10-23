"""
Refined Prompt Service
Focused on actual LLM tasks, not UI/UX features
"""
from typing import Dict, Any, List, Optional
from uuid import UUID
from ..services.prompt_service import prompt_service


class RefinedPromptService:
    """Focused prompt service for actual LLM tasks only"""
    
    # Core LLM Tasks Only
    CORE_INTENTS = {
        "explain_clause": {
            "description": "Explain specific term sheet clauses and their implications",
            "llm_task": True,
            "batna_aware": True
        },
        "revise_clause": {
            "description": "Review and suggest revisions to term sheet clauses", 
            "llm_task": True,
            "batna_aware": True
        },
        "simulate_trade": {
            "description": "Simulate trade negotiations between different terms",
            "llm_task": True,
            "batna_aware": True
        },
        "general_chat": {
            "description": "General VC lawyer advice and consultation",
            "llm_task": True,
            "batna_aware": True
        }
    }
    
    # UI/UX Features (Not LLM Tasks)
    UI_FEATURES = {
        "update_persona": {
            "description": "Persona creation and management",
            "llm_task": False,
            "implementation": "Form-based UI with real-time BATNA computation",
            "llm_role": "Explain what persona attributes mean, not create them"
        },
        "regenerate_document": {
            "description": "Term sheet generation and regeneration",
            "llm_task": False,
            "implementation": "NegotiationOrchestrator.run_round() + frontend redlining",
            "llm_role": "Explain generated terms, not generate them"
        }
    }
    
    def get_core_intents(self) -> List[Dict[str, Any]]:
        """Get list of core LLM intents"""
        return [
            {
                "intent": intent,
                "description": data["description"],
                "batna_aware": data["batna_aware"]
            }
            for intent, data in self.CORE_INTENTS.items()
        ]
    
    def get_ui_features(self) -> List[Dict[str, Any]]:
        """Get list of UI/UX features that shouldn't be LLM tasks"""
        return [
            {
                "feature": feature,
                "description": data["description"],
                "implementation": data["implementation"],
                "llm_role": data["llm_role"]
            }
            for feature, data in self.UI_FEATURES.items()
        ]
    
    def is_llm_task(self, intent: str) -> bool:
        """Check if intent is a valid LLM task"""
        return intent in self.CORE_INTENTS and self.CORE_INTENTS[intent]["llm_task"]
    
    def get_llm_prompt(self, intent: str, **kwargs) -> str:
        """Get prompt for valid LLM tasks only"""
        if not self.is_llm_task(intent):
            raise ValueError(f"'{intent}' is not a valid LLM task. Use UI/UX implementation instead.")
        
        return prompt_service.get_intent_prompt(intent, **kwargs)
    
    def get_ui_implementation_guide(self, feature: str) -> Dict[str, Any]:
        """Get implementation guide for UI/UX features"""
        if feature not in self.UI_FEATURES:
            raise ValueError(f"'{feature}' is not a recognized UI/UX feature")
        
        return self.UI_FEATURES[feature]


# Global instance
refined_prompt_service = RefinedPromptService()
