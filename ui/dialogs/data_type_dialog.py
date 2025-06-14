from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QDialogButtonBox, QMessageBox
)
from typing import List
from core.models import CurveData, DataType


class DataTypeDialog(QDialog):
    """Dialog letting the user choose data type for each curve."""

    def __init__(self, curves: List[CurveData], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Type de données")
        self.curves = curves
        self._combos = {}
        layout = QVBoxLayout(self)

        for curve in curves:
            row = QHBoxLayout()
            row.addWidget(QLabel(curve.name))
            combo = QComboBox()
            for dt in DataType:
                combo.addItem(dt.value, dt)
            combo.setCurrentIndex(list(DataType).index(curve.dtype))
            self._combos[curve] = combo
            row.addWidget(combo)
            layout.addLayout(row)

        check_btn = QPushButton("Vérifier")
        check_btn.clicked.connect(self._check)
        layout.addWidget(check_btn)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _check(self):
        if self._validate():
            QMessageBox.information(self, "OK", "Conversion possible")

    def _validate(self) -> bool:
        import numpy as np

        for curve, combo in self._combos.items():
            dtype: DataType = combo.currentData()
            if dtype == DataType.FLOAT64:
                continue
            data = curve.y
            if not np.all(np.isfinite(data)) or not np.allclose(data, np.round(data)):
                QMessageBox.warning(self, "Erreur", f"{curve.name}: valeurs non entières")
                return False
            max_val = int(np.max(data)) if data.size else 0
            if np.any(data < 0):
                QMessageBox.warning(self, "Erreur", f"{curve.name}: valeurs négatives")
                return False
            if dtype == DataType.UINT8 and max_val > 0xFF:
                QMessageBox.warning(self, "Erreur", f"{curve.name}: dépasse UINT8")
                return False
            if dtype == DataType.UINT16 and max_val > 0xFFFF:
                QMessageBox.warning(self, "Erreur", f"{curve.name}: dépasse UINT16")
                return False
            if dtype == DataType.UINT32 and max_val > 0xFFFFFFFF:
                QMessageBox.warning(self, "Erreur", f"{curve.name}: dépasse UINT32")
                return False
        return True

    def accept(self):
        import numpy as np

        if not self._validate():
            return
        for curve, combo in self._combos.items():
            dtype: DataType = combo.currentData()
            curve.dtype = dtype
            if dtype != DataType.FLOAT64:
                curve.y = curve.y.astype(dtype.value)
        super().accept()
