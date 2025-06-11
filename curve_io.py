
import json
from typing import List
from core.models import CurveData
from serializers import curve_to_dict, dict_to_curve


def export_curve_to_json(curve: CurveData, path: str):
    """Exporte une courbe unique vers un fichier JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(curve_to_dict(curve), f, indent=2)


def import_curve_from_json(path: str) -> CurveData:
    """Importe une courbe unique à partir d’un fichier JSON."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return dict_to_curve(data)
