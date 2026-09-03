"""Backend tests for /api/settings (LIS retention) and cleanup behavior."""
import os
import time
from datetime import datetime, timezone, timedelta

import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
API = f"{BASE_URL}/api"

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')


def _login(username, password):
    r = requests.post(f"{API}/auth/login", json={"username": username, "password": password}, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def koor_token():
    return _login("raihan", "rakhasivi123")


@pytest.fixture(scope="module")
def petugas_token():
    return _login("kalgen", "kalgen")


@pytest.fixture(scope="module")
def db():
    c = MongoClient(MONGO_URL)
    return c[DB_NAME]


# ---- GET /api/settings ----
class TestGetSettings:
    def test_get_settings_koordinator(self, koor_token):
        r = requests.get(f"{API}/settings", headers={"Authorization": f"Bearer {koor_token}"})
        assert r.status_code == 200
        data = r.json()
        assert data["lis_retention_days"] in (3, 7, 30)
        assert list(data["allowed_retention_days"]) == [3, 7, 30]
        assert "last_cleanup" in data

    def test_get_settings_petugas_allowed(self, petugas_token):
        r = requests.get(f"{API}/settings", headers={"Authorization": f"Bearer {petugas_token}"})
        assert r.status_code == 200

    def test_get_settings_unauth(self):
        r = requests.get(f"{API}/settings")
        assert r.status_code == 401


# ---- PUT /api/settings (RBAC + validation) ----
class TestPutSettings:
    def test_put_forbidden_for_petugas(self, petugas_token):
        r = requests.put(f"{API}/settings", json={"lis_retention_days": 3},
                         headers={"Authorization": f"Bearer {petugas_token}"})
        assert r.status_code == 403

    def test_put_invalid_value(self, koor_token):
        r = requests.put(f"{API}/settings", json={"lis_retention_days": 99},
                         headers={"Authorization": f"Bearer {koor_token}"})
        assert r.status_code == 400

    @pytest.mark.parametrize("val", [3, 7, 30])
    def test_put_valid_and_persist(self, koor_token, val):
        r = requests.put(f"{API}/settings", json={"lis_retention_days": val},
                         headers={"Authorization": f"Bearer {koor_token}"})
        assert r.status_code == 200
        assert r.json()["lis_retention_days"] == val
        # Verify persistence via GET
        g = requests.get(f"{API}/settings", headers={"Authorization": f"Bearer {koor_token}"})
        assert g.json()["lis_retention_days"] == val

    def test_reset_to_default_7(self, koor_token):
        r = requests.put(f"{API}/settings", json={"lis_retention_days": 7},
                         headers={"Authorization": f"Bearer {koor_token}"})
        assert r.status_code == 200


# ---- Auto-delete cleanup correctness (direct DB) ----
class TestRetentionCleanup:
    def test_existing_lis_raw_has_uploaded_at(self, db):
        """Backfill should have set uploaded_at on legacy docs at startup."""
        missing = db["lis_raw"].count_documents({"uploaded_at": {"$exists": False}})
        assert missing == 0, f"{missing} lis_raw docs still missing uploaded_at"

    def test_cleanup_deletes_old_preserves_new_and_leaves_usage_alone(self, db, koor_token):
        """Insert old & recent test rows, set retention=3, trigger cleanup, verify only old row deleted;
        also verify pemakaian_harian & stock_period untouched."""
        # Baseline counts
        pemakaian_before = db["pemakaian_harian"].count_documents({})
        stock_before = db["stock_period"].count_documents({})
        lis_before = db["lis_raw"].count_documents({})

        now = datetime.now(timezone.utc)
        old_iso = (now - timedelta(days=10)).isoformat()
        recent_iso = now.isoformat()
        test_marker = "TEST_RETENTION_MARKER"

        db["lis_raw"].insert_many([
            {"id": "TEST_OLD_1", "period": "2099-01", "nama_test": test_marker,
             "days": {}, "source_file": "TEST_RETENTION.xlsx", "uploaded_at": old_iso},
            {"id": "TEST_NEW_1", "period": "2099-01", "nama_test": test_marker,
             "days": {}, "source_file": "TEST_RETENTION.xlsx", "uploaded_at": recent_iso},
        ])

        # Set retention to 3
        r = requests.put(f"{API}/settings", json={"lis_retention_days": 3},
                         headers={"Authorization": f"Bearer {koor_token}"})
        assert r.status_code == 200

        # Trigger cleanup by importing the private function
        import asyncio
        import sys
        sys.path.insert(0, '/app/backend')
        from server import _run_lis_retention_cleanup

        deleted = asyncio.get_event_loop().run_until_complete(_run_lis_retention_cleanup()) \
            if False else asyncio.new_event_loop().run_until_complete(_run_lis_retention_cleanup())

        # Verify: old deleted, new preserved
        assert db["lis_raw"].find_one({"id": "TEST_OLD_1"}) is None
        assert db["lis_raw"].find_one({"id": "TEST_NEW_1"}) is not None

        # Verify pemakaian_harian & stock_period unaffected
        assert db["pemakaian_harian"].count_documents({}) == pemakaian_before
        assert db["stock_period"].count_documents({}) == stock_before

        # Cleanup: remove test row + reset retention
        db["lis_raw"].delete_many({"source_file": "TEST_RETENTION.xlsx"})
        requests.put(f"{API}/settings", json={"lis_retention_days": 7},
                     headers={"Authorization": f"Bearer {koor_token}"})

        # last_cleanup should appear in settings and import-log
        g = requests.get(f"{API}/settings", headers={"Authorization": f"Bearer {koor_token}"})
        lc = g.json().get("last_cleanup")
        assert lc is not None
        assert lc.get("type") == "lis_cleanup"

    def test_import_log_has_lis_cleanup_entries(self, koor_token):
        r = requests.get(f"{API}/import-log", headers={"Authorization": f"Bearer {koor_token}"})
        assert r.status_code == 200
        logs = r.json()
        cleanup_logs = [x for x in logs if x.get("type") == "lis_cleanup"]
        assert len(cleanup_logs) >= 1


# ---- Monitoring endpoint still healthy (regression) ----
class TestRegression:
    def test_monitoring_ok(self, koor_token):
        r = requests.get(f"{API}/monitoring?year=2025&month=1",
                         headers={"Authorization": f"Bearer {koor_token}"})
        assert r.status_code == 200

    def test_health(self):
        r = requests.get(f"{API}/health")
        assert r.status_code == 200
        assert r.json().get("seeded") is True

    def test_lis_raw_endpoint(self, koor_token):
        r = requests.get(f"{API}/lis/raw?limit=5",
                         headers={"Authorization": f"Bearer {koor_token}"})
        assert r.status_code == 200
        assert "items" in r.json()

    def test_users_list_koor(self, koor_token):
        r = requests.get(f"{API}/users", headers={"Authorization": f"Bearer {koor_token}"})
        assert r.status_code == 200

    def test_users_forbidden_petugas(self, petugas_token):
        r = requests.get(f"{API}/users", headers={"Authorization": f"Bearer {petugas_token}"})
        assert r.status_code == 403
