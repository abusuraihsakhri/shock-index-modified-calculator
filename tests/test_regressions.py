"""Regression checks for clinical formulas, security, HTTP and CSV behavior."""
import csv
import math

import pytest
from fastapi.testclient import TestClient

from agents.api import app
from agents.base import AuditTrail, PHIGuard, SecurityException
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from shock_index import (
    age_adjusted_si, calculate_shock_index, classify_msi, classify_si,
    map_from_bp, process_csv, shock_index,
)


def test_published_age_shock_index():
    assert age_adjusted_si(0.6, 50) == pytest.approx(30)
    assert calculate_shock_index(80, 120, age=50)["age_adjusted_si"] == pytest.approx(33.333, abs=0.001)


def test_msi_interval_distinct_from_si():
    result = calculate_shock_index(80, 120, dbp=80)
    assert result["si_classification"]["risk_level"] == "normal"
    assert result["msi_classification"]["risk_level"] == "within_studied_interval"
    assert classify_msi(1.31)["risk_level"] == "outside_studied_interval"
    assert classify_msi(0.69)["risk_level"] == "outside_studied_interval"


@pytest.mark.parametrize("call", [
    lambda: shock_index(float("nan"), 120),
    lambda: shock_index(80, float("inf")),
    lambda: map_from_bp(120, float("nan")),
    lambda: classify_si(float("nan")),
    lambda: age_adjusted_si(0.6, float("inf")),
    lambda: calculate_shock_index(80, 120, age=0),
    lambda: calculate_shock_index(80, 120, dbp=float("nan")),
])
def test_invalid_inputs_raise(call):
    with pytest.raises(ValueError):
        call()


def test_audit_hmac_detects_tampering():
    trail = AuditTrail(secret_key="test-only-not-for-production")
    assert trail.verify_integrity()
    trail.log("test", "clinical", "check", {"result": "ok"})
    trail.log("test", "clinical", "check", {"result": "followup"})
    assert trail.verify_integrity()
    snapshots = trail.get_trail()
    snapshots[0]["actor"] = "external"
    assert trail.verify_integrity(), "Public snapshot must be a defensive copy"
    trail.logs[0]["actor"] = "tampered"
    assert not trail.verify_integrity(), "Must recompute HMAC, not just chain links"


def test_nested_identifier_is_blocked():
    payload = SystemTaskPayload(
        task_id="CASE-1", target_identifier="SPEC-1",
        primary_metric=1.0, attributes={"contact": "example@example.com"},
    )
    with pytest.raises(SecurityException):
        SystemSupervisor().process_task(payload)


def test_csv_export_formula_escaping(tmp_path):
    source = tmp_path / "input.csv"
    output = tmp_path / "result.csv"
    source.write_text('hr,sbp,note\n80,120,"=2+2"\n', encoding="utf-8")
    result = process_csv(str(source), str(output))
    assert len(result) == 1
    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["note"] == "'=2+2"
    assert rows[0]["shock_index"] == "0.667"


def test_csv_malformed_row_is_annotated(tmp_path):
    source = tmp_path / "input.csv"
    output = tmp_path / "result.csv"
    source.write_text("hr,sbp\n80,120,extra\n", encoding="utf-8")
    process_csv(str(source), str(output))
    with output.open(newline="", encoding="utf-8") as handle:
        row = next(csv.DictReader(handle))
    assert "error" in row and "more columns" in row["error"]


def test_http_and_browser_routes():
    client = TestClient(app)
    response = client.post("/api/calculate", json={"hr": 80, "sbp": 120, "dbp": 80, "age": 50})
    assert response.status_code == 200
    assert response.json()["age_adjusted_si"] == pytest.approx(33.333, abs=0.001)
    assert client.post("/api/calculate", json={"hr": 80, "sbp": 100, "dbp": 110}).status_code == 422
    assert client.post("/api/calculate", json={"hr": "NaN", "sbp": 100}).status_code == 422
    assert client.get("/health").status_code == 200
    page = client.get("/")
    assert page.status_code == 200
    assert "Shock Index Calculator" in page.text
    assert client.get("/app.js").status_code == 200
    assert client.get("/style.css").status_code == 200
