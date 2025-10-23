# 🚀 Termcraft AI - VC Lawyer Copilot & Negotiation Engine

A sophisticated AI-powered negotiation engine with an intelligent VC lawyer copilot that provides data-driven advice based on actual BATNA (Best Alternative To Negotiated Agreement) analysis. Built with FastAPI, React, and Supabase.

## 🎯 **Overview**

Termcraft AI combines a **transaction-first negotiation engine** with an **intelligent VC lawyer copilot** that provides personalized, data-driven advice. The system uses real persona leverage, BATNA bands, and market data to generate intelligent responses rather than generic guidance.

### **Key Features**
- **🧠 Intelligent VC Lawyer Copilot**: BATNA-aware AI that provides personalized advice
- **📊 Transaction-First Architecture**: Decoupled personas from users, transaction-scoped negotiations
- **⚖️ BATNA-Driven Intelligence**: Real leverage analysis and negotiation positioning
- **🎯 Modular Prompt System**: Centralized, maintainable AI prompt management
- **🔄 Real-Time Negotiation**: Live term sheet generation with redlining
- **📈 Market Integration**: Real guidance and benchmarks from industry data
- **🔒 Policy Enforcement**: Hard constraints and validation
- **📚 Citation System**: RAG-powered explanations and justifications

---

## 🏗️ **Architecture**

### **System Overview**
```
Frontend (React + TypeScript) ←→ Backend (FastAPI + Python) ←→ Database (Supabase)
                                    ↓
                            VC Lawyer Copilot (BATNA-Aware AI)
```

### **🧠 Copilot Intelligence Layer**
- **BATNA-Aware Prompts**: AI responses based on real persona leverage and preferences
- **Modular Prompt System**: Centralized prompt management with intent-specific handlers
- **Context Service**: Transaction-aware persona and leverage analysis
- **Intent Detection**: Smart routing between explain, revise, simulate, and general chat

### **⚖️ Negotiation Engine**
- **Orchestrator**: Coordinates the entire negotiation flow
- **Skills Layer**: Clause-specific logic (exclusivity, vesting, preemption)
- **Solver**: Nash-lite compromise algorithm with leverage weighting
- **BATNA Engine**: Computes leverage, weights, and BATNA bands for personas
- **Policy Engine**: Constraint enforcement and validation
- **Market Engine**: Guidance and benchmark integration
- **RAG Retriever**: Citation and explanation system

### **📊 Transaction-First Data Model**
- **Transactions**: Root entity linking users, personas, and negotiations
- **Personas**: Decoupled from users, linked to transactions
- **Negotiation Sessions**: Transaction-scoped with persona context
- **BATNA Computation**: Real-time leverage and preference analysis

### **🎨 Frontend Components**
- **CopilotChat**: Intelligent VC lawyer interface with BATNA awareness
- **TermSheetEditor**: Live term sheet editing with redlining
- **TransactionSelector**: Transaction management interface
- **PersonaIntake**: Form-based persona creation with real-time BATNA
- **useNegotiation Hook**: Type-safe API integration

---

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.8+
- Node.js 18+
- Supabase account
- Ollama (for local AI) or OpenRouter API key

### **1. Database Setup**
```bash
# Apply migrations in Supabase SQL Editor
# Run: supabase/migrations/001_initial_schema.sql
# Run: supabase/migrations/002_seed_data.sql
# Run: supabase/migrations/003_dev_policies.sql
# Run: supabase/migrations/004_test_user.sql
# Run: supabase/migrations/005_transactions.sql
# Run: supabase/migrations/006_mvp_rls_bypass.sql
# Run: supabase/migrations/007_mvp_rls_fix.sql
```

### **2. Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export SUPABASE_URL="your_supabase_url"
export SUPABASE_SERVICE_ROLE_KEY="your_service_role_key"
export OPENROUTER_API_KEY="your-openrouter-key"  # Optional
export OPENROUTER_MODEL="meta-llama/llama-3.3-8b-instruct:free"

