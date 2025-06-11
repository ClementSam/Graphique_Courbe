
import json
from typing import Dict
from core.models import GraphData
from serializers import project_to_dict, dict_to_project

def export_project_to_json(graphs: Dict[str, GraphData], path: str):
    """Exporte un projet (ensemble de graphiques) vers un fichier JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(project_to_dict(graphs), f, indent=2)

def import_project_from_json(path: str) -> Dict[str, GraphData]:
    """Imprte un projet (ensemble de graphiques) depuis un fichier JSON."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return dict_to_project(data)
