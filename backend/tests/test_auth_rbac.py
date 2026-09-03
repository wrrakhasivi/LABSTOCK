"""Tests for JWT auth + role-based access control (Petugas vs Koordinator)."""
import os
import pytest
import requests

BASE_URL = os.environ['REACT_APP_BACKEND_URL'].rstrip('/')


@pytest.fixture(scope='module')
def petugas_token():
    r = requests.post(f'{BASE_URL}/api/auth/login',
                      json={'username': 'kalgen', 'password': 'kalgen'}, timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d['role'] == 'petugas'
    assert d['username'] == 'kalgen'
    assert isinstance(d.get('access_token'), str) and len(d['access_token']) > 10
    return d['access_token']


@pytest.fixture(scope='module')
def koord_token():
    r = requests.post(f'{BASE_URL}/api/auth/login',
                      json={'username': 'raihan', 'password': 'rakhasivi123'}, timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d['role'] == 'koordinator'
    return d['access_token']


def _h(tok):
    return {'Authorization': f'Bearer {tok}', 'Content-Type': 'application/json'}


# ---------- Login flows ----------
def test_login_wrong_password():
    r = requests.post(f'{BASE_URL}/api/auth/login',
                      json={'username': 'kalgen', 'password': 'salah'}, timeout=15)
    assert r.status_code in (400, 401)


def test_login_unknown_user():
    r = requests.post(f'{BASE_URL}/api/auth/login',
                      json={'username': 'ghost', 'password': 'x'}, timeout=15)
    assert r.status_code in (400, 401)


def test_public_endpoints_no_auth():
    r = requests.get(f'{BASE_URL}/api/health', timeout=15)
    assert r.status_code == 200
    r = requests.get(f'{BASE_URL}/api/', timeout=15)
    assert r.status_code == 200


def test_protected_endpoint_no_token_returns_401():
    for path in ['/api/reagen', '/api/mapping-tests', '/api/prf', '/api/penerimaan',
                 '/api/auth/me', '/api/notifikasi/whatsapp/jadwal']:
        r = requests.get(f'{BASE_URL}{path}', timeout=15)
        assert r.status_code == 401, f'{path} expected 401 got {r.status_code}'


def test_invalid_token_returns_401():
    r = requests.get(f'{BASE_URL}/api/reagen',
                     headers={'Authorization': 'Bearer garbage.token.here'}, timeout=15)
    assert r.status_code == 401


def test_auth_me(petugas_token, koord_token):
    r = requests.get(f'{BASE_URL}/api/auth/me', headers=_h(petugas_token), timeout=15)
    assert r.status_code == 200
    assert r.json()['role'] == 'petugas'
    r = requests.get(f'{BASE_URL}/api/auth/me', headers=_h(koord_token), timeout=15)
    assert r.status_code == 200
    assert r.json()['role'] == 'koordinator'


# ---------- Petugas GETs work ----------
@pytest.mark.parametrize('path', [
    '/api/reagen',
    '/api/mapping-tests',
    '/api/prf',
    '/api/penerimaan',
    '/api/notifikasi/whatsapp/jadwal',
    '/api/meta/periods',
])
def test_petugas_can_read(petugas_token, path):
    r = requests.get(f'{BASE_URL}{path}', headers=_h(petugas_token), timeout=15)
    assert r.status_code == 200, f'{path}: {r.status_code} {r.text[:150]}'


def test_petugas_can_read_monitoring(petugas_token):
    r = requests.get(f'{BASE_URL}/api/monitoring',
                     params={'year': 2026, 'month': 8},
                     headers=_h(petugas_token), timeout=30)
    assert r.status_code == 200


# ---------- Petugas mutations all return 403 ----------
KOORD_ONLY_MSG = 'Aksi ini hanya dapat dilakukan oleh Koordinator.'


def _assert_403_msg(r):
    assert r.status_code == 403, f'expected 403 got {r.status_code}: {r.text[:200]}'
    body = r.json()
    detail = body.get('detail', '')
    assert KOORD_ONLY_MSG in detail, f'unexpected detail: {detail}'


def test_petugas_cannot_create_mapping(petugas_token):
    r = requests.post(f'{BASE_URL}/api/mapping-tests',
                      json={'lis_name': 'TEST_RBAC_FORBIDDEN'},
                      headers=_h(petugas_token), timeout=15)
    _assert_403_msg(r)


def test_petugas_cannot_delete_mapping(petugas_token):
    r = requests.delete(f'{BASE_URL}/api/mapping-tests/nonexistent-id',
                        headers=_h(petugas_token), timeout=15)
    _assert_403_msg(r)


def test_petugas_cannot_update_mapping(petugas_token):
    r = requests.put(f'{BASE_URL}/api/mapping-tests/nonexistent-id',
                     json={'reagen_name': 'x', 'status': 'OK'},
                     headers=_h(petugas_token), timeout=15)
    _assert_403_msg(r)


def test_petugas_cannot_delete_periode(petugas_token):
    r = requests.delete(f'{BASE_URL}/api/monitoring/periode',
                        params={'year': 2026, 'month': 8},
                        headers=_h(petugas_token), timeout=15)
    _assert_403_msg(r)


def test_petugas_cannot_create_prf(petugas_token):
    r = requests.post(f'{BASE_URL}/api/prf',
                      json={'reagen_id': 'x', 'reagent_no': 1, 'kits': 1,
                            'tanggal_pr': '2026-08-15'},
                      headers=_h(petugas_token), timeout=15)
    _assert_403_msg(r)


def test_petugas_cannot_update_reagen(petugas_token):
    # first get any reagen id via koordinator? actually GET is public to petugas
    lst = requests.get(f'{BASE_URL}/api/reagen', headers=_h(petugas_token), timeout=15).json()
    items = lst['items'] if isinstance(lst, dict) else lst
    if not items:
        pytest.skip('no reagen')
    rid = items[0]['id']
    r = requests.put(f'{BASE_URL}/api/reagen/{rid}',
                     json={'nama_reagen': items[0].get('nama_reagen', 'x')},
                     headers=_h(petugas_token), timeout=15)
    _assert_403_msg(r)


def test_petugas_cannot_send_whatsapp(petugas_token):
    r = requests.post(f'{BASE_URL}/api/notifikasi/whatsapp',
                      json={'year': 2026, 'month': 8},
                      headers=_h(petugas_token), timeout=15)
    _assert_403_msg(r)


def test_petugas_cannot_set_qc(petugas_token):
    r = requests.put(f'{BASE_URL}/api/monitoring/qc',
                     json={'reagen_id': 'x', 'year': 2026, 'month': 8, 'day': 1, 'value': 1},
                     headers=_h(petugas_token), timeout=15)
    _assert_403_msg(r)


def test_petugas_cannot_set_saldo_awal(petugas_token):
    r = requests.put(f'{BASE_URL}/api/monitoring/saldo-awal',
                     json={'reagen_id': 'x', 'year': 2026, 'month': 8, 'reagent_no': 1, 'value': 1},
                     headers=_h(petugas_token), timeout=15)
    _assert_403_msg(r)


# ---------- Koordinator can mutate: create+delete mapping full flow ----------
def test_koord_full_mapping_flow(koord_token):
    name = 'TEST_RBAC_KOORD_OK'
    # cleanup any residue
    lst = requests.get(f'{BASE_URL}/api/mapping-tests', headers=_h(koord_token), timeout=15).json()
    for m in lst['items']:
        if (m.get('lis_name') or '').lower() == name.lower():
            requests.delete(f"{BASE_URL}/api/mapping-tests/{m['id']}", headers=_h(koord_token), timeout=15)

    r = requests.post(f'{BASE_URL}/api/mapping-tests',
                      json={'lis_name': name}, headers=_h(koord_token), timeout=15)
    assert r.status_code == 201, r.text
    mid = r.json()['id']
    try:
        r = requests.put(f'{BASE_URL}/api/mapping-tests/{mid}',
                         json={'reagen_name': None, 'status': 'TIDAK ADA'},
                         headers=_h(koord_token), timeout=15)
        assert r.status_code == 200
    finally:
        r = requests.delete(f'{BASE_URL}/api/mapping-tests/{mid}',
                            headers=_h(koord_token), timeout=15)
        assert r.status_code == 200


# ---------- Regression: previously-tested features still work under Koordinator ----------
def test_regression_wa_jadwal(koord_token):
    r = requests.get(f'{BASE_URL}/api/notifikasi/whatsapp/jadwal',
                     headers=_h(koord_token), timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert d['jam'] == '07:00'
    assert 'WIB' in d['timezone']


def test_regression_wa_preview_sudah_prf(koord_token):
    """Quick sanity: WhatsApp preview endpoint still works under koordinator token."""
    r = requests.get(f'{BASE_URL}/api/notifikasi/whatsapp/preview',
                     params={'year': 2026, 'month': 8},
                     headers=_h(koord_token), timeout=30)
    assert r.status_code == 200
    assert 'message' in r.json()
