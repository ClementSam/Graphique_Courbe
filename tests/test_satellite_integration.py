import os
import sys
import types
import importlib
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt5 import QtWidgets

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.app_state import AppState
from core.models import SatelliteItem
from ui.PropertiesPanel import PropertiesPanel

class DummySignal:
    def __init__(self):
        self.slots = []
        self.emitted = []
    def connect(self, func):
        self.slots.append(func)
    def emit(self, *args, **kwargs):
        self.emitted.append(args)
        for s in self.slots:
            s(*args, **kwargs)

def make_bus():
    return types.SimpleNamespace(
        graph_selected=DummySignal(),
        curve_selected=DummySignal(),
        curve_list_updated=DummySignal(),
        curve_updated=DummySignal(),
        graph_updated=DummySignal(),
        graph_visibility_changed=DummySignal(),
        curve_visibility_changed=DummySignal(),
    )

@pytest.fixture
def controller(monkeypatch):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    bus_module = types.ModuleType("signal_bus")
    bus_module.signal_bus = make_bus()
    monkeypatch.setitem(sys.modules, "signal_bus", bus_module)

    import ui.PropertiesPanel as pp
    pp.signal_bus = bus_module.signal_bus

    import controllers as ctrl
    importlib.reload(ctrl)

    AppState._instance = None
    state = AppState.get_instance()

    central = types.SimpleNamespace(
        add_plot_widget=lambda w: None,
        remove_plot_widget=lambda w: None,
    )
    panel = PropertiesPanel()
    bus_module.signal_bus.graph_updated.connect(panel.update_graph_ui)

    c = ctrl.GraphController({}, central, panel)
    return c, state, panel, bus_module.signal_bus, app


def test_satellite_items_persist_after_refresh(controller):
    c, state, panel, bus, app = controller
    c.add_graph()
    name = list(state.graphs.keys())[0]
    c.select_graph(name)

    c.set_satellite_items(
        "left",
        [SatelliteItem(type="text", text="hello", width=50, height=20, x=0, y=0)],
    )
    c.set_satellite_visible("left", True)
    app.processEvents()

    c.ui.refresh_plot()
    first = list(state.graphs[name].satellite_settings["left"].items)

    c.ui.refresh_plot()
    after = state.graphs[name].satellite_settings["left"].items

    assert after == first


def test_satellite_zone_move_updates_table(controller):
    c, state, panel, bus, app = controller
    c.add_graph()
    name = list(state.graphs.keys())[0]
    c.select_graph(name)
    c.set_satellite_items(
        "left",
        [{"type": "text", "text": "hello", "width": 50, "height": 20, "x": 0, "y": 0}],
    )
    c.set_satellite_visible("left", True)
    app.processEvents()

    view = (
        c.ui.views[name]
        .container.advanced_container.left_box.layout()
        .itemAt(0)
        .widget()
    )
    item = view.scene().items()[0]
    item.setPos(10, 20)

    c.set_satellite_items("left", view.get_items())
    app.processEvents()

    table = panel.satellite_left_table
    assert table.cellWidget(0, 5).value() == 10
    assert table.cellWidget(0, 6).value() == 20


def test_add_item_refreshes_table(controller, monkeypatch):
    c, state, panel, bus, app = controller
    c.add_graph()
    name = list(state.graphs.keys())[0]
    c.select_graph(name)
    panel.controller = c
    c.set_satellite_visible("left", True)
    app.processEvents()

    monkeypatch.setattr(QtWidgets.QInputDialog, "getItem", lambda *a, **k: ("Texte", True))
    panel._add_satellite_item("left")

    assert panel.satellite_left_table.rowCount() == 1
    assert isinstance(panel.satellite_left_table.cellWidget(0, 8), QtWidgets.QPushButton)
