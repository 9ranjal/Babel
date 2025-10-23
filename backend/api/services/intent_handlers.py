"""
Intent-Specific Handlers
Specialized handlers for different copilot intents
"""
from typing import Dict, Any, List
from uuid import UUID
from ..models.schemas import CopilotIntentRequest, CopilotIntentResponse
from .copilot_service import copilot_service


class IntentHandler:
    """Base class for intent handlers"""
    
    async def handle(self, request: CopilotIntentRequest) -> CopilotIntentResponse:
        """Handle the intent request"""
        raise NotImplementedError


class ExplainClauseHandler(IntentHandler):
    """Handler for explain_clause intent"""
    
    async def handle(self, request: CopilotIntentRequest) -> CopilotIntentResponse:
        return await copilot_service.handle_explain_clause(request)


class ReviseClauseHandler(IntentHandler):
    """Handler for revise_clause intent"""
    
    async def handle(self, request: CopilotIntentRequest) -> CopilotIntentResponse:
        return await copilot_service.handle_revise_clause(request)


class SimulateTradeHandler(IntentHandler):
    """Handler for simulate_trade intent"""
    
    async def handle(self, request: CopilotIntentRequest) -> CopilotIntentResponse:
        return await copilot_service.handle_simulate_trade(request)


class GeneralChatHandler(IntentHandler):
    """Handler for general_chat intent"""
    
    async def handle(self, request: CopilotIntentRequest) -> CopilotIntentResponse:
        return await copilot_service.handle_general_chat(request)


class IntentHandlerFactory:
    """Factory for creating intent handlers"""
    
    _handlers = {
        "explain_clause": ExplainClauseHandler(),
        "revise_clause": ReviseClauseHandler(),
        "simulate_trade": SimulateTradeHandler(),
        "general_chat": GeneralChatHandler(),
    }
    
    @classmethod
    def get_handler(cls, intent: str) -> IntentHandler:
        """Get handler for specific intent"""
        return cls._handlers.get(intent, ExplainClauseHandler())  # Default to explain_clause
    
    @classmethod
    def get_available_intents(cls) -> List[str]:
        """Get list of available intents"""
        return list(cls._handlers.keys())