# Start backend
python -m uvicorn api.main:app --host 0.0.0.0 --port 5002 --reload
```

### **3. Frontend Setup**
```bash
cd frontend-cra-old
npm install

# Set environment variables
echo "REACT_APP_API_BASE=http://localhost:5002" > .env.local
echo "REACT_APP_SUPABASE_URL=your-supabase-url" >> .env.local
echo "REACT_APP_SUPABASE_ANON_KEY=your-supabase-anon-key" >> .env.local

# Start frontend
npm start
```

### **4. Test the System**
- **Frontend**: Visit `http://localhost:5003` for the main interface
- **Backend API**: Visit `http://localhost:5002/docs` for API documentation
- **Copilot Test**: Try `http://localhost:5002/api/copilot/prompts` to see available intents
- **BATNA Test**: Try `http://localhost:5002/api/copilot/test-batna/{transaction_id}` for BATNA-aware prompts

---

## 🧠 **VC Lawyer Copilot Features**

### **Intelligent Intent Detection**
The copilot automatically detects user intent and routes to appropriate handlers:

- **`explain_clause`**: "Explain liquidation preference" → BATNA-aware clause explanation
- **`revise_clause`**: "Change exclusivity to 60 days" → Analysis based on actual BATNA bands  
- **`simulate_trade`**: "Trade exclusivity for board seats" → Trade simulation with real leverage data
- **`general_chat`**: "What should I prioritize?" → Personalized advice based on actual persona leverage

### **BATNA-Aware Intelligence**
The copilot provides data-driven advice using real negotiation data:

```json
{
  "leverage_analysis": "Founder has LOW leverage (0.30) with short runway",
  "batna_bands": "Founder's BATNA: 30 days exclusivity (weight: 0.80)",
  "positioning": "Time pressure may limit options",
  "market_context": "Market standard: 30-90 days"
}
```

### **Modular Prompt Architecture**
- **Centralized Prompts**: All AI prompts managed in one place
- **Intent-Specific Handlers**: Specialized logic for each copilot function
- **BATNA Integration**: Real persona data drives AI responses
- **Context Awareness**: Transaction-scoped persona and leverage analysis

### **API Endpoints**
- `GET /api/copilot/prompts` - View all available prompts and intents
- `POST /api/copilot/chat` - General VC lawyer consultation
- `POST /api/copilot/intent` - Intent-specific responses
- `GET /api/copilot/test-batna/{transaction_id}` - Test BATNA-aware prompts

---

## 📊 **Current Status**

### ✅ **Completed (90%)**
- **🧠 VC Lawyer Copilot**: BATNA-aware AI with modular prompt system
- **📊 Transaction-First Architecture**: Decoupled personas from users
- **⚖️ BATNA Engine**: Real leverage computation and negotiation positioning
- **🎯 Modular Prompt System**: Centralized, maintainable AI prompt management
- **🔄 Backend Engine**: Complete negotiation system with 17 files
- **🗄️ Database Schema**: Full Supabase schema with RLS and transaction support
- **🌐 API Endpoints**: 8 REST endpoints for negotiation and copilot
- **🎨 Frontend Components**: TypeScript React components
- **🧪 Testing**: Manual testing with real personas and BATNA integration

### 🔄 **In Progress (10%)**
- **🎨 Frontend Integration**: Connecting React components to backend
- **🔄 Real-Time Updates**: Live term sheet editing with redlining
- **📝 Persona Intake**: Form-based persona creation with real-time BATNA
- **🎯 UI Polish**: Enhanced styling and user experience
- **⚡ Performance**: Optimization and caching

### ❌ **Not Started**
- **🔍 RAG Implementation**: Semantic search and embeddings
- **📄 Document Export**: Term sheet generation and export
- **🚀 Advanced Features**: Automated graders and retry logic

---

## 🏗️ **Refined Architecture: LLM vs. UI/UX**

