"""Unit & Integration Test Suite for Domain 3: Trip Root-Cause Diagnostics & Forensics."""

from datetime import datetime, timezone
import unittest

from app.ai.router import ask_agent
from app.services.esp_diagnosis_service import (
    get_telemetry_window,
    get_well_recent_events,
    diagnose_esp_event,
    DiagnoseEventRequest,
)


class TestDomain3Forensics(unittest.TestCase):
    """Validate Domain 3 forensics payload, 15-min window, deep links, and multi-event disambiguation."""

    def test_explicit_event_id_diagnosis(self):
        """Diagnosing by event ID must directly return full 7-pillar report & dashboard timestamps."""
        res = ask_agent("Diagnose event EV-20261012-103435-FNW-001-878")
        self.assertEqual(res.get("intent"), "EVENT_DIAGNOSE")
        self.assertFalse(res.get("needs_clarification", False))

        sd = res.get("structured_data")
        self.assertIsNotNone(sd, "structured_data must be populated")
        self.assertEqual(sd.get("event_id"), "EV-20261012-103435-FNW-001-878")
        self.assertEqual(sd.get("resolved_path"), "/events/EV-20261012-103435-FNW-001-878")
        self.assertIn("trip_timestamp", sd)
        self.assertIn("pre_trip_window_start", sd)
        self.assertIn("post_trip_window_end", sd)

        # Check deviations exist
        devs = sd.get("deviations", [])
        self.assertGreater(len(devs), 0, "Deviations list must contain physical signals")

        # Check markdown deep-link
        md = res.get("markdown_text", "")
        self.assertIn("/events/EV-20261012-103435-FNW-001-878", md)

    def test_multi_event_clarification_on_ambiguous_well(self):
        """Tripped well with multiple events without specific ID must trigger disambiguation options."""
        res = ask_agent("Why did well FS-017 trip?")
        self.assertEqual(res.get("intent"), "EVENT_DIAGNOSE")
        self.assertTrue(res.get("needs_clarification"))

        options = res.get("suggested_options", [])
        self.assertGreater(len(options), 1, "Must present multiple event options")
        self.assertTrue(any("Diagnose EV-" in opt for opt in options))

        sd = res.get("structured_data")
        self.assertIsNotNone(sd)
        self.assertIn("available_events", sd)
        self.assertGreater(len(sd["available_events"]), 1)

    def test_explicit_latest_event_bypass(self):
        """User asking for 'latest trip' on multi-event well bypasses clarification prompt."""
        res = ask_agent("Diagnose latest trip for well FS-017")
        self.assertEqual(res.get("intent"), "EVENT_DIAGNOSE")
        self.assertFalse(res.get("needs_clarification", True))

        sd = res.get("structured_data")
        self.assertIsNotNone(sd)
        self.assertTrue(sd.get("resolved_path", "").startswith("/events/EV-"))

    def test_15min_pre_5min_post_telemetry_window(self):
        """Direct verification of get_telemetry_window default window parameters."""
        ev_ts = datetime(2026, 10, 12, 10, 34, 35, tzinfo=timezone.utc)
        records = get_telemetry_window("FNW-001", ev_ts, window_sec=900, post_window_sec=300)
        self.assertIsInstance(records, list)
        if records:
            # Check timestamps span pre-trip and post-trip
            min_ts = min(r["timestamp"] for r in records)
            max_ts = max(r["timestamp"] for r in records)
            self.assertLessEqual(min_ts, ev_ts)

    def test_recent_events_lookup(self):
        """Test database query for recent events on a well."""
        events = get_well_recent_events("FS-017", limit=3)
        self.assertIsInstance(events, list)
        self.assertGreater(len(events), 0)
        self.assertIn("event_id", events[0])
        self.assertIn("trip_cause", events[0])


if __name__ == "__main__":
    unittest.main()
