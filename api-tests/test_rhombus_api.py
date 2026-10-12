"""API tests for Rhombus AI (read-only).

Needs two values in .env at the repo root (never commit them):
  RHOMBUS_AUTHORIZATION = the full Authorization header from DevTools ("Bearer ...")
  RHOMBUS_ORG_ID        = the x-org-id header from DevTools
The token expires after a while, so copy a fresh one before running.

Run: pytest api-tests -v
"""
import os

import pytest
import requests
from dotenv import load_dotenv

load_dotenv()

BASE = "https://api.rhombusai.com/api"
PROJECT_ID = 5325
SCHEDULE_ID = 280
EXECUTIONS_URL = f"{BASE}/dataset/analyzer/v2/projects/{PROJECT_ID}/pipeline/schedules/{SCHEDULE_ID}/executions"
TIMEOUT = 15
KNOWN_RUN_IDS = {17842, 17936, 17965, 17970}  # runs recorded during testing


class HiddenHeaders(dict):
    """Headers that never print their values, so tokens cannot leak into test output."""

    def __repr__(self):
        return "{headers hidden}"


@pytest.fixture(scope="session")
def org_headers():
    org = os.getenv("RHOMBUS_ORG_ID")
    if not org:
        pytest.skip("RHOMBUS_ORG_ID is not set in .env")
    return HiddenHeaders({"x-org-id": org, "Accept": "application/json"})


@pytest.fixture(scope="session")
def auth_headers(org_headers):
    token = os.getenv("RHOMBUS_AUTHORIZATION")
    if not token:
        pytest.skip("RHOMBUS_AUTHORIZATION is not set in .env")
    return HiddenHeaders({**org_headers, "Authorization": token})


def test_executions_list_contains_our_runs(auth_headers):
    r = requests.get(EXECUTIONS_URL, headers=auth_headers,
                     params={"page": 1, "page_size": 20}, timeout=TIMEOUT)
    assert r.status_code == 200, r.text[:300]
    assert r.headers["content-type"].startswith("application/json")
    body = r.json()
    runs = body["executions"]
    ids = [run["id"] for run in runs]
    assert body["page"] == 1 and body["page_size"] == 20
    assert len(runs) == min(body["total"], 20)
    assert KNOWN_RUN_IDS <= set(ids), f"missing runs: {KNOWN_RUN_IDS - set(ids)}"
    assert all(run["project_id"] == PROJECT_ID for run in runs)
    assert all(run["schedule_id"] == SCHEDULE_ID for run in runs)
    assert ids == sorted(ids, reverse=True), "runs should be newest first"


def test_executions_without_token_is_refused(org_headers):
    r = requests.get(EXECUTIONS_URL, headers=org_headers, timeout=TIMEOUT)
    assert r.status_code in (401, 403), f"got {r.status_code}"
    assert "executions" not in r.text


def test_executions_with_fake_token_is_refused(org_headers):
    headers = {**org_headers, "Authorization": "Bearer not-a-real-token"}
    r = requests.get(EXECUTIONS_URL, headers=headers, timeout=TIMEOUT)
    assert r.status_code in (401, 403), f"got {r.status_code}"
    assert "executions" not in r.text


@pytest.mark.xfail(strict=True, reason="Known bug (12 Oct 2026): page_size=-1 returns HTTP 500 (HTML error page) instead of a 4xx")
def test_negative_page_size_is_rejected(auth_headers):
    r = requests.get(EXECUTIONS_URL, headers=auth_headers,
                     params={"page": 1, "page_size": -1}, timeout=TIMEOUT)
    assert 400 <= r.status_code < 500, f"got {r.status_code}: {r.text[:200]}"
