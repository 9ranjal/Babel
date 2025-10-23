# Quick Start Guide - Termcraft AI Negotiation Engine

## Prerequisites

1. **Database Migrations Applied**
   - Run migrations 003, 004, 005, 006 in Supabase SQL editor
   - Verify tables exist: `clause_guidance`, `embedded_snippets`

2. **Environment Variables**
   ```bash
   # Backend (.env in backend/)
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_service_role_key
   OPENROUTER_API_KEY=your_openrouter_key
   FRONTEND_ORIGIN=http://localhost:5173
   
   # Frontend (.env in frontend/)
   VITE_API_BASE=http://localhost:8000
   VITE_SUPABASE_URL=your_supabase_url
   VITE_SUPABASE_ANON_KEY=your_anon_key
   ```

## Step 1: Start Backend

```bash
cd backend
source venv/bin/activate
uvicorn api.main:app --reload --port 8000
```

**Verify it's running:**
```bash
curl http://localhost:8000/status
# Should return: {"status": "healthy"}
```

## Step 2: Start Frontend

```bash
cd frontend
npm install
npm run dev
```

**Access at:** http://localhost:5173

## Step 3: Create Test Personas

### Option A: Via Supabase UI

1. Go to Supabase Dashboard → Table Editor → `personas`
2. Insert two rows:

**Company Persona:**
```json
{
  "kind": "company",
  "attrs": {
    "stage": "seed",
    "region": "IN",
    "name": "TestCo",
    "runway_months": 12
  },
  "leverage_score": 0.4,
  "weights": {
    "exclusivity": 1.0,
    "preemption_rights": 0.8,
    "vesting": 0.6
  },
  "batna": {
    "exclusivity": {"period_days": 30},
    "preemption_rights": {"enabled": true, "expiry_next_round_only": true}
  }
}
```

**Investor Persona:**
```json
{
  "kind": "investor",
  "attrs": {
    "stage": "seed",
    "region": "IN",
    "name": "TestVC",
    "fund_size_m": 50
  },
  "leverage_score": 0.6,
  "weights": {
    "exclusivity": 1.0,
    "preemption_rights": 1.0,
    "vesting": 0.8
  },
  "batna": {
    "exclusivity": {"period_days": 60},
    "preemption_rights": {"enabled": true, "expiry_next_round_only": false}
  }
}
```

3. Copy the generated UUIDs

### Option B: Via API

```bash
# Create company persona
curl -X POST http://localhost:8000/api/personas \
  -H "Content-Type: application/json" \
  -d '{
    "kind": "company",
    "attrs": {"stage": "seed", "region": "IN"},
    "leverage_score": 0.4
  }'

# Create investor persona
curl -X POST http://localhost:8000/api/personas \
  -H "Content-Type: application/json" \
  -d '{
    "kind": "investor",
    "attrs": {"stage": "seed", "region": "IN"},
    "leverage_score": 0.6
  }'
```

## Step 4: Run First Negotiation

### Via Demo UI

1. Navigate to http://localhost:5173/demo (or wherever you mount `NegotiationDemo`)
2. Paste persona UUIDs
3. Click "Create Session"
4. Click "Run Negotiation Round"
5. View results!

### Via API (curl)

```bash
# 1. Create session
SESSION_ID=$(curl -X POST http://localhost:8000/api/negotiate/session \
  -H "Content-Type: application/json" \
  -d '{
    "company_persona": "COMPANY_UUID_HERE",
    "investor_persona": "INVESTOR_UUID_HERE",
    "regime": "IN"
  }' | jq -r '.id')

echo "Session ID: $SESSION_ID"

# 2. Run negotiation round
curl -X POST http://localhost:8000/api/negotiate/round \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\"
  }" | jq .

# 3. Get terms
curl http://localhost:8000/api/negotiate/session/$SESSION_ID/terms | jq .
```

## Step 5: Verify Results

You should see:

### Terms Generated
```json
{
  "exclusivity": {"period_days": 45},
  "preemption_rights": {"enabled": true, "expiry_next_round_only": false},
  "vesting": {"vesting_months": 42, "cliff_months": 6}
}
```

### Utilities Calculated
```json
{
  "company": 65.3,
  "investor": 72.1
}
```

### Traces & Citations
- Company proposed 30 days exclusivity
- Investor proposed 60 days
- Final: 45 days (weighted by leverage)
- Citations from `embedded_snippets` table

## Integration Into Existing UI

### Add to your main router:

```typescript
// In your App.tsx or router config
import { NegotiationDemo } from './pages/NegotiationDemo';

<Route path="/negotiate" element={<NegotiationDemo />} />
```

### Or use components directly:

```typescript
import { useNegotiation } from './hooks/useNegotiation';
import { NegotiationPanel } from './components/NegotiationPanel';
import { TermsDisplay } from './components/TermsDisplay';

function YourPage() {
  const { runRound, currentRound, terms } = useNegotiation();
  
  return (
    <div>
      <button onClick={() => runRound(sessionId)}>
        Generate Terms
      </button>
      <TermsDisplay terms={terms} />
      <NegotiationPanel round={currentRound} />
    </div>
  );
}
```

## Troubleshooting

### Backend won't start
- Check `backend/requirements.txt` has all dependencies
- Verify `.env` has correct Supabase credentials
- Check port 8000 isn't already in use

### Frontend compilation errors
- Run `npm install` to ensure all deps are installed
- Check TypeScript version compatibility
- Verify `vite.config.ts` is properly configured

### No terms generated
- Verify migrations 003-006 are applied
- Check `clause_guidance` table has seed data
- Verify persona `attrs` include `stage` and match guidance stage
- Check backend logs for errors

### API 404 errors
- Ensure backend is running on correct port
- Check `VITE_API_BASE` in frontend `.env`
- Verify router is mounted in `backend/api/main.py`

### Database permission errors
- Check Supabase RLS policies are correct
- Use service role key in backend (not anon key)
- Verify user authentication is working

## Next Steps

1. **Add more skills** - Implement remaining clause types
2. **Populate embeddings** - Add vector search for better citations
3. **Integrate auth** - Replace dummy user_id with real auth
4. **Add UI polish** - Animations, better error handling
5. **Document generation** - Use final terms to create term sheets

## Support

For issues or questions:
- Check `IMPLEMENTATION_COMPLETE.md` for architecture details
- Review code comments in engine modules
- Check Supabase logs for database errors
- Review FastAPI logs for backend errors

Happy negotiating! 🚀

