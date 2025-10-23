# 📋 Persona Details - Complete Breakdown

## Overview
You have **3 personas** created and ready for negotiation testing.

---

## 🏢 **PERSONA 1: Seed-Stage SaaS Company**

### **ID:** `38d28f41-9009-4005-9949-c7b3a6d94f24`

### **Basic Info:**
- **Type:** Company
- **Leverage Score:** 0.65 (Strong position)
- **Created:** 2025-10-22

### **Attributes:**
```json
{
  "stage": "seed",
  "team_size": 8,
  "revenue_run_rate": 500000
}
```

**Interpretation:**
- Early-stage SaaS company
- $500K annual revenue (decent traction for seed)
- Small but capable team of 8 people
- Strong leverage due to revenue traction

### **Clause Weights** (What matters most):
```json
{
  "exclusivity": 0.8,    // Very important - wants flexibility
  "vesting": 0.5         // Moderately important
}
```

**Interpretation:**
- **Exclusivity is crucial** (0.8/1.0) - company wants to keep options open
- Vesting is less critical since founders are committed

### **BATNA** (Ideal outcome for each clause):
```json
{
  "exclusivity": {
    "period_days": 30    // Wants only 30 days
  },
  "vesting": {
    "vesting_months": 36,  // Prefers 3 years
    "cliff_months": 0      // NO cliff preferred
  }
}
```

**Interpretation:**
- Wants **short exclusivity** (30 days) to talk to other investors
- Prefers **shorter vesting** (3 years vs standard 4)
- Wants **no cliff** - immediate vesting starts

### **Negotiation Strategy:**
With 0.65 leverage, this company will push hard for:
- Shorter exclusivity periods
- Less restrictive vesting terms
- More founder-friendly terms overall

---

## 💰 **PERSONA 2: Tier-1 Venture Capital Fund**

### **ID:** `3bce16e5-874a-4d92-a622-89edc11419c5`

### **Basic Info:**
- **Type:** Investor
- **Leverage Score:** 0.45 (Moderate position)
- **Created:** 2025-10-22

### **Attributes:**
```json
{
  "tier": "tier-1",
  "fund_size": 200000000,        // $200M fund
  "typical_check": 2000000,      // $2M checks
  "market_competitive": true     // Hot market = lower leverage
}
```

**Interpretation:**
- Top-tier VC brand (Sequoia/Accel caliber)
- Large fund ($200M)
- Writes $2M checks (Series A/B range)
- Lower leverage (0.45) because market is competitive - companies have options

### **Clause Weights** (What matters most):
```json
{
  "exclusivity": 0.9,    // Critical - needs time for diligence
  "vesting": 0.8         // Very important - wants founder commitment
}
```

**Interpretation:**
- **Exclusivity is critical** (0.9/1.0) - needs time for thorough diligence
- **Vesting very important** (0.8/1.0) - wants founders locked in

### **BATNA** (Ideal outcome):
```json
{
  "exclusivity": {
    "period_days": 60      // Wants 60 days for due diligence
  },
  "vesting": {
    "vesting_months": 48,  // Standard 4 years
    "cliff_months": 12     // 1-year cliff (industry standard)
  }
}
```

**Interpretation:**
- Wants **longer exclusivity** (60 days) for thorough due diligence
- Prefers **standard 4-year vesting**
- Wants **1-year cliff** to ensure founder commitment

