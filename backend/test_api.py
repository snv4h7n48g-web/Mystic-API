#!/usr/bin/env python3
"""
Test script for Mystic API with Bedrock integration.
Tests the complete flow: session creation → preview → full reading.
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_health():
    """Test health endpoint."""
    print_section("1. Testing Health Endpoint")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    print("✓ Health check passed")
    return True

def test_create_session():
    """Test session creation."""
    print_section("2. Creating Session")
    payload = {
        "client_type": "ios",
        "locale": "en-AU",
        "timezone": "Australia/Melbourne",
        "style": "grounded"
    }
    print(f"Request: {json.dumps(payload, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/v1/sessions", json=payload)
    print(f"\nStatus: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    assert response.status_code == 200
    assert "session_id" in data
    print(f"✓ Session created: {data['session_id']}")
    return data["session_id"]

def test_update_session(session_id):
    """Test updating session with user inputs."""
    print_section("3. Updating Session with Birth Data")
    payload = {
        "birth_date": "1984-08-30",
        "birth_time": "09:06",
        "birth_time_unknown": False,
        "birth_location_text": "Melbourne, Australia",
        "question_intention": "Why do I keep feeling responsible for everyone?"
    }
    print(f"Request: {json.dumps(payload, indent=2)}")
    
    response = requests.patch(f"{BASE_URL}/v1/sessions/{session_id}", json=payload)
    print(f"\nStatus: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    print("✓ Session updated with birth data")
    return True

def test_generate_preview(session_id):
    """Test preview generation with Bedrock."""
    print_section("4. Generating Preview (Bedrock Nova Lite)")
    print("⏳ Calling Bedrock API... (this may take 5-10 seconds)")
    
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/v1/sessions/{session_id}/preview")
    elapsed = time.time() - start_time
    
    print(f"\nStatus: {response.status_code}")
    print(f"Time: {elapsed:.2f}s")
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return False
    
    data = response.json()
    
    # Print preview structure
    print(f"\n📊 Preview Structure:")
    preview = data.get("preview", {})
    
    print(f"\nAstrology Facts:")
    astro = preview.get("astrology_facts", {})
    print(f"  Sun Sign: {astro.get('sun_sign')}")
    print(f"  Moon Sign: {astro.get('moon_sign')}")
    print(f"  Rising Sign: {astro.get('rising_sign')}")
    print(f"  Dominant Element: {astro.get('dominant_element')}")
    print(f"  Dominant Planet: {astro.get('dominant_planet')}")
    
    print(f"\nTarot Cards:")
    tarot = preview.get("tarot", {})
    for card in tarot.get("cards", []):
        print(f"  {card['position']}: {card['card']}")
    
    print(f"\n🔮 Generated Teaser:")
    print(f'  "{preview.get("teaser_text")}"')
    
    print(f"\n💰 LLM Metadata:")
    meta = preview.get("llm_metadata", {})
    print(f"  Model: {meta.get('model')}")
    print(f"  Input Tokens: {meta.get('input_tokens')}")
    print(f"  Output Tokens: {meta.get('output_tokens')}")
    
    assert response.status_code == 200
    assert "preview" in data
    print("\n✓ Preview generated successfully")
    return True

def test_generate_reading(session_id):
    """Test full reading generation with Bedrock."""
    print_section("5. Generating Full Reading (Bedrock Nova Pro)")
    print("⏳ Calling Bedrock API... (this may take 10-15 seconds)")
    
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/v1/sessions/{session_id}/reading")
    elapsed = time.time() - start_time
    
    print(f"\nStatus: {response.status_code}")
    print(f"Time: {elapsed:.2f}s")
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return False
    
    data = response.json()
    reading = data.get("reading", {})
    
    # Print sections
    print(f"\n📖 Reading Sections:")
    sections = reading.get("sections", [])
    for section in sections:
        section_id = section.get("id", "unknown")
        text = section.get("text", "")
        print(f"\n--- {section_id.upper().replace('_', ' ')} ---")
        # Print first 200 chars of each section
        preview_text = text[:200] + "..." if len(text) > 200 else text
        print(f"{preview_text}\n")
    
    # Print metadata
    print(f"💰 LLM Metadata:")
    meta = reading.get("metadata", {})
    print(f"  Model: {meta.get('model')}")
    print(f"  Input Tokens: {meta.get('input_tokens')}")
    print(f"  Output Tokens: {meta.get('output_tokens')}")
    print(f"  Themes: {', '.join(meta.get('dominant_themes', []))}")
    print(f"  Tone: {meta.get('tone')}")
    
    assert response.status_code == 200
    assert "reading" in data
    print("\n✓ Full reading generated successfully")
    return True

def test_get_costs(session_id):
    """Test cost analytics endpoint."""
    print_section("6. Checking Cost Analytics")
    
    response = requests.get(f"{BASE_URL}/v1/sessions/{session_id}/cost")
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return False
    
    data = response.json()
    print(f"\n💵 Cost Breakdown:")
    print(f"  Preview Cost:  ${data.get('preview_cost_usd', 0):.6f}")
    print(f"  Reading Cost:  ${data.get('reading_cost_usd', 0):.6f}")
    print(f"  Total Cost:    ${data.get('total_cost_usd', 0):.6f}")
    
    # Calculate margin
    revenue = 1.39  # After Apple's 30% cut
    total_cost = data.get('total_cost_usd', 0)
    margin = revenue - total_cost
    margin_pct = (margin / revenue) * 100 if revenue > 0 else 0
    
    print(f"\n📊 Unit Economics:")
    print(f"  Net Revenue:   ${revenue:.2f}")
    print(f"  Total Cost:    ${total_cost:.6f}")
    print(f"  Gross Margin:  ${margin:.2f} ({margin_pct:.1f}%)")
    
    assert response.status_code == 200
    print("\n✓ Cost analytics retrieved")
    return True

def main():
    """Run complete test suite."""
    print("\n" + "="*60)
    print("  MYSTIC API - BEDROCK INTEGRATION TEST")
    print("="*60)
    
    try:
        # Run tests
        test_health()
        session_id = test_create_session()
        test_update_session(session_id)
        test_generate_preview(session_id)
        test_generate_reading(session_id)
        test_get_costs(session_id)
        
        # Success
        print_section("✅ ALL TESTS PASSED")
        print(f"Session ID: {session_id}")
        print("\nYou can view the complete session at:")
        print(f"{BASE_URL}/v1/sessions/{session_id}")
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        return 1
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API")
        print("Make sure the server is running: uvicorn main:app --reload")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
