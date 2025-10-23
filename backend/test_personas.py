"""
Test script for Persona API endpoints

Run this after starting the backend server to test persona creation and management.

Usage:
    python test_personas.py
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_create_company_persona():
    """Test creating a company persona"""
    print("\n=== Testing: Create Company Persona ===")
    
    payload = {
        "kind": "company",
        "attrs": {
            "stage": "seed",
            "sector": "SaaS",
            "revenue_run_rate": 500000,
            "team_size": 8,
            "competing_offers": 2
        },
        "leverage_score": 0.65,
        "weights": {
            "exclusivity": 0.8,
            "vesting": 0.5,
            "preemption_rights": 0.3,
            "liquidation_preference": 0.7
        },
        "batna": {
            "exclusivity": {"period_days": 30},
            "vesting": {"vesting_months": 36, "cliff_months": 0},
            "liquidation_preference": {"multiple": 1.0, "participating": False}
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/personas/", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Created company persona: {data['id']}")
        print(f"   Leverage: {data['leverage_score']}")
        return data['id']
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return None


def test_create_investor_persona():
    """Test creating an investor persona"""
    print("\n=== Testing: Create Investor Persona ===")
    
    payload = {
        "kind": "investor",
        "attrs": {
            "fund_size": 200000000,
            "typical_check": 2000000,
            "portfolio_count": 25,
            "tier": "tier-1",
            "market_competitive": True
        },
        "leverage_score": 0.45,
        "weights": {
            "exclusivity": 0.9,
            "vesting": 0.8,
            "preemption_rights": 0.6,
            "liquidation_preference": 0.9
        },
        "batna": {
            "exclusivity": {"period_days": 60},
            "vesting": {"vesting_months": 48, "cliff_months": 12},
            "liquidation_preference": {"multiple": 1.0, "participating": True}
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/personas/", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Created investor persona: {data['id']}")
        print(f"   Leverage: {data['leverage_score']}")
        return data['id']
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return None


def test_calculate_leverage():
    """Test the leverage calculation helper"""
    print("\n=== Testing: Calculate Leverage ===")
    
    # Test company leverage
    payload = {
        "kind": "company",
        "attrs": {
            "revenue_run_rate": 2000000,
            "competing_offers": 3,
            "team_size": 15
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/personas/calculate-leverage", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Company leverage: {data['leverage_score']:.2f}")
        print(f"   Explanation: {data['explanation']}")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")


def test_list_personas():
    """Test listing all personas"""
    print("\n=== Testing: List All Personas ===")
    
    response = requests.get(f"{BASE_URL}/api/personas/")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {len(data)} personas")
        for persona in data:
            print(f"   - {persona['kind']}: {persona['id']} (leverage: {persona['leverage_score']})")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")


def test_filter_personas():
    """Test filtering personas by kind"""
    print("\n=== Testing: Filter Personas by Kind ===")
    
    for kind in ["company", "investor"]:
        response = requests.get(f"{BASE_URL}/api/personas/?kind={kind}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data)} {kind} personas")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")


def test_get_persona(persona_id):
    """Test getting a specific persona"""
    print(f"\n=== Testing: Get Persona {persona_id} ===")
    
    response = requests.get(f"{BASE_URL}/api/personas/{persona_id}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Retrieved persona:")
        print(f"   Kind: {data['kind']}")
        print(f"   Leverage: {data['leverage_score']}")
        print(f"   Attrs: {json.dumps(data['attrs'], indent=2)}")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")


def test_update_persona(persona_id):
    """Test updating a persona"""
    print(f"\n=== Testing: Update Persona {persona_id} ===")
    
    payload = {
        "kind": "company",
        "attrs": {
            "stage": "seed",
            "sector": "SaaS",
            "revenue_run_rate": 750000,  # Updated!
            "team_size": 12  # Updated!
        },
        "leverage_score": 0.70,  # Increased!
        "weights": {
            "exclusivity": 0.9,  # Increased priority
            "vesting": 0.5
        },
        "batna": {
            "exclusivity": {"period_days": 25}  # More aggressive
        }
    }
    
    response = requests.put(f"{BASE_URL}/api/personas/{persona_id}", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Updated persona")
        print(f"   New leverage: {data['leverage_score']}")
        print(f"   New revenue: {data['attrs']['revenue_run_rate']}")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")


def main():
    """Run all tests"""
    print("=" * 60)
    print("PERSONA API TEST SUITE")
    print("=" * 60)
    
    try:
        # Test leverage calculation
        test_calculate_leverage()
        
        # Create personas
        company_id = test_create_company_persona()
        investor_id = test_create_investor_persona()
        
        # List personas
        test_list_personas()
        test_filter_personas()
        
        # Get specific persona
        if company_id:
            test_get_persona(company_id)
            test_update_persona(company_id)
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 60)
        
        if company_id and investor_id:
            print("\n📝 Ready for negotiation!")
            print(f"   Company ID: {company_id}")
            print(f"   Investor ID: {investor_id}")
            print(f"\n   Next: Create a negotiation session:")
            print(f"   POST /api/negotiate/session")
            print(f"   {{")
            print(f"     \"company_persona\": \"{company_id}\",")
            print(f"     \"investor_persona\": \"{investor_id}\",")
            print(f"     \"regime\": \"IN\"")
            print(f"   }}")
    
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to backend server")
        print("   Make sure the server is running on http://localhost:8000")
        print("   Run: cd backend && python server.py")


if __name__ == "__main__":
    main()

