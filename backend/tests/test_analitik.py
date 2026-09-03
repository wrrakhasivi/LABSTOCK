"""Tests for GET /api/analitik/pemakaian (new Analitik feature)."""
import os
from datetime import date, timedelta

import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/') or \
    __import__('dotenv').dotenv_values('/app/frontend/.env').get('REACT_APP_BACKEND_URL', '').rstrip('/')

PETUGAS = {'username': 'kalgen', 'password': 'kalgen'}
KOORD = {'username': 'raihan', 'password': 'rakhasivi123'}


def _login(creds):
    r = requests.post(f'{BASE_URL}/api/auth/login', json=creds, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()['access_token']


@pytest.fixture(scope='module')
def petugas_token():
    return _login(PETUGAS)


@pytest.fixture(scope='module')
def koord_token():
    return _login(KOORD)


def _hdr(tok):
    return {'Authorization': f'Bearer {tok}'}


# ---- Auth ----
def test_requires_auth():
    r = requests.get(f'{BASE_URL}/api/analitik/pemakaian',
                     params={'start': '2026-08-01', 'end': '2026-09-30'}, timeout=15)
    assert r.status_code in (401, 403)


def test_petugas_can_access(petugas_token):
    r = requests.get(f'{BASE_URL}/api/analitik/pemakaian',
                     params={'start': '2026-08-01', 'end': '2026-09-30'},
                     headers=_hdr(petugas_token), timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    assert set(['start', 'end', 'trend', 'comparison']).issubset(data.keys())
    assert isinstance(data['trend'], list)
    assert isinstance(data['comparison'], list)
    assert len(data['comparison']) <= 10
    for c in data['comparison']:
        assert 'reagen_id' in c and 'nama_reagen' in c and 'jumlah' in c


def test_koordinator_can_access(koord_token):
    r = requests.get(f'{BASE_URL}/api/analitik/pemakaian',
                     params={'start': '2026-08-01', 'end': '2026-09-30'},
                     headers=_hdr(koord_token), timeout=20)
    assert r.status_code == 200


# ---- Validation ----
def test_start_after_end_returns_400(petugas_token):
    r = requests.get(f'{BASE_URL}/api/analitik/pemakaian',
                     params={'start': '2026-09-30', 'end': '2026-08-01'},
                     headers=_hdr(petugas_token), timeout=20)
    assert r.status_code == 400


def test_missing_params_returns_422(petugas_token):
    r = requests.get(f'{BASE_URL}/api/analitik/pemakaian',
                     headers=_hdr(petugas_token), timeout=20)
    assert r.status_code == 422


# ---- Empty range ----
def test_far_future_range_returns_empty_trend(petugas_token):
    r = requests.get(f'{BASE_URL}/api/analitik/pemakaian',
                     params={'start': '2099-01-01', 'end': '2099-01-31'},
                     headers=_hdr(petugas_token), timeout=20)
    assert r.status_code == 200
    d = r.json()
    assert d['trend'] == []
    assert d['comparison'] == []


# ---- reagen_id filter ----
def test_reagen_id_filters_trend_but_not_comparison(petugas_token):
    # Baseline (all reagens)
    r_all = requests.get(f'{BASE_URL}/api/analitik/pemakaian',
                        params={'start': '2026-07-01', 'end': '2026-09-30'},
                        headers=_hdr(petugas_token), timeout=20).json()
    if not r_all['comparison']:
        pytest.skip('No pemakaian data seeded in range')

    top_reagen_id = r_all['comparison'][0]['reagen_id']
    top_reagen_total = r_all['comparison'][0]['jumlah']

    r_filt = requests.get(f'{BASE_URL}/api/analitik/pemakaian',
                         params={'start': '2026-07-01', 'end': '2026-09-30',
                                 'reagen_id': top_reagen_id},
                         headers=_hdr(petugas_token), timeout=20).json()

    # Comparison is unaffected by reagen_id (same set of reagens & totals; ties may reorder)
    def _cmp_key(rows):
        return sorted([(c['reagen_id'], c['jumlah']) for c in rows])
    assert _cmp_key(r_filt['comparison']) == _cmp_key(r_all['comparison'])

    # Trend sum for that reagen equals its comparison total
    trend_sum = sum(t['jumlah'] for t in r_filt['trend'])
    assert trend_sum == top_reagen_total

    # Filtered trend total <= all-reagen trend total
    all_trend_sum = sum(t['jumlah'] for t in r_all['trend'])
    assert trend_sum <= all_trend_sum


def test_trend_sorted_ascending(petugas_token):
    r = requests.get(f'{BASE_URL}/api/analitik/pemakaian',
                     params={'start': '2026-07-01', 'end': '2026-09-30'},
                     headers=_hdr(petugas_token), timeout=20).json()
    dates = [t['date'] for t in r['trend']]
    assert dates == sorted(dates)


def test_comparison_sorted_desc(petugas_token):
    r = requests.get(f'{BASE_URL}/api/analitik/pemakaian',
                     params={'start': '2026-07-01', 'end': '2026-09-30'},
                     headers=_hdr(petugas_token), timeout=20).json()
    jumlahs = [c['jumlah'] for c in r['comparison']]
    assert jumlahs == sorted(jumlahs, reverse=True)


# ---- comparison_limit ----
@pytest.mark.parametrize('limit,expected_max', [(5, 5), (10, 10), (20, 20)])
def test_comparison_limit_respected(petugas_token, limit, expected_max):
    r = requests.get(f'{BASE_URL}/api/analitik/pemakaian',
                     params={'start': '2026-07-01', 'end': '2026-09-30',
                             'comparison_limit': limit},
                     headers=_hdr(petugas_token), timeout=20).json()
    assert len(r['comparison']) <= expected_max
    # For limit=5 with plenty seeded data expect exactly 5
    if limit == 5:
        assert len(r['comparison']) == 5


def test_invalid_comparison_limit_falls_back_to_10(petugas_token):
    r = requests.get(f'{BASE_URL}/api/analitik/pemakaian',
                     params={'start': '2026-07-01', 'end': '2026-09-30',
                             'comparison_limit': 7},
                     headers=_hdr(petugas_token), timeout=20).json()
    assert len(r['comparison']) <= 10


# ---- comparison_reagen_ids (custom) ----
def test_comparison_custom_ids_returns_exact_selection(petugas_token, koord_token):
    # get a couple reagen ids: one with usage, one without (obscure)
    base = requests.get(f'{BASE_URL}/api/analitik/pemakaian',
                        params={'start': '2026-07-01', 'end': '2026-09-30',
                                'comparison_limit': 20},
                        headers=_hdr(petugas_token), timeout=20).json()
    if len(base['comparison']) < 2:
        pytest.skip('not enough seeded data')
    used_id = base['comparison'][0]['reagen_id']

    # find a reagen id that is NOT in comparison list (likely no usage)
    all_reagen = requests.get(f'{BASE_URL}/api/reagen',
                              headers=_hdr(petugas_token), timeout=20).json()
    used_ids = {c['reagen_id'] for c in base['comparison']}
    obscure = next((r['id'] for r in all_reagen if r['id'] not in used_ids), None)
    if not obscure:
        pytest.skip('no obscure reagen available')

    ids_csv = f'{used_id},{obscure}'
    r = requests.get(f'{BASE_URL}/api/analitik/pemakaian',
                     params={'start': '2026-07-01', 'end': '2026-09-30',
                             'comparison_reagen_ids': ids_csv},
                     headers=_hdr(petugas_token), timeout=20).json()
    assert len(r['comparison']) == 2
    ret_ids = {c['reagen_id'] for c in r['comparison']}
    assert ret_ids == {used_id, obscure}
    # sorted desc by jumlah
    jumlahs = [c['jumlah'] for c in r['comparison']]
    assert jumlahs == sorted(jumlahs, reverse=True)
    # obscure reagen must be present (fill-zero behaviour); may or may not have data
    obscure_row = next(c for c in r['comparison'] if c['reagen_id'] == obscure)
    assert obscure_row['jumlah'] >= 0
    # verify at least one truly-zero fill by picking a fake id
    fake_id = 'nonexistent-reagen-id-xyz'
    r3 = requests.get(f'{BASE_URL}/api/analitik/pemakaian',
                      params={'start': '2026-07-01', 'end': '2026-09-30',
                              'comparison_reagen_ids': f'{used_id},{fake_id}'},
                      headers=_hdr(petugas_token), timeout=20).json()
    fake_row = next((c for c in r3['comparison'] if c['reagen_id'] == fake_id), None)
    assert fake_row is not None and fake_row['jumlah'] == 0

    # koordinator can also call (no RBAC restriction)
    r2 = requests.get(f'{BASE_URL}/api/analitik/pemakaian',
                      params={'start': '2026-07-01', 'end': '2026-09-30',
                              'comparison_reagen_ids': ids_csv},
                      headers=_hdr(koord_token), timeout=20)
    assert r2.status_code == 200


def test_comparison_custom_ignores_limit(petugas_token):
    base = requests.get(f'{BASE_URL}/api/analitik/pemakaian',
                        params={'start': '2026-07-01', 'end': '2026-09-30',
                                'comparison_limit': 20},
                        headers=_hdr(petugas_token), timeout=20).json()
    if len(base['comparison']) < 3:
        pytest.skip('not enough seeded data')
    ids = [c['reagen_id'] for c in base['comparison'][:3]]
    r = requests.get(f'{BASE_URL}/api/analitik/pemakaian',
                     params={'start': '2026-07-01', 'end': '2026-09-30',
                             'comparison_limit': 5,
                             'comparison_reagen_ids': ','.join(ids)},
                     headers=_hdr(petugas_token), timeout=20).json()
    # custom takes precedence: exactly 3 rows even though limit=5
    assert len(r['comparison']) == 3
