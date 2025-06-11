import os
import sys
import types
import importlib
import pytest

# add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.app_state import AppState

class DummySignal:
    def __init__(self):
        self.emitted = []
    def emit(self, *args, **kwargs):
        self.emitted.append(args)

def make_signal_bus():
    return types.SimpleNamespace(
        graph_selected=DummySignal(),
        curve_selected=DummySignal(),
        curve_list_updated=DummySignal(),
        curve_updated=DummySignal(),
        graph_updated=DummySignal(),
    )

class DummyCoordinator:
    def __init__(self, state, views, central_area):
        self.state = state
        self.views = views
        self.central_area = central_area
        self.plot_calls = 0
        self.curve_calls = 0
    def refresh_plot(self):
        self.plot_calls += 1
    def refresh_curve_ui(self):
        self.curve_calls += 1
    def reset_zoom(self):
        pass

@pytest.fixture
def controller(monkeypatch):
    # stub signal_bus before importing modules
    bus_module = types.ModuleType("signal_bus")
    bus_module.signal_bus = make_signal_bus()
    monkeypatch.setitem(sys.modules, "signal_bus", bus_module)

    # stub GraphUICoordinator module
    stub_coordinator_mod = types.ModuleType("ui.graph_ui_coordinator")
    stub_coordinator_mod.GraphUICoordinator = DummyCoordinator
    monkeypatch.setitem(sys.modules, "ui.graph_ui_coordinator", stub_coordinator_mod)

    # stub curve_generators
    curve_mod = types.ModuleType("curve_generators")
    from core.models import CurveData
    def gen(index=1):
        return CurveData(name=f"Courbe {index}", x=[0], y=[0])
    curve_mod.generate_random_curve = gen
    monkeypatch.setitem(sys.modules, "curve_generators", curve_mod)

    import controllers as ctrl
    importlib.reload(ctrl)

    AppState._instance = None
    state = AppState.get_instance()
    # start with empty views
    c = ctrl.GraphController({}, None)
    return c, state, bus_module.signal_bus


def test_controller_add_graph_and_curve(controller):
    c, state, bus = controller
    c.add_graph()
    assert len(state.graphs) == 1
    graph_name = list(state.graphs.keys())[0]
    c.add_curve(graph_name)
    assert len(state.graphs[graph_name].curves) == 1


def test_controller_rename_operations(controller):
    c, state, _ = controller
    c.add_graph()
    graph_name = list(state.graphs.keys())[0]
    c.add_curve(graph_name)
    c.rename_graph(graph_name, "RenamedGraph")
    assert "RenamedGraph" in state.graphs
    c.select_graph("RenamedGraph")
    c.rename_curve("Courbe 1", "C1")
    assert state.current_graph.curves[0].name == "C1"


def test_controller_reset_zoom_invokes_ui(controller):
    c, state, _ = controller

    called = {"count": 0}

    def stub():
        called["count"] += 1

    c.ui.reset_zoom = stub
    c.reset_zoom()

    assert called["count"] == 1
