"""Comprehensive Verification Test Suite for Domain 9: UI / Navigation / Route Awareness."""

import sys
import os
import unittest
import json

# Add apps/api and agent_service_v2 to Python path
sys.path.insert(0, os.path.abspath("apps/api"))

from app.schemas.esp_diagnosis import ESPIntentEnum, UIRouteEntry, UINavigatorReport
from app.services.esp_diagnosis_service import (
    load_ui_map,
    lookup_ui_route,
    get_ui_navigation_narrative,
    route_query_hybrid,
)


class TestDomain9UINavigation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = load_ui_map()
        print(f"\n[SETUP] UI Map Loaded with {len(cls.reg['entries'])} routes, "
              f"{len(cls.reg['components'])} components, {len(cls.reg['concepts'])} concepts.")

    def test_01_registry_integrity(self):
        """Verify all 8 primary routes from ui_map.yaml are loaded into memory."""
        expected_routes = [
            "navigation.operations_workspace",
            "route.fleet_cockpit",
            "route.working_status",
            "route.well_detail",
            "route.live_calculations",
            "route.event_intelligence",
            "route.reports_hub",
            "route.scenario_simulator",
        ]
        for rid in expected_routes:
            self.assertIn(rid, self.reg["entries"], f"Missing expected route {rid}")
            entry = self.reg["entries"][rid]
            self.assertIsInstance(entry, UIRouteEntry)
            self.assertTrue(len(entry.title) > 0)
            self.assertTrue(len(entry.summary) > 0)

    def test_02_route_query_working_status(self):
        """User asks 'what is the Working Status page?'"""
        q = "what is the Working Status page?"
        route = route_query_hybrid(q)
        self.assertEqual(route.intent, ESPIntentEnum.UI_NAVIGATION)

        report = get_ui_navigation_narrative(q)
        self.assertEqual(report.intent, "UI_NAVIGATION")
        self.assertEqual(report.route_id, "route.working_status")
        self.assertEqual(report.resolved_path, "/working-status")
        self.assertIn("working", report.narrative.lower())
        self.assertTrue(report.narrative.strip().endswith("]"), "Narrative must end with bracketed route_id")

    def test_03_route_query_fleet_cockpit(self):
        """User asks 'what is the Fleet Cockpit page?'"""
        q = "what is the Fleet Cockpit page?"
        route = route_query_hybrid(q)
        self.assertEqual(route.intent, ESPIntentEnum.UI_NAVIGATION)

        report = get_ui_navigation_narrative(q)
        self.assertEqual(report.route_id, "route.fleet_cockpit")
        self.assertEqual(report.resolved_path, "/")
        self.assertTrue(report.narrative.strip().endswith("]"))

    def test_04_route_query_live_calculations(self):
        """User asks 'where are live calculations?'"""
        q = "where are live calculations?"
        route = route_query_hybrid(q)
        self.assertEqual(route.intent, ESPIntentEnum.UI_NAVIGATION)

        report = get_ui_navigation_narrative(q)
        self.assertEqual(report.route_id, "route.live_calculations")
        self.assertEqual(report.resolved_path, "/live-calculations")
        self.assertTrue(report.narrative.strip().endswith("]"))

    def test_05_route_query_scenario_simulator(self):
        """User asks 'explain the Scenario Simulator screen'"""
        q = "explain the Scenario Simulator screen"
        route = route_query_hybrid(q)
        self.assertEqual(route.intent, ESPIntentEnum.UI_NAVIGATION)

        report = get_ui_navigation_narrative(q)
        self.assertEqual(report.route_id, "route.scenario_simulator")
        self.assertEqual(report.resolved_path, "/custom-testing")
        self.assertTrue(report.narrative.strip().endswith("]"))

    def test_06_route_query_reports_hub(self):
        """User asks 'where can I find operational reports?'"""
        q = "where can I find operational reports?"
        route = route_query_hybrid(q)
        self.assertEqual(route.intent, ESPIntentEnum.UI_NAVIGATION)

        report = get_ui_navigation_narrative(q)
        self.assertEqual(report.route_id, "route.reports_hub")
        self.assertEqual(report.resolved_path, "/reports")
        self.assertTrue(report.narrative.strip().endswith("]"))

    def test_07_route_query_event_intelligence(self):
        """User asks 'where do I find trip forensics and event intelligence?'"""
        q = "where do I find trip forensics and event intelligence?"
        route = route_query_hybrid(q)
        self.assertEqual(route.intent, ESPIntentEnum.UI_NAVIGATION)

        report = get_ui_navigation_narrative(q)
        self.assertEqual(report.route_id, "route.event_intelligence")
        self.assertEqual(report.resolved_path, "/events")
        self.assertTrue(report.narrative.strip().endswith("]"))

    def test_08_component_string_visualizer(self):
        """User asks 'where can I find the 2D ESP string visualizer?'"""
        q = "where can I find the 2D ESP string visualizer?"
        route = route_query_hybrid(q)
        self.assertEqual(route.intent, ESPIntentEnum.UI_NAVIGATION)

        report = get_ui_navigation_narrative(q)
        self.assertEqual(report.route_id, "route.well_detail")
        self.assertEqual(report.entry_type, "component")
        self.assertIn("visualizer", report.title.lower())
        self.assertTrue(report.narrative.strip().endswith("]"))

    def test_09_component_equalizer(self):
        """User asks 'what does the 4-subsystem equalizer display?'"""
        q = "what does the 4-subsystem equalizer display?"
        route = route_query_hybrid(q)
        self.assertEqual(route.intent, ESPIntentEnum.UI_NAVIGATION)

        report = get_ui_navigation_narrative(q)
        self.assertEqual(report.route_id, "route.well_detail")
        self.assertEqual(report.entry_type, "component")
        self.assertTrue(report.narrative.strip().endswith("]"))

    def test_10_concept_affinity_laws(self):
        """User asks 'what are affinity laws?'"""
        q = "what are affinity laws?"
        route = route_query_hybrid(q)
        self.assertEqual(route.intent, ESPIntentEnum.UI_NAVIGATION)

        report = get_ui_navigation_narrative(q)
        self.assertEqual(report.route_id, "route.well_detail")
        self.assertEqual(report.entry_type, "concept")
        self.assertTrue(report.narrative.strip().endswith("]"))

    def test_11_concept_virtual_flow_metering(self):
        """User asks 'what is virtual flow metering (VFM)?'"""
        q = "what is virtual flow metering (VFM)?"
        route = route_query_hybrid(q)
        self.assertEqual(route.intent, ESPIntentEnum.UI_NAVIGATION)

        report = get_ui_navigation_narrative(q)
        self.assertEqual(report.route_id, "route.live_calculations")
        self.assertEqual(report.entry_type, "concept")
        self.assertTrue(report.narrative.strip().endswith("]"))

    def test_12_concept_14_fault_classifier(self):
        """User asks 'what is the 14-fault classifier spectrum?'"""
        q = "what is the 14-fault classifier spectrum?"
        route = route_query_hybrid(q)
        self.assertEqual(route.intent, ESPIntentEnum.UI_NAVIGATION)

        report = get_ui_navigation_narrative(q)
        self.assertEqual(report.route_id, "route.working_status")
        self.assertEqual(report.entry_type, "concept")
        self.assertTrue(report.narrative.strip().endswith("]"))

    def test_13_parametric_well_binding(self):
        """User asks 'where can I find pump curves for FS-017?'"""
        q = "where can I find pump curves for FS-017?"
        route = route_query_hybrid(q)
        self.assertEqual(route.intent, ESPIntentEnum.UI_NAVIGATION)
        self.assertEqual(route.entity, "FS-017")

        report = get_ui_navigation_narrative(q, entity=route.entity)
        self.assertEqual(report.route_id, "route.well_detail")
        self.assertEqual(report.resolved_path, "/wells/FS-017")
        self.assertIn("/wells/FS-017", report.markdown_report)
        self.assertTrue(report.narrative.strip().endswith("]"))

    def test_14_parametric_event_binding(self):
        """User asks 'where is the forensics screen for EV-20261012-101438-FS-017-571?'"""
        q = "where is the forensics screen for EV-20261012-101438-FS-017-571?"
        route = route_query_hybrid(q)
        self.assertEqual(route.intent, ESPIntentEnum.UI_NAVIGATION)

        report = get_ui_navigation_narrative(q, event_id="EV-20261012-101438-FS-017-571")
        self.assertEqual(report.route_id, "route.event_intelligence")
        self.assertEqual(report.resolved_path, "/events")

    def test_15_workspace_overview_all_screens(self):
        """User asks 'show all screens in operations workspace'"""
        q = "show all screens in operations workspace"
        route = route_query_hybrid(q)
        self.assertEqual(route.intent, ESPIntentEnum.UI_NAVIGATION)

        report = get_ui_navigation_narrative(q)
        self.assertEqual(report.route_id, "navigation.operations_workspace")
        self.assertTrue(report.narrative.strip().endswith("]"))

    def test_16_out_of_scope_undocumented_fallback(self):
        """User asks 'where is the pizza ordering screen?'"""
        q = "where is the pizza ordering screen?"
        route = route_query_hybrid(q)
        self.assertEqual(route.intent, ESPIntentEnum.UI_NAVIGATION)

        report = get_ui_navigation_narrative(q)
        self.assertEqual(report.narrative.strip(), "That's not documented in the platform guide yet.")
        self.assertEqual(report.markdown_report.strip(), "That's not documented in the platform guide yet.")

    def test_17_out_of_scope_3d_seismic(self):
        """User asks 'what is the 3D seismic voxel viewer page?'"""
        q = "what is the 3D seismic voxel viewer page?"
        route = route_query_hybrid(q)
        self.assertEqual(route.intent, ESPIntentEnum.UI_NAVIGATION)

        report = get_ui_navigation_narrative(q)
        self.assertEqual(report.narrative.strip(), "That's not documented in the platform guide yet.")

    def test_18_agent_service_v2_parity(self):
        """Verify standalone Agent Service V2 provides identical routing and narration."""
        import importlib
        sys.path.insert(0, os.path.abspath("agent_service_v2"))
        v2_service = importlib.import_module("app.services.esp_diagnosis_service")

        q = "what is the Working Status page?"
        v2_route = v2_service.route_query_hybrid(q)
        self.assertEqual(v2_route.intent.value, "UI_NAVIGATION")

        v2_report = v2_service.get_ui_navigation_narrative(q)
        self.assertEqual(v2_report.route_id, "route.working_status")
        self.assertTrue(v2_report.narrative.strip().endswith("]"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
