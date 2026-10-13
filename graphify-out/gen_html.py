import json
from pathlib import Path
from graphify.build import build_from_json
from graphify.export import to_html

extraction = json.loads(Path('graphify-out/.graphify_extract.json').read_text(encoding="utf-8"))
analysis   = json.loads(Path('graphify-out/.graphify_analysis.json').read_text(encoding="utf-8"))
labels_raw = json.loads(Path('graphify-out/.graphify_labels.json').read_text(encoding="utf-8"))
labels = {int(k): v for k, v in labels_raw.items()}

G = build_from_json(extraction, root='.', directed=False)
communities = {int(k): v for k, v in analysis['communities'].items()}

to_html(G, communities, 'graphify-out/graph.html', community_labels=labels)
print('graph.html generated successfully!')
