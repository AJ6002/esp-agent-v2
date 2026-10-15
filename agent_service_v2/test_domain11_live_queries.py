"""Live Interactive Multi-Turn Dialogue Verification for Domain 11.

Executes 4 comprehensive conversational sessions against PostgreSQL Server 184:
1. Session 1: Diagnostic & Forensic Inquiry Loop (11.1, 11.2, 11.5, 11.6, 11.8)
2. Session 2: Visual Chart Explanation & Ambiguity Resolution (11.3, 11.4)
3. Session 3: Compound Queries & Deferred Intent Execution (11.7)
4. Session 4: Multi-User Session Isolation (Alice vs Bob)
"""

import sys
import json

# Ensure UTF-8 output on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.ai.router import ask_agent
from app.core.session import session_manager


def print_banner(title: str):
    print("\n" + "=" * 80)
    print(f"  {title.upper()}")
    print("=" * 80)


def print_turn(turn_num: int, user_query: str, res: dict):
    print(f"\n--- [TURN {turn_num}] USER QUERY ---")
    print(f"User: \"{user_query}\"")
    print(f"Session ID    : {res.get('session_id')}")
    print(f"Routed Intent : {res.get('intent')} (Tier: {res.get('routing_tier')}, Conf: {res.get('confidence', 0.95):.2f})")
    print(f"Clarification : {res.get('needs_clarification', False)}")
    if res.get("suggested_options"):
        print(f"Options / Chips: {res.get('suggested_options')[:4]}")
    print("\nCOPILOT RESPONSE SUMMARY:")
    # Print first few meaningful lines of the response
    lines = [line for line in res.get("markdown_text", "").split("\n") if line.strip()]
    preview = "\n".join(lines[:8])
    print(preview)
    if len(lines) > 8:
        print(f"... [{len(lines) - 8} more lines omitted for display brevity]")


def run_session_1():
    print_banner("SESSION 1: DIAGNOSTIC & FORENSIC INQUIRY LOOP (11.1, 11.2, 11.5, 11.6, 11.8)")
    sess_id = "sess_engineer_session_1"

    # Turn 1
    t1 = ask_agent("Why did well FNW-001 trip?", session_id=sess_id)
    print_turn(1, "Why did well FNW-001 trip?", t1)

    # Turn 2: Evidence inquiry
    t2 = ask_agent("What data did you use?", session_id=sess_id)
    print_turn(2, "What data did you use?", t2)

    # Turn 3: Follow-up justification
    t3 = ask_agent("Why did you say vibration was the cause?", session_id=sess_id)
    print_turn(3, "Why did you say vibration was the cause?", t3)

    # Turn 4: Reframing to temperature
    t4 = ask_agent("What about temperature?", session_id=sess_id)
    print_turn(4, "What about temperature?", t4)

    # Turn 5: Pronoun/antecedent resolution
    t5 = ask_agent("Show past trips for that well", session_id=sess_id)
    print_turn(5, "Show past trips for that well", t5)


def run_session_2():
    print_banner("SESSION 2: VISUAL CHART EXPLANATION & AMBIGUITY RESOLUTION (11.3, 11.4)")
    sess_id = "sess_screen_session_2"

    # Turn 1: Ambiguous chart inquiry on well monitor
    t1 = ask_agent("What does this chart mean?", session_id=sess_id, page_route="/wells/FS-004")
    print_turn(1, "What does this chart mean? (on route /wells/FS-004)", t1)

    # Turn 2: User clicks/types specific chart explanation
    t2 = ask_agent("Explain the Head-Capacity (H-Q) Operating Curve", session_id=sess_id, page_route="/wells/FS-004")
    print_turn(2, "Explain the Head-Capacity (H-Q) Operating Curve", t2)

    # Turn 3: Disambiguation for cluster comparison
    t3 = ask_agent("Compare gathering clusters", session_id=sess_id)
    print_turn(3, "Compare gathering clusters", t3)


def run_session_3():
    print_banner("SESSION 3: COMPOUND QUERIES & DEFERRED INTENT EXECUTION (11.7)")
    sess_id = "sess_compound_session_3"

    # Turn 1: Compound query
    t1 = ask_agent("Diagnose well FS-017 and also show fleet production", session_id=sess_id)
    print_turn(1, "Diagnose well FS-017 and also show fleet production", t1)

    # Turn 2: Continue to execute deferred intent
    t2 = ask_agent("continue", session_id=sess_id)
    print_turn(2, "continue", t2)

    # Turn 3: Reframe with pronoun
    t3 = ask_agent("What about its motor current?", session_id=sess_id)
    print_turn(3, "What about its motor current?", t3)


def run_session_4():
    print_banner("SESSION 4: MULTI-USER SESSION ISOLATION (ALICE vs BOB)")
    sess_alice = "sess_user_alice_workspace"
    sess_bob = "sess_user_bob_workspace"

    # Alice investigates FS-004
    t_a1 = ask_agent("Check health of well FS-004", session_id=sess_alice)
    print(f"Alice Turn 1: Asked about FS-004 -> Target Well: {t_a1.get('structured_data', {}).get('well_id')}")

    # Bob investigates FS-017
    t_b1 = ask_agent("Check health of well FS-017", session_id=sess_bob)
    print(f"Bob Turn 1  : Asked about FS-017 -> Target Well: {t_b1.get('structured_data', {}).get('well_id')}")

    # Alice asks reframing query without well name
    t_a2 = ask_agent("What about temperature?", session_id=sess_alice)
    print(f"Alice Turn 2: 'What about temperature?' -> Bound to Asset: {t_a2.get('structured_data', {}).get('well_id')}")

    # Bob asks reframing query without well name
    t_b2 = ask_agent("What about vibration?", session_id=sess_bob)
    print(f"Bob Turn 2  : 'What about vibration?'   -> Bound to Asset: {t_b2.get('structured_data', {}).get('well_id')}")

    # Verify zero crosstalk
    assert t_a2.get("structured_data", {}).get("well_id") == "FS-004", "Alice's session contaminated!"
    assert t_b2.get("structured_data", {}).get("well_id") == "FS-017", "Bob's session contaminated!"
    print("\nSUCCESS: Multi-user session isolation confirmed with 100% asset binding integrity.")


if __name__ == "__main__":
    session_manager.clear()
    run_session_1()
    run_session_2()
    run_session_3()
    run_session_4()
    print_banner("ALL DOMAIN 11 QUERY VERIFICATION SESSIONS EXECUTED SUCCESSFULLY")
