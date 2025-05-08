from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QFileDialog, QLineEdit

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

        # Label + liste déroulante des formats
        layout.addWidget(QLabel("Choisissez le format de fichier :"))
        self.format_combo = QComboBox()
        self.format_combo.addItem("Gestionnaire de courbes / JSON", "internal_json")
        self.format_combo.addItem("Oscilloscope Keysight V5 / JSON", "keysight_json_v5")
        self.format_combo.addItem("Oscilloscope TEKTRO V1.2 / JSON", "tektro_json_v1_2")
        self.format_combo.addItem("CSV Standard", "csv_standard")
        layout.addWidget(self.format_combo)

        # Sélecteur de fichier
        file_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        browse_btn = QPushButton("Parcourir")
        browse_btn.clicked.connect(self._on_browse)
        file_layout.addWidget(self.path_edit)
        file_layout.addWidget(browse_btn)
        layout.addLayout(file_layout)

        # Boutons bas
        btn_layout = QHBoxLayout()
        import_btn = QPushButton("Importer")
        cancel_btn = QPushButton("Annuler")
        import_btn.clicked.connect(self._on_accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(import_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def _on_browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Sélectionner un fichier", "", "Tous les fichiers (*)")
        if path:
            self.path_edit.setText(path)

    def _on_accept(self):
        path = self.path_edit.text().strip()
        if not path:
            QtWidgets.QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un fichier.")
            return
        self.selected_path = path
        self.selected_format = self.format_combo.currentData()
        self.accept()

    def get_selected_path_and_format(self):
        return self.selected_path, self.selected_format
