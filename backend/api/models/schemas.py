"""
Pydantic schemas for Termcraft AI API
"""
from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


# ============================================================================
# PERSONA SCHEMAS
# ============================================================================

class PersonaCreate(BaseModel):
    kind: Literal["company", "investor"]
    attrs: Dict[str, Any]
    leverage_score: Optional[float] = None
    weights: Optional[Dict[str, float]] = None
    batna: Optional[Dict[str, Any]] = None


class PersonaResponse(PersonaCreate):
    id: UUID
    owner_user: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# NEGOTIATION SCHEMAS
# ============================================================================

class NegotiationSessionCreate(BaseModel):
    company_persona: UUID
    investor_persona: UUID
    transaction_id: UUID  # Required - session belongs to transaction
    regime: str = "IN"  # default to India
    status: Literal["draft", "negotiating", "final"] = "draft"


class NegotiationSessionResponse(BaseModel):
    id: UUID
    owner_user: UUID
    company_persona: UUID
    investor_persona: UUID
    transaction_id: UUID
    regime: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# CLAUSE & TERM SCHEMAS
# ============================================================================

class ClauseGuidance(BaseModel):
    """Guidance data for a specific clause"""
    clause_key: str
    stage: str
    region: str
    detail_md: str
    founder_pov_md: Optional[str] = None
    investor_pov_md: Optional[str] = None
    batna_base: Optional[str] = None
    balance_note_md: Optional[str] = None
    units: Optional[str] = None
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    default_low: Optional[float] = None
    default_high: Optional[float] = None


class EmbeddedSnippet(BaseModel):
    """RAG citation snippet"""
    id: int
    clause_key: str
    perspective: Literal["detail", "founder", "investor", "batna", "balance"]
    stage: Optional[str] = None
    region: Optional[str] = None
    content: str
    tags: Optional[Dict[str, Any]] = None


class TermProposal(BaseModel):
    """A proposed value for a clause"""
    clause_key: str
    value: Dict[str, Any]
    rationale: str
    snippet_ids: List[int] = Field(default_factory=list)


class SessionTermUpdate(BaseModel):
    """Update/create a term in a session"""
    clause_key: str
    value: Dict[str, Any]
    source: Literal["rule", "persona", "copilot"] = "copilot"
    confidence: Optional[float] = None
    pinned_by: Optional[Literal["company", "investor", "system"]] = None


class SessionTermResponse(BaseModel):
    """A term value in a session"""
    session_id: UUID
    clause_key: str
    value: Dict[str, Any]
    source: str
    confidence: Optional[float] = None
    pinned_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# NEGOTIATION ROUND SCHEMAS
# ============================================================================

class NegotiationRoundRequest(BaseModel):
    """Request to run a negotiation round"""
    session_id: UUID
    round_no: Optional[int] = None  # Auto-increment if None
    user_overrides: Optional[Dict[str, Any]] = None  # Manual term overrides


class ProposalSet(BaseModel):
    """Set of proposals from one party"""
    terms: Dict[str, Dict[str, Any]]  # clause_key -> value
    rationales: Dict[str, str]  # clause_key -> rationale


class NegotiationTrace(BaseModel):
    """Trace of negotiation logic for transparency"""
    clause_key: str
    company_proposal: Dict[str, Any]
    investor_proposal: Dict[str, Any]
    final_value: Dict[str, Any]
    rationale: str
    snippet_ids: List[int] = Field(default_factory=list)
    confidence: float


class NegotiationRoundResponse(BaseModel):
    """Result of a negotiation round"""
    session_id: UUID
    round_no: int
    company_proposal: Dict[str, Any]  # Full proposal set
    investor_proposal: Dict[str, Any]  # Full proposal set
    mediator_choice: Dict[str, Any]  # Final chosen terms
    utilities: Dict[str, float]  # {company: x, investor: y}
    rationale_md: str  # Overall explanation
    traces: List[NegotiationTrace]  # Per-clause trace
    citations: List[EmbeddedSnippet]  # Referenced snippets
    grades: Optional[Dict[str, Any]] = None  # {policy_ok: bool, grounding: float}
    decided: bool = False
    created_at: Optional[datetime] = None
    # Transaction-scoped trace fields
    anchored_by: Optional[str] = None  # "Alpha Ventures" or "Weighted Aggregate"
    investor_weights: Optional[Dict[str, float]] = None  # {"Alpha": 0.6, "Beta": 0.4}
    transaction_id: Optional[UUID] = None  # Transaction context

    class Config:
        from_attributes = True


# ============================================================================
# MARKET DATA SCHEMAS
# ============================================================================

class MarketBenchmark(BaseModel):
    """Market benchmark data point"""
    clause_key: str
    stage: str
    region: str
    p25: Optional[float] = None
    p50: Optional[float] = None
    p75: Optional[float] = None
    asof_date: Optional[datetime] = None
    source: Optional[str] = None


# ============================================================================
# CONTEXT SCHEMAS (for skills/engine)
# ============================================================================

