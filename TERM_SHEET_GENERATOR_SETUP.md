# Term Sheet Generator - Setup & Usage

## Dependencies

### Backend Dependencies

The following dependency needs to be installed in the backend:

```bash
cd backend
pip install langgraph>=0.2.0
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

**Note:** `langgraph>=0.2.0` has already been added to `backend/requirements.txt`.

### Frontend Dependencies

The frontend uses existing dependencies:
- `react-markdown` (already in use for MarkdownRenderer)
- `lucide-react` (for icons)
- Standard React hooks

No additional frontend dependencies are required.

## Backend Implementation

### Files Created

1. **`backend/api/models/deal_schemas.py`** - Pydantic models for deal configuration
2. **`backend/api/services/ts_generator/`** - Term sheet generator module:
   - `__init__.py` - Module exports
   - `templates.py` - Clause template definitions
   - `clause_selector.py` - Template selection logic
   - `renderer.py` - Markdown rendering
   - `graph.py` - LangGraph workflow
3. **`backend/api/routes/ts_generator.py`** - API endpoint
4. **`backend/tests/test_ts_generator.py`** - Test suite

### API Endpoint

**POST** `/api/ts-generator/generate`

**Request:**
```json
{
  "nl_input": "5M at 25 premoney, 1 board seat"
}
```

**Response:**
```json
{
  "term_sheet": "# Term Sheet\n\n...",
  "deal_config": {
    "investment_amount": 5000000,
    "pre_money_valuation": 25000000,
    ...
  },
  "validation_errors": [],
  "clarification_questions": null
}
```

## Frontend Implementation

### Files Created

1. **`frontend/src/lib/api.ts`** - Added `generateTermSheet()` function
2. **`frontend/src/components/TermSheetGenerator.tsx`** - Main UI component
3. **`frontend/src/pages/TermSheet.tsx`** - Page component
4. **`frontend/src/App.tsx`** - Added route for `/term-sheet`

### Usage

1. **Navigate to the term sheet generator:**
   - Visit `/term-sheet` in your browser
   - Or import and use `<TermSheetGenerator />` component

2. **Generate a term sheet:**
   - Enter natural language description (e.g., "5M at 25 premoney, 1 board seat")
   - Click "Generate Term Sheet"
   - View the generated Markdown term sheet
   - Copy to clipboard if needed

3. **Example inputs:**
   - `"5M at 25 premoney, 1 board seat"`
   - `"2M SAFE at 8 cap, no discount, 1 board observer"`
   - `"10M Series A at 50 premoney, 2 board seats, 20% option pool pre-money"`

## How It Works

### Backend Flow (LangGraph)

1. **INPUT_NODE** - Receives natural language input
2. **PARSE_NL_NODE** - Uses LLM (OpenRouter) to extract structured deal terms
3. **APPLY_DEFAULTS_NODE** - Merges user input with market-standard defaults
4. **VALIDATE_DEAL_NODE** - Validates deal configuration
5. **SELECT_TS_CLAUSES_NODE** - Selects appropriate clause templates
6. **RENDER_TS_NODE** - Renders templates with deal values into Markdown
7. **OUTPUT_NODE** - Returns generated term sheet

### Frontend Flow

1. User enters natural language input
2. Frontend calls `generateTermSheet()` API function
3. API sends request to `/api/ts-generator/generate`
4. Backend processes through LangGraph workflow
5. Response contains:
   - Generated Markdown term sheet
   - Structured deal configuration
   - Validation errors (if any)
   - Clarification questions (if any)
6. Frontend displays:
   - Rendered term sheet (using MarkdownRenderer)
   - Validation warnings (if any)
   - Deal config summary (collapsible)

## Testing

Run backend tests:
```bash
cd backend
pytest tests/test_ts_generator.py -v
```

## Notes

- The LLM parsing requires `OPENROUTER_API_KEY` to be set in backend environment
- If API key is missing, the system will still work but NL parsing may fail
- Market defaults are defined in `get_base_deal_config()` function
- Clause templates can be extended in `backend/api/services/ts_generator/templates.py`

