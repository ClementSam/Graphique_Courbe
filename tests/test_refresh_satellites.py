import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5 import QtWidgets

# ensure repo root in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.models import GraphData
from ui.views import MyPlotView


def test_refresh_does_not_overwrite_set_items():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    graph = GraphData(name="g")
    zone = "left"
    graph.satellite_visibility[zone] = True
    graph.satellite_settings[zone]["items"] = [
        {"type": "text", "text": "old", "x": 0, "y": 0}
    ]

    view = MyPlotView(graph)
    view.refresh_satellites()

    new_items = [
        {"type": "text", "text": "new", "x": 10, "y": 10}
    ]
    graph.satellite_settings[zone]["items"] = list(new_items)
    view.refresh_satellites()

    assert graph.satellite_settings[zone]["items"] == new_items
