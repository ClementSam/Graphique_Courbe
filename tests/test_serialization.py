import os
import sys
import numpy as np
import pytest


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.models import CurveData, GraphData

from IO_dossier.curve_io import export_curve_to_json, import_curve_from_json
from IO_dossier.graph_io import export_graph_to_json, import_graph_from_json
from IO_dossier.project_io import export_project_to_json, import_project_from_json
from IO_dossier import serializers


def create_sample_curve(name="c1"):
    c = CurveData(name=name, x=[0,1,2], y=[1,2,3], time_offset=1.5)
    # attributes expected by serializers but missing in dataclass
    c.show_zero_line = False
    c.show_label = False
    return c


@pytest.fixture(autouse=True)
def patch_serializers(monkeypatch):
    def patched_dict_to_curve(data: dict) -> CurveData:
        curve = CurveData(
            name=data["name"],
            x=data["x"],
            y=data["y"],
            color=data.get("color", "b"),
            width=data.get("width", 2),
            style=data.get("style"),
            downsampling_mode=data.get("downsampling_mode", "auto"),
            downsampling_ratio=data.get("downsampling_ratio", 1),
            opacity=data.get("opacity", 100.0),
            symbol=data.get("symbol"),
            fill=data.get("fill", False),
            display_mode=data.get("display_mode", "line"),
            gain=data.get("gain", 1.0),
            offset=data.get("offset", 0.0),
            time_offset=data.get("time_offset", 0.0),
            label_mode=data.get("label_mode", "none"),
            zero_indicator=data.get("zero_indicator", "none"),
        )
        curve.show_zero_line = data.get("show_zero_line", False)
        curve.show_label = data.get("show_label", False)
        return curve

    monkeypatch.setattr(serializers, "dict_to_curve", patched_dict_to_curve)
    import IO_dossier.curve_io as curve_io
    monkeypatch.setattr(curve_io, "dict_to_curve", patched_dict_to_curve)


def test_curve_serialization(tmp_path):
    curve = create_sample_curve()
    path = tmp_path / "curve.json"
    export_curve_to_json(curve, str(path))
    loaded = import_curve_from_json(str(path))
    assert loaded.name == curve.name
    assert np.array_equal(loaded.x, curve.x)
    assert np.array_equal(loaded.y, curve.y)
    assert loaded.time_offset == curve.time_offset


def test_graph_serialization(tmp_path):
    graph = GraphData(name="g")
    graph.add_curve(create_sample_curve())
    path = tmp_path / "graph.json"
    export_graph_to_json(graph, str(path))
    loaded = import_graph_from_json(str(path))
    assert loaded.name == graph.name
    assert len(loaded.curves) == 1
    assert loaded.curves[0].name == graph.curves[0].name
    assert loaded.curves[0].time_offset == graph.curves[0].time_offset


def test_project_serialization(tmp_path):
    g1 = GraphData(name="g1")
    g1.add_curve(create_sample_curve("c1"))
    g2 = GraphData(name="g2")
    g2.add_curve(create_sample_curve("c2"))
    graphs = {"g1": g1, "g2": g2}
    path = tmp_path / "project.json"
    export_project_to_json(graphs, str(path))
    loaded = import_project_from_json(str(path))
    assert set(loaded.keys()) == {"g1", "g2"}
    assert len(loaded["g1"].curves) == 1
    assert loaded["g1"].curves[0].name == "c1"
    assert loaded["g1"].curves[0].time_offset == g1.curves[0].time_offset
