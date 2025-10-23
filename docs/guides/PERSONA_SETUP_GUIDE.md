# 📋 Persona Setup Guide

## Overview

Personas are the foundation of Termcraft's negotiation system. Each persona represents either a **company** or **investor** with their unique:
- **Attributes**: Basic info (stage, revenue, fund size, etc.)
- **Leverage Score**: Negotiation strength (0.0 - 1.0)
- **Weights**: Which clauses matter most
- **BATNA**: Best Alternative To Negotiated Agreement (ideal values)

---

## 🎯 What Controls Persona Setup?

### **Backend Scripts:**

1. **`api/routes/personas.py`** ✨ *NEW*
   - CRUD endpoints for persona management
   - Leverage calculation helper
   
2. **`api/models/schemas.py`**
   - `PersonaCreate`: Input model
   - `PersonaResponse`: Output model

3. **Database: `personas` table**
   - Stores all persona data
   - See: `supabase/migrations/001_initial_schema.sql` (lines 55-75)

---

## 🔌 API Endpoints

### **1. Create a Persona**
```http
POST /api/personas/
Content-Type: application/json

{
  "kind": "company",
  "attrs": {
    "stage": "seed",
    "sector": "SaaS",
    "revenue_run_rate": 500000,
    "team_size": 8
  },
  "leverage_score": 0.6,
  "weights": {
    "exclusivity": 0.8,
    "vesting": 0.5
  },
  "batna": {
    "exclusivity": {"period_days": 30},
    "vesting": {"vesting_months": 36, "cliff_months": 0}
  }
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "owner_user": "00000000-0000-0000-0000-000000000000",
  "kind": "company",
  "attrs": {...},
  "leverage_score": 0.6,
  "weights": {...},
  "batna": {...},
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

### **2. List All Personas**
```http
GET /api/personas/
GET /api/personas/?kind=company  # Filter by type
```

---

### **3. Get Specific Persona**
```http
GET /api/personas/{persona_id}
```

---

### **4. Update Persona**
```http
PUT /api/personas/{persona_id}
Content-Type: application/json

{
  "kind": "company",
  "attrs": {...},
  "leverage_score": 0.7,  # Updated!
  ...
}
```

---

### **5. Delete Persona**
```http
DELETE /api/personas/{persona_id}
```

---

### **6. Calculate Leverage (Helper)**
```http
POST /api/personas/calculate-leverage
Content-Type: application/json

{
  "kind": "company",
  "attrs": {
    "revenue_run_rate": 2000000,
    "competing_offers": 3,
    "team_size": 15
  }
}
```

**Response:**
```json
{
  "leverage_score": 0.75,
  "explanation": "Strong position due to: strong revenue traction, 3 competing offers"
}
```

---

## 🏗️ Persona Structure Explained

### **Company Persona Example**

```json
{
  "kind": "company",
  
  // ===== ATTRS: Raw company details =====
  "attrs": {
    "stage": "seed",           // seed, series-a, series-b
    "sector": "SaaS",           // Industry
    "revenue_run_rate": 500000, // Annual revenue
    "team_size": 8,             // Number of employees
    "competing_offers": 2,      // Other term sheets?
    "market_competitive": true  // Hot market?
  },
  
  // ===== LEVERAGE: Negotiation strength =====
  "leverage_score": 0.65,  // 0.0 (weak) to 1.0 (strong)
  
  // ===== WEIGHTS: Clause priorities =====
  "weights": {
    "exclusivity": 0.8,          // Very important (0.0 - 1.0)
    "vesting": 0.5,              // Moderately important
    "preemption_rights": 0.3,    // Less important
    "liquidation_preference": 0.7
  },
  
  // ===== BATNA: Ideal values for each clause =====
  "batna": {
    "exclusivity": {
      "period_days": 30          // Company wants 30 days max
    },
    "vesting": {
      "vesting_months": 36,      // Prefer 3 years
      "cliff_months": 0          // No cliff ideally
    },
    "liquidation_preference": {
      "multiple": 1.0,           // Standard 1x
      "participating": false     // Non-participating
    }
  }
}
```

### **Investor Persona Example**

```json
{
  "kind": "investor",
  
  // ===== ATTRS: Fund/investor details =====
  "attrs": {
    "fund_size": 200000000,      // $200M fund
    "typical_check": 2000000,    // $2M average investment
    "portfolio_count": 25,       // 25 companies
    "tier": "tier-1",            // Brand quality
    "market_competitive": true   // Lots of other VCs?
  },
  
  // ===== LEVERAGE: Negotiation strength =====
  "leverage_score": 0.45,  // Lower if market is competitive
  
  // ===== WEIGHTS: What matters to this VC =====
  "weights": {
    "exclusivity": 0.9,          // Critical for due diligence
    "vesting": 0.8,              // Important for commitment
    "preemption_rights": 0.6,
    "liquidation_preference": 0.9
  },
  
  // ===== BATNA: Ideal values =====
  "batna": {
    "exclusivity": {
      "period_days": 60          // Investor wants 60 days
    },
    "vesting": {
      "vesting_months": 48,      // Standard 4 years
      "cliff_months": 12         // 1-year cliff
    },
    "liquidation_preference": {
      "multiple": 1.0,           // 1x preference
      "participating": true      // Prefer participating
    }
  }
}
```

---

## 🎯 How Personas Drive Negotiation

### **Step 1: Skills Use Persona Data**

```python
# backend/api/engine/skills/exclusivity_skill.py

