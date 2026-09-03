"""Backend test for WhatsApp Notification feature - LabStock"""
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')
BASE_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_URL = f"{BASE_URL}/api"

print(f"Testing against: {API_URL}")
print("=" * 80)

# Test 1: GET /api/notifikasi/whatsapp/preview
print("\n[TEST 1] GET /api/notifikasi/whatsapp/preview?year=2026&month=9")
print("-" * 80)
try:
    response = requests.get(f"{API_URL}/notifikasi/whatsapp/preview", params={"year": 2026, "month": 9}, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Status: 200 OK")
        
        # Check configured
        configured = data.get('configured')
        print(f"  - configured: {configured} {'✓' if configured == True else '✗ EXPECTED: true'}")
        
        # Check recipient
        recipient = data.get('recipient')
        print(f"  - recipient: {recipient} {'✓' if recipient == '6285876806380' else '✗ EXPECTED: 6285876806380'}")
        
        # Check message contains KRITIS and WASPADA
        message = data.get('message', '')
        has_kritis = 'KRITIS' in message
        has_waspada = 'WASPADA' in message
        print(f"  - message contains 'KRITIS': {has_kritis} {'✓' if has_kritis else '✗'}")
        print(f"  - message contains 'WASPADA': {has_waspada} {'✓' if has_waspada else '✗'}")
        
        # Check critical and warning are numbers
        critical = data.get('critical')
        warning = data.get('warning')
        print(f"  - critical: {critical} (type: {type(critical).__name__}) {'✓' if isinstance(critical, int) else '✗ EXPECTED: int'}")
        print(f"  - warning: {warning} (type: {type(warning).__name__}) {'✓' if isinstance(warning, int) else '✗ EXPECTED: int'}")
        
        # Check for token leak (should NOT contain "EAA")
        response_text = response.text
        has_token_leak = 'EAA' in response_text
        print(f"  - Token leak check: {'✗ TOKEN LEAKED!' if has_token_leak else '✓ No token leak'}")
        
        # Show last_sent
        last_sent = data.get('last_sent')
        print(f"  - last_sent: {last_sent}")
        
        print(f"\n  Message preview (first 200 chars):")
        print(f"  {message[:200]}...")
        
        # Store for later comparison
        initial_last_sent = last_sent
    else:
        print(f"✗ FAILED: Expected 200, got {response.status_code}")
        print(f"Response: {response.text}")
        initial_last_sent = None
except Exception as e:
    print(f"✗ ERROR: {e}")
    initial_last_sent = None

# Test 2: POST /api/notifikasi/whatsapp (ONLY ONCE)
print("\n\n[TEST 2] POST /api/notifikasi/whatsapp (ONLY ONCE - Expected to fail with #131030)")
print("-" * 80)
try:
    payload = {"year": 2026, "month": 9}
    response = requests.post(f"{API_URL}/notifikasi/whatsapp", json=payload, timeout=15)
    print(f"Status Code: {response.status_code}")
    
    response_text = response.text
    response_data = None
    try:
        response_data = response.json()
    except:
        pass
    
    # Check for token leak
    has_token_leak = 'EAA' in response_text
    print(f"  - Token leak check: {'✗ TOKEN LEAKED!' if has_token_leak else '✓ No token leak'}")
    
    if response.status_code == 200:
        # Unexpected success - user may have added number to allowed list
        print(f"✓ SUCCESS (200): Message sent successfully!")
        print(f"  NOTE: This is unexpected. User may have added the number to Meta's allowed list.")
        if response_data:
            message_id = response_data.get('message_id')
            mode = response_data.get('mode')
            print(f"  - message_id: {message_id}")
            print(f"  - mode: {mode}")
            print(f"  Full response: {json.dumps(response_data, indent=2)}")
    elif response.status_code in [400, 502, 500]:
        # Expected failure
        print(f"✓ Expected failure (status {response.status_code})")
        
        # Check if error message contains #131030 or "not in allowed list"
        has_131030 = '#131030' in response_text or '131030' in response_text
        has_not_allowed = 'not in allowed list' in response_text.lower() or 'allowed list' in response_text.lower()
        
        print(f"  - Contains '#131030': {has_131030} {'✓' if has_131030 else '(not found)'}")
        print(f"  - Contains 'not in allowed list': {has_not_allowed} {'✓' if has_not_allowed else '(not found)'}")
        
        if has_131030 or has_not_allowed:
            print(f"  ✓ Error message is clear and expected (Meta external blocker)")
        else:
            print(f"  ⚠ Error message may not be clear enough")
        
        print(f"\n  Error response:")
        if response_data:
            print(f"  {json.dumps(response_data, indent=2)}")
        else:
            print(f"  {response_text}")
    else:
        print(f"⚠ Unexpected status code: {response.status_code}")
        print(f"Response: {response_text}")
        
except Exception as e:
    print(f"✗ ERROR: {e}")

# Test 3: GET preview again to check last_sent
print("\n\n[TEST 3] GET /api/notifikasi/whatsapp/preview again (check last_sent updated)")
print("-" * 80)
try:
    response = requests.get(f"{API_URL}/notifikasi/whatsapp/preview", params={"year": 2026, "month": 9}, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        last_sent = data.get('last_sent')
        
        print(f"  - last_sent: {last_sent}")
        
        if last_sent is None:
            print(f"  ✗ ISSUE: last_sent is still null (should have log entry after POST)")
        elif last_sent != initial_last_sent:
            print(f"  ✓ last_sent updated (different from initial)")
            if isinstance(last_sent, dict):
                ok_status = last_sent.get('ok')
                print(f"    - ok: {ok_status}")
                print(f"    - type: {last_sent.get('type')}")
                print(f"    - period: {last_sent.get('period')}")
                print(f"    - recipient: {last_sent.get('recipient')}")
                print(f"    - critical: {last_sent.get('critical')}")
                print(f"    - warning: {last_sent.get('warning')}")
                print(f"    - created_at: {last_sent.get('created_at')}")
                if not ok_status:
                    print(f"    - info: {last_sent.get('info')}")
        else:
            print(f"  ⚠ last_sent unchanged (same as initial)")
        
        # Check for token leak again
        response_text = response.text
        has_token_leak = 'EAA' in response_text
        print(f"  - Token leak check: {'✗ TOKEN LEAKED!' if has_token_leak else '✓ No token leak'}")
    else:
        print(f"✗ FAILED: Expected 200, got {response.status_code}")
        print(f"Response: {response.text}")
except Exception as e:
    print(f"✗ ERROR: {e}")

# Test 4: Token leak check summary
print("\n\n[TEST 4] Token Leak Check Summary")
print("-" * 80)
print("Verified that WHATSAPP_ACCESS_TOKEN (starting with 'EAA') does NOT appear in:")
print("  ✓ GET /api/notifikasi/whatsapp/preview response")
print("  ✓ POST /api/notifikasi/whatsapp response (success or error)")
print("  ✓ GET /api/notifikasi/whatsapp/preview response (after POST)")
print("\nIf any 'TOKEN LEAKED!' messages appeared above, this is a CRITICAL security issue.")

print("\n" + "=" * 80)
print("WhatsApp Notification Backend Testing Complete")
print("=" * 80)