### **✅ ACTUAL LLM Tasks (Keep These Prompts)**
- **`explain_clause`**: Explain what clauses mean with BATNA awareness
- **`revise_clause`**: Analyze proposed changes based on actual BATNA bands
- **`simulate_trade`**: Simulate negotiations with real leverage data
- **`general_chat`**: General VC lawyer advice with persona context

### **❌ NOT LLM Tasks (UI/UX Features)**
- **`update_persona`**: Form-based persona creation with real-time BATNA computation
- **`regenerate_document`**: Orchestrator-driven term sheet generation + frontend redlining

### **🎯 Benefits of Refined Architecture**
- **Clear Separation**: LLM for intelligence, UI/UX for data management
- **Better Performance**: LLM only for complex reasoning, system for fast operations
- **More Reliable**: LLM focused on reasoning, system for deterministic operations
- **Easier Maintenance**: Fewer, focused prompts with clear API boundaries

---

## 🎯 **Usage Examples**

### **Test VC Lawyer Copilot**
```bash
# View available intents
curl http://localhost:5002/api/copilot/prompts

# Test BATNA-aware prompts
curl http://localhost:5002/api/copilot/test-batna/{transaction_id}?clause_key=exclusivity

# General chat with VC lawyer
curl -X POST http://localhost:5002/api/copilot/chat \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "general_chat",
    "session_id": "uuid-here",
    "message": "What should I prioritize in this negotiation?",
    "transaction_id": "uuid-here"
  }'
```

### **Create Negotiation Session**
```bash
curl -X POST http://localhost:5002/api/negotiate/session \
  -H "Content-Type: application/json" \
  -d '{
    "company_persona": "38d28f41-9009-4005-9949-c7b3a6d94f24",
    "investor_persona": "3bce16e5-874a-4d92-a622-89edc11419c5",
    "transaction_id": "uuid-here",
    "regime": "IN"
  }'
```

### **Run Negotiation Round**
```bash
curl -X POST http://localhost:5002/api/negotiate/round \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id"
  }'
```

### **Frontend Integration**
```typescript
import { useNegotiation } from './hooks/useNegotiation';

function MyComponent() {
  const { runRound, currentRound, terms, loading } = useNegotiation();
  
  const handleGenerate = async () => {
    const result = await runRound(sessionId);
    console.log('Round complete:', result);
  };
  
  return (
    <div>
      <button onClick={handleGenerate}>Generate Terms</button>
      <TermsDisplay terms={terms} />
      <NegotiationPanel round={currentRound} loading={loading} />
    </div>
  );
}
```

---

## 📋 **API Endpoints**

### **Negotiation Endpoints**
- `POST /api/negotiate/session` - Create negotiation session
- `POST /api/negotiate/round` - Run negotiation round
- `GET /api/negotiate/session/{id}` - Get session details
- `GET /api/negotiate/session/{id}/terms` - Get session terms
- `PUT /api/negotiate/session/{id}/terms/{key}` - Update specific term
- `GET /api/negotiate/session/{id}/rounds` - Get round history

### **Persona Endpoints**
- `GET /api/personas/` - List all personas
- `POST /api/personas/` - Create new persona
- `GET /api/personas/{id}` - Get persona details

---

## 🧪 **Testing**

### **Manual Testing**
```bash
# List available personas
python list_personas.py

# Test complete copilot flow
python test_copilot_flow.py

# Test database schema
python test_schema.py
```

### **API Testing**
```bash
# Health check
curl http://localhost:8000/api/health

# Create test transaction
curl -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Transaction"}'
```

---

## 📁 **Project Structure**

