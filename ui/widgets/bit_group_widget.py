"""Widget for creating grouped bit curves."""

from PyQt5 import QtWidgets
from core.app_state import AppState


class BitGroupWidget(QtWidgets.QWidget):
    """Widget to manage bit groups for curve decomposition."""

    def __init__(self, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self._setup_ui()

    def set_controller(self, controller):
        self.controller = controller

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Nom", "Bits", ""])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        btn_layout = QtWidgets.QHBoxLayout()
        self.add_btn = QtWidgets.QPushButton("Ajouter un groupe")
        self.create_all_btn = QtWidgets.QPushButton("Créer tous")
        btn_layout.addWidget(self.add_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.create_all_btn)
        layout.addLayout(btn_layout)

        self.add_btn.clicked.connect(self.add_row)
        self.create_all_btn.clicked.connect(self.create_all)

    def add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        name_edit = QtWidgets.QLineEdit()
        bits_edit = QtWidgets.QLineEdit()
        create_btn = QtWidgets.QPushButton("Créer")
        create_btn.clicked.connect(lambda: self.create_row(row))
        self.table.setCellWidget(row, 0, name_edit)
        self.table.setCellWidget(row, 1, bits_edit)
        self.table.setCellWidget(row, 2, create_btn)

    def _parse_bits(self, text):
        indices = []
        for part in text.replace(" ", "").split(','):
            if not part:
                continue
            if '-' in part:
                start, end = part.split('-', 1)
                indices.extend(range(int(start), int(end) + 1))
            else:
                indices.append(int(part))
        return indices

    def create_row(self, row):
        if not self.controller:
            return
        name_edit = self.table.cellWidget(row, 0)
        bits_edit = self.table.cellWidget(row, 1)
        try:
            indices = self._parse_bits(bits_edit.text())
        except Exception:
            QtWidgets.QMessageBox.warning(self, "Erreur", "Indices invalides")
            return
        if not indices:
            QtWidgets.QMessageBox.warning(self, "Erreur", "Aucun bit spécifié")
            return
        state = AppState.get_instance()
        curve = state.current_curve
        if not curve:
            return
        group_name = name_edit.text().strip() or None
        try:
            self.controller.create_bit_group_curve(curve.name, indices, group_name)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Erreur", str(e))

    def create_all(self):
        for row in range(self.table.rowCount()):
            self.create_row(row)
