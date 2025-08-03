import os
import sys
import types
import importlib
import numpy as np
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
        graph_visibility_changed=DummySignal(),
        curve_visibility_changed=DummySignal(),
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
    def reset_zoom_x(self):
        pass
    def reset_zoom_y(self):
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


def test_controller_reset_zoom_x_invokes_ui(controller):
    c, _, _ = controller
    called = {"count": 0}
    def stub():
        called["count"] += 1
    c.ui.reset_zoom_x = stub
    c.reset_zoom_x()
    assert called["count"] == 1


def test_controller_reset_zoom_y_invokes_ui(controller):
    c, _, _ = controller
    called = {"count": 0}
    def stub():
        called["count"] += 1
    c.ui.reset_zoom_y = stub
    c.reset_zoom_y()
    assert called["count"] == 1


def test_controller_set_visibility(controller):
    c, state, bus = controller
    c.add_graph()
    graph = list(state.graphs.keys())[0]
    c.add_curve(graph)

    bus.graph_updated.emitted.clear()
    bus.curve_updated.emitted.clear()
    c.set_graph_visible(graph, False)
    assert state.graphs[graph].visible is False
    assert len(bus.graph_updated.emitted) == 1
    assert len(bus.curve_updated.emitted) == 1

    bus.graph_updated.emitted.clear()
    bus.curve_updated.emitted.clear()
    c.set_curve_visible(graph, "Courbe 1", False)
    assert state.graphs[graph].curves[0].visible is False
    assert len(bus.graph_updated.emitted) == 1
    assert len(bus.curve_updated.emitted) == 1

def test_controller_graph_options(controller):
    c, state, bus = controller
    c.add_graph()
    graph = list(state.graphs.keys())[0]
    c.select_graph(graph)

    bus.graph_updated.emitted.clear()
    c.set_dark_mode(True)
    assert state.graphs[graph].dark_mode is True
    assert len(bus.graph_updated.emitted) == 1

    bus.graph_updated.emitted.clear()
    c.set_grid_visible(True)
    assert state.graphs[graph].grid_visible is True
    assert len(bus.graph_updated.emitted) == 1


def test_selection_flow_updates_state_and_ui(controller):
    c, state, bus = controller
    c.add_graph()
    graph_name = list(state.graphs.keys())[0]

    bus.curve_selected.emitted.clear()
    c.add_curve(graph_name)

    assert state.current_graph.name == graph_name
    assert state.current_curve.name == "Courbe 1"
    assert bus.curve_selected.emitted[0] == (graph_name, "Courbe 1")

    c.ui.curve_calls = 0
    c.select_curve("Courbe 1")

    assert state.current_curve.name == "Courbe 1"
    assert c.ui.curve_calls == 1


def test_set_width_updates_curve(controller):
    c, state, _ = controller
    c.add_graph()
    graph_name = list(state.graphs.keys())[0]
    c.add_curve(graph_name)

    c.set_width(5)
    assert state.current_curve.width == 5


def test_set_time_offset_updates_curve(controller):
    c, state, _ = controller
    c.add_graph()
    graph_name = list(state.graphs.keys())[0]
    c.add_curve(graph_name)

    c.set_time_offset(3.0)
    assert state.current_curve.time_offset == 3.0


def test_bring_curve_to_front_invokes_service_and_refresh(controller):
    c, state, _ = controller
    c.add_graph()
    graph_name = list(state.graphs.keys())[0]

    c.add_curve(graph_name)
    c.add_curve(graph_name)

    c.select_curve("Courbe 1")
    c.ui.plot_calls = 0

    c.bring_curve_to_front()

    curves = [curve.name for curve in state.current_graph.curves]
    assert curves[-1] == "Courbe 1"
    assert c.ui.plot_calls == 1


def test_controller_create_bit_curves(controller):
    c, state, bus = controller
    c.add_graph()
    graph = list(state.graphs.keys())[0]
    c.add_curve(graph)
    curve = state.current_curve
    curve.y = np.array([0, 1, 2, 3])
    curve.x = np.array([0, 1, 2, 3])

    bus.curve_updated.emitted.clear()
    created = c.create_bit_curves(curve.name)

    assert created == [f"{curve.name}[0]", f"{curve.name}[1]"]
    assert len(state.current_graph.curves) == 3
    assert len(bus.curve_updated.emitted) == 1


def test_controller_create_bit_group_curve(controller):
    c, state, bus = controller
    c.add_graph()
    graph = list(state.graphs.keys())[0]
    c.add_curve(graph)
    curve = state.current_curve
    curve.y = np.array([0, 1, 2, 3])
    curve.x = np.array([0, 1, 2, 3])

    bus.curve_updated.emitted.clear()
    created = c.create_bit_group_curve(curve.name, [1, 0], "grp")

    assert created == "grp"
    assert len(state.current_graph.curves) == 2
    assert len(bus.curve_updated.emitted) == 1
