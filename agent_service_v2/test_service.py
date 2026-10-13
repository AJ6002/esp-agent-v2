"""Empirical verification suite for standalone Agent Service V2."""

import json
from fastapi.testclient import TestClient
from main import app
from app.ai.router import ask_agent

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    print("Health response:", data)
    assert data["status"] == "HEALTHY"
    assert data["port"] == 8092
    assert data["database_connected"] is True


def test_fleet_status_via_router():
    res = ask_agent("what is the current status of the fleet?")
    assert res["intent"] == "FLEET_INVENTORY"
    s_data = res["structured_data"]
    assert s_data["total_wells"] == 10
    assert s_data["running_wells_count"] == 5
    assert s_data["tripped_wells_count"] == 5
    assert s_data["unmonitored_wells_count"] == 0
    print("Fleet verification passed: 10 total wells (5 running, 5 tripped).")


def test_event_diagnose_via_router():
    res = ask_agent("Why did well FNW-001 trip and what are the recommended actions?")
    assert res["intent"] == "EVENT_DIAGNOSE"
    assert "FNW-001" in res["markdown_text"]
    assert "HIGH_VIBRATION" in res["markdown_text"]
    print("Diagnosis verification passed.")


def test_streaming_query_endpoint():
    res = client.post("/query", json={"message": "what is the current status of the fleet?"})
    assert res.status_code == 200
    lines = [line.strip() for line in res.text.split("\n") if line.strip()]
    assert len(lines) >= 3

    frame_types = []
    for line in lines:
        parsed = json.loads(line)
        frame_types.append(parsed.get("type"))

    print("Observed frame sequence:", frame_types)
    assert "status" in frame_types
    assert "text_delta" in frame_types
    assert "done" in frame_types
    assert parsed["status"] == "COMPLETED"
    print("Streaming NDJSON endpoint verified successfully.")


if __name__ == "__main__":
    print("Running Agent Service V2 verification tests...")
    test_health_endpoint()
    test_fleet_status_via_router()
    test_event_diagnose_via_router()
    test_streaming_query_endpoint()
    print("ALL AGENT SERVICE V2 TESTS PASSED GREEN!")
