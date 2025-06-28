import os
import sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt5 import QtWidgets, QtGui
import tempfile

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

    obj_btn = SatelliteObjectData(
        obj_type="button",
        name="btn",
        config={"value": "click", "width": 40, "height": 30},
    )
    w = view._create_satellite_widget(obj_btn)
    assert isinstance(w, QtWidgets.QToolButton)
    assert w.text() == "click"
    assert w.width() == 40
    assert w.height() == 30

    pix = QtGui.QPixmap(20, 20)
    pix.fill(QtGui.QColor("red"))
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    pix.save(tmp.name)
    obj_img = SatelliteObjectData(
        obj_type="image",
        name="img",
        config={"value": tmp.name, "width": 5, "height": 8},
    )
    w = view._create_satellite_widget(obj_img)
    assert isinstance(w, QtWidgets.QLabel)
    assert w.pixmap().width() == 5
    assert w.pixmap().height() == 8
    tmp.close()
    os.unlink(tmp.name)

