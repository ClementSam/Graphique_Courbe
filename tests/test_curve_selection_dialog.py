import os
import sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt5 import QtWidgets

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.models import CurveData, DataType
from ui.dialogs.curve_selection_dialog import CurveSelectionDialog
import numpy as np


def test_filter_and_selection():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    curves = [CurveData(name="temp1", x=[0], y=[0]),
              CurveData(name="volt2", x=[0], y=[0]),
              CurveData(name="temp3", x=[0], y=[0])]
    dlg = CurveSelectionDialog(curves)
    dlg.filter_edit.setText("temp*")
    dlg._apply_filter()
    visible = [not dlg.available_list.item(i).isHidden() for i in range(dlg.available_list.count())]
    assert visible == [True, False, True]

    dlg.available_list.setCurrentRow(0)
    dlg._add_selected()
    selected = dlg.get_selected_curves()
    assert len(selected) == 1
    assert selected[0].name == "temp1"
    assert selected[0].dtype == DataType.FLOAT64


def test_warning_label_updates():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    curves = [CurveData(name="c", x=[0, 1], y=[0, 2.5])]
    dlg = CurveSelectionDialog(curves)
    dlg.available_list.setCurrentRow(0)
    dlg._add_selected()
    combo = dlg.selected_table.cellWidget(0, 1)
    warn = dlg.selected_table.cellWidget(0, 2)
    assert warn.text() == ""
    combo.setCurrentIndex(list(DataType).index(DataType.UINT8))
    assert warn.text() == "1/2"
