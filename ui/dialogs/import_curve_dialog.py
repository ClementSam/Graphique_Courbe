from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QFileDialog,
    QLineEdit,
)

class ImportCurveDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Importer une courbe")
        self.setMinimumWidth(400)

        self.selected_path = None
        self.selected_format = None
        self.selected_sep = ","

        self._init_ui()
        self._on_format_changed()

    def _init_ui(self):
        layout = QVBoxLayout()

        # Label + liste déroulante des formats
        layout.addWidget(QLabel("Choisissez le format de fichier :"))
        self.format_combo = QComboBox()
        self.format_combo.addItem("Oscilloscope Keysight / fichier .BIN", "keysight_bin")
        self.format_combo.addItem("Gestionnaire de courbes / JSON", "internal_json")
        self.format_combo.addItem("Oscilloscope Keysight V5 / JSON", "keysight_json_v5")
        self.format_combo.addItem("Oscilloscope TEKTRO V1.2 / JSON", "tektro_json_v1_2")
        self.format_combo.addItem("CSV Standard", "csv_standard")
        self.format_combo.addItem("➕ Générer une courbe aléatoire", "random_curve")
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        layout.addWidget(self.format_combo)

        # Sélecteur de fichier
        file_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.browse_btn = QPushButton("Parcourir")
        self.browse_btn.clicked.connect(self._on_browse)
        file_layout.addWidget(self.path_edit)
        file_layout.addWidget(self.browse_btn)
        layout.addLayout(file_layout)

        # Champ séparateur CSV
        sep_layout = QHBoxLayout()
        self.sep_label = QLabel("Séparateur CSV :")
        self.sep_edit = QLineEdit(",")
        sep_layout.addWidget(self.sep_label)
        sep_layout.addWidget(self.sep_edit)
        layout.addLayout(sep_layout)

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

    def _on_format_changed(self):
        fmt = self.format_combo.currentData()
        disabled = fmt == "random_curve"
        self.path_edit.setDisabled(disabled)
        self.browse_btn.setDisabled(disabled)
        csv = fmt == "csv_standard"
        self.sep_label.setVisible(csv)
        self.sep_edit.setVisible(csv)

    def _on_browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Sélectionner un fichier", "", "Tous les fichiers (*)")
        if path:
            self.path_edit.setText(path)

    def _on_accept(self):
        fmt = self.format_combo.currentData()
        path = self.path_edit.text().strip()
        if fmt != "random_curve" and not path:
            QtWidgets.QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un fichier.")
            return
        self.selected_path = path if fmt != "random_curve" else None
        self.selected_format = fmt
        self.selected_sep = self.sep_edit.text() or ","
        self.accept()

    def get_selected_path_and_format(self):
        return self.selected_path, self.selected_format, self.selected_sep
