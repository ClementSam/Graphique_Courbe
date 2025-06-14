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
        self._warn_labels = {}
        layout = QVBoxLayout(self)

        for curve in curves:
            row = QHBoxLayout()
            row.addWidget(QLabel(curve.name))
            combo = QComboBox()
            for dt in DataType:
                combo.addItem(dt.value, dt)
            combo.setCurrentIndex(list(DataType).index(curve.dtype))
            combo.currentIndexChanged.connect(
                lambda _=None, c=curve: self._update_warning(c)
            )
            key = id(curve)
            self._combos[key] = combo
            row.addWidget(combo)
            warn = QLabel("")
            warn.setStyleSheet("color: orange")
            self._warn_labels[key] = warn
            row.addWidget(warn)
            layout.addLayout(row)
            self._update_warning(curve)

        check_btn = QPushButton("Vérifier")
        check_btn.clicked.connect(self._check)
        layout.addWidget(check_btn)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # --- internal helpers ---

    def _get_invalid_mask(self, data, dtype: DataType):
        import numpy as np

        mask = ~np.isfinite(data) | ~np.isclose(data, np.round(data)) | (data < 0)
        if dtype == DataType.UINT8:
            mask |= data > 0xFF
        elif dtype == DataType.UINT16:
            mask |= data > 0xFFFF
        elif dtype == DataType.UINT32:
            mask |= data > 0xFFFFFFFF
        return mask

    def _update_warning(self, curve: CurveData):
        import numpy as np

        key = id(curve)
        combo = self._combos[key]
        dtype: DataType = combo.currentData()
        data = np.asarray(curve.y, dtype=float)
        count = int(self._get_invalid_mask(data, dtype).sum()) if dtype != DataType.FLOAT64 else 0
        lbl = self._warn_labels[key]
        if count:
            lbl.setText(f"{count}/{len(data)} invalid")
        else:
            lbl.setText("")

    def _check(self):
        if self._validate():
            QMessageBox.information(self, "OK", "Conversion possible")

    def _validate(self) -> bool:
        import numpy as np

        warnings = []
        for curve in self.curves:
            combo = self._combos[id(curve)]
            dtype: DataType = combo.currentData()
            if dtype == DataType.FLOAT64:
                continue
            data = np.asarray(curve.y, dtype=float)
            mask = self._get_invalid_mask(data, dtype)
            count = int(mask.sum())
            if count:
                warnings.append(f"{curve.name}: {count}/{len(data)}")
        if warnings:
            msg = "\n".join(warnings) + "\nLes valeurs incompatibles seront remplac\xc3\xa9es par NaN. Continuer ?"
            resp = QMessageBox.question(self, "Conversion", msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            return resp == QMessageBox.Yes
        return True

    def accept(self):
        import numpy as np

        if not self._validate():
            return
        for curve in self.curves:
            combo = self._combos[id(curve)]
            dtype: DataType = combo.currentData()
            curve.dtype = dtype
            data = np.asarray(curve.y, dtype=float)
            if dtype != DataType.FLOAT64:
                mask = self._get_invalid_mask(data, dtype)
                data[mask] = np.nan
            curve.y = data
        super().accept()
