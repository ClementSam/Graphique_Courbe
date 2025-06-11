from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QFileDialog, QLineEdit
)

class ImportCurveDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Importer une courbe")
        self.setMinimumWidth(400)

        self.selected_path = None
        self.selected_format = None

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        self._add_format_selector(layout)
        self._add_file_selector(layout)
        self._add_buttons(layout)
        self.setLayout(layout)

    def _add_format_selector(self, layout):
        layout.addWidget(QLabel("Choisissez le format de fichier :"))
        self.format_combo = QComboBox()
        self.format_combo.addItem("Oscilloscope Keysight / fichier .BIN", "keysight_bin")
        self.format_combo.addItem("Gestionnaire de courbes / JSON", "internal_json")
        self.format_combo.addItem("Oscilloscope Keysight V5 / JSON", "keysight_json_v5")
        self.format_combo.addItem("Oscilloscope TEKTRO V1.2 / JSON", "tektro_json_v1_2")
        self.format_combo.addItem("CSV Standard", "csv_standard")
        self.format_combo.addItem("➕ Générer une courbe aléatoire", "random_curve")
        layout.addWidget(self.format_combo)

    def _add_file_selector(self, layout):
        file_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        browse_btn = QPushButton("Parcourir")
        browse_btn.clicked.connect(self._on_browse)
        file_layout.addWidget(self.path_edit)
        file_layout.addWidget(browse_btn)
        layout.addLayout(file_layout)

    def _add_buttons(self, layout):
        btn_layout = QHBoxLayout()
        import_btn = QPushButton("Importer")
        cancel_btn = QPushButton("Annuler")
        import_btn.clicked.connect(self._on_accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(import_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _on_browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choisir un fichier", "", "Tous les fichiers (*)")
        if path:
            self.path_edit.setText(path)

    def _on_accept(self):
        self.selected_path = self.path_edit.text()
        self.selected_format = self.format_combo.currentData()
        self.accept()
