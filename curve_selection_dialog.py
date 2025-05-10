from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QDialogButtonBox, QCheckBox
)
from PyQt5.QtCore import Qt

from typing import List
from models import CurveData

class CurveSelectionDialog(QDialog):
    """
    Dialogue permettant à l'utilisateur de choisir quelles courbes importer.
    Utilisable avec tout format de données (bin, csv, excel, etc.)
    """
    def __init__(self, curves: List[CurveData], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sélection des courbes à importer")
        self.resize(400, 300)

        self.curves = curves
        self.selected_indices = []

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Sélectionnez les courbes à importer :"))

        self.list_widget = QListWidget()
        for curve in curves:
            item = QListWidgetItem(curve.name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            self.list_widget.addItem(item)

        layout.addWidget(self.list_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_selected_curves(self) -> List[CurveData]:
        selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(self.curves[i])
        return selected
