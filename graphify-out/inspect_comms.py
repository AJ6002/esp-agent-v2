import json

analysis = json.loads(open("graphify-out/.graphify_analysis.json", encoding="utf-8").read())
graph = json.loads(open("graphify-out/graph.json", encoding="utf-8").read())

# map nodes to community
node_map = {n["id"]: n for n in graph["nodes"]}
communities = analysis["communities"]

# Find top communities by size
sorted_comms = sorted(communities.items(), key=lambda x: len(x[1]), reverse=True)
print(f"Total communities: {len(sorted_comms)}")
for cid, nids in sorted_comms[:15]:
    labels = [node_map[nid].get("label", nid) for nid in nids if nid in node_map][:8]
    print(f"Community {cid} ({len(nids)} nodes): {', '.join(labels)}")
