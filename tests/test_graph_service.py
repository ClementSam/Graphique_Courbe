import os
import sys
import types
import importlib
import pytest
from core.models import CurveData

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
    assert state.current_curve.name == "Courbe 1"


def test_rename_graph_and_curve(service):
    svc, state, _ = service
    svc.add_graph()
    name = list(state.graphs.keys())[0]
    svc.add_curve(name, curve=CurveData(name="tmp", x=[0], y=[0]))
    svc.rename_graph(name, "NewGraph")
    assert "NewGraph" in state.graphs
    svc.select_graph("NewGraph")
    svc.rename_curve("Courbe 1", "Renamed")
    assert state.current_graph.curves[0].name == "Renamed"


def test_set_visibility(service):
    svc, state, _ = service
    svc.add_graph()
    graph = list(state.graphs.keys())[0]
    svc.add_curve(graph, curve=CurveData(name="tmp", x=[0], y=[0]))

    svc.set_graph_visible(graph, False)
    assert state.graphs[graph].visible is False

    svc.set_curve_visible(graph, "Courbe 1", False)
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
