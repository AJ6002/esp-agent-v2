"""Tests for ESP APM Event Diagnosis Service and Endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.esp_diagnosis import DiagnoseEventRequest
from app.services.esp_diagnosis_service import (
    diagnose_esp_event,
    get_active_wells,
    get_asset_baseline,
    get_recent_events,
)


@pytest.fixture
def api_client():
    return TestClient(app)


def test_esp_db_health(api_client):
    res = api_client.get("/api/v1/esp/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["esp_apm_db_connected"] is True
    assert data["esp_apm_db_readonly"] is True


def test_get_active_wells():
    wells = get_active_wells()
    assert len(wells) > 0
    well_ids = [w.well_id for w in wells]
    assert "FNW-001" in well_ids
    assert "FS-017" in well_ids


def test_get_recent_events():
    events = get_recent_events(limit=5)
    assert len(events) > 0
    assert events[0].event_id is not None
    assert events[0].well_id is not None


def test_get_asset_baseline_fnw001():
    baseline = get_asset_baseline("FNW-001")
    assert baseline["well_id"] == "FNW-001"
    assert baseline["rated_amp_a"] == 20.3
    assert baseline["max_vibration_g"] == 2.0
    assert baseline["overload_trip_pct"] == 115.0


def test_diagnose_fnw001_live_event():
    req = DiagnoseEventRequest(event_id="EV-20261012-103435-FNW-001-878")
    resp = diagnose_esp_event(req)
    assert resp.event_id == "EV-20261012-103435-FNW-001-878"
    assert resp.well_id == "FNW-001"
    assert resp.mathematical_confidence_pct >= 80

    # Verify 7 required sections in Markdown
    md = resp.markdown_report
    assert "1. TRIGGER" in md
    assert "2. DEVIATION" in md
    assert "3. POINT ANALYSIS" in md
    assert "4. SIGNATURE" in md
    assert "5. RANKED HYPOTHESES" in md
    assert "6. IMPACT" in md
    assert "7. NEXT STEPS" in md

    # Verify structured JSON
    data = resp.structured_data
    assert "ranked_hypotheses" in data
    assert len(data["ranked_hypotheses"]) >= 2
    assert "deviations" in data
    assert len(data["deviations"]) >= 3
    assert "impact" in data
    assert data["impact"]["deferred_bbl_per_hour"] > 0


def test_esp_diagnose_endpoint(api_client):
    res = api_client.post(
        "/api/v1/esp/diagnose-event",
        json={"event_id": "EV-20261012-103435-FNW-001-878"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["well_id"] == "FNW-001"
    assert data["mathematical_confidence_pct"] >= 80
    assert "markdown_report" in data


def test_normalize_well_id():
    from app.services.esp_diagnosis_service import normalize_well_id

    assert normalize_well_id("fs 17") == "FS-017"
    assert normalize_well_id("FS17") == "FS-017"
    assert normalize_well_id("fs-017") == "FS-017"
    assert normalize_well_id("fnw1") == "FNW-001"
    assert normalize_well_id("FNW-001") == "FNW-001"
    assert normalize_well_id("well without id") is None


def test_search_petroleum_kb():
    from app.services.esp_diagnosis_service import search_petroleum_kb

    chunks = search_petroleum_kb("bearing wear", limit=3)
    assert len(chunks) > 0
    assert chunks[0].chunk_id is not None
    assert len(chunks[0].content) > 20


def test_get_well_health_status():
    from app.services.esp_diagnosis_service import get_well_health_status

    rep = get_well_health_status("FNW-001")
    assert rep.well_id == "FNW-001"
    assert 0 <= rep.health_index_pct <= 100
    assert rep.rated_amps > 0
    assert rep.max_vibration_g > 0
    assert len(rep.markdown_report) > 50


def test_get_fleet_inventory_status():
    from app.services.esp_diagnosis_service import get_fleet_inventory_status

    fleet = get_fleet_inventory_status()
    assert fleet.total_wells >= 10
    assert fleet.active_wells > 0
    assert fleet.total_motor_hp > 500
    assert len(fleet.clusters) >= 2


def test_get_well_production_metrics():
    from app.services.esp_diagnosis_service import get_well_production_metrics

    prod = get_well_production_metrics("FS-017")
    assert prod.well_id == "FS-017"
    assert len(prod.markdown_report) > 50


def test_route_query_hybrid_all_intents():
    from app.services.esp_diagnosis_service import route_query_hybrid
    from app.schemas.esp_diagnosis import ESPIntentEnum

    # Event ID
    r1 = route_query_hybrid("Diagnose EV-20261012-103435-FNW-001-878")
    assert r1.intent == ESPIntentEnum.EVENT_DIAGNOSE
    assert r1.entity == "EV-20261012-103435-FNW-001-878"

    # Well History with typo normalization
    r2 = route_query_hybrid("What is failure history of well fs 17?")
    assert r2.intent == ESPIntentEnum.WELL_HISTORY
    assert r2.entity == "FS-017"

    # Well Health
    r3 = route_query_hybrid("Is well fnw1 healthy right now?")
    assert r3.intent == ESPIntentEnum.WELL_HEALTH
    assert r3.entity == "FNW-001"

    # Fleet
    r4 = route_query_hybrid("Show me fleet inventory and clusters")
    assert r4.intent == ESPIntentEnum.FLEET_INVENTORY

    # Production
    r5 = route_query_hybrid("What is production flow rate of fs-040?")
    assert r5.intent == ESPIntentEnum.PRODUCTION
    assert r5.entity == "FS-040"

    # Chit-chat
    r6 = route_query_hybrid("hello")
    assert r6.intent == ESPIntentEnum.CHAT

    # Missing entity -> clarification
    r7 = route_query_hybrid("why did the pump trip?")
    assert r7.needs_clarification is True
    assert len(r7.suggested_options) >= 3


def test_new_esp_endpoints(api_client):
    # KB search
    r_kb = api_client.get("/api/v1/esp/kb/search?query=vibration&limit=2")
    assert r_kb.status_code == 200
    assert len(r_kb.json()) > 0

    # Well Health
    r_h = api_client.get("/api/v1/esp/wells/FNW-001/health")
    assert r_h.status_code == 200
    assert r_h.json()["well_id"] == "FNW-001"

    # Fleet Inventory
    r_f = api_client.get("/api/v1/esp/fleet/inventory")
    assert r_f.status_code == 200
    assert r_f.json()["total_wells"] >= 10

    # Route Intent
    r_rt = api_client.get("/api/v1/esp/route-intent?question=hello")
    assert r_rt.status_code == 200
    assert r_rt.json()["intent"] == "CHAT"

