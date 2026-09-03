"""Security fixes regression tests (SEC-001..SEC-004)."""
import io
import os
import time
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://stock-status-5.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"


def _login(u, p):
    r = requests.post(f"{API}/auth/login", json={"username": u, "password": p}, timeout=15)
    return r


def _koor_headers():
    r = _login("raihan", "rakhasivi123")
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ---------- SEC-001: seed_accounts must not overwrite existing passwords ----------
class TestSEC001SeedIdempotent:
    def test_original_credentials_still_work(self):
        assert _login("raihan", "rakhasivi123").status_code == 200
        assert _login("kalgen", "kalgen").status_code == 200

    def test_change_password_persists_across_uses(self):
        # Create throwaway user
        h = _koor_headers()
        uname = f"sectest_{int(time.time())}"
        r = requests.post(f"{API}/users",
                          json={"username": uname, "password": "oldpass", "role": "petugas"},
                          headers=h, timeout=15)
        assert r.status_code == 201, r.text
        try:
            # login old, change password
            tok_old = _login(uname, "oldpass").json()["access_token"]
            r = requests.post(f"{API}/auth/change-password",
                              json={"current_password": "oldpass", "new_password": "newpass"},
                              headers={"Authorization": f"Bearer {tok_old}"}, timeout=15)
            assert r.status_code == 200
            # New password works, old does not
            assert _login(uname, "newpass").status_code == 200
            assert _login(uname, "oldpass").status_code == 401
        finally:
            requests.delete(f"{API}/users/{uname}", headers=h, timeout=15)


# ---------- SEC-002: token_version invalidates old sessions ----------
class TestSEC002TokenVersion:
    def test_change_password_invalidates_old_token(self):
        h = _koor_headers()
        uname = f"sectest_{int(time.time())}_a"
        requests.post(f"{API}/users",
                      json={"username": uname, "password": "oldpass", "role": "petugas"},
                      headers=h, timeout=15)
        try:
            tok_old = _login(uname, "oldpass").json()["access_token"]
            old_h = {"Authorization": f"Bearer {tok_old}"}
            # works before change
            assert requests.get(f"{API}/auth/me", headers=old_h).status_code == 200
            # change pwd
            requests.post(f"{API}/auth/change-password",
                          json={"current_password": "oldpass", "new_password": "newpass"},
                          headers=old_h, timeout=15)
            # old token dead
            r = requests.get(f"{API}/auth/me", headers=old_h)
            assert r.status_code == 401, r.text
            # new token alive
            tok_new = _login(uname, "newpass").json()["access_token"]
            assert requests.get(f"{API}/auth/me",
                                headers={"Authorization": f"Bearer {tok_new}"}).status_code == 200
        finally:
            requests.delete(f"{API}/users/{uname}", headers=h, timeout=15)

    def test_delete_user_invalidates_token(self):
        h = _koor_headers()
        uname = f"sectest_{int(time.time())}_b"
        requests.post(f"{API}/users",
                      json={"username": uname, "password": "pass", "role": "petugas"},
                      headers=h, timeout=15)
        tok = _login(uname, "pass").json()["access_token"]
        old_h = {"Authorization": f"Bearer {tok}"}
        assert requests.get(f"{API}/auth/me", headers=old_h).status_code == 200
        requests.delete(f"{API}/users/{uname}", headers=h, timeout=15)
        r = requests.get(f"{API}/auth/me", headers=old_h)
        assert r.status_code == 401


# ---------- SEC-003: ReDoS-safe reagen search ----------
class TestSEC003ReagenSearchEscape:
    def test_normal_search_works(self):
        h = _koor_headers()
        r = requests.get(f"{API}/reagen", params={"query": "a"}, headers=h, timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_special_chars_no_crash_and_fast(self):
        h = _koor_headers()
        for q in [".", "*", "+", "(", ")", ".*", "(.*)+", "a" * 500]:
            t0 = time.time()
            r = requests.get(f"{API}/reagen", params={"query": q}, headers=h, timeout=10)
            elapsed = time.time() - t0
            assert r.status_code == 200, f"failed on {q!r}: {r.text}"
            assert elapsed < 3, f"too slow ({elapsed:.2f}s) for {q!r}"


# ---------- SEC-004: LIS import size/count limits ----------
class TestSEC004LisImportLimits:
    def test_oversize_file_rejected(self):
        h = _koor_headers()
        big = io.BytesIO(b"x" * (11 * 1024 * 1024))  # 11MB
        files = {"files": ("big.xlsx", big, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        r = requests.post(f"{API}/lis/import", files=files, headers=h, timeout=30)
        assert r.status_code == 400
        assert "melebihi" in r.text.lower() or "10mb" in r.text.lower()

    def test_wrong_extension_rejected(self):
        h = _koor_headers()
        files = {"files": ("bad.txt", io.BytesIO(b"hi"), "text/plain")}
        r = requests.post(f"{API}/lis/import", files=files, headers=h, timeout=15)
        assert r.status_code == 400


# ---------- General regression: basic endpoints reachable ----------
class TestRegressionEndpoints:
    def test_health(self):
        assert requests.get(f"{API}/health").status_code == 200

    def test_petugas_rbac_denied_on_write(self):
        r = _login("kalgen", "kalgen")
        assert r.status_code == 200
        tok = r.json()["access_token"]
        h = {"Authorization": f"Bearer {tok}"}
        # write endpoint denied
        r2 = requests.post(f"{API}/reagen", json={"nama_reagen": "TEST_x"}, headers=h, timeout=15)
        assert r2.status_code == 403
        # read endpoints OK
        for ep in ["/monitoring?year=2026&month=1", "/reagen", "/prf", "/penerimaan",
                   "/mapping-tests", "/notifikasi/whatsapp/jadwal"]:
            r3 = requests.get(f"{API}{ep}", headers=h, timeout=15)
            assert r3.status_code == 200, f"{ep}: {r3.status_code} {r3.text[:200]}"

    def test_koordinator_can_read_all(self):
        h = _koor_headers()
        for ep in ["/users", "/monitoring?year=2026&month=1", "/reagen",
                   "/prf", "/penerimaan", "/mapping-tests"]:
            r = requests.get(f"{API}{ep}", headers=h, timeout=15)
            assert r.status_code == 200, f"{ep}: {r.status_code}"
