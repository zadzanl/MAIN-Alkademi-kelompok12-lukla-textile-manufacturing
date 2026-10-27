"""
Contract tests for the Sampling & Spec R&D API.

Purpose: pin the request/response contract of every endpoint in
src/api/routes.py so the frontend can be refactored (transport layer, adapters)
without silently drifting from the backend.

Scope: 33 endpoints — happy path plus the 400/404 error paths that the
frontend actually depends on. These are the regression net for the frontend
integration work (see plan FASE -1).

Run:  pytest -q        (from the backend/ directory)
"""

from __future__ import annotations

from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.main import app

PREFIX = "/api/sampling-spec-rnd"
TENANT = "tenant-001"


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        login = test_client.post(
            "/api/auth/login",
            json={"identifier": "ADMIN-IT", "password": "Admin#12345"},
        )
        assert login.status_code == 200, login.text
        test_client.headers.update(
            {"Authorization": f"Bearer {login.json()['accessToken']}"}
        )
        yield test_client


# ─── Helpers ────────────────────────────────────────────────────────────────


def _create_study(client: TestClient) -> str:
    response = client.post(
        f"{PREFIX}/studies/create",
        params={
            "tenant_id": TENANT,
            "process_id": "PROC-CT",
            "process_name": "Jahit Kerah",
            "operator_id": "OPR-CT",
            "target_sample_size": 5,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["study_id"]


def _create_spec(client: TestClient) -> str:
    response = client.post(
        f"{PREFIX}/specs/create",
        params={
            "tenant_id": TENANT,
            "spec_id": "SPEC-CT",
            "spec_name": "Kaos CT",
            "created_by": "tester",
            "version_number": "1.0.0",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["version_id"]


def _create_sample_version(client: TestClient, article_id: str) -> str:
    response = client.post(
        f"{PREFIX}/sample-versions/create",
        params={
            "tenant_id": TENANT,
            "article_id": article_id,
            "article_name": "Artikel CT",
            "created_by": "tester",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["version_id"]


# ─── Health & workflow ──────────────────────────────────────────────────────


def test_health(client: TestClient) -> None:
    response = client.get(f"{PREFIX}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_workflow_summary(client: TestClient) -> None:
    response = client.get(f"{PREFIX}/workflow/summary", params={"tenant_id": TENANT})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert {"active_studies", "completed_studies", "total_sample_versions"} <= set(body["summary"])


# ─── Time study ─────────────────────────────────────────────────────────────


def test_time_study_lifecycle(client: TestClient) -> None:
    study_id = _create_study(client)

    listing = client.get(f"{PREFIX}/studies/all", params={"tenant_id": TENANT})
    assert listing.status_code == 200
    assert listing.json()["success"] is True

    assert client.post(f"{PREFIX}/studies/{study_id}/start").status_code == 200

    for cycle_time in (3500, 3200, 3800):
        response = client.post(
            f"{PREFIX}/studies/{study_id}/add-sample",
            params={"cycle_time_ms": cycle_time, "element_name": "Kerah"},
        )
        assert response.status_code == 200, response.text

    stats = client.get(f"{PREFIX}/studies/{study_id}/stats")
    assert stats.status_code == 200
    assert stats.json()["statistics"]["total_samples"] == 3

    assert client.post(f"{PREFIX}/studies/{study_id}/pause").status_code == 200
    assert client.post(f"{PREFIX}/studies/{study_id}/resume").status_code == 200
    assert client.post(f"{PREFIX}/studies/{study_id}/complete").status_code == 200

    data = client.get(f"{PREFIX}/studies/{study_id}/data")
    assert data.status_code == 200
    assert data.json()["data"]["status"] == "completed"


def test_time_study_error_paths(client: TestClient) -> None:
    # Unknown study on a mutation -> 400 (service returns "Study not found").
    assert client.post(f"{PREFIX}/studies/does-not-exist/start").status_code == 400

    # add-sample on a draft study must be rejected (only in_progress allowed).
    study_id = _create_study(client)
    response = client.post(
        f"{PREFIX}/studies/{study_id}/add-sample",
        params={"cycle_time_ms": 3000},
    )
    assert response.status_code == 400

    # Unknown study on a read -> 404.
    assert client.get(f"{PREFIX}/studies/does-not-exist/data").status_code == 404
    assert client.get(f"{PREFIX}/studies/does-not-exist/stats").status_code == 404

    # stats for a study with no samples returns the full zeroed shape (not a
    # bare {"status": "no_samples"}), so the UI can render without null checks.
    empty_stats = client.get(f"{PREFIX}/studies/{study_id}/stats")
    assert empty_stats.status_code == 200
    stats_body = empty_stats.json()["statistics"]
    assert stats_body["status"] == "no_samples"
    assert stats_body["total_samples"] == 0
    assert stats_body["mean_cycle_time_ms"] == 0.0


# ─── Spec version ───────────────────────────────────────────────────────────


def test_spec_lifecycle(client: TestClient) -> None:
    version_id = _create_spec(client)

    listing = client.get(f"{PREFIX}/specs/all", params={"tenant_id": TENANT})
    assert listing.status_code == 200
    assert listing.json()["success"] is True

    change = client.post(
        f"{PREFIX}/specs/{version_id}/record-change",
        params={
            "change_type": "TOLERANCE_CHANGE",
            "parameter_name": "Lebar",
            "old_value": "150",
            "new_value": "152",
            "changed_by": "tester",
        },
    )
    assert change.status_code == 200, change.text

    drift = client.post(
        f"{PREFIX}/specs/{version_id}/record-drift",
        params={
            "parameter_name": "Lebar",
            "specification_limit": 152,
            "measured_value": 160,
            "severity": "high",
        },
    )
    assert drift.status_code == 200, drift.text

    report = client.get(f"{PREFIX}/specs/{version_id}/drift-report")
    assert report.status_code == 200
    drifts = report.json()["report"]["drifts"]
    assert len(drifts) == 1
    drift_id = drifts[0]["drift_id"]

    resolve = client.post(
        f"{PREFIX}/specs/{version_id}/resolve-drift/{drift_id}",
        params={"corrective_action": "Kalibrasi mesin"},
    )
    assert resolve.status_code == 200, resolve.text

    analysis = client.get(f"{PREFIX}/specs/{version_id}/drift-analysis")
    assert analysis.status_code == 200
    assert "risk_score" in analysis.json()

    history = client.get(f"{PREFIX}/specs/{version_id}/change-history")
    assert history.status_code == 200

    assert (
        client.post(
            f"{PREFIX}/specs/{version_id}/submit-review",
            params={"reviewer_id": "rev-1"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"{PREFIX}/specs/{version_id}/approve",
            params={"approver_id": "mgr-1"},
        ).status_code
        == 200
    )
    assert client.post(f"{PREFIX}/specs/{version_id}/activate").status_code == 200

    data = client.get(f"{PREFIX}/specs/{version_id}/data")
    assert data.status_code == 200
    assert data.json()["data"]["status"] == "active"


def test_spec_error_paths(client: TestClient) -> None:
    assert client.get(f"{PREFIX}/specs/does-not-exist/data").status_code == 404
    assert client.get(f"{PREFIX}/specs/does-not-exist/drift-report").status_code == 404
    assert client.get(f"{PREFIX}/specs/does-not-exist/drift-analysis").status_code == 404
    assert client.get(f"{PREFIX}/specs/does-not-exist/change-history").status_code == 404

    version_id = _create_spec(client)

    invalid_change = client.post(
        f"{PREFIX}/specs/{version_id}/record-change",
        params={
            "change_type": "NOT_A_TYPE",
            "parameter_name": "x",
            "old_value": "1",
            "new_value": "2",
            "changed_by": "tester",
        },
    )
    assert invalid_change.status_code == 400

    # approve before submit-review (still draft) must be rejected.
    approve_draft = client.post(
        f"{PREFIX}/specs/{version_id}/approve",
        params={"approver_id": "mgr"},
    )
    assert approve_draft.status_code == 400


# ─── Sample versions ────────────────────────────────────────────────────────


def test_sample_version_lifecycle(client: TestClient) -> None:
    article_id = f"ART-FLOW-{uuid4()}"
    version_id = _create_sample_version(client, article_id)

    listing = client.get(f"{PREFIX}/sample-versions/all", params={"tenant_id": TENANT})
    assert listing.status_code == 200
    assert listing.json()["success"] is True

    detail = client.get(f"{PREFIX}/sample-versions/{version_id}")
    assert detail.status_code == 200
    assert detail.json()["data"]["version_label"] == "v1"

    history = client.get(
        f"{PREFIX}/sample-versions/article/{article_id}/history",
        params={"tenant_id": TENANT},
    )
    assert history.status_code == 200
    assert history.json()["total_versions"] >= 1

    components = client.put(
        f"{PREFIX}/sample-versions/{version_id}/components",
        params={"updated_by": "tester"},
        json={"components": [{"component_id": "c1", "part_name": "Kerah"}]},
    )
    assert components.status_code == 200, components.text

    materials = client.put(
        f"{PREFIX}/sample-versions/{version_id}/materials",
        params={"updated_by": "tester"},
        json={"materials": [{"material_code": "M1", "estimated_usage": 2, "unit_cost": 1000}]},
    )
    assert materials.status_code == 200, materials.text
    assert materials.json()["estimated_total_cost"] == 2000

    revision = client.post(
        f"{PREFIX}/sample-versions/{version_id}/new-revision",
        params={"revised_by": "tester", "revision_note": "v2"},
    )
    assert revision.status_code == 200
    assert revision.json()["version_label"] == "v2"

    assert (
        client.post(
            f"{PREFIX}/sample-versions/{version_id}/submit-approval",
            params={"submitted_by": "tester"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"{PREFIX}/sample-versions/{version_id}/approve",
            params={"approved_by": "mgr"},
        ).status_code
        == 200
    )

    converted = client.post(
        f"{PREFIX}/sample-versions/{version_id}/convert-to-order",
        params={"order_id": "SO-1", "converted_by": "tester"},
    )
    assert converted.status_code == 200
    assert converted.json()["status"] == "converted"


def test_sample_version_error_paths(client: TestClient) -> None:
    assert client.get(f"{PREFIX}/sample-versions/does-not-exist").status_code == 404

    version_id = _create_sample_version(client, f"ART-ERR-{uuid4()}")

    # approve while still draft
    assert (
        client.post(
            f"{PREFIX}/sample-versions/{version_id}/approve",
            params={"approved_by": "mgr"},
        ).status_code
        == 400
    )
    # convert while still draft
    assert (
        client.post(
            f"{PREFIX}/sample-versions/{version_id}/convert-to-order",
            params={"order_id": "X", "converted_by": "tester"},
        ).status_code
        == 400
    )

    # components can only be edited on draft versions
    client.post(
        f"{PREFIX}/sample-versions/{version_id}/submit-approval",
        params={"submitted_by": "tester"},
    )
    blocked = client.put(
        f"{PREFIX}/sample-versions/{version_id}/components",
        params={"updated_by": "tester"},
        json={"components": []},
    )
    assert blocked.status_code == 400
