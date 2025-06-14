from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QDialogButtonBox,
    QPushButton,
    QLineEdit,
    QComboBox,
)
from PyQt5.QtCore import Qt
import fnmatch

from typing import List
from core.models import CurveData, DataType

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

        lists_layout = QHBoxLayout()
        self.available_list = QListWidget()
        self.available_list.setSelectionMode(QListWidget.MultiSelection)
        for curve in curves:
            item = QListWidgetItem(curve.name)
            item.setData(Qt.UserRole, curve)
            self.available_list.addItem(item)

        self.selected_table = QTableWidget()
        self.selected_table.setColumnCount(2)
        self.selected_table.setHorizontalHeaderLabels(["Nom", "Type"])
        self.selected_table.horizontalHeader().setStretchLastSection(True)
        self.selected_table.setSelectionBehavior(QAbstractItemView.SelectRows)

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
        lists_layout.addWidget(self.selected_table)
        main_layout.addLayout(lists_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        # double click pour déplacer
        self.available_list.itemDoubleClicked.connect(self._add_item)
        self.selected_table.itemDoubleClicked.connect(self._remove_item)

    def get_selected_curves(self) -> List[CurveData]:
        """Retourne les courbes sélectionnées dans la table de droite."""
        selected = []
        for row in range(self.selected_table.rowCount()):
            name_item = self.selected_table.item(row, 0)
            curve = name_item.data(Qt.UserRole)
            curve.name = name_item.text().strip()
            combo = self.selected_table.cellWidget(row, 1)
            dtype = combo.currentData()
            curve.dtype = dtype
            if dtype != DataType.FLOAT64:
                curve.y = curve.y.astype(dtype.value)
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
        self._move_to_selected([item])

    def _remove_item(self, item):
        row = item.row()
        self._move_row_to_available(row)
        self._apply_filter()

    def _add_selected(self):
        items = self.available_list.selectedItems()
        self._move_to_selected(items)

    def _remove_selected(self):
        rows = sorted({item.row() for item in self.selected_table.selectedItems()}, reverse=True)
        for row in rows:
            self._move_row_to_available(row)
        self._apply_filter()
    def _move_to_selected(self, items):
        for item in list(items):
            self.available_list.takeItem(self.available_list.row(item))
            row = self.selected_table.rowCount()
            self.selected_table.insertRow(row)
            name_item = QTableWidgetItem(item.text())
            name_item.setFlags(name_item.flags() | Qt.ItemIsEditable)
            curve = item.data(Qt.UserRole)
            name_item.setData(Qt.UserRole, curve)
            self.selected_table.setItem(row, 0, name_item)
            combo = QComboBox()
            for dt in DataType:
                combo.addItem(dt.value, dt)
            combo.setCurrentIndex(list(DataType).index(curve.dtype))
            self.selected_table.setCellWidget(row, 1, combo)

    def _move_row_to_available(self, row: int):
        name_item = self.selected_table.item(row, 0)
        curve = name_item.data(Qt.UserRole)
        new_name = name_item.text().strip()
        curve.name = new_name
        item = QListWidgetItem(new_name)
        item.setData(Qt.UserRole, curve)
        self.available_list.addItem(item)
        self.selected_table.removeRow(row)
