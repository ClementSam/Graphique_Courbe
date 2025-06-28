import os
import sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt5 import QtWidgets

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core import GraphData, SatelliteObjectData
from ui.views import MyPlotView


def test_satellite_widget_uses_param():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    graph = GraphData(name="g")
    view = MyPlotView(graph)

    obj = SatelliteObjectData(obj_type="text", name="foo", config={"value": "lbl"})
    w = view._create_satellite_widget(obj)
    assert isinstance(w, QtWidgets.QLabel)
    assert w.text() == "lbl"

    obj_btn = SatelliteObjectData(obj_type="button", name="btn", config={"value": "click"})
    w = view._create_satellite_widget(obj_btn)
    assert isinstance(w, QtWidgets.QToolButton)
    assert w.text() == "click"

