"""Backend test for LabStock LIS import bug fix - per-row Tanggal column."""
import os
import requests
import openpyxl
from openpyxl import Workbook
from datetime import datetime

# Backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://stock-status-5.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

print(f"Testing against: {API_BASE}")

def create_excel_per_row_tanggal():
    """TEST 1: Create Excel with per-row Tanggal column (the bug scenario)."""
    wb = Workbook()
    ws = wb.active
    
    # Header row
    ws.append(['Grup', 'Nama Test', 'Tanggal', 'Jumlah'])
    
    # Data rows with different dates
    ws.append(['Kimia', 'UIBC', datetime(2026, 8, 2), 4])
    ws.append(['Kimia', 'UIBC', datetime(2026, 8, 9), 6])
    ws.append(['Hema', 'Hematology Lengkap', datetime(2026, 8, 20), 5])
    ws.append(['Hema', 'Hematology Lengkap', datetime(2026, 8, 27), 7])
    
    filename = '/tmp/LIS_260831.xlsx'
    wb.save(filename)
    print(f"✓ Created {filename}")
    return filename

def create_excel_matrix_day_columns():
    """TEST 2: Create Excel with matrix day-columns (regression test)."""
    wb = Workbook()
    ws = wb.active
    
    # Header row: Nama Test | 1 | 2 | ... | 31
    header = ['Nama Test'] + list(range(1, 32))
    ws.append(header)
    
    # Data row: UIBC with values only on days 5 and 12
    row = ['UIBC'] + [None] * 31
    row[5] = 3  # day 5 (index 5 in the row, which is column 6)
    row[12] = 8  # day 12 (index 12 in the row, which is column 13)
    ws.append(row)
    
    filename = '/tmp/LIS_260830.xlsx'
    wb.save(filename)
    print(f"✓ Created {filename}")
    return filename

def create_excel_single_date_filename():
    """TEST 3: Create Excel with single date from filename (regression test)."""
    wb = Workbook()
    ws = wb.active
    
    # Header row
    ws.append(['Grup', 'Nama Test', 'Jumlah'])
    
    # Data row
    ws.append(['Kimia', 'UIBC', 2])
    
    filename = '/tmp/LIS_260803.xlsx'
    wb.save(filename)
    print(f"✓ Created {filename}")
    return filename

