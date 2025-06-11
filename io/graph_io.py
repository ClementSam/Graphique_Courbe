
import json
from core.models import GraphData
from .serializers import graph_to_dict, dict_to_graph

def export_graph_to_json(graph: GraphData, path: str):
    """Exporte un graphique (et ses courbes) vers un fichier JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(graph_to_dict(graph), f, indent=2)

def import_graph_from_json(path: str) -> GraphData:
    """Importe un graphique (et ses courbes) depuis un fichier JSON."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return dict_to_graph(data)
