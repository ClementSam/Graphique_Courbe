import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5 import QtWidgets

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.app_state import AppState
from core.models import GraphData, CurveData, SatelliteObjectData
from ui.PropertiesPanel import PropertiesPanel


def test_update_curve_ui_resets_when_no_selection():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    AppState._instance = None
    state = AppState.get_instance()

    graph = GraphData(name="g")
    curve = CurveData(name="c1", x=[0], y=[0])
    graph.add_curve(curve)

    state.graphs["g"] = graph
    state.current_graph = graph
    state.current_curve = curve

    panel = PropertiesPanel()
    panel.update_curve_ui()
    assert panel.label_curve_name.text() == "c1"

    state.current_curve = None
    panel.update_curve_ui()

    assert panel.label_curve_name.text() == "—"
    assert panel.display_mode_combo.currentIndex() == 0
    assert not panel.downsampling_ratio_input.isEnabled()
    assert not panel.downsampling_apply_btn.isEnabled()
    assert panel.time_offset_input.value() == 0.0


def test_text_height_spin_disabled():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    panel = PropertiesPanel()
    panel.satellite_left_checkbox.setChecked(True)
    panel._create_satellite_row(
        "left",
        0,
        SatelliteObjectData(obj_type="text", name="t"),
    )
    table = panel.satellite_left_table
    spin_h = table.cellWidget(0, 4)
    assert isinstance(spin_h, QtWidgets.QSpinBox)
    assert not spin_h.isEnabled()
