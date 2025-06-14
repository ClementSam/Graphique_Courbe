import os
import sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt5 import QtWidgets

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.models import CurveData, DataType
from ui.dialogs.data_type_dialog import DataTypeDialog


def test_warning_label_updates():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    curve = CurveData(name="c", x=[0, 1], y=[0, 2.5])
    dlg = DataTypeDialog([curve])
    label = dlg._warn_labels[id(curve)]
    assert label.text() == ""
    combo = dlg._combos[id(curve)]
    combo.setCurrentIndex(list(DataType).index(DataType.UINT8))
    assert label.text() == "1/2 invalid"
