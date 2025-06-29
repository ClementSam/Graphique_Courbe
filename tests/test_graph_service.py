import os
import sys
import types
import importlib
import numpy as np
import pytest
from core.models import CurveData, SatelliteObjectData

# ensure repository root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.app_state import AppState

class DummySignal:
    def __init__(self):
        self.emitted = []
    def emit(self, *args, **kwargs):
        self.emitted.append(args)

@pytest.fixture
def service(monkeypatch):
    # stub signal_bus before importing GraphService
    bus_module = types.ModuleType("signal_bus")
    bus_module.signal_bus = types.SimpleNamespace(
        graph_selected=DummySignal(),
        curve_selected=DummySignal(),
        curve_list_updated=DummySignal(),
        curve_updated=DummySignal(),
        graph_updated=DummySignal(),
    )
    monkeypatch.setitem(sys.modules, "signal_bus", bus_module)

    import core.graph_service as gs
    importlib.reload(gs)

    AppState._instance = None
    state = AppState.get_instance()
    service = gs.GraphService(state)
    return service, state, bus_module.signal_bus


def test_add_graph_and_curve(service):
    svc, state, bus = service
    svc.add_graph()
    name = list(state.graphs.keys())[0]
    assert state.current_graph.name == name
    svc.add_curve(name, curve=CurveData(name="tmp", x=[0], y=[0]))
    assert len(state.current_graph.curves) == 1
    # the provided name should be kept since no conflict exists
    assert state.current_curve.name == "tmp"


def test_rename_graph_and_curve(service):
    svc, state, _ = service
    svc.add_graph()
    name = list(state.graphs.keys())[0]
    svc.add_curve(name, curve=CurveData(name="tmp", x=[0], y=[0]))
    svc.rename_graph(name, "NewGraph")
    assert "NewGraph" in state.graphs
    svc.select_graph("NewGraph")
    svc.rename_curve("tmp", "Renamed")
    assert state.current_graph.curves[0].name == "Renamed"


def test_set_visibility(service):
    svc, state, _ = service
    svc.add_graph()
    graph = list(state.graphs.keys())[0]
    svc.add_curve(graph, curve=CurveData(name="tmp", x=[0], y=[0]))

    svc.set_graph_visible(graph, False)
    assert state.graphs[graph].visible is False

    svc.set_curve_visible(graph, "tmp", False)
    assert state.graphs[graph].curves[0].visible is False

def test_graph_options(service):
    svc, state, _ = service
    svc.add_graph()
    name = list(state.graphs.keys())[0]
    svc.select_graph(name)

    svc.set_dark_mode(True)
    svc.set_grid_visible(True)
    svc.set_log_x(True)
    svc.set_log_y(True)

    assert state.current_graph.dark_mode is True
    assert state.current_graph.grid_visible is True
    assert state.current_graph.log_x is True
    assert state.current_graph.log_y is True


def test_axis_settings(service):
    svc, state, _ = service
    svc.add_graph()
    name = list(state.graphs.keys())[0]
    svc.select_graph(name)

    svc.set_x_unit("s")
    svc.set_y_unit("V")
    svc.set_x_format("scientific")
    svc.set_y_format("scaled")
    svc.set_fix_y_range(True)
    svc.set_y_limits(-1, 1)

    g = state.current_graph
    assert g.x_unit == "s"
    assert g.y_unit == "V"
    assert g.x_format == "scientific"
    assert g.y_format == "scaled"
    assert g.fix_y_range is True
    assert g.y_min == -1
    assert g.y_max == 1


def test_set_time_offset(service):
    svc, state, _ = service
    svc.add_graph()
    graph = list(state.graphs.keys())[0]
    svc.add_curve(graph, curve=CurveData(name="tmp", x=[0], y=[0]))

    svc.set_time_offset(2.5)
    assert state.current_curve.time_offset == 2.5




def test_add_zone(service):
    svc, state, _ = service
    svc.add_graph()
    name = list(state.graphs.keys())[0]
    svc.select_graph(name)

    svc.add_zone({"type": "vlinear", "bounds": [0, 1]})

    zones = state.current_graph.zones
    assert len(zones) == 1
    assert zones[0]["type"] == "vlinear"


def test_remove_zone(service):
    svc, state, _ = service
    svc.add_graph()
    name = list(state.graphs.keys())[0]
    svc.select_graph(name)

    svc.add_zone({"type": "vlinear", "bounds": [0, 1]})
    svc.add_zone({"type": "rect", "rect": [0, 0, 1, 1]})

    svc.remove_zone(0)

    zones = state.current_graph.zones
    assert len(zones) == 1
    assert zones[0]["type"] == "rect"


def test_bring_curve_to_front_moves_curve(service):
    svc, state, _ = service
    svc.add_graph()
    graph = list(state.graphs.keys())[0]

    svc.add_curve(graph, curve=CurveData(name="a", x=[0], y=[0]))
    svc.add_curve(graph, curve=CurveData(name="b", x=[0], y=[0]))

    svc.select_curve("a")
    svc.bring_curve_to_front()

    curves = [c.name for c in state.current_graph.curves]
    assert curves[-1] == "a"


