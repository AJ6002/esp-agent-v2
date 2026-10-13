import json
import time
from app.db.session import SessionLocal
from app.ai.copilot import ask as ai_ask
from app.services.esp_diagnosis_service import route_query_hybrid

print("=" * 80)
print("VERIFICATION SUITE: ADVANCED CAPABILITY UPGRADES")
print("1. Multi-Well Comparative Analysis")
print("2. Temporal Filtering on Historical Audits")
print("3. Multi-Turn Conversational Memory & Antecedent Resolution")
print("4. Conceptual vs Active Trip Disambiguation")
print("=" * 80)

db = SessionLocal()

# Test 1: Conceptual vs Active Trip Disambiguation
print("\n--- TEST 1: Conceptual vs Active Trip Disambiguation ---")
q_conceptual_1 = "What causes an ESP pump to trip?"
route_c1 = route_query_hybrid(q_conceptual_1)
print(f"Query: '{q_conceptual_1}'")
print(f"Routing Intent: {route_c1.intent} | Tier: {route_c1.routing_tier} | Needs Clarify: {route_c1.needs_clarification}")
assert route_c1.needs_clarification == False, "FAILED: Conceptual query should NOT trigger HITL clarification!"
assert str(route_c1.intent) == "ESPIntentEnum.KNOWLEDGE", f"FAILED: Expected KNOWLEDGE, got {route_c1.intent}"
print("PASSED: Correctly routed conceptual question to KNOWLEDGE RAG without HITL interruption.")

q_conceptual_2 = "How to prevent high vibration trips in ESPs?"
route_c2 = route_query_hybrid(q_conceptual_2)
print(f"Query: '{q_conceptual_2}'")
print(f"Routing Intent: {route_c2.intent} | Tier: {route_c2.routing_tier} | Needs Clarify: {route_c2.needs_clarification}")
assert route_c2.needs_clarification == False, "FAILED: Conceptual query should NOT trigger HITL clarification!"
print("PASSED: Conceptual vibration prevention query routed cleanly.")

# Test 2: Multi-Well Comparison
print("\n--- TEST 2: Multi-Well Comparative Analysis ---")
q_compare = "Compare well FS-017 vs FS-040"
route_comp = route_query_hybrid(q_compare)
print(f"Query: '{q_compare}'")
print(f"Routing Intent: {route_comp.intent} | Entities: {route_comp.entities} | Tier: {route_comp.routing_tier}")
assert str(route_comp.intent) == "ESPIntentEnum.MULTI_WELL_COMPARE", f"FAILED: Expected MULTI_WELL_COMPARE, got {route_comp.intent}"
assert "FS-017" in route_comp.entities and "FS-040" in route_comp.entities, "FAILED: Missing well IDs in entities!"

res_comp = ai_ask(db, q_compare)
print(f"Comparison Response Length: {len(res_comp.answer)} chars | Confidence: {res_comp.confidence}")
print("\n[Snippet of Comparison Output]:")
print("\n".join(res_comp.answer.splitlines()[:25]))
assert "Operating State" in res_comp.answer, "FAILED: Comparison table missing Operating State!"
assert "FS-017" in res_comp.answer and "FS-040" in res_comp.answer, "FAILED: Comparison table missing well columns!"
print("PASSED: Multi-well side-by-side comparison generated successfully.")

# Test 3: Temporal Window Filtering on Historical Audits
print("\n--- TEST 3: Temporal Window Filtering on Historical Audits ---")
q_temporal = "Show trips for well FS-017 in the last 7 days"
route_temp = route_query_hybrid(q_temporal)
print(f"Query: '{q_temporal}'")
print(f"Routing Intent: {route_temp.intent} | Entity: {route_temp.entity} | Time Filter: {route_temp.time_filter_label}")
assert str(route_temp.intent) == "ESPIntentEnum.WELL_HISTORY"
assert route_temp.time_filter_label == "Last 7 Days", f"FAILED: Expected 'Last 7 Days', got {route_temp.time_filter_label}"

res_temp = ai_ask(db, q_temporal)
print(f"Temporal Response Length: {len(res_temp.answer)} chars | Citations: {len(res_temp.citations)}")
print("\n[Snippet of Temporal Output Header]:")
print("\n".join(res_temp.answer.splitlines()[:10]))
assert "Audit Window" in res_temp.answer, "FAILED: Audit Window missing from report!"
print("PASSED: Temporal filtering applied to historical audit successfully.")

# Test 4: Multi-Turn Antecedent Resolution
print("\n--- TEST 4: Multi-Turn Antecedent Resolution ---")
# Turn 1: User asks about well FS-017
t1_query = "Check health condition for well FS-017"
res_t1 = ai_ask(db, t1_query)
print(f"Turn 1 Query: '{t1_query}' -> Status: Answered for FS-017")

# Turn 2: Follow-up question using pronoun 'it' without well ID
conversation_history = [
    {"role": "user", "content": t1_query},
    {"role": "assistant", "content": res_t1.answer},
]
t2_query = "Why did it trip?"
route_t2 = route_query_hybrid(t2_query, conversation_history=conversation_history)
print(f"Turn 2 Query: '{t2_query}'")
print(f"Resolved Entity: {route_t2.entity} | Intent: {route_t2.intent} | Tier: {route_t2.routing_tier} | Needs Clarify: {route_t2.needs_clarification}")
assert route_t2.needs_clarification == False, "FAILED: Should resolve 'it' to FS-017 instead of prompting HITL clarification!"
assert route_t2.entity == "FS-017", f"FAILED: Expected entity FS-017, got {route_t2.entity}"

res_t2 = ai_ask(db, t2_query, conversation_history=conversation_history)
print(f"Turn 2 Answer Length: {len(res_t2.answer)} chars | Needs Clarify: {res_t2.needs_clarification}")
print("PASSED: Multi-turn pronoun 'it' successfully bound to Turn 1 asset context.")

# Turn 3: Second follow-up question
conversation_history.extend([
    {"role": "user", "content": t2_query},
    {"role": "assistant", "content": res_t2.answer},
])
t3_query = "What is its current temperature?"
route_t3 = route_query_hybrid(t3_query, conversation_history=conversation_history)
print(f"Turn 3 Query: '{t3_query}'")
print(f"Resolved Entity: {route_t3.entity} | Intent: {route_t3.intent} | Tier: {route_t3.routing_tier}")
assert route_t3.entity == "FS-017", f"FAILED: Expected entity FS-017, got {route_t3.entity}"
res_t3 = ai_ask(db, t3_query, conversation_history=conversation_history)
print(f"Turn 3 Answer Length: {len(res_t3.answer)} chars | Needs Clarify: {res_t3.needs_clarification}")
print("PASSED: Multi-turn telemetry query successfully bound to context asset.")

db.close()
print("\n" + "=" * 80)
print("ALL 4 CAPABILITY UPGRADE VERIFICATIONS PASSED WITH ZERO ERRORS!")
print("=" * 80)
