import os
import sys
import types
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt5 import QtCore, QtWidgets

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.app_state import AppState
from ui.PropertiesPanel import PropertiesPanel

class DummySignal:
    def __init__(self):
        self.slots = []
    def connect(self, func):
        self.slots.append(func)
    def emit(self, *args, **kwargs):
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
    import importlib
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

def test_drop_updates_graph_data(controller):
    c, state, panel, bus, app = controller
    c.add_graph()
    name = list(state.graphs.keys())[0]
    c.select_graph(name)

    c.set_satellite_visible("left", True)
    c.set_satellite_edit_mode("left", True)
    app.processEvents()

    view = (
        c.ui.views[name]
        .container.advanced_container.left_box.layout()
        .itemAt(0)
        .widget()
    )

    class DummyDropEvent:
        def __init__(self, text, x, y):
            self._pos = QtCore.QPoint(x, y)
            self._mime = QtCore.QMimeData()
            self._mime.setText(text)
            self.accepted = False
        def mimeData(self):
            return self._mime
        def pos(self):
            return self._pos
        def acceptProposedAction(self):
            self.accepted = True

    event = DummyDropEvent("text", 10, 15)
    view.dropEvent(event)
    app.processEvents()

    items = state.graphs[name].satellite_settings["left"]["items"]
    assert len(items) == 1
    assert items[0]["type"] == "text"
    assert items[0]["x"] == 10
    assert items[0]["y"] == 15
