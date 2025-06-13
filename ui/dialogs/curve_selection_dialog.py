from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QDialogButtonBox,
    QPushButton,
    QLineEdit,
    QSpinBox,
    QCheckBox,
)
from PyQt5.QtCore import Qt
import fnmatch

from typing import List
from core.models import CurveData
import numpy as np

class CurveSelectionDialog(QDialog):
    """
    Dialogue permettant à l'utilisateur de choisir quelles courbes importer.
    Utilisable avec tout format de données (bin, csv, excel, etc.)
    """
    def __init__(self, curves: List[CurveData], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sélection des courbes à importer")
        self.resize(500, 350)

        self.curves = curves

        main_layout = QVBoxLayout(self)

        # zone de filtre
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtre :"))
        self.filter_edit = QLineEdit()
        self.filter_edit.textChanged.connect(self._apply_filter)
        filter_layout.addWidget(self.filter_edit)
        main_layout.addLayout(filter_layout)

        # Bit extraction option
        bit_layout = QHBoxLayout()
        self.bit_checkbox = QCheckBox("Extraire le bit :")
        self.bit_spin = QSpinBox()
        self.bit_spin.setRange(0, 31)
        self.bit_spin.setValue(0)
        self.bit_spin.setEnabled(False)
        self.bit_checkbox.stateChanged.connect(
            lambda state: self.bit_spin.setEnabled(state == Qt.Checked)
        )
        bit_layout.addWidget(self.bit_checkbox)
        bit_layout.addWidget(self.bit_spin)
        main_layout.addLayout(bit_layout)

        lists_layout = QHBoxLayout()
        self.available_list = QListWidget()
        self.available_list.setSelectionMode(QListWidget.MultiSelection)
        for curve in curves:
            item = QListWidgetItem(curve.name)
            item.setData(Qt.UserRole, curve)
            self.available_list.addItem(item)

        self.selected_list = QListWidget()
        self.selected_list.setSelectionMode(QListWidget.MultiSelection)

        btn_layout = QVBoxLayout()
        add_btn = QPushButton("→")
        remove_btn = QPushButton("←")
        add_btn.clicked.connect(self._add_selected)
        remove_btn.clicked.connect(self._remove_selected)
        btn_layout.addStretch()
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        btn_layout.addStretch()

        lists_layout.addWidget(self.available_list)
        lists_layout.addLayout(btn_layout)
        lists_layout.addWidget(self.selected_list)
        main_layout.addLayout(lists_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        # double click pour déplacer
        self.available_list.itemDoubleClicked.connect(self._add_item)
        self.selected_list.itemDoubleClicked.connect(self._remove_item)

    def get_selected_curves(self) -> List[CurveData]:
        """Retourne les courbes sélectionnées dans la liste de droite."""
        selected = []
        for i in range(self.selected_list.count()):
            item = self.selected_list.item(i)
            curve = item.data(Qt.UserRole)
            new_name = item.text().strip()
            curve.name = new_name
            if self.bit_checkbox.isChecked():
                bit = self.bit_spin.value()
                y_int = np.array(curve.y, dtype=int)
                curve.y = ((y_int >> bit) & 1).astype(curve.y.dtype)
            selected.append(curve)
        return selected

    # --- actions internes ---

    def _apply_filter(self):
        pattern = self.filter_edit.text().strip()
        for i in range(self.available_list.count()):
            item = self.available_list.item(i)
            visible = True
            if pattern:
                visible = fnmatch.fnmatch(item.text(), pattern)
            item.setHidden(not visible)

    def _add_item(self, item: QListWidgetItem):
        self._move_items([item], self.available_list, self.selected_list)

    def _remove_item(self, item: QListWidgetItem):
        self._move_items([item], self.selected_list, self.available_list)
        self._apply_filter()

    def _add_selected(self):
        items = self.available_list.selectedItems()
        self._move_items(items, self.available_list, self.selected_list)

    def _remove_selected(self):
        items = self.selected_list.selectedItems()
        self._move_items(items, self.selected_list, self.available_list)
        self._apply_filter()

    def _move_items(self, items, src: QListWidget, dst: QListWidget):
        for item in list(items):
            src.takeItem(src.row(item))
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            dst.addItem(item)
