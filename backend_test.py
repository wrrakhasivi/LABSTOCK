#!/usr/bin/env python3
"""
Backend test for LabStock mapping_test feature.
Tests POST /api/mapping-tests, PUT /api/mapping-tests/{id}, and seed_data.json persistence.
"""
import os
import sys
import json
import requests
from pymongo import MongoClient

# Configuration
BACKEND_URL = "https://stock-status-5.preview.emergentagent.com/api"
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "labstock"
SEED_FILE = "/app/backend/seed/seed_data.json"

# Test data prefix
TEST_PREFIX = "TEST_AGENT_"

def log(msg):
    print(f"[TEST] {msg}")

def load_seed_data():
    """Load seed_data.json"""
    with open(SEED_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_seed_data(data):
    """Save seed_data.json"""
    with open(SEED_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def cleanup_mongodb():
    """Clean up test data from MongoDB"""
    log("Cleaning up MongoDB test data...")
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Delete test mappings
    mapping_result = db.mapping_test.delete_many({"lis_name": {"$regex": f"^{TEST_PREFIX}", "$options": "i"}})
    log(f"  Deleted {mapping_result.deleted_count} mapping_test documents")
    
    # Find test reagents
    test_reagents = list(db.master_reagen.find({"nama_reagen": {"$regex": f"^{TEST_PREFIX}", "$options": "i"}}, {"_id": 0, "id": 1}))
    test_reagen_ids = [r["id"] for r in test_reagents]
    log(f"  Found {len(test_reagen_ids)} test reagents")
    
    # Delete stock_period entries for test reagents
    if test_reagen_ids:
        stock_result = db.stock_period.delete_many({"reagen_id": {"$in": test_reagen_ids}})
        log(f"  Deleted {stock_result.deleted_count} stock_period documents")
    
    # Delete test reagents
    reagen_result = db.master_reagen.delete_many({"nama_reagen": {"$regex": f"^{TEST_PREFIX}", "$options": "i"}})
    log(f"  Deleted {reagen_result.deleted_count} master_reagen documents")
    
    client.close()

def cleanup_seed_file():
    """Clean up test data from seed_data.json"""
    log("Cleaning up seed_data.json test data...")
    data = load_seed_data()
    
    # Clean Mapping_Test
    original_mapping_count = len(data.get("Mapping_Test", []))
    data["Mapping_Test"] = [m for m in data.get("Mapping_Test", []) 
                            if not (m.get("lis_name") or "").upper().startswith(TEST_PREFIX)]
    cleaned_mapping = original_mapping_count - len(data["Mapping_Test"])
    log(f"  Removed {cleaned_mapping} Mapping_Test entries")
    
    # Clean Master_Extra
    original_extra_count = len(data.get("Master_Extra", []))
    data["Master_Extra"] = [r for r in data.get("Master_Extra", []) 
                           if not (r.get("nama_reagen") or "").upper().startswith(TEST_PREFIX)]
    cleaned_extra = original_extra_count - len(data["Master_Extra"])
    log(f"  Removed {cleaned_extra} Master_Extra entries")
    
    save_seed_data(data)
    log("  seed_data.json saved successfully")

def verify_cleanup():
    """Verify cleanup was successful"""
    log("Verifying cleanup...")
    
    # Check API endpoints
    resp = requests.get(f"{BACKEND_URL}/mapping-tests")
    if resp.status_code == 200:
        items = resp.json().get("items", [])
        test_items = [i for i in items if (i.get("lis_name") or "").upper().startswith(TEST_PREFIX)]
        if test_items:
            log(f"  ❌ WARNING: Found {len(test_items)} test mappings still in API")
        else:
            log(f"  ✅ No test mappings in GET /api/mapping-tests")
    
    resp = requests.get(f"{BACKEND_URL}/reagen")
    if resp.status_code == 200:
        items = resp.json()
        test_items = [i for i in items if (i.get("nama_reagen") or "").upper().startswith(TEST_PREFIX)]
        if test_items:
            log(f"  ❌ WARNING: Found {len(test_items)} test reagents still in API")
        else:
            log(f"  ✅ No test reagents in GET /api/reagen")

def run_tests():
    """Run all test scenarios"""
    log("=" * 80)
    log("Starting LabStock Mapping Test Backend Tests")
    log("=" * 80)
    
    results = []
    test_mapping_id_1 = None
    
    # Test 1: POST new mapping with new reagent
    log("\n[TEST 1] POST /api/mapping-tests with new lis_name + new reagen_name")
    try:
        payload = {"lis_name": "TEST_AGENT_LIS_1", "reagen_name": "TEST_AGENT_REAGEN_1"}
        resp = requests.post(f"{BACKEND_URL}/mapping-tests", json=payload)
        log(f"  Status: {resp.status_code}")
        
        if resp.status_code == 201:
            data = resp.json()
            test_mapping_id_1 = data.get("id")
            log(f"  Response: {json.dumps(data, indent=2)}")
            
            # Verify response
            checks = []
            checks.append(("status == 'OK'", data.get("status") == "OK"))
            checks.append(("reagen_name == 'TEST_AGENT_REAGEN_1'", data.get("reagen_name") == "TEST_AGENT_REAGEN_1"))
            checks.append(("sync.action == 'created'", data.get("sync", {}).get("action") == "created"))
            
            # Verify in GET /api/reagen
            resp_reagen = requests.get(f"{BACKEND_URL}/reagen")
            if resp_reagen.status_code == 200:
                reagents = resp_reagen.json()
                found = any(r.get("nama_reagen") == "TEST_AGENT_REAGEN_1" for r in reagents)
                checks.append(("Reagen in GET /api/reagen", found))
            
            # Verify in GET /api/mapping-tests
            resp_mapping = requests.get(f"{BACKEND_URL}/mapping-tests")
            if resp_mapping.status_code == 200:
                mappings = resp_mapping.json().get("items", [])
                found = any(m.get("lis_name") == "TEST_AGENT_LIS_1" for m in mappings)
                checks.append(("Mapping in GET /api/mapping-tests", found))
            
            all_passed = all(c[1] for c in checks)
            for check_name, passed in checks:
                log(f"    {'✅' if passed else '❌'} {check_name}")
            
            results.append(("Test 1: POST new mapping + reagent", all_passed))
        else:
            log(f"  ❌ Expected 201, got {resp.status_code}: {resp.text}")
            results.append(("Test 1: POST new mapping + reagent", False))
    except Exception as e:
        log(f"  ❌ Exception: {e}")
        results.append(("Test 1: POST new mapping + reagent", False))
    
    # Test 2: POST duplicate lis_name (case-insensitive) -> 409
    log("\n[TEST 2] POST /api/mapping-tests with duplicate lis_name (different case)")
    try:
        payload = {"lis_name": "test_agent_lis_1"}  # lowercase
        resp = requests.post(f"{BACKEND_URL}/mapping-tests", json=payload)
        log(f"  Status: {resp.status_code}")
        
        if resp.status_code == 409:
            log(f"  ✅ Correctly rejected duplicate (409)")
            results.append(("Test 2: Duplicate lis_name -> 409", True))
        else:
            log(f"  ❌ Expected 409, got {resp.status_code}: {resp.text}")
            results.append(("Test 2: Duplicate lis_name -> 409", False))
    except Exception as e:
        log(f"  ❌ Exception: {e}")
        results.append(("Test 2: Duplicate lis_name -> 409", False))
    
    # Test 3: POST empty lis_name -> 400
    log("\n[TEST 3] POST /api/mapping-tests with empty lis_name")
    try:
        payload = {"lis_name": "   "}
        resp = requests.post(f"{BACKEND_URL}/mapping-tests", json=payload)
        log(f"  Status: {resp.status_code}")
        
        if resp.status_code == 400:
            log(f"  ✅ Correctly rejected empty lis_name (400)")
            results.append(("Test 3: Empty lis_name -> 400", True))
        else:
            log(f"  ❌ Expected 400, got {resp.status_code}: {resp.text}")
            results.append(("Test 3: Empty lis_name -> 400", False))
    except Exception as e:
        log(f"  ❌ Exception: {e}")
        results.append(("Test 3: Empty lis_name -> 400", False))
    
    # Test 4: POST without reagen_name -> status TIDAK ADA
    log("\n[TEST 4] POST /api/mapping-tests without reagen_name")
    try:
        payload = {"lis_name": "TEST_AGENT_LIS_2"}
        resp = requests.post(f"{BACKEND_URL}/mapping-tests", json=payload)
        log(f"  Status: {resp.status_code}")
        
        if resp.status_code == 201:
            data = resp.json()
            log(f"  Response: {json.dumps(data, indent=2)}")
            
            checks = []
            checks.append(("status == 'TIDAK ADA'", data.get("status") == "TIDAK ADA"))
            checks.append(("reagen_name is null", data.get("reagen_name") is None))
            
            all_passed = all(c[1] for c in checks)
            for check_name, passed in checks:
                log(f"    {'✅' if passed else '❌'} {check_name}")
            
            results.append(("Test 4: POST without reagen_name", all_passed))
        else:
            log(f"  ❌ Expected 201, got {resp.status_code}: {resp.text}")
            results.append(("Test 4: POST without reagen_name", False))
    except Exception as e:
        log(f"  ❌ Exception: {e}")
        results.append(("Test 4: POST without reagen_name", False))
    
    # Test 5: POST with existing reagent (different case) -> linked
    log("\n[TEST 5] POST /api/mapping-tests with existing reagent (case-insensitive)")
    try:
        # First, verify "Vidas Ca 15-3" exists in seed data
        payload = {"lis_name": "TEST_AGENT_LIS_3", "reagen_name": "vidas ca 15-3"}  # lowercase
        resp = requests.post(f"{BACKEND_URL}/mapping-tests", json=payload)
        log(f"  Status: {resp.status_code}")
        
        if resp.status_code == 201:
            data = resp.json()
            log(f"  Response: {json.dumps(data, indent=2)}")
            
            checks = []
            checks.append(("sync.action == 'linked'", data.get("sync", {}).get("action") == "linked"))
            # Should use master spelling "Vidas Ca 15-3"
            checks.append(("reagen_name uses master spelling", data.get("reagen_name") == "Vidas Ca 15-3"))
            
            all_passed = all(c[1] for c in checks)
            for check_name, passed in checks:
                log(f"    {'✅' if passed else '❌'} {check_name}")
            
            results.append(("Test 5: POST with existing reagent -> linked", all_passed))
        else:
            log(f"  ❌ Expected 201, got {resp.status_code}: {resp.text}")
            results.append(("Test 5: POST with existing reagent -> linked", False))
    except Exception as e:
        log(f"  ❌ Exception: {e}")
        results.append(("Test 5: POST with existing reagent -> linked", False))
    
    # Test 6: Verify seed_data.json persistence
    log("\n[TEST 6] Verify seed_data.json contains test entries")
    try:
        data = load_seed_data()
        
        # Check Mapping_Test
        mapping_test = data.get("Mapping_Test", [])
        test_mappings = [m for m in mapping_test if (m.get("lis_name") or "").upper().startswith(TEST_PREFIX)]
        log(f"  Found {len(test_mappings)} test mappings in seed_data.json")
        
        checks = []
        # Should have TEST_AGENT_LIS_1, TEST_AGENT_LIS_2, TEST_AGENT_LIS_3
        lis_1 = next((m for m in test_mappings if m.get("lis_name") == "TEST_AGENT_LIS_1"), None)
        lis_2 = next((m for m in test_mappings if m.get("lis_name") == "TEST_AGENT_LIS_2"), None)
        lis_3 = next((m for m in test_mappings if m.get("lis_name") == "TEST_AGENT_LIS_3"), None)
        
        checks.append(("TEST_AGENT_LIS_1 in Mapping_Test", lis_1 is not None))
        if lis_1:
            checks.append(("  LIS_1 reagen == TEST_AGENT_REAGEN_1", lis_1.get("reagen") == "TEST_AGENT_REAGEN_1"))
            checks.append(("  LIS_1 status == OK", lis_1.get("status") == "OK"))
        
        checks.append(("TEST_AGENT_LIS_2 in Mapping_Test", lis_2 is not None))
        if lis_2:
            checks.append(("  LIS_2 reagen is null", lis_2.get("reagen") is None))
            checks.append(("  LIS_2 status == TIDAK ADA", lis_2.get("status") == "TIDAK ADA"))
        
        checks.append(("TEST_AGENT_LIS_3 in Mapping_Test", lis_3 is not None))
        
        # Check Master_Extra
        master_extra = data.get("Master_Extra", [])
        test_reagents = [r for r in master_extra if (r.get("nama_reagen") or "").upper().startswith(TEST_PREFIX)]
        log(f"  Found {len(test_reagents)} test reagents in Master_Extra")
        
        reagen_1 = next((r for r in test_reagents if r.get("nama_reagen") == "TEST_AGENT_REAGEN_1"), None)
        checks.append(("TEST_AGENT_REAGEN_1 in Master_Extra", reagen_1 is not None))
        
        all_passed = all(c[1] for c in checks)
        for check_name, passed in checks:
            log(f"    {'✅' if passed else '❌'} {check_name}")
        
        results.append(("Test 6: seed_data.json persistence", all_passed))
    except Exception as e:
        log(f"  ❌ Exception: {e}")
        results.append(("Test 6: seed_data.json persistence", False))
    
    # Test 7: PUT rename reagent
    log("\n[TEST 7] PUT /api/mapping-tests/{id} to rename reagent")
    try:
        if not test_mapping_id_1:
            log(f"  ⚠️  Skipping: test_mapping_id_1 not available")
            results.append(("Test 7: PUT rename reagent", False))
        else:
            payload = {"reagen_name": "TEST_AGENT_REAGEN_1B"}
            resp = requests.put(f"{BACKEND_URL}/mapping-tests/{test_mapping_id_1}", json=payload)
            log(f"  Status: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                log(f"  Response: {json.dumps(data, indent=2)}")
                
                checks = []
                checks.append(("sync.action == 'renamed'", data.get("sync", {}).get("action") == "renamed"))
                
                # Verify in seed_data.json
                seed_data = load_seed_data()
                mapping_test = seed_data.get("Mapping_Test", [])
                lis_1 = next((m for m in mapping_test if m.get("lis_name") == "TEST_AGENT_LIS_1"), None)
                if lis_1:
                    checks.append(("seed Mapping_Test reagen == TEST_AGENT_REAGEN_1B", 
                                  lis_1.get("reagen") == "TEST_AGENT_REAGEN_1B"))
                
                master_extra = seed_data.get("Master_Extra", [])
                reagen_1b = next((r for r in master_extra if r.get("nama_reagen") == "TEST_AGENT_REAGEN_1B"), None)
                reagen_1 = next((r for r in master_extra if r.get("nama_reagen") == "TEST_AGENT_REAGEN_1"), None)
                checks.append(("seed Master_Extra has TEST_AGENT_REAGEN_1B", reagen_1b is not None))
                checks.append(("seed Master_Extra no longer has TEST_AGENT_REAGEN_1", reagen_1 is None))
                
                all_passed = all(c[1] for c in checks)
                for check_name, passed in checks:
                    log(f"    {'✅' if passed else '❌'} {check_name}")
                
                results.append(("Test 7: PUT rename reagent", all_passed))
            else:
                log(f"  ❌ Expected 200, got {resp.status_code}: {resp.text}")
                results.append(("Test 7: PUT rename reagent", False))
    except Exception as e:
        log(f"  ❌ Exception: {e}")
        results.append(("Test 7: PUT rename reagent", False))
    
    # Test 8: Verify monitoring only shows OK-mapped reagents
    log("\n[TEST 8] GET /api/monitoring?year=2026&month=9 - only OK-mapped reagents")
    try:
        resp_monitoring = requests.get(f"{BACKEND_URL}/monitoring?year=2026&month=9")
        resp_mapping = requests.get(f"{BACKEND_URL}/mapping-tests?status=OK")
        
        if resp_monitoring.status_code == 200 and resp_mapping.status_code == 200:
            monitoring_data = resp_monitoring.json()
            mapping_data = resp_mapping.json()
            
            monitoring_rows = monitoring_data.get("rows", [])
            ok_mappings = mapping_data.get("items", [])
            ok_reagen_names = {m.get("reagen_name") for m in ok_mappings if m.get("reagen_name")}
            
            log(f"  Monitoring rows: {len(monitoring_rows)}")
            log(f"  OK-mapped reagents: {len(ok_reagen_names)}")
            
            # Every reagent in monitoring should be in OK-mapped set
            checks = []
            unmapped_in_monitoring = []
            for row in monitoring_rows:
                reagen_name = row.get("nama_reagen")
                if reagen_name not in ok_reagen_names:
                    unmapped_in_monitoring.append(reagen_name)
            
            checks.append(("All monitoring reagents have OK mapping", len(unmapped_in_monitoring) == 0))
            if unmapped_in_monitoring:
                log(f"    ❌ Found {len(unmapped_in_monitoring)} unmapped reagents in monitoring:")
                for name in unmapped_in_monitoring[:5]:  # Show first 5
                    log(f"       - {name}")
            
            # Check if TEST_AGENT_REAGEN_1B appears (it should, as it has OK mapping)
            test_reagen_in_monitoring = any(r.get("nama_reagen") == "TEST_AGENT_REAGEN_1B" for r in monitoring_rows)
            log(f"    {'✅' if test_reagen_in_monitoring else '⚠️ '} TEST_AGENT_REAGEN_1B in monitoring (expected: yes)")
            
            all_passed = all(c[1] for c in checks)
            for check_name, passed in checks:
                log(f"    {'✅' if passed else '❌'} {check_name}")
            
            results.append(("Test 8: Monitoring shows only OK-mapped reagents", all_passed))
        else:
            log(f"  ❌ API calls failed: monitoring={resp_monitoring.status_code}, mapping={resp_mapping.status_code}")
            results.append(("Test 8: Monitoring shows only OK-mapped reagents", False))
    except Exception as e:
        log(f"  ❌ Exception: {e}")
        results.append(("Test 8: Monitoring shows only OK-mapped reagents", False))
    
    # Summary
    log("\n" + "=" * 80)
    log("TEST SUMMARY")
    log("=" * 80)
    for test_name, passed in results:
        log(f"  {'✅' if passed else '❌'} {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    log(f"\nTotal: {passed}/{total} tests passed")
    
    return all(p for _, p in results)

if __name__ == "__main__":
    try:
        all_passed = run_tests()
        
        # Cleanup
        log("\n" + "=" * 80)
        log("CLEANUP")
        log("=" * 80)
        cleanup_mongodb()
        cleanup_seed_file()
        verify_cleanup()
        
        log("\n" + "=" * 80)
        log("TESTING COMPLETE")
        log("=" * 80)
        
        sys.exit(0 if all_passed else 1)
    except Exception as e:
        log(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
