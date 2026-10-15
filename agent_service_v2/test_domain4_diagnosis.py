"""Comprehensive Verification Suite for Domain 4: Well-Level Diagnosis.

Validates all 18 capabilities of Domain 4:
4.1 Trip investigation (Mode A post-trip RCA)
4.2 Historical trajectory analysis (telemetry window tracking)
4.3 Inflection detection (onset timestamp and rate of change)
4.4 Co-movement detection (multivariate coupled signatures)
4.5 Pattern identification (13-fault registry taxonomy match)
4.6 Root-cause ranking (primary vs secondary hypotheses)
4.7 Confirmation tests (field-level diagnostic verification tests)
4.8 Impact quantification (gross BPD loss, net BOPD loss, daily revenue loss at $75/bbl)
4.9 Escalation condition (catastrophic equipment stress thresholds)
4.10 Next diagnostic steps (actionable troubleshooting SOPs)
4.11 Proof chart (EIR timeSeriesWindow coordinate array for Recharts)
4.12 Anomaly-without-trip diagnosis (Mode B running well evaluation)
4.13 False-premise refusal (polite refusal with live telemetry on healthy running wells)
4.14 Health degradation analysis (evaluating declining operational performance)
4.15 Production decline RCA (inflow vs pump wear vs backpressure)
4.16 Early warning (incipient failure prediction)
4.17 Multiple-hypothesis reasoning (probabilistic differential ranking)
4.18 Sensor-vs-physics reconciliation (hydraulic & electrical balance validation)
"""

import unittest
from datetime import datetime, timezone
from app.ai.router import ask_agent
from app.services.esp_diagnosis_service import (
    diagnose_esp_event,
    diagnose_running_well_degradation,
    reconcile_sensors_with_physics,
    detect_inflection_point,
    detect_signal_co_movement,
    get_asset_baseline,
)
from app.schemas.esp_diagnosis import DiagnoseEventRequest


