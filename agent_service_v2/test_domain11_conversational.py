"""Comprehensive Verification Suite for Domain 11 — Conversational Intelligence & Session Layer.

Tests all 8 capabilities:
11.1 Follow-up on prior answer ("Why did you say X?")
11.2 Evidence inquiry ("What data did you use?")
11.3 Graph explanation ("What does that chart mean?")
11.4 Clarification on ambiguity
11.5 Multi-turn context preservation
11.6 Pronoun resolution ("It" / "its" binds to session well)
11.7 Deferred intent & compound query handling ("A and also B")
11.8 Reframing ("What about temperature?" after prior well query)
"""

import sys
import unittest

from app.core.session import session_manager
from app.ai.router import ask_agent
from app.schemas.esp_diagnosis import ESPIntentEnum


class TestDomain11Conversational(unittest.TestCase):

    def setUp(self):
        session_manager.clear()

    def test_11_2_evidence_inquiry_after_diagnosis(self):
        """11.2 Evidence Inquiry: Cites exact SCADA numbers and table from prior diagnosis."""
        sess_id = "sess_test_evidence_001"
        
        # Turn 1: Run diagnostic on FNW-001
        res1 = ask_agent("Diagnose well FNW-001", session_id=sess_id)
        self.assertEqual(res1["intent"], "EVENT_DIAGNOSE")
        self.assertIn("FNW-001", res1["markdown_text"])
        self.assertEqual(res1["session_id"], sess_id)

        # Turn 2: Ask for evidence
        res2 = ask_agent("What data did you use?", session_id=sess_id)
        self.assertEqual(res2["intent"], "EVIDENCE_INQUIRY")
        self.assertIn("opg_well_telemetry", res2["markdown_text"])
        self.assertIn("Ground Truth Sensor Signals", res2["markdown_text"])
        self.assertIn("FNW-001", res2["markdown_text"])
        self.assertIsNotNone(res2["structured_data"])
        self.assertTrue(res2["structured_data"]["has_prior_evidence"])
        self.assertEqual(res2["structured_data"]["well_id"], "FNW-001")
        print("PASS: 11.2 Evidence Inquiry verified with SCADA audit table.")

    def test_11_1_follow_up_justification(self):
        """11.1 Follow-up on prior answer: Cites SOP standard and physical trigger."""
        sess_id = "sess_test_followup_001"

        # Turn 1: Diagnose well FS-017
        res1 = ask_agent("Why did well FS-017 trip?", session_id=sess_id)
        self.assertEqual(res1["intent"], "EVENT_DIAGNOSE")

        # Turn 2: Ask for justification
        res2 = ask_agent("Why did you say that was the fault?", session_id=sess_id)
        self.assertEqual(res2["intent"], "FOLLOW_UP_JUSTIFY")
        self.assertIn("Diagnostic Justification", res2["markdown_text"])
        self.assertIn("Standard Operating Procedure", res2["markdown_text"])
        self.assertEqual(res2["structured_data"]["well_id"], "FS-017")
        print("PASS: 11.1 Follow-up justification verified with SOP standard.")

    def test_11_3_graph_explanation_clarification_and_direct(self):
        """11.3 Graph Explanation: Disambiguates on page route, explains named charts."""
        sess_id = "sess_test_graph_001"

        # Scenario A: Ambiguous chart inquiry on Well Monitor route -> requests clarification
        res_ambig = ask_agent("What does that chart mean?", session_id=sess_id, page_route="/wells/FS-004")
        self.assertEqual(res_ambig["intent"], "GRAPH_EXPLAIN")
        self.assertTrue(res_ambig["needs_clarification"])
        self.assertIn("4-Subsystem Health Equalizer", res_ambig["suggested_options"])
        self.assertIn("2D Downhole String Visualizer", res_ambig["suggested_options"])

        # Scenario B: Specific named chart -> returns direct engineering explanation
        res_direct = ask_agent("Explain the 2D Downhole String Visualizer", session_id=sess_id)
        self.assertEqual(res_direct["intent"], "GRAPH_EXPLAIN")
        self.assertFalse(res_direct["needs_clarification"])
        self.assertIn("2D Downhole String Visualizer", res_direct["markdown_text"])
        self.assertIn("Multistage Centrifugal Impellers", res_direct["markdown_text"])
        print("PASS: 11.3 Graph explanation disambiguation & direct explanation verified.")

    def test_11_4_ambiguity_clarification(self):
        """11.4 Clarification on Ambiguity: Asks clarification rather than guessing."""
        res = ask_agent("Compare gathering clusters")
        self.assertTrue(res["needs_clarification"])
        self.assertIn("suggested_options", res)
        self.assertGreaterEqual(len(res["suggested_options"]), 2)
        print("PASS: 11.4 Ambiguity clarification verified.")

    def test_11_5_and_11_6_multi_turn_context_and_pronouns(self):
        """11.5 Multi-turn context & 11.6 Pronoun resolution: 'it' binds to session well."""
        sess_id = "sess_test_pronoun_001"

        # Turn 1: Inspect tripped well FS-017
        res1 = ask_agent("What is the health status of well FS-017?", session_id=sess_id)
        self.assertEqual(res1["intent"], "WELL_HEALTH")
        self.assertIn("FS-017", res1["markdown_text"])

        # Turn 2: Query using pronoun "its" without mentioning well name
        res2 = ask_agent("Why did it trip?", session_id=sess_id)
        self.assertEqual(res2["intent"], "EVENT_DIAGNOSE")
        self.assertIn("FS-017", res2["markdown_text"])

        # Turn 3: Query using "that well"
        res3 = ask_agent("Show past trips for that well", session_id=sess_id)
        self.assertEqual(res3["intent"], "WELL_HISTORY")
        self.assertIn("FS-017", res3["markdown_text"])
        print("PASS: 11.5 Multi-turn context & 11.6 Pronoun resolution verified.")

    def test_11_7_compound_query_deferred_intent(self):
        """11.7 Deferred Intent Handling: Compound query splits primary and queues secondary."""
        sess_id = "sess_test_compound_001"

        # Turn 1: Compound query with "and also" on tripped well FS-017
        compound_q = "Diagnose well FS-017 and also show fleet inventory"
        res1 = ask_agent(compound_q, session_id=sess_id)
        
        # Primary query executed immediately
        self.assertEqual(res1["intent"], "EVENT_DIAGNOSE")
        self.assertIn("FS-017", res1["markdown_text"])
        
        # Interactive continuation chip and footer banner present
        self.assertTrue(any("Continue: show fleet inventory" in opt for opt in res1["suggested_options"]))
        self.assertIn("Queued Follow-Up", res1["markdown_text"])

        # Turn 2: Trigger continuation
        res2 = ask_agent("continue", session_id=sess_id)
        self.assertEqual(res2["intent"], "FLEET_INVENTORY")
        self.assertIn("Fleet Real-Time Operational Status", res2["markdown_text"])
        print("PASS: 11.7 Compound query splitting & deferred intent execution verified.")

    def test_11_8_reframing_metric_pivot(self):
        """11.8 Reframing: 'What about temperature?' pivots to thermal subsystem for active well."""
        sess_id = "sess_test_reframe_001"

        # Turn 1: Check status of well FS-017
        res1 = ask_agent("Check health of well FS-017", session_id=sess_id)
        self.assertEqual(res1["intent"], "WELL_HEALTH")
        self.assertIn("FS-017", res1["markdown_text"])

        # Turn 2: Reframe to thermal subsystem
        res2 = ask_agent("What about temperature?", session_id=sess_id)
        self.assertEqual(res2["intent"], "WELL_HEALTH")
        self.assertIn("Thermal Subsystem", res2["markdown_text"])
        self.assertIn("Motor Winding Temp", res2["markdown_text"])
        self.assertIn("FS-017", res2["markdown_text"])
        self.assertIn("Safe Limit", res2["markdown_text"])

        # Turn 3: Reframe to mechanical vibration
        res3 = ask_agent("What about vibration?", session_id=sess_id)
        self.assertEqual(res3["intent"], "WELL_HEALTH")
        self.assertIn("Mechanical Subsystem", res3["markdown_text"])
        self.assertIn("Radial Vibration", res3["markdown_text"])
        self.assertIn("FS-017", res3["markdown_text"])
        print("PASS: 11.8 Reframing metric pivot verified.")


if __name__ == "__main__":
    unittest.main()
