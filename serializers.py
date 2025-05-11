
import numpy as np
from typing import List, Dict
from models import CurveData, GraphData


def curve_to_dict(curve: CurveData) -> dict:
    return {
        "name": curve.name,
        "x": curve.x.tolist(),
        "y": curve.y.tolist(),
        "color": curve.color,
        "width": curve.width,
        "style": curve.style,
        "downsampling_mode": curve.downsampling_mode,
        "downsampling_ratio": curve.downsampling_ratio
    }


def dict_to_curve(data: dict) -> CurveData:
    return CurveData(
        name=data["name"],
        x=data["x"],
        y=data["y"],
        color=data.get("color", "b"),
        width=data.get("width", 2),
        style=data.get("style"),
        downsampling_mode=data.get("downsampling_mode", "auto"),
        downsampling_ratio=data.get("downsampling_ratio", 1)
    )


def graph_to_dict(graph: GraphData) -> dict:
    return {
        "name": graph.name,
        "properties": {
            "grid_visible": graph.grid_visible,
            "dark_mode": graph.dark_mode,
            "log_x": graph.log_x,
            "log_y": graph.log_y,
            "font": graph.font
        },
        "curves": [curve_to_dict(c) for c in graph.curves]
    }


def dict_to_graph(data: dict) -> GraphData:
    g = GraphData(name=data["name"])
    props = data.get("properties", {})
    g.grid_visible = props.get("grid_visible", False)
    g.dark_mode = props.get("dark_mode", False)
    g.log_x = props.get("log_x", False)
    g.log_y = props.get("log_y", False)
    g.font = props.get("font", "Arial")
    for cdict in data.get("curves", []):
        g.add_curve(dict_to_curve(cdict))
    return g


def project_to_dict(graphs: Dict[str, GraphData]) -> dict:
    return {
        "version": 1,
        "graphs": [graph_to_dict(g) for g in graphs.values()]
    }


def dict_to_project(data: dict) -> Dict[str, GraphData]:
    graphs = {}
    for gdict in data.get("graphs", []):
        g = dict_to_graph(gdict)
        graphs[g.name] = g
    return graphs
