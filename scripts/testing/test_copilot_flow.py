#!/usr/bin/env python3
"""
Test the complete copilot intake flow
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_complete_intake_flow():
    """Test the complete intake flow"""
    print("🧪 Testing Copilot Intake Flow")
    print("=" * 50)
    
    # Step 1: Start founder intake
    print("\n1️⃣ Starting founder intake...")
    start_response = requests.post(f"{BASE_URL}/api/copilot/intake/start", json={
        "role": "founder",
        "stage": "seed",
        "region": "SG"
    })
    
    if start_response.status_code != 200:
        print(f"❌ Failed to start intake: {start_response.text}")
        return
    
    start_data = start_response.json()
    session_id = start_data.get("session_id")
    print(f"✅ Started intake with session: {session_id}")
    print(f"   Question: {start_data['question_text']}")
    
    # Step 2: Answer all questions
    questions = [
        ("construct", "Premoney"),
        ("round_size", 1000000),
        ("runway", 12),
        ("alt_offers", 2),
        ("repeat_founder", True),
        ("diligence_speed", "accelerated")
    ]
    
    for question_id, answer in questions:
        print(f"\n2️⃣ Answering {question_id}: {answer}")
        
        answer_response = requests.post(f"{BASE_URL}/api/copilot/intake/answer", json={
            "question_id": question_id,
            "answer": answer,
            "session_id": session_id
        })
        
        if answer_response.status_code != 200:
            print(f"❌ Failed to answer {question_id}: {answer_response.text}")
            return
        
        answer_data = answer_response.json()
        
        if answer_data.get("completed"):
            persona_id = answer_data.get("persona_id")
            print(f"✅ Intake completed! Persona ID: {persona_id}")
            break
        elif answer_data.get("next_question"):
            next_q = answer_data["next_question"]
            print(f"   Next: {next_q['question_text']}")
        else:
            print(f"   Response: {answer_data}")
    
    # Step 3: Test Draft 0 generation
    print(f"\n3️⃣ Testing Draft 0 generation...")
    
    # First, create an investor persona
    investor_response = requests.post(f"{BASE_URL}/api/personas/", json={
        "kind": "investor",
        "attrs": {
            "stage": "seed",
            "region": "SG",
            "ownership_target_pct": 15,
            "marquee": True,
            "diligence_speed": "standard"
        },
        "leverage_score": 0.6,
        "weights": {
            "exclusivity": 0.8,
            "vesting": 0.7,
            "pro_rata_rights": 0.6
        },
        "batna": {
            "exclusivity": {"period_days": 60},
            "vesting": {"vesting_months": 48, "cliff_months": 12},
            "pro_rata_rights": {"enabled": True, "threshold_ownership_pct": 2}
        }
    })
    
    if investor_response.status_code != 200:
        print(f"❌ Failed to create investor: {investor_response.text}")
        return
    
    investor_id = investor_response.json()["id"]
    print(f"✅ Created investor persona: {investor_id}")
    
    # Generate Draft 0
    draft_response = requests.post(f"{BASE_URL}/api/copilot/draft0", json={
        "company_persona_id": persona_id,
        "investor_persona_ids": [investor_id],
        "stage": "seed",
        "region": "SG",
        "clauses_enabled": ["exclusivity", "pro_rata_rights"]
    })
    
    if draft_response.status_code != 200:
        print(f"❌ Failed to generate Draft 0: {draft_response.text}")
        return
    
    draft_data = draft_response.json()
    print(f"✅ Draft 0 generated!")
    print(f"   Session ID: {draft_data['session_id']}")
    print(f"   Clauses: {len(draft_data['clauses'])}")
    print(f"   Company Utility: {draft_data['utilities'].get('company', 0):.1%}")
    print(f"   Investor Utility: {draft_data['utilities'].get('investor', 0):.1%}")
    print(f"   Anchor: {draft_data.get('anchor_investor', 'Unknown')}")
    
    # Show clause details
    print(f"\n📋 Clause Details:")
    for clause in draft_data['clauses']:
        print(f"   {clause['title']}: {clause['current_value']}")
        if clause['redlines']:
            print(f"     ⚠️  Issues: {', '.join(clause['redlines'])}")
    
    print(f"\n✅ Complete copilot flow tested successfully!")

if __name__ == "__main__":
    test_complete_intake_flow()
