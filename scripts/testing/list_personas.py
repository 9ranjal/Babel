#!/usr/bin/env python3
import requests
import json

response = requests.get("http://localhost:8000/api/personas/")
data = response.json()

print(f"\n{'='*60}")
print(f"PERSONA LIBRARY - Total: {len(data)} personas")
print(f"{'='*60}\n")

for p in data:
    icon = "🏢" if p["kind"] == "company" else "💰"
    print(f'{icon} {p["kind"].upper()}: {p["id"][:8]}...')
    print(f'   Leverage Score: {p["leverage_score"]:.2f}')
    
    if p['kind'] == 'company':
        attrs = p['attrs']
        print(f'   Stage: {attrs.get("stage", "N/A")}')
        print(f'   Revenue: ${attrs.get("revenue_run_rate", 0):,}')
        print(f'   Team: {attrs.get("team_size", "N/A")} people')
    else:
        attrs = p['attrs']
        print(f'   Fund Size: ${attrs.get("fund_size", 0):,}')
        print(f'   Check Size: ${attrs.get("typical_check", 0):,}')
        print(f'   Focus: {attrs.get("stage_focus", "general")}')
        print(f'   Type: {attrs.get("investor_type", attrs.get("tier", "N/A"))}')
    
    # Show key preferences
    if p.get('batna'):
        print(f'   Key Preferences:')
        batna = p['batna']
        if 'exclusivity' in batna:
            print(f'      - Exclusivity: {batna["exclusivity"]["period_days"]} days')
        if 'vesting' in batna:
            v = batna['vesting']
            print(f'      - Vesting: {v["vesting_months"]}mo / {v["cliff_months"]}mo cliff')
    print()

print(f"{'='*60}\n")

