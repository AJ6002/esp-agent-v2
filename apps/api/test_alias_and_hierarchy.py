import sys
sys.stdout.reconfigure(encoding="utf-8")

from app.services.esp_diagnosis_service import normalize_well_id, extract_all_well_ids, route_query_hybrid, get_fleet_inventory_status

# Test 1: Alias normalization
aliases = [
    'fnw 1', 'fnw01', 'fnw-1', 'fnw1', 'FNW-001',
    'fs 17', 'fs17', 'fs-17', 'fs017', 'FS-017',
    'fs 40', 'fs40', 'fs-040', 'FS-040',
    'fsws-003', 'fsws 3', 'fsws003', 'fsws-001-a', 'fsws 1 a',
    'fws 1', 'fws-001', 'fws01'
]

print("--- 1. ALIAS NORMALIZATION RESULTS ---")
all_passed = True
for a in aliases:
    norm = normalize_well_id(a)
    print(f"  {a:<15} -> {norm}")
    if not norm:
        all_passed = False
print(f"All aliases normalized successfully: {all_passed}")

# Test 2: Fleet & Cluster Hierarchy Routing
print("\n--- 2. FLEET & CLUSTER HIERARCHY ROUTING ---")
test_queries = [
    "Show me the fleet inventory and cluster hierarchy",
    "How many wells are in cluster GCS-15?",
    "List wells in gcs 4",
    "What is the status of field FS?"
]

for q in test_queries:
    res = route_query_hybrid(q)
    print(f"  Query: \"{q}\" -> Intent: {res.intent.value}, Entity: {res.entity}")

# Test 3: Fleet Status Output
print("\n--- 3. FLEET STATUS HIERARCHY REPORT OUTPUT ---")
fleet = get_fleet_inventory_status()
print(fleet.markdown_report)