```
├── backend/                          # FastAPI Backend
│   ├── api/                          # API modules
│   │   ├── main.py                   # FastAPI app
│   │   ├── models/schemas.py         # Pydantic models
│   │   ├── services/                 # Service layer
│   │   ├── engine/                   # Negotiation engine
│   │   │   ├── orchestrator.py      # Main coordinator
│   │   │   ├── policy.py            # Constraint enforcement
│   │   │   ├── market.py            # Market data
│   │   │   ├── utility.py           # Utility calculation
│   │   │   ├── solver.py            # Nash-lite solver
│   │   │   └── skills/              # Clause-specific logic
│   │   ├── rag/retriever.py         # Citation system
│   │   └── routes/                  # API endpoints
│   └── requirements.txt
├── frontend-cra-old/                 # React Frontend
│   ├── src/
│   │   ├── components/              # React components
│   │   ├── hooks/useNegotiation.ts  # API integration
│   │   └── pages/                   # Page components
│   └── package.json
├── docs/                             # Documentation
│   ├── status/
│   │   └── PROJECT_STATUS.md        # Current status
│   ├── guides/
│   │   ├── IMPLEMENTATION_GUIDE.md  # Implementation details
│   │   ├── PERSONA_DETAILS.md       # Persona information
│   │   ├── QUICK_START.md           # Getting started
│   │   └── APPLY_DEV_POLICIES.md    # Development policies
│   └── architecture/
│       └── ARCHITECTURE_DIAGRAM.md   # System architecture
├── scripts/                          # Utility Scripts
│   ├── migration/                    # Database migrations
│   │   ├── apply_migration_simple.py
│   │   ├── run_migration.sql
│   │   └── create_test_transaction.sql
│   ├── testing/                      # Test scripts
│   │   ├── test_copilot_flow.py
│   │   ├── test_schema.py
│   │   └── list_personas.py
│   └── setup/                        # Setup scripts
│       ├── setup_backend.sh
│       ├── start_backend_5001.sh
│       ├── start_frontend_5000.sh
│       └── start_termcraft.sh
├── config/                           # Configuration
│   ├── package.json
│   └── package-lock.json
├── supabase/migrations/              # Database migrations
└── README.md                         # This file
```

---

## 🔧 **Development**

### **Backend Development**
```bash
cd backend
source venv/bin/activate
uvicorn api.main:app --reload --port 8000
```

### **Frontend Development**
   ```bash
cd frontend-cra-old
   npm start
   ```

### **Database Development**
   ```bash
# Apply new migration
# 1. Create SQL file in supabase/migrations/
# 2. Run in Supabase SQL Editor
# 3. Test with python test_schema.py
```

---

## 📚 **Documentation**

### **Status & Progress**
- **[docs/status/PROJECT_STATUS.md](docs/status/PROJECT_STATUS.md)** - Current implementation status

### **Guides & Tutorials**
- **[docs/guides/QUICK_START.md](docs/guides/QUICK_START.md)** - Getting started guide
- **[docs/guides/IMPLEMENTATION_GUIDE.md](docs/guides/IMPLEMENTATION_GUIDE.md)** - Detailed implementation guide
- **[docs/guides/PERSONA_DETAILS.md](docs/guides/PERSONA_DETAILS.md)** - Persona information for testing
- **[docs/guides/APPLY_DEV_POLICIES.md](docs/guides/APPLY_DEV_POLICIES.md)** - Development policies

### **Architecture**
- **[docs/architecture/ARCHITECTURE_DIAGRAM.md](docs/architecture/ARCHITECTURE_DIAGRAM.md)** - System architecture

---

## 🎯 **Next Steps**

### **Immediate (Next 1-2 days)**
1. Apply database migrations
2. Test complete negotiation flow
3. Fix authentication integration

### **Short Term (Next 1 week)**
4. Build persona creation UI
5. Integrate with main app
6. Implement RAG functionality

### **Medium Term (Next 2-4 weeks)**
7. Add document export
8. Implement advanced features
9. Add comprehensive testing

---

## 🤝 **Contributing**

### **Development Guidelines**
1. Follow TypeScript/Python type hints
2. Use existing component patterns
3. Test all API endpoints
4. Update documentation

### **Code Style**
- **Backend**: Black formatting, type hints
- **Frontend**: ESLint, Prettier
- **Database**: Consistent naming conventions

---

## 📄 **License**

This project is proprietary software. All rights reserved.

---

**Built with ❤️ for the legal technology community**

**Status**: Phase 2 & 2.5 Complete - Ready for Phase 3  
**Last Updated**: December 2024