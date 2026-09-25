import json
import pickle
from pathlib import Path
import networkx as nx
from networkx.readwrite import node_link_data

old = Path("./graph/htb_graph.pkl")
new = Path("./graph/htb_graph.json")

if old.exists():
    with open(old, "rb") as f:
        G = pickle.load(f)
    data = node_link_data(G)
    new.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Migrated {old} -> {new} ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)")

else:
    print(f"{old} does not exist. Nothing to migrate.")
