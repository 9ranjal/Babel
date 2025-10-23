"""
Intake Q&A state machine for copilot
"""
from typing import Dict, Any, List, Optional, Tuple
from ..models.schemas import IntakeStartResponse, IntakeAnswerResponse
from ..services.supabase import get_supabase
from ..services.ollama import get_ollama_client


class IntakeEngine:
    """Handles static and dynamic Q&A for persona creation"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.ollama = get_ollama_client()
        # Note: Use persisted persona.attrs.intake_session for durability
        self.sessions = {}
    
    async def start_intake(self, role: str, stage: str, region: str, transaction_id: str = None) -> IntakeStartResponse:
        """Start intake flow with first question"""
        import uuid
        session_id = str(uuid.uuid4())
        
        # Auto-create transaction if not provided
        if not transaction_id:
            try:
                # Use the transactions API to create transaction
                from ..routes.transactions import create_transaction
                tx_request = type('obj', (object,), {'name': f"Intake {role} - {stage}"})()
                tx_response = create_transaction(tx_request, self.supabase)
                transaction_id = str(tx_response.id)
            except Exception as e:
                # Fallback: use a placeholder transaction_id
                transaction_id = "temp-transaction-id"
        
        # Create a persona immediately and persist intake session
        attrs = {
            "stage": stage,
            "region": region,
            "transaction_id": transaction_id,
            "intake_session": {
                "session_id": session_id,
                "state": "static_collecting",
                "answers": {},
                "role": role
            }
        }
        persona_kind = "company" if role == "founder" else "investor"
        persona_data = {
            "owner_user": "00000000-0000-0000-0000-000000000000",
            "kind": persona_kind,
            "attrs": attrs,
            "leverage_score": 0.5,
            "weights": {"exclusivity": 0.5, "vesting": 0.5, "pro_rata_rights": 0.3},
            "batna": {}
        }
        result = self.supabase.table("personas").insert(persona_data).execute()
        persona_id = result.data[0]["id"]
        
        # Link persona to transaction (skip if table doesn't exist)
        try:
            link_data = {
                "transaction_id": transaction_id,
                "kind": "company" if role == "founder" else "investor",
                "label": f"{role.title()} Persona",
                "persona_id": persona_id
            }
            self.supabase.table("transaction_personas").insert(link_data).execute()
        except Exception as e:
            # Skip linking if transactions table doesn't exist
            pass
        
        # Mirror minimal session in memory for speed
        self.sessions[session_id] = {"role": role, "stage": stage, "region": region, "answers": {}, "persona_id": persona_id, "transaction_id": transaction_id}
        
        # Generate first question using Ollama
        try:
            question_data = await self.ollama.generate_intake_question(role, stage, region)
            question = IntakeStartResponse(
                question_id=question_data.get("question_id", "dynamic_1"),
                question_text=question_data["question_text"],
                question_type=question_data["question_type"],
                options=question_data.get("options"),
                next_questions=question_data.get("next_questions", []),
                session_id=session_id,
                persona_id=persona_id,
                transaction_id=transaction_id
            )
            return question
        except Exception as e:
            # Fallback to static questions
            if role == "founder":
                question = self._get_founder_question("construct")
                question.session_id = session_id
                question.persona_id = persona_id
                question.transaction_id = transaction_id
                return question
            else:
                question = self._get_investor_question("ownership")
                question.session_id = session_id
                question.persona_id = persona_id
                question.transaction_id = transaction_id
                return question
    
    async def answer_question(self, question_id: str, answer: Any, session_id: str = None, persona_id: str = None) -> IntakeAnswerResponse:
        """Process answer and return next question or completion"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
        else:
            # Try to recover from persona.attrs.intake_session
            if not persona_id:
                raise ValueError("Invalid session ID")
            pr = self.supabase.table("personas").select("*").eq("id", persona_id).execute()
            if not pr.data:
                raise ValueError("Invalid session ID")
            persona = pr.data[0]
            intake = (persona.get("attrs") or {}).get("intake_session") or {}
            if intake.get("session_id") != session_id:
                raise ValueError("Invalid session ID")
            # Rebuild minimal session in memory
            session = {
                "role": intake.get("role"),
                "stage": (persona.get("attrs") or {}).get("stage"),
                "region": (persona.get("attrs") or {}).get("region"),
                "answers": intake.get("answers", {}),
                "persona_id": str(persona.get("id"))
            }
            self.sessions[session_id] = session
        
        session["answers"][question_id] = answer
        # Persist answer into persona.attrs and recompute
        self._persist_answer_and_recompute(session["persona_id"], question_id, answer, session)
        
        # Handle dynamic questions from OpenRouter
        if question_id.startswith("dynamic_"):
            return await self._process_dynamic_answer(question_id, session)
        elif session["role"] == "founder":
            return self._process_founder_answer(question_id, session)
        else:
            return self._process_investor_answer(question_id, session)
    
    def _get_founder_question(self, question_id: str) -> IntakeStartResponse:
        """Get founder question by ID"""
        questions = {
            "construct": IntakeStartResponse(
                question_id="construct",
                question_text="Premoney or Postmoney construct, and planned investment size?",
                question_type="choice",
                options=["Premoney", "Postmoney"],
                next_questions=["round_size", "runway", "alt_offers", "repeat_founder", "diligence_speed"]
            ),
            "round_size": IntakeStartResponse(
                question_id="round_size",
                question_text="What's the planned investment size (USD)?",
                question_type="number",
                next_questions=["runway", "alt_offers", "repeat_founder", "diligence_speed"]
            ),
            "runway": IntakeStartResponse(
                question_id="runway",
                question_text="Months of runway remaining?",
                question_type="number",
                next_questions=["alt_offers", "repeat_founder", "diligence_speed"]
            ),
            "alt_offers": IntakeStartResponse(
                question_id="alt_offers",
                question_text="Any active/credible alternate offers (0-3+)?",
                question_type="number",
                next_questions=["repeat_founder", "diligence_speed"]
            ),
            "repeat_founder": IntakeStartResponse(
                question_id="repeat_founder",
                question_text="Are any founders repeat founders?",
                question_type="boolean",
                next_questions=["diligence_speed"]
            ),
            "diligence_speed": IntakeStartResponse(
                question_id="diligence_speed",
                question_text="Diligence timeline: accelerated, standard, or extended?",
                question_type="choice",
                options=["accelerated", "standard", "extended"],
                next_questions=[]
            )
        }
        return questions[question_id]
    
    def _get_investor_question(self, question_id: str) -> IntakeStartResponse:
        """Get investor question by ID"""
        questions = {
            "ownership": IntakeStartResponse(
                question_id="ownership",
                question_text="Target ownership percentage for this round?",
                question_type="number",
                next_questions=["marquee", "diligence_speed", "construct", "round_size", "fund_constraints"]
            ),
            "marquee": IntakeStartResponse(
                question_id="marquee",
                question_text="Are you a marquee fund for this deal?",
                question_type="boolean",
                next_questions=["diligence_speed", "construct", "round_size", "fund_constraints"]
            ),
            "diligence_speed": IntakeStartResponse(
                question_id="diligence_speed",
                question_text="Diligence timeline: accelerated, standard, or extended?",
                question_type="choice",
                options=["accelerated", "standard", "extended"],
                next_questions=["construct", "round_size", "fund_constraints"]
            ),
            "construct": IntakeStartResponse(
                question_id="construct",
                question_text="Premoney or Postmoney construct, and planned investment size?",
                question_type="choice",
                options=["Premoney", "Postmoney"],
                next_questions=["round_size", "fund_constraints"]
            ),
            "round_size": IntakeStartResponse(
                question_id="round_size",
                question_text="What's the planned investment size (USD)?",
                question_type="number",
                next_questions=["fund_constraints"]
            ),
            "fund_constraints": IntakeStartResponse(
                question_id="fund_constraints",
                question_text="Any special constraints (e.g., IC cadence, fund vintage)?",
                question_type="text",
                next_questions=[]
            )
        }
        return questions[question_id]
    
    def _process_founder_answer(self, question_id: str, session: Dict[str, Any]) -> IntakeAnswerResponse:
        """Process founder answer and determine next step"""
        if question_id == "diligence_speed":
            # Complete founder intake
            persona_id = self._create_founder_persona(session)
            return IntakeAnswerResponse(
                completed=True,
                persona_id=persona_id,
                message="Founder persona created successfully!"
            )
        else:
            # Get next question
            next_questions = self._get_founder_question(question_id).next_questions
            if next_questions:
                next_q = self._get_founder_question(next_questions[0])
                return IntakeAnswerResponse(next_question=next_q)
            else:
                return IntakeAnswerResponse(completed=True)
    
    def _process_investor_answer(self, question_id: str, session: Dict[str, Any]) -> IntakeAnswerResponse:
        """Process investor answer and determine next step"""
        if question_id == "fund_constraints":
            # Complete investor intake
            persona_id = self._create_investor_persona(session)
            return IntakeAnswerResponse(
                completed=True,
                persona_id=persona_id,
                message="Investor persona created successfully!"
            )
        else:
            # Get next question
            next_questions = self._get_investor_question(question_id).next_questions
            if next_questions:
                next_q = self._get_investor_question(next_questions[0])
                return IntakeAnswerResponse(next_question=next_q)
            else:
                return IntakeAnswerResponse(completed=True)
    
    def _create_founder_persona(self, session: Dict[str, Any]) -> str:
        """Create founder persona from answers"""
        answers = session["answers"]
        attrs = {
            "stage": session["stage"],
            "region": session["region"],
            "construct": answers.get("construct"),
            "round_size": answers.get("round_size"),
            "runway_months": answers.get("runway"),
            "alt_offers": answers.get("alt_offers", 0),
            "repeat_founder_any": answers.get("repeat_founder", False),
            "diligence_speed": answers.get("diligence_speed", "standard")
        }
        
        # Compute leverage and weights
        leverage, weights, batna = self._compute_founder_derivations(attrs)
        
        persona_data = {
            "owner_user": "00000000-0000-0000-0000-000000000000",
            "kind": "company",
            "attrs": attrs,
            "leverage_score": leverage,
            "weights": weights,
            "batna": batna
        }
        
        result = self.supabase.table("personas").insert(persona_data).execute()
        return result.data[0]["id"]
    
    def _create_investor_persona(self, session: Dict[str, Any]) -> str:
        """Create investor persona from answers"""
        answers = session["answers"]
        attrs = {
            "stage": session["stage"],
            "region": session["region"],
            "ownership_target_pct": answers.get("ownership"),
            "marquee": answers.get("marquee", False),
            "diligence_speed": answers.get("diligence_speed", "standard"),
            "construct": answers.get("construct"),
            "round_size": answers.get("round_size"),
            "fund_constraints": answers.get("fund_constraints", "")
        }
        
        # Compute leverage and weights
        leverage, weights, batna = self._compute_investor_derivations(attrs)
        
        persona_data = {
            "owner_user": "00000000-0000-0000-0000-000000000000",
            "kind": "investor",
            "attrs": attrs,
            "leverage_score": leverage,
            "weights": weights,
            "batna": batna
        }
        
        result = self.supabase.table("personas").insert(persona_data).execute()
        return result.data[0]["id"]

    def _persist_answer_and_recompute(self, persona_id: str, question_id: str, answer: Any, session: Dict[str, Any]) -> None:
        """Merge answer into persona.attrs.intake_session.answers and recompute derivations."""
        # Fetch persona
        pr = self.supabase.table("personas").select("*").eq("id", persona_id).execute()
        if not pr.data:
            return
        persona = pr.data[0]
        attrs = persona.get("attrs", {})
        intake = attrs.get("intake_session", {"answers": {}, "state": "static_collecting", "session_id": session.get("session_id"), "role": session.get("role")})
        intake_answers = intake.get("answers", {})
        intake_answers[question_id] = answer
        intake["answers"] = intake_answers
        attrs["intake_session"] = intake
        
        # Also promote known keys into top-level attrs convenience
        promote = {
            "construct": "construct",
            "round_size": "round_size",
            "runway": "runway_months",
            "alt_offers": "alt_offers",
            "repeat_founder": "repeat_founder_any",
            "diligence_speed": "diligence_speed",
            "ownership": "ownership_target_pct",
            "marquee": "marquee",
            "fund_constraints": "fund_constraints"
        }
        if question_id in promote:
            attrs[promote[question_id]] = answer
        
        # Recompute leverage, weights, batna using derivations
        kind = persona.get("kind")
        if kind == "company":
            leverage, weights, batna = self._compute_founder_derivations(attrs)
        else:
            leverage, weights, batna = self._compute_investor_derivations(attrs)
        
        update_data = {
            "attrs": attrs,
            "leverage_score": leverage,
            "weights": weights,
            "batna": batna
        }
        self.supabase.table("personas").update(update_data).eq("id", persona_id).execute()
    
    def _compute_founder_derivations(self, attrs: Dict[str, Any]) -> Tuple[float, Dict[str, float], Dict[str, Any]]:
        """Compute leverage, weights, and BATNA for founder"""
        leverage = 0.5  # Base
        
        # Leverage factors
        if attrs.get("repeat_founder_any"):
            leverage += 0.2
        if attrs.get("alt_offers", 0) > 0:
            leverage += 0.15
        if attrs.get("runway_months", 0) > 6:
            leverage += 0.1
        if attrs.get("runway_months", 0) < 4:
            leverage -= 0.2
        
        leverage = max(0.0, min(1.0, leverage))
        
        # Weights
        weights = {"exclusivity": 0.5, "vesting": 0.5, "pro_rata_rights": 0.3}
        if attrs.get("runway_months", 0) < 6 or attrs.get("diligence_speed") == "accelerated":
            weights["exclusivity"] = 0.8
        
        # BATNA (ideal values)
        batna = {
            "exclusivity": {"period_days": 30},
            "vesting": {"vesting_months": 36, "cliff_months": 0},
            "pro_rata_rights": {"enabled": False}
        }
        
        return leverage, weights, batna
    
    def _compute_investor_derivations(self, attrs: Dict[str, Any]) -> Tuple[float, Dict[str, float], Dict[str, Any]]:
        """Compute leverage, weights, and BATNA for investor"""
        leverage = 0.5  # Base
        
        # Leverage factors
        if attrs.get("marquee"):
            leverage += 0.2
        if attrs.get("ownership_target_pct", 0) > 0.15:
            leverage += 0.1
        if attrs.get("diligence_speed") == "accelerated":
            leverage -= 0.1
        
        leverage = max(0.0, min(1.0, leverage))
        
        # Weights
        weights = {"exclusivity": 0.7, "vesting": 0.8, "pro_rata_rights": 0.5}
        if attrs.get("marquee"):
            weights["pro_rata_rights"] = 0.8
        
        # BATNA (ideal values)
        batna = {
            "exclusivity": {"period_days": 60},
            "vesting": {"vesting_months": 48, "cliff_months": 12},
            "pro_rata_rights": {"enabled": True, "threshold_ownership_pct": 2}
        }
        
        return leverage, weights, batna
    
    async def _process_dynamic_answer(self, question_id: str, session: Dict[str, Any]) -> IntakeAnswerResponse:
        """Process dynamic question answer using OpenRouter"""
        try:
            # Generate next question using Ollama
            question_data = await self.ollama.generate_intake_question(
                session["role"],
                session.get("stage", "seed"),
                session.get("region", "SG"),
                session["answers"]
            )
            
            # Check if intake is complete (no more questions)
            if not question_data.get("next_questions") or len(session["answers"]) >= 5:
                # Create persona and complete intake
                persona_id = self._create_persona_from_session(session)
                return IntakeAnswerResponse(
                    completed=True,
                    persona_id=persona_id,
                    message="Intake completed successfully!"
                )
            
            # Return next question
            next_question = IntakeStartResponse(
                question_id=question_data.get("question_id", f"dynamic_{len(session['answers']) + 1}"),
                question_text=question_data["question_text"],
                question_type=question_data["question_type"],
                options=question_data.get("options"),
                next_questions=question_data.get("next_questions", []),
                session_id=session.get("session_id"),
                persona_id=session.get("persona_id"),
                transaction_id=session.get("transaction_id")
            )
            
            return IntakeAnswerResponse(next_question=next_question)
            
        except Exception as e:
            # Fallback to completion
            persona_id = self._create_persona_from_session(session)
            return IntakeAnswerResponse(
                completed=True,
                persona_id=persona_id,
                message="Intake completed with fallback"
            )
    
    def _create_persona_from_session(self, session: Dict[str, Any]) -> str:
        """Create persona from session data"""
        attrs = {
            "stage": session.get("stage", "seed"),
            "region": session.get("region", "SG"),
            "answers": session["answers"]
        }
        
        persona_data = {
            "owner_user": "00000000-0000-0000-0000-000000000000",
            "kind": "company" if session["role"] == "founder" else "investor",
            "attrs": attrs,
            "leverage_score": 0.5,
            "weights": {"exclusivity": 0.5, "vesting": 0.5},
            "batna": {}
        }
        
        result = self.supabase.table("personas").insert(persona_data).execute()
        return result.data[0]["id"]
