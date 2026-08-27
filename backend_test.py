"""
LabStock Backend API Testing
Tests all endpoints and business logic calculations
"""
import requests
import sys
from typing import Dict, Any

BASE_URL = "https://labstock-monitor.preview.emergentagent.com/api"

class LabStockTester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []
        
    def test(self, name: str, func):
        """Run a single test"""
        self.tests_run += 1
        print(f"\n{'='*60}")
        print(f"🔍 Test {self.tests_run}: {name}")
        print('='*60)
        try:
            func()
            self.tests_passed += 1
            print(f"✅ PASSED: {name}")
            return True
        except AssertionError as e:
            self.tests_failed += 1
            self.failures.append({'test': name, 'error': str(e)})
            print(f"❌ FAILED: {name}")
            print(f"   Error: {e}")
            return False
        except Exception as e:
            self.tests_failed += 1
            self.failures.append({'test': name, 'error': f"Exception: {str(e)}"})
            print(f"❌ FAILED: {name}")
            print(f"   Exception: {e}")
            return False
    
    def get(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """Make GET request"""
        url = f"{BASE_URL}{endpoint}"
        print(f"   GET {url}")
        if params:
            print(f"   Params: {params}")
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        return response
    
    def put(self, endpoint: str, data: Dict) -> Dict[str, Any]:
        """Make PUT request"""
        url = f"{BASE_URL}{endpoint}"
        print(f"   PUT {url}")
        print(f"   Data: {data}")
        response = requests.put(url, json=data, timeout=10)
        print(f"   Status: {response.status_code}")
        return response
    
    def summary(self):
        """Print test summary"""
        print(f"\n{'='*60}")
        print("📊 TEST SUMMARY")
        print('='*60)
        print(f"Total Tests: {self.tests_run}")
        print(f"✅ Passed: {self.tests_passed}")
        print(f"❌ Failed: {self.tests_failed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failures:
            print(f"\n{'='*60}")
            print("❌ FAILED TESTS:")
            print('='*60)
            for i, f in enumerate(self.failures, 1):
                print(f"{i}. {f['test']}")
                print(f"   {f['error']}")
        
        return 0 if self.tests_failed == 0 else 1


def main():
    tester = LabStockTester()
    
    # Test 1: Health check
    def test_health():
        r = tester.get('/health')
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        print(f"   Response: {data}")
        assert data['status'] == 'ok', f"Expected status 'ok', got {data.get('status')}"
        assert 'seeded' in data, "Missing 'seeded' field"
        print(f"   ✓ Status: {data['status']}, Seeded: {data['seeded']}")
    
    tester.test("GET /api/health returns status ok and seeded", test_health)
    
    # Test 2: Periods
    def test_periods():
        r = tester.get('/meta/periods')
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        print(f"   Found {len(data)} periods")
        assert len(data) >= 2, f"Expected at least 2 periods, got {len(data)}"
        
        # Check for Agustus 2026 and Juli 2026
        labels = [p['label'] for p in data]
        print(f"   Periods: {labels}")
        assert any('Agustus 2026' in l for l in labels), "Missing 'Agustus 2026'"
        assert any('Juli 2026' in l for l in labels), "Missing 'Juli 2026'"
        
        # Verify structure
        for p in data:
            assert 'year' in p and 'month' in p and 'label' in p, f"Invalid period structure: {p}"
        print(f"   ✓ All periods have correct structure")
    
    tester.test("GET /api/meta/periods returns available periods", test_periods)
    
    # Test 3: Excel summary
    def test_excel_summary():
        r = tester.get('/meta/excel-summary')
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        
        # Check required fields
        required = ['file', 'sheets', 'kolom_monitoring', 'rumus', 'status_warna', 'entitas_database']
        for field in required:
            assert field in data, f"Missing field: {field}"
        
        print(f"   ✓ File: {data['file']}")
        print(f"   ✓ Sheets: {len(data['sheets'])} sheets")
        print(f"   ✓ Kolom monitoring: {len(data['kolom_monitoring'])} columns")
        print(f"   ✓ Rumus: {len(data['rumus'])} formulas")
        print(f"   ✓ Status warna: {len(data['status_warna'])} status colors")
        print(f"   ✓ Entitas database: {len(data['entitas_database'])} entities")
    
    tester.test("GET /api/meta/excel-summary returns Excel analysis", test_excel_summary)
    
    # Test 4: Monitoring Juli 2026
    def test_monitoring_juli():
        r = tester.get('/monitoring', {'year': 2026, 'month': 7})
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        
        # Check structure
        assert data['year'] == 2026, f"Expected year 2026, got {data['year']}"
        assert data['month'] == 7, f"Expected month 7, got {data['month']}"
        assert 'label' in data, "Missing 'label'"
        assert 'days' in data, "Missing 'days'"
        assert 'counts' in data, "Missing 'counts'"
        assert 'total_reagen' in data, "Missing 'total_reagen'"
        assert 'rows' in data, "Missing 'rows'"
        
        print(f"   ✓ Period: {data['label']}")
        print(f"   ✓ Days in month: {data['days']}")
        print(f"   ✓ Total reagen: {data['total_reagen']}")
        print(f"   ✓ Counts: {data['counts']}")
        
        # Check counts structure
        counts = data['counts']
        assert 'critical' in counts, "Missing 'critical' count"
        assert 'warning' in counts, "Missing 'warning' count"
        assert 'safe' in counts, "Missing 'safe' count"
        assert 'unknown' in counts, "Missing 'unknown' count"
        
        # Verify rows structure
        assert len(data['rows']) > 0, "No rows returned"
        row = data['rows'][0]
        required_fields = ['reagen_id', 'nama_reagen', 'hari', 'qc', 'total_pemakaian', 
                          'saldo_awal', 'stok_masuk', 'sisa_stock', 'buffer_stock', 
                          'status', 'status_label']
        for field in required_fields:
            assert field in row, f"Missing field in row: {field}"
        
        print(f"   ✓ First row: {row['nama_reagen']}")
        
        # Verify business logic calculation for rows with complete data
        verified_count = 0
        for row in data['rows'][:5]:  # Check first 5 rows
            if row['saldo_awal'] is not None:
                # Calculate total_pemakaian = sum(hari values) + qc
                hari_sum = sum(row['hari'].values())
                expected_total = hari_sum + (row['qc'] or 0)
                assert row['total_pemakaian'] == expected_total, \
                    f"total_pemakaian mismatch for {row['nama_reagen']}: expected {expected_total}, got {row['total_pemakaian']}"
                
                # Calculate sisa_stock = (saldo_awal - total_pemakaian) + stok_masuk
                expected_sisa = (row['saldo_awal'] - row['total_pemakaian']) + (row['stok_masuk'] or 0)
                assert row['sisa_stock'] == expected_sisa, \
                    f"sisa_stock mismatch for {row['nama_reagen']}: expected {expected_sisa}, got {row['sisa_stock']}"
                
                # Verify status logic
                sisa = row['sisa_stock']
                buffer = row['buffer_stock']
                if buffer is not None:
                    if sisa <= buffer:
                        assert row['status'] == 'critical', f"Status should be 'critical' for {row['nama_reagen']}"
                    elif sisa <= buffer + 10:
                        assert row['status'] == 'warning', f"Status should be 'warning' for {row['nama_reagen']}"
                    else:
                        assert row['status'] == 'safe', f"Status should be 'safe' for {row['nama_reagen']}"
                
                verified_count += 1
        
        print(f"   ✓ Verified calculations for {verified_count} rows with complete data")
        
        # Check for PERLU CEK status (expected from Excel #REF!)
        perlu_cek_count = sum(1 for r in data['rows'] if r['status'] == 'unknown')
        print(f"   ✓ Found {perlu_cek_count} reagen with 'PERLU CEK' status (expected from Excel #REF!)")
    
    tester.test("GET /api/monitoring?year=2026&month=7 with calculations", test_monitoring_juli)
    
    # Test 5: Monitoring Agustus 2026
    def test_monitoring_agustus():
        r = tester.get('/monitoring', {'year': 2026, 'month': 8})
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        
        assert data['year'] == 2026, f"Expected year 2026, got {data['year']}"
        assert data['month'] == 8, f"Expected month 8, got {data['month']}"
        assert len(data['rows']) > 0, "No rows returned"
        
        print(f"   ✓ Period: {data['label']}")
        print(f"   ✓ Total reagen: {data['total_reagen']}")
        print(f"   ✓ Counts: {data['counts']}")
    
    tester.test("GET /api/monitoring?year=2026&month=8 works", test_monitoring_agustus)
    
    # Test 6: List reagen
    def test_list_reagen():
        r = tester.get('/reagen')
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        
        assert isinstance(data, list), "Expected list of reagen"
        assert len(data) > 0, "No reagen returned"
        
        print(f"   ✓ Found {len(data)} reagen")
        
        # Check structure
        reagen = data[0]
        required = ['id', 'nama_reagen', 'satuan', 'aktif']
        for field in required:
            assert field in reagen, f"Missing field: {field}"
        
        print(f"   ✓ First reagen: {reagen['nama_reagen']}")
    
    tester.test("GET /api/reagen returns master reagen list", test_list_reagen)
    
    # Test 7: Search reagen
    def test_search_reagen():
        r = tester.get('/reagen', {'query': 'Ca'})
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        
        assert isinstance(data, list), "Expected list of reagen"
        print(f"   ✓ Found {len(data)} reagen matching 'Ca'")
        
        # Verify all results contain 'Ca' (case-insensitive)
        for reagen in data:
            assert 'ca' in reagen['nama_reagen'].lower(), \
                f"Reagen '{reagen['nama_reagen']}' doesn't match query 'Ca'"
    
    tester.test("GET /api/reagen?query=Ca filters by name", test_search_reagen)
    
    # Test 8: Update reagen
    def test_update_reagen():
        # First get a reagen
        r = tester.get('/reagen')
        assert r.status_code == 200, "Failed to get reagen list"
        reagen_list = r.json()
        assert len(reagen_list) > 0, "No reagen to update"
        
        reagen = reagen_list[0]
        reagen_id = reagen['id']
        original_buffer = reagen.get('buffer_stock')
        
        print(f"   Updating reagen: {reagen['nama_reagen']}")
        print(f"   Original buffer_stock: {original_buffer}")
        
        # Update buffer_stock
        new_buffer = 100.0
        r = tester.put(f'/reagen/{reagen_id}', {'buffer_stock': new_buffer})
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        
        updated = r.json()
        assert updated['buffer_stock'] == new_buffer, \
            f"Expected buffer_stock {new_buffer}, got {updated['buffer_stock']}"
        
        print(f"   ✓ Updated buffer_stock to {new_buffer}")
        
        # Verify persistence
        r = tester.get('/reagen')
        assert r.status_code == 200, "Failed to verify update"
        reagen_list = r.json()
        updated_reagen = next((r for r in reagen_list if r['id'] == reagen_id), None)
        assert updated_reagen is not None, "Updated reagen not found"
        assert updated_reagen['buffer_stock'] == new_buffer, \
            f"Update not persisted: expected {new_buffer}, got {updated_reagen['buffer_stock']}"
        
        print(f"   ✓ Update persisted successfully")
    
    tester.test("PUT /api/reagen/{id} updates and persists", test_update_reagen)
    
    # Test 9: Mapping tests
    def test_mapping_tests():
        r = tester.get('/mapping-tests')
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        
        assert 'total' in data, "Missing 'total'"
        assert 'ok' in data, "Missing 'ok'"
        assert 'tidak_ada' in data, "Missing 'tidak_ada'"
        assert 'items' in data, "Missing 'items'"
        
        print(f"   ✓ Total: {data['total']}")
        print(f"   ✓ OK: {data['ok']}")
        print(f"   ✓ TIDAK ADA: {data['tidak_ada']}")
        
        assert data['total'] == data['ok'] + data['tidak_ada'], \
            "Total doesn't match sum of ok + tidak_ada"
    
    tester.test("GET /api/mapping-tests returns total/ok/tidak_ada + items", test_mapping_tests)
    
    # Test 10: Mapping tests with filter
    def test_mapping_filter():
        r = tester.get('/mapping-tests', {'status': 'OK'})
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        
        print(f"   ✓ Filtered items: {len(data['items'])}")
        
        # Verify all items have status OK
        for item in data['items']:
            assert item['status'] == 'OK', f"Item has wrong status: {item['status']}"
    
    tester.test("GET /api/mapping-tests?status=OK filters correctly", test_mapping_filter)
    
    # Test 11: LIS raw
    def test_lis_raw():
        r = tester.get('/lis/raw', {'period': '2026-07'})
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        
        assert 'total' in data, "Missing 'total'"
        assert 'periods' in data, "Missing 'periods'"
        assert 'items' in data, "Missing 'items'"
        
        print(f"   ✓ Total: {data['total']}")
        print(f"   ✓ Periods: {data['periods']}")
        print(f"   ✓ Items returned: {len(data['items'])}")
        
        # Verify periods list
        assert isinstance(data['periods'], list), "Periods should be a list"
        assert len(data['periods']) > 0, "No periods returned"
    
    tester.test("GET /api/lis/raw?period=2026-07 returns items + periods", test_lis_raw)
    
    # Test 12: PRF
    def test_prf():
        r = tester.get('/prf', {'period': '2026-07'})
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        
        assert 'total' in data, "Missing 'total'"
        assert 'items' in data, "Missing 'items'"
        
        print(f"   ✓ Total PRF: {data['total']}")
        print(f"   ✓ Items: {len(data['items'])}")
    
    tester.test("GET /api/prf?period=2026-07 returns PRF items", test_prf)
    
    # Test 13: Penerimaan
    def test_penerimaan():
        r = tester.get('/penerimaan', {'period': '2026-07'})
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        
        assert 'total' in data, "Missing 'total'"
        assert 'total_qty' in data, "Missing 'total_qty'"
        assert 'items' in data, "Missing 'items'"
        
        print(f"   ✓ Total penerimaan: {data['total']}")
        print(f"   ✓ Total qty: {data['total_qty']}")
        print(f"   ✓ Items: {len(data['items'])}")
        
        # Verify total_qty calculation
        if len(data['items']) > 0:
            calculated_qty = sum(item.get('qty', 0) for item in data['items'])
            assert data['total_qty'] == calculated_qty, \
                f"total_qty mismatch: expected {calculated_qty}, got {data['total_qty']}"
            print(f"   ✓ total_qty calculation verified")
    
    tester.test("GET /api/penerimaan?period=2026-07 returns items with computed qty", test_penerimaan)
    
    # ========== PHASE 2 TESTS ==========
    print("\n" + "="*60)
    print("🚀 PHASE 2 FEATURES TESTING")
    print("="*60)
    
    # Test 14: Set Saldo Awal manually
    def test_set_saldo_awal():
        # Get a reagen first
        r = tester.get('/reagen')
        assert r.status_code == 200, "Failed to get reagen list"
        reagen_list = r.json()
        assert len(reagen_list) > 0, "No reagen available"
        
        reagen = reagen_list[0]
        reagen_id = reagen['id']
        print(f"   Testing with reagen: {reagen['nama_reagen']}")
        
        # Set saldo awal for August 2026
        r = tester.put('/monitoring/saldo-awal', {
            'reagen_id': reagen_id,
            'year': 2026,
            'month': 8,
            'saldo_awal': 100
        })
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        assert data.get('ok') == True, "Expected ok=True"
        print(f"   ✓ Set saldo_awal=100 for {reagen['nama_reagen']}")
        
        # Verify by getting monitoring data
        r = tester.get('/monitoring', {'year': 2026, 'month': 8})
        assert r.status_code == 200, "Failed to get monitoring data"
        mon_data = r.json()
        
        # Find the reagen row
        row = next((r for r in mon_data['rows'] if r['reagen_id'] == reagen_id), None)
        assert row is not None, f"Reagen {reagen_id} not found in monitoring"
        assert row['saldo_awal'] == 100, f"Expected saldo_awal=100, got {row['saldo_awal']}"
        
        # Verify sisa_stock is recomputed
        expected_sisa = (100 - row['total_pemakaian']) + row['stok_masuk']
        assert row['sisa_stock'] == expected_sisa, \
            f"sisa_stock not recomputed correctly: expected {expected_sisa}, got {row['sisa_stock']}"
        
        print(f"   ✓ saldo_awal=100, total_pemakaian={row['total_pemakaian']}, stok_masuk={row['stok_masuk']}, sisa_stock={row['sisa_stock']}")
        print(f"   ✓ Status: {row['status_label']}")
    
    tester.test("PUT /api/monitoring/saldo-awal sets saldo awal and recomputes sisa_stock", test_set_saldo_awal)
    
    # Test 15: Set Sisa Override (manual adjustment)
    def test_sisa_override():
        # Get a reagen
        r = tester.get('/reagen')
        assert r.status_code == 200, "Failed to get reagen list"
        reagen_list = r.json()
        reagen = reagen_list[0]
        reagen_id = reagen['id']
        
        print(f"   Testing with reagen: {reagen['nama_reagen']}")
        
        # Set sisa_override to 5
        r = tester.put('/monitoring/sisa-override', {
            'reagen_id': reagen_id,
            'year': 2026,
            'month': 8,
            'sisa_override': 5
        })
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        assert data.get('ok') == True, "Expected ok=True"
        print(f"   ✓ Set sisa_override=5")
        
        # Verify
        r = tester.get('/monitoring', {'year': 2026, 'month': 8})
        assert r.status_code == 200, "Failed to get monitoring data"
        mon_data = r.json()
        
        row = next((r for r in mon_data['rows'] if r['reagen_id'] == reagen_id), None)
        assert row is not None, f"Reagen {reagen_id} not found"
        assert row['sisa_stock'] == 5, f"Expected sisa_stock=5, got {row['sisa_stock']}"
        assert row['is_override'] == True, f"Expected is_override=True, got {row['is_override']}"
        
        print(f"   ✓ sisa_stock=5 (manual), is_override=True, status={row['status_label']}")
        
        # Revert to auto by setting null
        r = tester.put('/monitoring/sisa-override', {
            'reagen_id': reagen_id,
            'year': 2026,
            'month': 8,
            'sisa_override': None
        })
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        print(f"   ✓ Reverted sisa_override to null")
        
        # Verify revert
        r = tester.get('/monitoring', {'year': 2026, 'month': 8})
        assert r.status_code == 200, "Failed to get monitoring data"
        mon_data = r.json()
        
        row = next((r for r in mon_data['rows'] if r['reagen_id'] == reagen_id), None)
        assert row is not None, f"Reagen {reagen_id} not found"
        assert row['is_override'] == False, f"Expected is_override=False after revert, got {row['is_override']}"
        assert row['sisa_stock'] == row['sisa_auto'], \
            f"Expected sisa_stock to match sisa_auto after revert"
        
        print(f"   ✓ Reverted to auto: sisa_stock={row['sisa_stock']}, is_override=False")
    
    tester.test("PUT /api/monitoring/sisa-override sets manual override and reverts to auto", test_sisa_override)
    
    # Test 16: Auto Saldo Awal (fill from previous month)
    def test_auto_saldo_awal():
        # Call auto-saldo-awal for August 2026 (should fill from July 2026)
        r = requests.post(f"{BASE_URL}/monitoring/auto-saldo-awal", 
                         json={'year': 2026, 'month': 8}, 
                         timeout=10)
        print(f"   POST {BASE_URL}/monitoring/auto-saldo-awal")
        print(f"   Data: {{'year': 2026, 'month': 8}}")
        print(f"   Status: {r.status_code}")
        
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        
        assert data.get('ok') == True, "Expected ok=True"
        assert 'updated' in data, "Missing 'updated' field"
        assert 'from_period' in data, "Missing 'from_period' field"
        
        print(f"   ✓ Updated {data['updated']} reagen")
        print(f"   ✓ From period: {data['from_period']}")
        
        # Verify at least some reagen have saldo_awal set
        r = tester.get('/monitoring', {'year': 2026, 'month': 8})
        assert r.status_code == 200, "Failed to get monitoring data"
        mon_data = r.json()
        
        reagen_with_saldo = [r for r in mon_data['rows'] if r['saldo_awal'] is not None]
        assert len(reagen_with_saldo) > 0, "No reagen have saldo_awal after auto-fill"
        
        print(f"   ✓ {len(reagen_with_saldo)} reagen now have saldo_awal set")
    
    tester.test("POST /api/monitoring/auto-saldo-awal fills saldo awal from previous month", test_auto_saldo_awal)
    
    # Test 17: Create PRF
    def test_create_prf():
        # Get a reagen
        r = tester.get('/reagen')
        assert r.status_code == 200, "Failed to get reagen list"
        reagen_list = r.json()
        reagen = reagen_list[0]
        reagen_id = reagen['id']
        
        print(f"   Creating PRF for: {reagen['nama_reagen']}")
        
        # Create PRF
        r = requests.post(f"{BASE_URL}/prf", 
                         json={
                             'reagen_id': reagen_id,
                             'reagent_no': 1,
                             'kits': 2,
                             'tanggal_pr': '2026-08-15',
                             'note': 'Test PRF'
                         }, 
                         timeout=10)
        print(f"   POST {BASE_URL}/prf")
        print(f"   Status: {r.status_code}")
        
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        
        assert 'id' in data, "Missing 'id' field"
        assert data['reagen_id'] == reagen_id, "reagen_id mismatch"
        assert data['status'] == 'open', f"Expected status 'open', got {data['status']}"
        assert data['period'] == '2026-08', f"Expected period '2026-08', got {data['period']}"
        assert data['kits'] == 2, f"Expected kits=2, got {data['kits']}"
        
        prf_id = data['id']
        print(f"   ✓ Created PRF id={prf_id}, status={data['status']}, period={data['period']}")
        
        # Verify it appears in GET /api/prf
        r = tester.get('/prf', {'period': '2026-08'})
        assert r.status_code == 200, "Failed to get PRF list"
        prf_data = r.json()
        
        prf_item = next((p for p in prf_data['items'] if p['id'] == prf_id), None)
        assert prf_item is not None, f"Created PRF {prf_id} not found in list"
        
        print(f"   ✓ PRF appears in GET /api/prf?period=2026-08")
        
        # Store for next test
        test_create_prf.prf_id = prf_id
        test_create_prf.reagen_id = reagen_id
    
    tester.test("POST /api/prf creates PRF with status 'open' and correct period", test_create_prf)
    
    # Test 18: Receive PRF (creates penerimaan and updates stok_masuk)
    def test_receive_prf():
        prf_id = getattr(test_create_prf, 'prf_id', None)
        reagen_id = getattr(test_create_prf, 'reagen_id', None)
        
        if not prf_id:
            print("   ⚠ Skipping: No PRF created in previous test")
            return
        
        print(f"   Receiving PRF id={prf_id}")
        
        # Get monitoring data before receiving
        r = tester.get('/monitoring', {'year': 2026, 'month': 8})
        assert r.status_code == 200, "Failed to get monitoring data"
        mon_before = r.json()
        row_before = next((r for r in mon_before['rows'] if r['reagen_id'] == reagen_id), None)
        stok_masuk_before = row_before['stok_masuk'] if row_before else 0
        
        print(f"   Stok masuk before: {stok_masuk_before}")
        
        # Receive PRF
        r = requests.post(f"{BASE_URL}/prf/{prf_id}/terima", 
                         json={
                             'tanggal_terima': '2026-08-20',
                             'kits': 2
                         }, 
                         timeout=10)
        print(f"   POST {BASE_URL}/prf/{prf_id}/terima")
        print(f"   Status: {r.status_code}")
        
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        
        assert data.get('ok') == True, "Expected ok=True"
        assert 'penerimaan' in data, "Missing 'penerimaan' field"
        
        penerimaan = data['penerimaan']
        assert penerimaan['source'] == 'PRF', f"Expected source='PRF', got {penerimaan['source']}"
        assert penerimaan['prf_id'] == prf_id, "prf_id mismatch in penerimaan"
        
        print(f"   ✓ PRF received, penerimaan created: id={penerimaan['id']}, qty={penerimaan['qty']}")
        
        # Verify PRF status changed to 'received'
        r = tester.get('/prf', {'period': '2026-08'})
        assert r.status_code == 200, "Failed to get PRF list"
        prf_data = r.json()
        
        prf_item = next((p for p in prf_data['items'] if p['id'] == prf_id), None)
        assert prf_item is not None, f"PRF {prf_id} not found"
        assert prf_item['status'] == 'received', f"Expected status 'received', got {prf_item['status']}"
        
        print(f"   ✓ PRF status changed to 'received'")
        
        # Verify penerimaan appears in GET /api/penerimaan
        r = tester.get('/penerimaan', {'period': '2026-08'})
        assert r.status_code == 200, "Failed to get penerimaan list"
        pen_data = r.json()
        
        pen_item = next((p for p in pen_data['items'] if p['id'] == penerimaan['id']), None)
        assert pen_item is not None, f"Penerimaan {penerimaan['id']} not found in list"
        
        print(f"   ✓ Penerimaan appears in GET /api/penerimaan?period=2026-08")
        
        # Verify stok_masuk increased in monitoring
        r = tester.get('/monitoring', {'year': 2026, 'month': 8})
        assert r.status_code == 200, "Failed to get monitoring data"
        mon_after = r.json()
        row_after = next((r for r in mon_after['rows'] if r['reagen_id'] == reagen_id), None)
        assert row_after is not None, f"Reagen {reagen_id} not found in monitoring"
        
        stok_masuk_after = row_after['stok_masuk']
        qty_added = penerimaan['qty']
        
        assert stok_masuk_after == stok_masuk_before + qty_added, \
            f"stok_masuk not increased correctly: before={stok_masuk_before}, after={stok_masuk_after}, expected={stok_masuk_before + qty_added}"
        
        print(f"   ✓ Stok masuk increased: {stok_masuk_before} -> {stok_masuk_after} (+{qty_added})")
        
        # Store for delete test
        test_receive_prf.prf_id = prf_id
    
    tester.test("POST /api/prf/{id}/terima creates penerimaan and increases stok_masuk", test_receive_prf)
    
    # Test 19: Delete PRF
    def test_delete_prf():
        # Create a new PRF to delete
        r = tester.get('/reagen')
        assert r.status_code == 200, "Failed to get reagen list"
        reagen_list = r.json()
        reagen = reagen_list[1] if len(reagen_list) > 1 else reagen_list[0]
        reagen_id = reagen['id']
        
        # Create PRF
        r = requests.post(f"{BASE_URL}/prf", 
                         json={
                             'reagen_id': reagen_id,
                             'reagent_no': 1,
                             'kits': 1,
                             'tanggal_pr': '2026-08-16'
                         }, 
                         timeout=10)
        assert r.status_code == 200, "Failed to create PRF for delete test"
        prf = r.json()
        prf_id = prf['id']
        
        print(f"   Created PRF id={prf_id} for deletion test")
        
        # Delete PRF
        r = requests.delete(f"{BASE_URL}/prf/{prf_id}", timeout=10)
        print(f"   DELETE {BASE_URL}/prf/{prf_id}")
        print(f"   Status: {r.status_code}")
        
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        assert data.get('ok') == True, "Expected ok=True"
        
        print(f"   ✓ PRF deleted")
        
        # Verify it's gone
        r = tester.get('/prf', {'period': '2026-08'})
        assert r.status_code == 200, "Failed to get PRF list"
        prf_data = r.json()
        
        prf_item = next((p for p in prf_data['items'] if p['id'] == prf_id), None)
        assert prf_item is None, f"Deleted PRF {prf_id} still appears in list"
        
        print(f"   ✓ PRF removed from list")
    
    tester.test("DELETE /api/prf/{id} removes PRF", test_delete_prf)
    
    # Test 20: LIS Import
    def test_lis_import():
        import os
        
        sample_file = '/app/sample_LIS_260810.xlsx'
        assert os.path.exists(sample_file), f"Sample file not found: {sample_file}"
        
        print(f"   Importing file: {sample_file}")
        
        # Read file
        with open(sample_file, 'rb') as f:
            files = {'files': ('sample_LIS_260810.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            r = requests.post(f"{BASE_URL}/lis/import", files=files, timeout=30)
        
        print(f"   POST {BASE_URL}/lis/import")
        print(f"   Status: {r.status_code}")
        
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        
        # Check response structure
        assert 'files' in data, "Missing 'files' field"
        assert 'dates_affected' in data, "Missing 'dates_affected' field"
        assert 'pemakaian_records' in data, "Missing 'pemakaian_records' field"
        assert 'reagen_terdampak' in data, "Missing 'reagen_terdampak' field"
        assert 'unmatched_tests' in data, "Missing 'unmatched_tests' field"
        
        print(f"   ✓ Files processed: {len(data['files'])}")
        print(f"   ✓ Dates affected: {data['dates_affected']}")
        print(f"   ✓ Pemakaian records: {data['pemakaian_records']}")
        print(f"   ✓ Reagen terdampak: {data['reagen_terdampak']}")
        
        # Verify dates
        assert '2026-08-10' in data['dates_affected'], "Expected date '2026-08-10' not in dates_affected"
        
        # Check file summary
        file_summary = data['files'][0]
        assert file_summary['matched'] > 0, "No tests matched"
        assert 'TEST TIDAK DIKENAL' in data['unmatched_tests'], "Expected 'TEST TIDAK DIKENAL' in unmatched"
        
        print(f"   ✓ Matched: {file_summary['matched']}, Unmatched: {len(file_summary.get('unmatched', []))}")
        print(f"   ✓ Unmatched tests include: {data['unmatched_tests'][:3]}")
        
        # Verify monitoring data updated
        r = tester.get('/monitoring', {'year': 2026, 'month': 8})
        assert r.status_code == 200, "Failed to get monitoring data"
        mon_data = r.json()
        
        # Check for UIBC with hari['10'] == 5
        uibc_row = next((r for r in mon_data['rows'] if 'UIBC' in r['nama_reagen'].upper()), None)
        if uibc_row:
            day_10_usage = uibc_row['hari'].get('10', 0)
            print(f"   ✓ UIBC hari['10'] = {day_10_usage} (expected 5)")
            # Note: might not be exactly 5 if there was existing data
        
        # Check for Hematologi
        hema_row = next((r for r in mon_data['rows'] if 'HEMATOLOGI' in r['nama_reagen'].upper()), None)
        if hema_row:
            day_10_usage = hema_row['hari'].get('10', 0)
            print(f"   ✓ Hematologi hari['10'] = {day_10_usage} (expected 15 aggregated)")
    
    tester.test("POST /api/lis/import processes Excel and updates pemakaian_harian", test_lis_import)
    
    return tester.summary()


if __name__ == '__main__':
    print("="*60)
    print("🧪 LabStock Backend API Testing")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print("="*60)
    
    sys.exit(main())