class NegotiationContext(BaseModel):
    """Full context for negotiation engine"""
    session_id: UUID
    round_no: int
    regime: str
    stage: str  # derived from persona attrs
    region: str
    company_persona: PersonaResponse
    investor_persona: PersonaResponse
    guidance: Dict[str, ClauseGuidance]  # clause_key -> guidance
    market_data: Dict[str, MarketBenchmark]  # clause_key -> benchmark
    existing_terms: Dict[str, SessionTermResponse]  # clause_key -> term
    user_overrides: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# COPILOT INTAKE SCHEMAS
# ============================================================================

class IntakeStartRequest(BaseModel):
    """Start copilot intake flow"""
    role: Literal["founder", "investor"]
    stage: str
    region: str = "SG"  # Default to Singapore
    transaction_id: Optional[UUID] = None  # Auto-create if missing


class IntakeStartResponse(BaseModel):
    """Response with first question"""
    question_id: str
    question_text: str
    question_type: Literal["choice", "number", "text", "boolean"]
    options: Optional[List[str]] = None
    next_questions: List[str] = Field(default_factory=list)
    session_id: Optional[str] = None
    persona_id: Optional[UUID] = None
    transaction_id: Optional[UUID] = None  # Return created/used transaction


class IntakeAnswerRequest(BaseModel):
    """Answer to intake question"""
    question_id: str
    answer: Any
    session_id: Optional[str] = None
    persona_id: Optional[UUID] = None
    transaction_id: Optional[UUID] = None  # For session recovery


class IntakeAnswerResponse(BaseModel):
    """Response after answering"""
    next_question: Optional[IntakeStartResponse] = None
    completed: bool = False
    persona_id: Optional[UUID] = None
    message: Optional[str] = None


# ============================================================================
# DRAFT GENERATION SCHEMAS
# ============================================================================

class Draft0Request(BaseModel):
    """Generate Draft 0 term sheet"""
    company_persona_id: UUID
    investor_persona_ids: List[UUID] = Field(default_factory=list)
    stage: str
    region: str = "SG"
    clauses_enabled: List[str] = Field(default_factory=lambda: ["exclusivity", "pro_rata_rights"])
    transaction_id: UUID  # Required


class ClauseBlock(BaseModel):
    """Term sheet clause block with redlines"""
    id: str
    title: str
    content_md: str
    redlines: List[str] = Field(default_factory=list)
    citations: List["ChatCitation"] = Field(default_factory=list)
    current_value: Dict[str, Any] = Field(default_factory=dict)
    default_band: Optional[tuple[float, float]] = None
    walk_away: Optional[tuple[float, float]] = None


class ChatCitation(BaseModel):
    """Citation chip for explanations"""
    id: int
    clause_key: str
    perspective: Literal["detail", "founder", "investor", "batna", "balance"]
    content: str


class Draft0Response(BaseModel):
    """Draft 0 term sheet with clauses"""
    session_id: UUID
    company_persona_id: UUID
    investor_persona_ids: List[UUID]
    clauses: List[ClauseBlock]
    summary_md: str
    utilities: Dict[str, float] = Field(default_factory=dict)
    anchor_investor: Optional[str] = None
    created_at: datetime


# ============================================================================
# CHAT INTENT SCHEMAS
# ============================================================================

class CopilotIntentRequest(BaseModel):
    """Chat intent request"""
    intent: Literal["explain_clause", "revise_clause", "simulate_trade", "regenerate_document", "update_persona", "general_chat"]
    session_id: UUID
    clause_key: Optional[str] = None
    new_value: Optional[Dict[str, Any]] = None
    persona_updates: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    transaction_id: Optional[UUID] = None  # For context
    acting_as: Optional[Literal["founder", "investor"]] = None  # Role-play context


class CopilotIntentResponse(BaseModel):
    """Chat intent response"""
    intent: str
    success: bool
    message: str
    updated_clauses: List[ClauseBlock] = Field(default_factory=list)
    utilities: Dict[str, float] = Field(default_factory=dict)
    suggested_trades: List[str] = Field(default_factory=list)
    citations: List[ChatCitation] = Field(default_factory=list)


# ============================================================================
# ERROR SCHEMAS
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


# ============================================================================
# TRANSACTION SCHEMAS
# ============================================================================

class TransactionCreateRequest(BaseModel):
    """Create a new transaction"""
    name: Optional[str] = None


class TransactionResponse(BaseModel):
    """Transaction response"""
    id: UUID
    name: Optional[str]
    created_at: datetime
    owner_user: UUID


class TransactionPersonaLinkRequest(BaseModel):
    """Link a persona to a transaction"""
    kind: Literal["company", "investor"]
    label: Optional[str] = None
    persona_id: Optional[UUID] = None  # Link existing
    attrs: Optional[Dict[str, Any]] = None  # Create new


class TransactionPersonaResponse(BaseModel):
    """Transaction persona response"""
    id: UUID
    transaction_id: UUID
    kind: str
    label: Optional[str]
    persona_id: UUID
    created_at: datetime

