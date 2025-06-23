
import numpy as np
from typing import List, Dict
from core.models import CurveData, GraphData
from core.utils import generate_random_color


def curve_to_dict(curve: CurveData) -> dict:
    return {
        "name": curve.name,
        "x": curve.x.tolist(),
        "y": curve.y.tolist(),
        "color": curve.color,
        "width": curve.width,
        "style": curve.style,
        "downsampling_mode": curve.downsampling_mode,
        "downsampling_ratio": curve.downsampling_ratio,
        "opacity": curve.opacity,
        "symbol": curve.symbol,
        "fill": curve.fill,
        "display_mode": curve.display_mode,
        "gain": curve.gain,
        "units_per_grid": curve.units_per_grid,
        "gain_mode": curve.gain_mode,
        "offset": curve.offset,
        "time_offset": curve.time_offset,
        "show_zero_line": curve.show_zero_line,
        "label_mode": curve.label_mode,
        "zero_indicator": curve.zero_indicator

    }


def dict_to_curve(data: dict) -> CurveData:
    color = data.get("color")
    if not color or color.lower() in {"#000000", "black", "#ffffff", "white", "b", "w"}:
        color = generate_random_color()
    return CurveData(
        name=data["name"],
        x=data["x"],
        y=data["y"],
        color=color,
        width=data.get("width", 2),
        style=data.get("style"),
        downsampling_mode=data.get("downsampling_mode", "auto"),
        downsampling_ratio=data.get("downsampling_ratio", 1),
        opacity=data.get("opacity", 100.0),
        symbol=data.get("symbol"),
        fill=data.get("fill", False),
        display_mode=data.get("display_mode", "line"),
        gain=data.get("gain", 1.0),
        units_per_grid=data.get("units_per_grid", 1.0),
        gain_mode=data.get("gain_mode", "multiplier"),
        offset=data.get("offset", 0.0),
        time_offset=data.get("time_offset", 0.0),
        show_zero_line=data.get("show_zero_line", False),
        show_label=data.get("show_label", False),
        label_mode=data.get("label_mode", "none"),
        zero_indicator=data.get("zero_indicator", "none")


    )


def graph_to_dict(graph: GraphData) -> dict:
    return {
        "name": graph.name,
        "properties": {
            "grid_visible": graph.grid_visible,
            "dark_mode": graph.dark_mode,
            "log_x": graph.log_x,
            "log_y": graph.log_y,
            "font": graph.font,
            "fix_y_range": graph.fix_y_range,
            "y_min": graph.y_min,
            "y_max": graph.y_max,
            "x_unit": graph.x_unit,
            "y_unit": graph.y_unit,
            "x_format": graph.x_format,
            "y_format": graph.y_format,
            "mode": graph.mode
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
    g.fix_y_range = props.get("fix_y_range", False)
    g.y_min = props.get("y_min", -5.0)
    g.y_max = props.get("y_max", 5.0)
    g.x_unit = props.get("x_unit", "")
    g.y_unit = props.get("y_unit", "")
    g.x_format = props.get("x_format", "normal")
    g.y_format = props.get("y_format", "normal")
    g.mode = props.get("mode", "standard")


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