def propose_company(context):
    # Company persona BATNA: wants 30 days
    company_batna = context.company_persona.batna["exclusivity"]
    # → Proposes {"period_days": 30}

def propose_investor(context):
    # Investor persona BATNA: wants 60 days
    investor_batna = context.investor_persona.batna["exclusivity"]
    # → Proposes {"period_days": 60}
```

### **Step 2: Solver Uses Leverage**

```python
# backend/api/engine/solver.py

company_leverage = 0.6  # From persona
investor_leverage = 0.4 # From persona

# Weighted compromise:
final_days = (0.6 * 30) + (0.4 * 60) = 42 days
```

### **Step 3: Utility Uses Weights & BATNA**

```python
# backend/api/engine/utility.py

# Company utility for exclusivity
weight = 0.8        # From persona.weights
batna = 30          # From persona.batna
actual = 42         # Final negotiated value

distance = |42 - 30| = 12
utility = 100 * (1 - distance/range) = 84.2
weighted = 84.2 * 0.8 = 67.4
```

---

## 🧪 Testing Personas

### **Quick Test**
```bash
# 1. Start backend
cd backend
source venv/bin/activate
python server.py

# 2. Run test script
python test_personas.py
```

### **Manual cURL Tests**

```bash
# Create company
curl -X POST http://localhost:8000/api/personas/ \
  -H "Content-Type: application/json" \
  -d '{
    "kind": "company",
    "attrs": {"stage": "seed", "revenue_run_rate": 500000},
    "leverage_score": 0.6,
    "weights": {"exclusivity": 0.8},
    "batna": {"exclusivity": {"period_days": 30}}
  }'

# List personas
curl http://localhost:8000/api/personas/

# Calculate leverage
curl -X POST http://localhost:8000/api/personas/calculate-leverage \
  -H "Content-Type: application/json" \
  -d '{
    "kind": "company",
    "attrs": {"revenue_run_rate": 2000000, "competing_offers": 3}
  }'
```

---

## 📊 Leverage Score Guide

### **Company Leverage Factors**

| Factor | Impact | Example |
|--------|--------|---------|
| Revenue > $5M | +0.20 | Strong traction |
| Revenue > $1M | +0.15 | Good traction |
| Revenue > $100K | +0.10 | Some traction |
| Competing offers | +0.10 | Multiple VCs interested |
| Team size > 10 | +0.05 | Mature team |

**Example:**
- Base: 0.50
- Revenue $2M: +0.15
- 3 competing offers: +0.10
- Team of 12: +0.05
- **Total: 0.80** (Strong leverage!)

### **Investor Leverage Factors**

| Factor | Impact | Example |
|--------|--------|---------|
| Fund > $500M | +0.15 | Mega fund |
| Fund > $100M | +0.10 | Large fund |
| Tier-1 brand | +0.10 | Top VC |
| Tier-2 brand | +0.05 | Good VC |
| Competitive market | -0.15 | Many VCs chasing deals |

**Example:**
- Base: 0.50
- Fund $200M: +0.10
- Tier-1: +0.10
- Competitive market: -0.15
- **Total: 0.55** (Moderate leverage)

---

## 🔄 Typical Workflow

```
1. Create Company Persona
   ↓
2. Create Investor Persona
   ↓
3. Create Negotiation Session
   POST /api/negotiate/session
   {
     "company_persona": "{company_id}",
     "investor_persona": "{investor_id}",
     "regime": "IN"
   }
   ↓
4. Run Negotiation Round
   POST /api/negotiate/round
   {
     "session_id": "{session_id}"
   }
   ↓
5. Review Results
   - See proposed terms
   - Check utilities
   - Adjust personas if needed
```

---

## 🎨 Frontend Integration

*Coming Soon: Frontend UI for persona creation*

The frontend should provide:
1. **Persona Builder Form**
   - Input attrs (revenue, stage, etc.)
   - Auto-calculate leverage
   - Set clause priorities (weights)
   - Define ideal values (BATNA)

2. **Persona Library**
   - List saved personas
   - Edit/clone personas
   - Delete personas

3. **Negotiation Setup**
   - Select company & investor personas
   - Preview leverage dynamics
   - Start negotiation

---

## ✅ Next Steps

- [ ] Test persona API endpoints
- [ ] Create sample personas for testing
- [ ] Build frontend persona creation UI
- [ ] Add persona templates (e.g., "Typical Seed Company")
- [ ] Implement persona sharing between users

---

## 🐛 Troubleshooting

**Error: "Failed to create persona"**
- Check if backend is running
- Verify Supabase connection
- Check database migrations ran successfully

**Error: "Persona not found"**
- Verify persona_id is correct UUID
- Check if persona belongs to current user (auth)

**Leverage score seems wrong?**
- Use `/calculate-leverage` endpoint to see explanation
- Adjust attrs to reflect actual company/investor strength
- Override auto-calculated leverage if needed

