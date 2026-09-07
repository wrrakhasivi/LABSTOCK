"""Backend tests for the 3 new features:
1) DELETE /api/mapping-tests/{id} - hapus pemetaan + persist to seed_data.json
2) GET /api/notifikasi/whatsapp/jadwal - jadwal info
3) GET /api/notifikasi/whatsapp/preview - message contains '(sudah PRF)' when a PRF exists
Plus regression on mapping add/edit and general reads.
"""
import json
import os
from pathlib import Path
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://lets-preview-4.preview.emergentagent.com').rstrip('/')
SEED_FILE = Path('/app/backend/seed/seed_data.json')


@pytest.fixture(scope='module')
def s():
    sess = requests.Session()
    sess.headers.update({'Content-Type': 'application/json'})
    return sess


# ---------- Basic health ----------
def test_health(s):
    r = s.get(f'{BASE_URL}/api/health', timeout=15)
    assert r.status_code == 200
    assert r.json().get('status') == 'ok'


# ---------- Jadwal endpoint ----------
def test_wa_jadwal_shape(s):
    r = s.get(f'{BASE_URL}/api/notifikasi/whatsapp/jadwal', timeout=15)
    assert r.status_code == 200
    d = r.json()
    for k in ('enabled', 'jam', 'timezone', 'sudah_terkirim_hari_ini'):
        assert k in d, f'missing key {k}'
    assert d['jam'] == '07:00'
    assert 'Asia/Jakarta' in d['timezone']
    assert 'WIB' in d['timezone']
    assert isinstance(d['enabled'], bool)


# ---------- DELETE mapping + regression add ----------
def test_mapping_add_then_delete_persists_to_seed(s):
    lis_name = 'TEST_MAPPING_DEL_XYZ'

    # Cleanup any prior residue
    lst = s.get(f'{BASE_URL}/api/mapping-tests', timeout=15).json()
    for m in lst['items']:
        if (m.get('lis_name') or '').lower() == lis_name.lower():
            s.delete(f"{BASE_URL}/api/mapping-tests/{m['id']}", timeout=15)

    # CREATE mapping (no reagen_name -> TIDAK ADA)
    r = s.post(f'{BASE_URL}/api/mapping-tests',
               json={'lis_name': lis_name}, timeout=15)
    assert r.status_code == 201, r.text
    created = r.json()
    mid = created['id']
    assert created['lis_name'] == lis_name
    assert created['status'] == 'TIDAK ADA'

    # Verify present in seed_data.json
    seed = json.loads(SEED_FILE.read_text())
    assert any((m.get('lis_name') or '').lower() == lis_name.lower()
               for m in seed.get('Mapping_Test', [])), 'not persisted after create'

    # Verify GET returns it
    lst = s.get(f'{BASE_URL}/api/mapping-tests', timeout=15).json()
    assert any(m['id'] == mid for m in lst['items'])

    # DELETE
    r = s.delete(f'{BASE_URL}/api/mapping-tests/{mid}', timeout=15)
    assert r.status_code == 200, r.text
    assert r.json().get('ok') is True

    # DELETE again should 404
    r2 = s.delete(f'{BASE_URL}/api/mapping-tests/{mid}', timeout=15)
    assert r2.status_code == 404

    # Verify removed from GET
    lst = s.get(f'{BASE_URL}/api/mapping-tests', timeout=15).json()
    assert not any(m['id'] == mid for m in lst['items'])

    # Verify removed from seed_data.json
    seed = json.loads(SEED_FILE.read_text())
    assert not any((m.get('lis_name') or '').lower() == lis_name.lower()
                   for m in seed.get('Mapping_Test', [])), 'not removed from seed_data.json'


# ---------- Update mapping regression ----------
def test_mapping_update_regression(s):
    lst = s.get(f'{BASE_URL}/api/mapping-tests?status=OK', timeout=15).json()
    assert lst['items'], 'expected some OK mappings'
    m = lst['items'][0]
    original = m['reagen_name']
    r = s.put(f"{BASE_URL}/api/mapping-tests/{m['id']}",
              json={'reagen_name': original, 'status': 'OK'}, timeout=15)
    assert r.status_code == 200, r.text


# ---------- WhatsApp preview with '(sudah PRF)' ----------
def test_wa_preview_sudah_prf_suffix(s):
    # Find a period with critical/warning reagen
    picked = None
    for y, m in [(2026, 8), (2026, 7)]:
        mon = s.get(f'{BASE_URL}/api/monitoring',
                    params={'year': y, 'month': m}, timeout=30).json()
        for row in mon['rows']:
            if row['status'] in ('critical', 'warning'):
                picked = (y, m, row)
                break
        if picked:
            break
    assert picked, 'no critical/warning reagen found to test'
    year, month, row = picked
    reagen_id = row['reagen_id']
    reagen_name = row['nama_reagen']

    # Preview BEFORE creating PRF - check that this reagen line does NOT have (sudah PRF)
    # (unless a PRF already exists for it in this period)
    r = s.get(f'{BASE_URL}/api/notifikasi/whatsapp/preview',
              params={'year': year, 'month': month}, timeout=30)
    assert r.status_code == 200
    before_msg = r.json()['message']
    has_prf_before = f'{reagen_name}:' in before_msg and '(sudah PRF)' in _line_for(before_msg, reagen_name)

    # Create PRF
    tanggal = f'{year}-{month:02d}-15'
    created = None
    if not has_prf_before:
        pr = s.post(f'{BASE_URL}/api/prf',
                    json={'reagen_id': reagen_id, 'reagent_no': 1, 'kits': 1,
                          'tanggal_pr': tanggal, 'note': 'TEST_SUDAH_PRF'},
                    timeout=15)
        assert pr.status_code == 200, pr.text
        created = pr.json()

    try:
        r = s.get(f'{BASE_URL}/api/notifikasi/whatsapp/preview',
                  params={'year': year, 'month': month}, timeout=30)
        assert r.status_code == 200
        msg = r.json()['message']
        line = _line_for(msg, reagen_name)
        assert line, f'reagen name {reagen_name} not found in preview message'
        assert '(sudah PRF)' in line, f'expected (sudah PRF) suffix in line: {line!r}'
    finally:
        if created:
            s.delete(f"{BASE_URL}/api/prf/{created['id']}", timeout=15)


def _line_for(msg, reagen_name):
    for ln in msg.splitlines():
        if reagen_name and reagen_name in ln:
            return ln
    return ''


# ---------- Preview no-suffix check ----------
def test_wa_preview_no_prf_no_suffix(s):
    """A critical/warning reagen without PRF in the period should NOT have (sudah PRF)."""
    for y, m in [(2026, 8), (2026, 7)]:
        mon = s.get(f'{BASE_URL}/api/monitoring',
                    params={'year': y, 'month': m}, timeout=30).json()
        # find a critical/warning reagen with empty prf list
        target = None
        for row in mon['rows']:
            if row['status'] in ('critical', 'warning') and not row.get('prf'):
                target = row
                break
        if not target:
            continue
        r = s.get(f'{BASE_URL}/api/notifikasi/whatsapp/preview',
                  params={'year': y, 'month': m}, timeout=30)
        msg = r.json()['message']
        line = _line_for(msg, target['nama_reagen'])
        assert line, f'reagen {target["nama_reagen"]} not in preview'
        assert '(sudah PRF)' not in line, f'unexpected (sudah PRF) in {line!r}'
        return
    pytest.skip('no critical/warning reagen without PRF found to assert negative case')