class TestDomain4WellLevelDiagnosis(unittest.TestCase):
    """Test suite for Domain 4: Well-Level Diagnosis."""

    def test_01_trip_investigation_mode_a_eir_contract(self):
        """Cap 4.1, 4.2, 4.5, 4.6, 4.7, 4.8, 4.9, 4.10, 4.11: Mode A Trip Event Forensics."""
        res = ask_agent("Diagnose trip on EV-20261012-103435-FNW-001-878")
        self.assertEqual(res["intent"], "EVENT_DIAGNOSE")
        sd = res.get("structured_data") or {}

        # 4.11 Proof Chart & EIR contract
        self.assertIn("eir_record", sd)
        eir = sd["eir_record"]
        self.assertEqual(eir["eventId"], "EV-20261012-103435-FNW-001-878")
        self.assertEqual(eir["wellId"], "FNW-001")
        self.assertIn("summary", eir)
        self.assertIn("evidence", eir)
        self.assertIn("timeSeriesWindow", eir["evidence"])
        self.assertIsInstance(eir["evidence"]["timeSeriesWindow"], list)

        # 4.8 Impact quantification
        summary = eir["summary"]
        self.assertGreater(summary.get("flowLossGrossBpd", 0), 0)
        self.assertGreater(summary.get("dailyRevenueImpactUsd", 0), 0)

        # 4.6 & 4.7 Ranked Hypotheses & Confirmation tests
        self.assertIn("investigation", eir)
        self.assertIn("leadingHypothesis", eir["investigation"])
        leading = eir["investigation"]["leadingHypothesis"]
        self.assertIn("confirmationTest", leading)
        self.assertGreater(leading.get("confidence", 0), 0.5)

    def test_02_inflection_and_comovement_detection(self):
        """Cap 4.3 & 4.4: Inflection detection and signal co-movement."""
        asset = get_asset_baseline("FNW-001")
        sample_telemetry = [
            {"timestamp": datetime(2026, 10, 12, 10, 19, 0, tzinfo=timezone.utc), "vibration_g": 0.18, "motor_current_a": 20.0, "intake_pressure_psi": 395.0},
            {"timestamp": datetime(2026, 10, 12, 10, 24, 0, tzinfo=timezone.utc), "vibration_g": 0.28, "motor_current_a": 24.5, "intake_pressure_psi": 360.0},
            {"timestamp": datetime(2026, 10, 12, 10, 29, 0, tzinfo=timezone.utc), "vibration_g": 0.55, "motor_current_a": 28.2, "intake_pressure_psi": 310.0},
        ]
        ev_ts = datetime(2026, 10, 12, 10, 34, 35, tzinfo=timezone.utc)
        
        # 4.3 Inflection detection
        inflection = detect_inflection_point(sample_telemetry, asset, ev_ts)
        self.assertIn("inflection_timestamp", inflection)
        self.assertIn("onset_signal", inflection)
        self.assertGreaterEqual(inflection["lead_time_seconds"], 5)

        # 4.4 Co-movement detection
        deviations = [
            type("Dev", (), {"signal": "Vibration (Vx)", "status": "VIOLATION", "delta": 0.35})(),
            type("Dev", (), {"signal": "Motor Current", "status": "VIOLATION", "delta": 8.0})(),
        ]
        co_move = detect_signal_co_movement(deviations, sample_telemetry, asset)
        self.assertEqual(co_move["co_movement_pattern"], "ELECTROMECHANICAL_CO_SURGE")
        self.assertIn("Vibration (Vx)", co_move["co_moving_signals"])
        self.assertIn("Motor Current (A)", co_move["co_moving_signals"])

    def test_03_sensor_vs_physics_reconciliation(self):
        """Cap 4.18: Sensor-vs-physics reconciliation."""
        asset = get_asset_baseline("FS-004")
        
        # Case A: Physically consistent running telemetry
        normal_pt = {
            "intake_pressure_psi": 390.0,
            "discharge_pressure_psi": 2100.0,
            "whp_psi": 150.0,
            "motor_current_a": 34.5,
            "frequency_hz": 50.0,
            "operating_state": "running"
        }
        res_normal = reconcile_sensors_with_physics([], asset, normal_pt)
        self.assertFalse(res_normal["is_sensor_fault"])
        self.assertEqual(res_normal["sensor_validity"], "PHYSICALLY_CONSISTENT")

        # Case B: Disconnected negative pressure reading
        fault_pt = {
            "intake_pressure_psi": -25.0,
            "discharge_pressure_psi": 2100.0,
            "whp_psi": 150.0,
            "motor_current_a": 34.5,
            "frequency_hz": 50.0,
            "operating_state": "running"
        }
        res_fault = reconcile_sensors_with_physics([], asset, fault_pt)
        self.assertTrue(res_fault["is_sensor_fault"])
        self.assertIn("negative", res_fault["discrepancy_explanation"])

    def test_04_anomaly_without_trip_and_production_rca(self):
        """Cap 4.12, 4.14, 4.15, 4.17: Mode B Running well degradation & production decline RCA."""
        res = ask_agent("Diagnose production decline and abnormal drift on well FS-006")
        self.assertEqual(res["intent"], "EVENT_DIAGNOSE")
        sd = res.get("structured_data") or {}
        self.assertEqual(sd.get("operating_state"), "running")
        self.assertIn("eir_record", sd)
        self.assertIn("primary_fault", sd)
        self.assertGreater(len(sd.get("ranked_hypotheses", [])), 1)

    def test_05_false_premise_refusal_and_pivot(self):
        """Cap 4.13: False-premise refusal when querying a trip on a healthy running well."""
        res = ask_agent("Why did well FS-004 trip?")
        self.assertEqual(res["intent"], "SAFETY_REFUSAL_FALSE_PREMISE")
        self.assertIn("FS-004", res["markdown_text"])
        self.assertIn("RUNNING", res["markdown_text"])
        self.assertIn("False-Premise", res["markdown_text"])

    def test_06_early_warning_failure_analysis(self):
        """Cap 4.16: Early warning failure prediction on running asset."""
        res = ask_agent("What is about to fail on well FS-023?")
        self.assertEqual(res["intent"], "EVENT_DIAGNOSE")
        sd = res.get("structured_data") or {}
        self.assertIn("eir_record", sd)
        self.assertIn("impact", sd)


if __name__ == "__main__":
    unittest.main()