def import_lis_file(filepath):
    """Import a LIS Excel file via POST /api/lis/import."""
    filename = os.path.basename(filepath)
    with open(filepath, 'rb') as f:
        files = {'files': (filename, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = requests.post(f"{API_BASE}/lis/import", files=files)
    
    if response.status_code != 200:
        print(f"✗ Import failed for {filename}: {response.status_code} - {response.text}")
        return None
    
    result = response.json()
    print(f"✓ Imported {filename}: {result.get('pemakaian_records', 0)} pemakaian records")
    return result

def get_monitoring(year, month):
    """Get monitoring data for a specific period."""
    response = requests.get(f"{API_BASE}/monitoring", params={'year': year, 'month': month})
    if response.status_code != 200:
        print(f"✗ Failed to get monitoring: {response.status_code} - {response.text}")
        return None
    return response.json()

def get_source_files(period):
    """Get list of source files for a period."""
    response = requests.get(f"{API_BASE}/lis/source-files", params={'period': period})
    if response.status_code != 200:
        print(f"✗ Failed to get source files: {response.status_code} - {response.text}")
        return None
    return response.json()

def delete_source_file(source_file):
    """Delete a source file and its data."""
    response = requests.delete(f"{API_BASE}/lis/source-file/{source_file}")
    if response.status_code != 200:
        print(f"✗ Failed to delete {source_file}: {response.status_code} - {response.text}")
        return False
    result = response.json()
    print(f"✓ Deleted {source_file}: {result.get('lis_raw_dihapus', 0)} lis_raw, {result.get('pemakaian_dihapus', 0)} pemakaian")
    return True

def get_mapping_tests():
    """Get mapping tests with status OK."""
    response = requests.get(f"{API_BASE}/mapping-tests", params={'status': 'OK'})
    if response.status_code != 200:
        print(f"✗ Failed to get mapping tests: {response.status_code} - {response.text}")
        return None
    return response.json()

def find_reagen_by_name(rows, name):
    """Find a reagen row by name (case-insensitive)."""
    name_lower = name.lower()
    for row in rows:
        if row.get('nama_reagen', '').lower() == name_lower:
            return row
    return None

print("\n" + "="*80)
print("LABSTOCK LIS IMPORT BUG FIX TEST")
print("="*80)

# First, verify mappings exist
print("\n--- Verifying Mappings ---")
mappings = get_mapping_tests()
if mappings:
    print(f"✓ Total OK mappings: {mappings.get('ok', 0)}")
    items = mappings.get('items', [])
    uibc_mapping = next((m for m in items if m.get('lis_name', '').lower() == 'uibc'), None)
    hema_mapping = next((m for m in items if 'hematology lengkap' in m.get('lis_name', '').lower()), None)
    
    if uibc_mapping:
        print(f"  - UIBC maps to: {uibc_mapping.get('reagen_name')}")
    else:
        print("  ⚠ UIBC mapping not found")
    
    if hema_mapping:
        print(f"  - Hematology Lengkap maps to: {hema_mapping.get('reagen_name')}")
    else:
        print("  ⚠ Hematology Lengkap mapping not found")

# Get initial state
print("\n--- Initial State ---")
initial_files = get_source_files('2026-08')
if initial_files:
    print(f"Initial source files for 2026-08: {len(initial_files)}")
    for f in initial_files:
        print(f"  - {f.get('source_file')}: {f.get('tests')} tests")

# TEST 1: Per-row Tanggal column (the bug scenario)
print("\n" + "="*80)
print("TEST 1: Per-row Tanggal column (BUG FIX)")
print("="*80)

file1 = create_excel_per_row_tanggal()
result1 = import_lis_file(file1)

if result1:
    print(f"\nImport summary:")
    print(f"  - Files: {len(result1.get('files', []))}")
    print(f"  - Dates affected: {result1.get('dates_affected', [])}")
    print(f"  - Pemakaian records: {result1.get('pemakaian_records', 0)}")
    print(f"  - Reagen affected: {result1.get('reagen_terdampak', 0)}")
    if result1.get('unmatched_tests'):
        print(f"  - Unmatched tests: {result1.get('unmatched_tests')}")

# Verify monitoring data
print("\n--- Verifying Monitoring Data ---")
monitoring = get_monitoring(2026, 8)

if monitoring:
    print(f"Total reagen: {monitoring.get('total_reagen', 0)}")
    rows = monitoring.get('rows', [])
    
    # Check UIBC
    uibc = find_reagen_by_name(rows, 'UIBC')
    if uibc:
        hari = uibc.get('hari', {})
        print(f"\nUIBC hari: {hari}")
        
        # Expected: day 2 = 4, day 9 = 6
        day_2 = hari.get('2', 0)
        day_9 = hari.get('9', 0)
        day_31 = hari.get('31', 0)
        
        print(f"  - Day 2: {day_2} (expected: 4)")
        print(f"  - Day 9: {day_9} (expected: 6)")
        print(f"  - Day 31: {day_31} (should NOT be the only populated day)")
        
        # Check if values are on correct days
        test1_pass = True
        if day_2 < 4:
            print(f"  ✗ FAIL: Day 2 should have at least 4 (got {day_2})")
            test1_pass = False
        if day_9 < 6:
            print(f"  ✗ FAIL: Day 9 should have at least 6 (got {day_9})")
            test1_pass = False
        
        # Check that not everything is on day 31
        total_hari = sum(hari.values())
        if total_hari > 0 and day_31 == total_hari:
            print(f"  ✗ FAIL: All usage is on day 31 (bug not fixed)")
            test1_pass = False
        
        if test1_pass:
            print(f"  ✓ PASS: UIBC values are spread across correct days")
    else:
        print("  ✗ UIBC not found in monitoring data")
        test1_pass = False
    
    # Check Hematologi
    hematologi = find_reagen_by_name(rows, 'Hematologi')
    if hematologi:
        hari = hematologi.get('hari', {})
        print(f"\nHematologi hari: {hari}")
        
        # Expected: day 20 = 5, day 27 = 7
        day_20 = hari.get('20', 0)
        day_27 = hari.get('27', 0)
        day_31 = hari.get('31', 0)
        
        print(f"  - Day 20: {day_20} (expected: 5)")
        print(f"  - Day 27: {day_27} (expected: 7)")
        print(f"  - Day 31: {day_31} (should NOT be the only populated day)")
        
        if day_20 < 5:
            print(f"  ✗ FAIL: Day 20 should have at least 5 (got {day_20})")
            test1_pass = False
        if day_27 < 7:
            print(f"  ✗ FAIL: Day 27 should have at least 7 (got {day_27})")
            test1_pass = False
        
        # Check that not everything is on day 31
        total_hari = sum(hari.values())
        if total_hari > 0 and day_31 == total_hari:
            print(f"  ✗ FAIL: All usage is on day 31 (bug not fixed)")
            test1_pass = False
        
        if test1_pass:
            print(f"  ✓ PASS: Hematologi values are spread across correct days")
    else:
        print("  ✗ Hematologi not found in monitoring data")
        test1_pass = False

# TEST 2: Matrix day-columns (regression test)
print("\n" + "="*80)
print("TEST 2: Matrix day-columns (REGRESSION)")
print("="*80)

file2 = create_excel_matrix_day_columns()
result2 = import_lis_file(file2)

if result2:
    print(f"\nImport summary:")
    print(f"  - Dates affected: {result2.get('dates_affected', [])}")
    print(f"  - Pemakaian records: {result2.get('pemakaian_records', 0)}")

# Verify monitoring data
print("\n--- Verifying Monitoring Data ---")
monitoring2 = get_monitoring(2026, 8)

if monitoring2:
    rows = monitoring2.get('rows', [])
    uibc = find_reagen_by_name(rows, 'UIBC')
    
    if uibc:
        hari = uibc.get('hari', {})
        print(f"\nUIBC hari after matrix import: {hari}")
        
        day_5 = hari.get('5', 0)
        day_12 = hari.get('12', 0)
        
        print(f"  - Day 5: {day_5} (should include matrix value 3)")
        print(f"  - Day 12: {day_12} (should include matrix value 8)")
        
        test2_pass = True
        if day_5 < 3:
            print(f"  ✗ FAIL: Day 5 should have at least 3 (got {day_5})")
            test2_pass = False
        if day_12 < 8:
            print(f"  ✗ FAIL: Day 12 should have at least 8 (got {day_12})")
            test2_pass = False
        
        if test2_pass:
            print(f"  ✓ PASS: Matrix day-columns still work correctly")
    else:
        print("  ✗ UIBC not found in monitoring data")
        test2_pass = False

# TEST 3: Single date from filename (regression test)
print("\n" + "="*80)
print("TEST 3: Single date from filename (REGRESSION)")
print("="*80)

file3 = create_excel_single_date_filename()
result3 = import_lis_file(file3)

if result3:
    print(f"\nImport summary:")
    print(f"  - Dates affected: {result3.get('dates_affected', [])}")
    print(f"  - Pemakaian records: {result3.get('pemakaian_records', 0)}")

# Verify monitoring data
print("\n--- Verifying Monitoring Data ---")
monitoring3 = get_monitoring(2026, 8)

if monitoring3:
    rows = monitoring3.get('rows', [])
    uibc = find_reagen_by_name(rows, 'UIBC')
    
    if uibc:
        hari = uibc.get('hari', {})
        print(f"\nUIBC hari after single-date import: {hari}")
        
        day_3 = hari.get('3', 0)
        
        print(f"  - Day 3: {day_3} (should include value 2 from filename date)")
        
        test3_pass = True
        if day_3 < 2:
            print(f"  ✗ FAIL: Day 3 should have at least 2 (got {day_3})")
            test3_pass = False
        else:
            print(f"  ✓ PASS: Single date from filename still works correctly")
    else:
        print("  ✗ UIBC not found in monitoring data")
        test3_pass = False

# CLEANUP
print("\n" + "="*80)
print("CLEANUP")
print("="*80)

print("\n--- Source files before cleanup ---")
files_before = get_source_files('2026-08')
if files_before:
    for f in files_before:
        print(f"  - {f.get('source_file')}: {f.get('tests')} tests")

# Delete test files
test_files = ['LIS_260831', 'LIS_260830', 'LIS_260803']
deleted_count = 0

for source_file in test_files:
    # Check if this file was created by us (not seed data)
    file_info = next((f for f in files_before if f.get('source_file') == source_file), None)
    if file_info:
        # Only delete if it's our test file
        # We can identify our files by checking if they were just created
        if delete_source_file(source_file):
            deleted_count += 1

print(f"\n✓ Deleted {deleted_count} test source files")

print("\n--- Source files after cleanup ---")
files_after = get_source_files('2026-08')
if files_after:
    for f in files_after:
        print(f"  - {f.get('source_file')}: {f.get('tests')} tests")

# Final verification
print("\n--- Final Monitoring State ---")
final_monitoring = get_monitoring(2026, 8)
if final_monitoring:
    rows = final_monitoring.get('rows', [])
    uibc = find_reagen_by_name(rows, 'UIBC')
    hematologi = find_reagen_by_name(rows, 'Hematologi')
    
    if uibc:
        print(f"\nUIBC final hari: {uibc.get('hari', {})}")
    if hematologi:
        print(f"Hematologi final hari: {hematologi.get('hari', {})}")

# Summary
print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80)

if test1_pass:
    print("✓ TEST 1 PASSED: Per-row Tanggal column works correctly")
else:
    print("✗ TEST 1 FAILED: Per-row Tanggal column has issues")

if test2_pass:
    print("✓ TEST 2 PASSED: Matrix day-columns still work (regression)")
else:
    print("✗ TEST 2 FAILED: Matrix day-columns broken (regression)")

if test3_pass:
    print("✓ TEST 3 PASSED: Single date from filename still works (regression)")
else:
    print("✗ TEST 3 FAILED: Single date from filename broken (regression)")

print("\n" + "="*80)
