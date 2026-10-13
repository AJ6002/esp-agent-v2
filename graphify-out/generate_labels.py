import json, sys
sys.stdout.reconfigure(encoding='utf-8')

analysis = json.loads(open("graphify-out/.graphify_analysis.json", encoding="utf-8").read())
graph = json.loads(open("graphify-out/graph.json", encoding="utf-8").read())

node_map = {n["id"]: n for n in graph["nodes"]}
communities = analysis["communities"]

labels_dict = {}

for cid, nids in communities.items():
    sources = [node_map[nid].get("source_file", "") for nid in nids if nid in node_map]
    sources = [s for s in sources if s]
    # compute most common directory or module
    modules = {}
    for s in sources:
        parts = s.replace("\\", "/").split("/")
        mod = "/".join(parts[:3]) if len(parts) >= 3 else (parts[0] if parts else "general")
        modules[mod] = modules.get(mod, 0) + 1
    top_mod = sorted(modules.items(), key=lambda x: x[1], reverse=True)[0][0] if modules else "general"
    
    # derive a descriptive 2-5 word label
    if "industrial_gateway" in top_mod:
        if any("alarm" in s.lower() for s in sources):
            name = "Industrial Alarm Intelligence Engine"
        elif any("opcua" in s.lower() for s in sources):
            name = "OPC UA Gateway & Protocol Subscription"
        elif any("simulator" in s.lower() for s in sources):
            name = "Equipment OPC UA Simulator"
        else:
            name = "Industrial Gateway & Quality Pipeline"
    elif "ml" in top_mod:
        if any("rul" in s.lower() for s in sources):
            name = "RUL Research & Lifetime Prediction"
        elif any("fault" in s.lower() for s in sources):
            name = "Bearing Fault Classification V2"
        elif any("feature" in s.lower() for s in sources):
            name = "Vibration Feature Extraction"
        else:
            name = "Predictive ML & Model Registry"
    elif "ai" in top_mod:
        if any("knowledge" in s.lower() for s in sources):
            name = "RAG & Knowledge Retrieval System"
        else:
            name = "AI Copilot & LLM Agent Diagnostics"
    elif "services" in top_mod:
        if any("approval" in s.lower() for s in sources):
            name = "Human-in-the-Loop Approval Service"
        elif any("workorder" in s.lower() for s in sources):
            name = "Work Order Lifecycle Service"
        elif any("observability" in s.lower() for s in sources):
            name = "Trace & Observability Service"
        else:
            name = "Core Maintenance Services"
    elif "api" in top_mod and "endpoints" in str(sources):
        if any("intelligence" in s.lower() for s in sources):
            name = "Intelligence & Simulation Endpoints"
        elif any("work_orders" in s.lower() for s in sources):
            name = "Work Orders & Scheduling Endpoints"
        elif any("observability" in s.lower() for s in sources):
            name = "Observability & Tracing Endpoints"
        elif any("equipment" in s.lower() for s in sources):
            name = "Equipment & Spare Parts Endpoints"
        else:
            name = f"API Endpoints ({top_mod.split('/')[-1]})"
    elif "web" in top_mod:
        if any("observability" in s.lower() for s in sources):
            name = "Web Observability & Traces UI"
        elif any("work-orders" in s.lower() for s in sources) or any("work_order" in s.lower() for s in sources):
            name = "Web Work Orders & Dispatch UI"
        elif any("approvals" in s.lower() for s in sources):
            name = "Web Human Approval Center"
        elif any("telemetry" in s.lower() for s in sources) or any("monitoring" in s.lower() for s in sources):
            name = "Web Telemetry & Realtime Monitoring"
        elif any("demo" in s.lower() for s in sources):
            name = "Web Interactive Demo Console"
        elif any("test" in s.lower() for s in sources):
            name = "Web UI Testing & Specs"
        else:
            name = f"Web Frontend Components ({cid})"
    elif "scripts" in top_mod:
        name = "Dataset Preparation & ML Research Scripts"
    elif "models" in top_mod:
        name = "SQLAlchemy Domain Models"
    elif "schemas" in top_mod:
        name = "Pydantic Schemas & Data Contracts"
    elif "core" in top_mod:
        name = "Core Config, Security & OpenTelemetry"
    else:
        name = f"Module Group {cid} ({top_mod})"
    labels_dict[int(cid)] = name

print("Sample labeled communities:")
for cid in list(labels_dict.keys())[:10]:
    print(f"  {cid}: {labels_dict[cid]}")

open("graphify-out/.graphify_labels_gen.json", "w", encoding="utf-8").write(json.dumps(labels_dict, ensure_ascii=False))