### **Negotiation Strategy:**
Despite being Tier-1, moderate leverage (0.45) means:
- Will compromise on exclusivity (won't get full 60 days)
- Will fight hard for vesting terms
- Brand helps, but competitive market limits power

---

## 💰 **PERSONA 3: Seed-Focused VC Fund**

### **ID:** `09a52009-ad00-4a8a-9e5f-e98a309379b3`

### **Basic Info:**
- **Type:** Investor
- **Leverage Score:** 0.35 (Weaker position)
- **Created:** 2025-10-22

### **Attributes:**
```json
{
  "stage_focus": "seed",
  "fund_size": 50000000,         // $50M fund
  "typical_check": 500000,       // $500K checks
  "portfolio_count": 40,
  "tier": "tier-2",
  "market_competitive": true,
  "investor_type": "seed_vc"
}
```

**Interpretation:**
- Focused on seed-stage deals
- Smaller fund ($50M vs $200M)
- Writes $500K checks (typical seed size)
- Active portfolio (40 companies)
- Tier-2 brand (less prestigious)
- Low leverage (0.35) - must compete hard for deals

### **Clause Weights** (What matters most):
```json
{
  "vesting": 0.9,               // Critical - wants commitment
  "exclusivity": 0.7,            // Important but flexible
  "liquidation_preference": 0.6, // Wants downside protection
  "preemption_rights": 0.5       // Moderate importance
}
```

**Interpretation:**
- **Vesting is critical** (0.9/1.0) - biggest concern for seed investor
- Exclusivity important but more flexible than Tier-1
- Wants downside protection (liquidation preference)
- Cares about pro-rata rights

### **BATNA** (Ideal outcome):
```json
{
  "exclusivity": {
    "period_days": 45        // Middle ground
  },
  "vesting": {
    "vesting_months": 48,    // Standard 4 years
    "cliff_months": 12       // 1-year cliff
  },
  "liquidation_preference": {
    "multiple": 1.0,         // Standard 1x
    "participating": false   // Non-participating (fair)
  },
  "preemption_rights": {
    "enabled": true,
    "threshold_ownership_pct": 3  // Lower threshold (3% vs 5%)
  }
}
```

**Interpretation:**
- Wants **45 days exclusivity** (compromise between 30-60)
- Standard **4-year vesting with cliff**
- Fair terms: **1x non-participating** liquidation preference
- Wants **pro-rata rights** at lower threshold (3%)

### **Negotiation Strategy:**
With lowest leverage (0.35), this investor:
- Will make most concessions
- Might accept shorter exclusivity
- Will fight hardest on vesting (their #1 priority)
- May offer sweeter terms to compete

---

## 📊 **Comparison Matrix**

| Attribute | Company | Tier-1 VC | Seed VC |
|-----------|---------|-----------|---------|
| **Leverage** | 0.65 | 0.45 | 0.35 |
| **Position** | Strongest | Moderate | Weakest |
| **Exclusivity Want** | 30 days | 60 days | 45 days |
| **Vesting Want** | 36mo/0cliff | 48mo/12cliff | 48mo/12cliff |
| **Top Priority** | Exclusivity (0.8) | Exclusivity (0.9) | Vesting (0.9) |

---

## 🎯 **Predicted Negotiation Outcomes**

### **Company vs Tier-1 VC:**
```
Company Leverage: 0.65 (60%)
Investor Leverage: 0.45 (40%)

Expected Compromise:
- Exclusivity: ~42 days (closer to company's 30)
- Vesting: ~40 months, ~5 month cliff
- Company utility: ~85/100 (favorable)
- Investor utility: ~75/100 (acceptable)
```

### **Company vs Seed VC:**
```
Company Leverage: 0.65 (65%)
Investor Leverage: 0.35 (35%)

Expected Compromise:
- Exclusivity: ~35 days (very close to company's ask)
- Vesting: ~39 months, ~4 month cliff
- Company utility: ~90/100 (very favorable)
- Investor utility: ~70/100 (must accept to compete)
```

---

## 🔄 **Usage Examples**

### **Test Negotiation: Company vs Tier-1 VC**
```bash
# Create session
curl -X POST http://localhost:8000/api/negotiate/session \
  -H "Content-Type: application/json" \
  -d '{
    "company_persona": "38d28f41-9009-4005-9949-c7b3a6d94f24",
    "investor_persona": "3bce16e5-874a-4d92-a622-89edc11419c5",
    "regime": "IN",
    "status": "negotiating"
  }'

# Save the session_id from response, then run negotiation round
curl -X POST http://localhost:8000/api/negotiate/round \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID"
  }'
```

### **Test Negotiation: Company vs Seed VC**
```bash
curl -X POST http://localhost:8000/api/negotiate/session \
  -H "Content-Type: application/json" \
  -d '{
    "company_persona": "38d28f41-9009-4005-9949-c7b3a6d94f24",
    "investor_persona": "09a52009-ad00-4a8a-9e5f-e98a309379b3",
    "regime": "IN"
  }'
```

---

## 💡 **Key Insights**

### **Leverage Dynamics:**
- **Company (0.65)** has strongest position due to revenue traction
- **Tier-1 VC (0.45)** has moderate power - brand helps but market is competitive
- **Seed VC (0.35)** has weakest position - must compete aggressively

### **Priority Differences:**
- **Company** cares most about **flexibility** (short exclusivity)
- **Tier-1 VC** cares most about **due diligence time** (long exclusivity)
- **Seed VC** cares most about **founder commitment** (vesting)

### **Negotiation Sweet Spots:**
- **Exclusivity**: Will land between 30-60 days based on leverage
- **Vesting**: Will land between 36-48 months based on leverage
- **Cliff**: Will be partial (0-12 months) based on leverage

---

## 📝 **Notes**

- All personas use test user: `00000000-0000-0000-0000-000000000000`
- Regime: India (IN) - uses Indian market benchmarks
- Created: October 22, 2025
- Status: Ready for negotiation testing

---

## 🚀 **Next Steps**

1. ✅ Personas created and configured
2. ⏳ Create a negotiation session
3. ⏳ Run negotiation rounds
4. ⏳ Analyze results and utilities
5. ⏳ Iterate on persona parameters