def test_add_curve_duplicate_name_appends_index(service):
    svc, state, _ = service
    svc.add_graph()
    graph = list(state.graphs.keys())[0]

    svc.add_curve(graph, curve=CurveData(name="dup", x=[0], y=[0]))
    svc.add_curve(graph, curve=CurveData(name="dup", x=[0], y=[0]))

    assert state.graphs[graph].curves[0].name == "dup"
    assert state.graphs[graph].curves[1].name == "dup (1)"


def test_create_bit_curves(service):
    svc, state, _ = service
    svc.add_graph()
    graph = list(state.graphs.keys())[0]
    curve = CurveData(name="base", x=[0, 1, 2, 3], y=[0, 1, 2, 3])
    svc.add_curve(graph, curve=curve)

    created = svc.create_bit_curves("base")

    assert created == ["base[0]", "base[1]"]
    assert len(state.current_graph.curves) == 3
    bit0 = state.current_graph.curves[1]
    assert bit0.parent_curve == "base"
    assert bit0.bit_index == 0


def test_create_bit_curves_invalid_data_raises(service):
    svc, state, _ = service
    svc.add_graph()
    graph = list(state.graphs.keys())[0]
    curve = CurveData(name="bad", x=[0, 1], y=[0.1, 1.2])
    svc.add_curve(graph, curve=curve)

    with pytest.raises(ValueError):
        svc.create_bit_curves("bad")


def test_create_bit_curves_negative_values_raises(service):
    svc, state, _ = service
    svc.add_graph()
    graph = list(state.graphs.keys())[0]
    curve = CurveData(name="neg", x=[0, 1], y=[-1, 0])
    svc.add_curve(graph, curve=curve)

    with pytest.raises(ValueError):
        svc.create_bit_curves("neg")


def test_create_bit_curves_with_nan_values(service):
    svc, state, _ = service
    svc.add_graph()
    graph = list(state.graphs.keys())[0]
    curve = CurveData(name="nan", x=[0, 1, 2], y=[0, float('nan'), 3])
    svc.add_curve(graph, curve=curve)

    created = svc.create_bit_curves("nan")

    assert created == ["nan[0]", "nan[1]"]
    assert np.isnan(state.current_graph.curves[1].y[1])
    assert np.isnan(state.current_graph.curves[2].y[1])


def test_create_bit_group_curve(service):
    svc, state, _ = service
    svc.add_graph()
    graph = list(state.graphs.keys())[0]
    curve = CurveData(name="base", x=[0, 1, 2, 3], y=[0, 1, 2, 3])
    svc.add_curve(graph, curve=curve)

    created = svc.create_bit_group_curve("base", [1, 0], "grp")

    assert created == "grp"
    assert len(state.current_graph.curves) == 2
    new_curve = state.current_graph.curves[1]
    assert np.array_equal(new_curve.y, [0, 2, 1, 3])


def test_logic_analyzer_mode_applies_offsets(service):
    svc, state, _ = service
    svc.add_graph()
    gname = list(state.graphs.keys())[0]
    c1 = CurveData(name="c1", x=[0], y=[0])
    c2 = CurveData(name="c2", x=[0], y=[0])
    c3 = CurveData(name="c3", x=[0], y=[0])
    state.graphs[gname].curves = [c1, c2, c3]

    svc.apply_mode(gname, "logic_analyzer")

    assert c3.offset == pytest.approx(0.05)
    assert c2.offset == pytest.approx(1.05)
    assert c1.offset == pytest.approx(2.05)

    zones = state.graphs[gname].zones
    assert len(zones) == 3
    assert all(z["type"] == "hlinear" for z in zones)
    assert zones[0]["bounds"] == [0, 1]
    assert zones[1]["bounds"] == [1, 2]
    assert zones[2]["bounds"] == [2, 3]
    assert all(z["line_color"] == "#000000" for z in zones)
    assert all(z["line_width"] == 1 for z in zones)
    assert all(z["fill_alpha"] == 50 for z in zones)

    c2.visible = False
    svc.apply_mode(gname, "logic_analyzer")
    assert c3.offset == pytest.approx(0.05)
    assert c1.offset == pytest.approx(1.05)
    zones = state.graphs[gname].zones
    assert len(zones) == 2
    assert zones[0]["bounds"] == [0, 1]
    assert zones[1]["bounds"] == [1, 2]


def test_satellite_object_operations(service):
    svc, state, _ = service
    svc.add_graph()
    name = list(state.graphs.keys())[0]
    svc.select_graph(name)

    obj = SatelliteObjectData(obj_type="text", name="label")
    svc.add_satellite_object("left", obj)
    assert len(state.current_graph.satellite_objects["left"]) == 1

    new = SatelliteObjectData(obj_type="button", name="btn")
    svc.update_satellite_object("left", 0, new)
    assert state.current_graph.satellite_objects["left"][0].name == "btn"

    svc.add_satellite_object("left", obj)
    svc.move_satellite_object("left", 0, 1)
    assert state.current_graph.satellite_objects["left"][1].name == "btn"

    svc.remove_satellite_object("left", 0)
    assert len(state.current_graph.satellite_objects["left"]) == 1

