"""
Orchestrator: Coordinates the full negotiation round flow
"""
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime

from ..models.schemas import (
    NegotiationContext,
    NegotiationRoundResponse,
    NegotiationTrace,
    PersonaResponse,
    SessionTermResponse,
    TermProposal,
    EmbeddedSnippet
)
from .market import MarketEngine
from .policy import PolicyEngine
from .utility import UtilityEngine
from .solver import NegotiationSolver
from .skills import ExclusivitySkill, PreemptionSkill, VestingSkill, TransferSkill
from ..rag.retriever import GuidanceRetriever


class NegotiationOrchestrator:
    """Coordinates full negotiation round execution"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.market_engine = MarketEngine(supabase_client)
        self.policy_engine = PolicyEngine(supabase_client)
        self.utility_engine = UtilityEngine()
        self.solver = NegotiationSolver(supabase_client)
        self.retriever = GuidanceRetriever(supabase_client)
        
        # Register skills
        self.skills = {
            "exclusivity": ExclusivitySkill(supabase_client),
            "preemption_rights": PreemptionSkill(supabase_client),
            "vesting": VestingSkill(supabase_client),
            "transfer_restrictions": TransferSkill(supabase_client)
        }
    
    async def run_round(
        self,
        session_id: UUID,
        round_no: Optional[int] = None,
        user_overrides: Optional[Dict[str, Any]] = None
    ) -> NegotiationRoundResponse:
        """
        Execute a full negotiation round
        
        Steps:
        1. Fetch context (session, personas, guidance, market data)
        2. Generate proposals (company & investor) using skills
        3. Solve for compromise using Nash-lite
        4. Grade & justify
        5. Persist to negotiation_rounds & session_terms
        6. Return response with trace & citations
        """
        # Step 1: Fetch context
        context = await self._fetch_context(session_id, round_no, user_overrides)
        
        # Step 2: Generate proposals
        company_proposals = self._generate_proposals(context, "company")
        investor_proposals = self._generate_proposals(context, "investor")
        
        # Step 3: Solve for compromise
        final_terms = self.solver.solve(company_proposals, investor_proposals, context)
        
        # Step 4: Calculate utilities
        utilities = self.utility_engine.get_utilities(final_terms, context)
        
        # Step 5: Build traces & collect citations
        traces, all_snippet_ids = self._build_traces(
            company_proposals,
            investor_proposals,
            final_terms,
            context
        )
        
        # Fetch all cited snippets
        citations = self.retriever.get_snippets_by_ids(all_snippet_ids)
        
        # Step 6: Grade (simple policy check for now)
        grades = self._grade_solution(final_terms, context)
        
        # Step 7: Build overall rationale
        rationale_md = self._build_rationale(traces, utilities, grades)
        
        # Step 8: Persist to database
        round_response = await self._persist_round(
            session_id,
            context.round_no,
            company_proposals,
            investor_proposals,
            final_terms,
            utilities,
            rationale_md,
            traces,
            grades
        )
        
        # Add traces and citations to response
        round_response.traces = traces
        round_response.citations = citations
        
        return round_response
    
    async def _fetch_context(
        self,
        session_id: UUID,
        round_no: Optional[int],
        user_overrides: Optional[Dict[str, Any]]
    ) -> NegotiationContext:
        """Fetch all context needed for negotiation"""
        
        # Fetch session with transaction context
        session_result = self.supabase.table("negotiation_sessions").select(
            "*, company_persona:personas!company_persona(*), investor_persona:personas!investor_persona(*), transaction_id"
        ).eq("id", str(session_id)).execute()
        
        if not session_result.data or len(session_result.data) == 0:
            raise ValueError(f"Session {session_id} not found")
        
        session = session_result.data[0]
        
        # Parse personas
        company_persona = PersonaResponse(**session["company_persona"])
        investor_persona = PersonaResponse(**session["investor_persona"])
        
        # Derive stage from company persona attrs
        stage = company_persona.attrs.get("stage", "seed")
        region = session.get("regime", "IN")
        
        # Determine round number
        if round_no is None:
            # Auto-increment: find max existing round + 1
            rounds_result = self.supabase.table("negotiation_rounds").select(
                "round_no"
            ).eq("session_id", str(session_id)).order("round_no", desc=True).limit(1).execute()
            
            if rounds_result.data and len(rounds_result.data) > 0:
                round_no = rounds_result.data[0]["round_no"] + 1
            else:
                round_no = 1
        
        # Fetch guidance for all active clauses
        clause_keys = list(self.skills.keys())
        guidance = self.market_engine.get_all_guidance(stage, region, clause_keys)
        market_data = self.market_engine.get_all_benchmarks(stage, region, clause_keys)
        
        # Fetch existing terms
        terms_result = self.supabase.table("session_terms").select("*").eq(
            "session_id", str(session_id)
        ).execute()
        
        existing_terms = {}
        if terms_result.data:
            for row in terms_result.data:
                term = SessionTermResponse(**row)
                existing_terms[term.clause_key] = term
        
        return NegotiationContext(
            session_id=session_id,
            round_no=round_no,
            regime=region,
            stage=stage,
            region=region,
            company_persona=company_persona,
            investor_persona=investor_persona,
            guidance=guidance,
            market_data=market_data,
            existing_terms=existing_terms,
            user_overrides=user_overrides or {}
        )
    
    def _generate_proposals(
        self,
        context: NegotiationContext,
        party: str
    ) -> Dict[str, TermProposal]:
        """Generate proposals for all clauses from one party's perspective"""
        proposals = {}
        
        for clause_key, skill in self.skills.items():
            # Skip if pinned or overridden
            existing_term = context.existing_terms.get(clause_key)
            if existing_term and existing_term.pinned_by:
                continue
            
            if clause_key in context.user_overrides:
                continue
            
            # Generate proposal using skill
            try:
                if party == "company":
                    proposal = skill.propose_company(context)
                else:
                    proposal = skill.propose_investor(context)
                
                proposals[clause_key] = proposal
            except Exception as e:
                print(f"Error generating {party} proposal for {clause_key}: {e}")
                # Skip this clause
                continue
        
        return proposals
    
    def _build_traces(
        self,
        company_proposals: Dict[str, TermProposal],
        investor_proposals: Dict[str, TermProposal],
        final_terms: Dict[str, Dict[str, Any]],
        context: NegotiationContext
    ) -> tuple[List[NegotiationTrace], List[int]]:
        """Build per-clause traces and collect all snippet IDs"""
        traces = []
        all_snippet_ids = []
        
        for clause_key, final_value in final_terms.items():
            company_prop = company_proposals.get(clause_key)
            investor_prop = investor_proposals.get(clause_key)
            
            # Collect snippet IDs
            snippet_ids = []
            if company_prop:
                snippet_ids.extend(company_prop.snippet_ids)
            if investor_prop:
                snippet_ids.extend(investor_prop.snippet_ids)
            
            all_snippet_ids.extend(snippet_ids)
            
            # Build rationale
            rationale_parts = []
            if company_prop:
                rationale_parts.append(f"Company: {company_prop.rationale}")
            if investor_prop:
                rationale_parts.append(f"Investor: {investor_prop.rationale}")
            
            rationale = " | ".join(rationale_parts) if rationale_parts else "Compromise reached"
            
            trace = NegotiationTrace(
                clause_key=clause_key,
                company_proposal=company_prop.value if company_prop else {},
                investor_proposal=investor_prop.value if investor_prop else {},
                final_value=final_value,
                rationale=rationale,
                snippet_ids=snippet_ids,
                confidence=0.85  # TODO: Calculate real confidence
            )
            
            traces.append(trace)
        
        return traces, all_snippet_ids
    
    def _grade_solution(
        self,
        final_terms: Dict[str, Dict[str, Any]],
        context: NegotiationContext
    ) -> Dict[str, Any]:
        """Grade the solution for policy compliance and grounding"""
        
        policy_ok = True
        validation_errors = []
        
        for clause_key, value in final_terms.items():
            is_valid, error_msg = self.policy_engine.validate_term(clause_key, value, context)
            if not is_valid:
                policy_ok = False
                validation_errors.append(f"{clause_key}: {error_msg}")
        
        # Calculate grounding score (how well-supported by guidance)
        grounding_score = 0.9  # TODO: Calculate based on snippet relevance
        
        return {
            "policy_ok": policy_ok,
            "grounding": grounding_score,
            "validation_errors": validation_errors
        }
    
    def _build_rationale(
        self,
        traces: List[NegotiationTrace],
        utilities: Dict[str, float],
        grades: Dict[str, Any]
    ) -> str:
        """Build overall markdown rationale"""
        
        parts = [
            "## Negotiation Round Summary\n",
            f"**Company Utility:** {utilities['company']:.1f}/100",
            f"**Investor Utility:** {utilities['investor']:.1f}/100",
            f"**Policy Compliant:** {'✓' if grades['policy_ok'] else '✗'}",
            f"**Grounding Score:** {grades['grounding']:.2f}\n",
            "### Term-by-Term Analysis\n"
        ]
        
        for trace in traces:
            parts.append(f"**{trace.clause_key}:**")
            parts.append(f"- Company proposed: {trace.company_proposal}")
            parts.append(f"- Investor proposed: {trace.investor_proposal}")
            parts.append(f"- **Final:** {trace.final_value}")
            parts.append(f"- Rationale: {trace.rationale}\n")
        
        return "\n".join(parts)
    
    async def _persist_round(
        self,
        session_id: UUID,
        round_no: int,
        company_proposals: Dict[str, TermProposal],
        investor_proposals: Dict[str, TermProposal],
        final_terms: Dict[str, Dict[str, Any]],
        utilities: Dict[str, float],
        rationale_md: str,
        traces: List[NegotiationTrace],
        grades: Dict[str, Any]
    ) -> NegotiationRoundResponse:
        """Persist round to database and update session terms"""
        
        # Convert proposals to dicts
        company_prop_dict = {k: v.value for k, v in company_proposals.items()}
        investor_prop_dict = {k: v.value for k, v in investor_proposals.items()}
        
        # Build state snapshot
        state_snapshot = {
            "traces": [t.dict() for t in traces],
            "final_terms": final_terms
        }
        
        # Insert negotiation round
        round_data = {
            "session_id": str(session_id),
            "round_no": round_no,
            "company_proposal": company_prop_dict,
            "investor_proposal": investor_prop_dict,
            "mediator_choice": final_terms,
            "utilities": utilities,
            "rationale_md": rationale_md,
            "state_snapshot": state_snapshot,
            "grades": grades,
            "decided": False
        }
        
        round_result = self.supabase.table("negotiation_rounds").insert(round_data).execute()
        
        # Upsert session terms
        for clause_key, value in final_terms.items():
            term_data = {
                "session_id": str(session_id),
                "clause_key": clause_key,
                "value": value,
                "source": "copilot",
                "confidence": 0.85  # TODO: Calculate real confidence
            }
            
            self.supabase.table("session_terms").upsert(term_data).execute()
        
        # Compute anchor investor and weights
        anchored_by, investor_weights = self._compute_anchor_and_weights(context)
        
        # Build response
        return NegotiationRoundResponse(
            session_id=session_id,
            round_no=round_no,
            company_proposal=company_prop_dict,
            investor_proposal=investor_prop_dict,
            mediator_choice=final_terms,
            utilities=utilities,
            rationale_md=rationale_md,
            traces=[],  # Will be added by caller
            citations=[],  # Will be added by caller
            grades=grades,
            decided=False,
            created_at=datetime.now(),
            anchored_by=anchored_by,
            investor_weights=investor_weights,
            transaction_id=context.session.get("transaction_id")
        )
    
    def _compute_anchor_and_weights(self, context: NegotiationContext) -> tuple[Optional[str], Optional[Dict[str, float]]]:
        """Compute anchor investor and weights for transaction-scoped negotiation"""
        try:
            # Get transaction personas for this session
            transaction_id = context.session.get("transaction_id")
            if not transaction_id:
                return None, None
            
            # Fetch all investor personas in this transaction
            tx_personas_result = self.supabase.table("transaction_personas").select(
                "*, persona:personas!persona_id(*)"
            ).eq("transaction_id", str(transaction_id)).eq("kind", "investor").execute()
            
            if not tx_personas_result.data:
                return None, None
            
            investors = []
            for tp in tx_personas_result.data:
                persona = tp.get("persona", {})
                attrs = persona.get("attrs", {})
                investors.append({
                    "id": persona.get("id"),
                    "label": tp.get("label", f"Investor {persona.get('id', '')[:8]}"),
                    "marquee": attrs.get("marquee", False),
                    "ownership_target_pct": attrs.get("ownership_target_pct", 0.0)
                })
            
            if not investors:
                return None, None
            
            # Find anchor investor (marquee first, then highest ownership)
            marquee_investors = [inv for inv in investors if inv.get("marquee")]
            if marquee_investors:
                anchor = max(marquee_investors, key=lambda x: x.get("ownership_target_pct", 0))
                anchored_by = anchor["label"]
            else:
                anchor = max(investors, key=lambda x: x.get("ownership_target_pct", 0))
                anchored_by = anchor["label"]
            
            # Compute weights by ownership_target_pct (equal if unknown)
            total_ownership = sum(inv.get("ownership_target_pct", 0) for inv in investors)
            if total_ownership > 0:
                weights = {
                    inv["label"]: inv.get("ownership_target_pct", 0) / total_ownership
                    for inv in investors
                }
            else:
                # Equal weights if no ownership data
                equal_weight = 1.0 / len(investors)
                weights = {inv["label"]: equal_weight for inv in investors}
            
            return anchored_by, weights
            
        except Exception as e:
            # Return None if computation fails
            return None, None

