import json
from typing import List
from models import CurveData
from serializers import dict_to_curve
from import_utils import load_curves_from_file


def load_curve_by_format(path: str, fmt: str) -> List[CurveData]:
    if fmt == "internal_json":
        return [load_internal_json(path)]
    elif fmt == "csv_standard":
        return load_curves_from_file(path)
    elif fmt == "keysight_json_v5":
        return load_keysight_json_v5(path)
    elif fmt == "tektro_json_v1_2":
        return load_tektro_json_v1_2(path)
    else:
        raise ValueError(f"Format inconnu : {fmt}")


def load_internal_json(path: str) -> CurveData:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return dict_to_curve(data)


def load_keysight_json_v5(path: str) -> List[CurveData]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict) or "samples" not in data:
        raise ValueError("Fichier Keysight V5 invalide")

    x = [pt[0] for pt in data["samples"]]
    y = [pt[1] for pt in data["samples"]]
    name = data.get("label", "Keysight")
    curve = CurveData(name=name, x=x, y=y)
    return [curve]


def load_tektro_json_v1_2(path: str) -> List[CurveData]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    metadata = data.get("meta", {})
    waveform = data.get("waveform", {})

    if not waveform or "X" not in waveform or "Y" not in waveform:
        raise ValueError("Fichier TEKTRO V1.2 invalide")

    x = waveform["X"]
    y = waveform["Y"]
    name = metadata.get("name", "Tektro")
    curve = CurveData(name=name, x=x, y=y)
    return [curve]
