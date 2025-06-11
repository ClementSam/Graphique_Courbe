from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton,
                             QLineEdit, QHBoxLayout, QMessageBox)
from .. import layout_manager as lm


class LayoutManagerDialog(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle("Gestion des dispositions")
        self.setMinimumWidth(400)
        self._setup_ui()
        self._refresh_layouts()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Liste déroulante des dispositions
        self.combo = QComboBox()
        layout.addWidget(QLabel("Dispositions enregistrées :"))
        layout.addWidget(self.combo)

        # Boutons d'action
        btn_layout = QHBoxLayout()
        self.apply_btn = QPushButton("🪄 Appliquer")
        self.delete_btn = QPushButton("🗑 Supprimer")
        self.set_default_btn = QPushButton("⭐ Définir comme défaut")
        btn_layout.addWidget(self.apply_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.set_default_btn)
        layout.addLayout(btn_layout)

        # Enregistrement d'une nouvelle disposition
        layout.addSpacing(10)
        layout.addWidget(QLabel("Nom pour une nouvelle disposition :"))
        self.name_input = QLineEdit()
        self.save_btn = QPushButton("💾 Enregistrer la disposition actuelle")
        layout.addWidget(self.name_input)
        layout.addWidget(self.save_btn)

        # Connexions
        self.apply_btn.clicked.connect(self.apply_layout)
        self.delete_btn.clicked.connect(self.delete_layout)
        self.set_default_btn.clicked.connect(self.set_default)
        self.save_btn.clicked.connect(self.save_new_layout)

    def _refresh_layouts(self):
        self.combo.clear()
        self.combo.addItems(lm.list_layouts())
        default = lm.get_default_layout()
        if default:
            index = self.combo.findText(default)
            if index != -1:
                self.combo.setCurrentIndex(index)

    def apply_layout(self):
        name = self.combo.currentText()
        try:
            lm.load_layout(name, self.main_window)
        except Exception as e:
            QMessageBox.warning(self, "Erreur", str(e))

    def delete_layout(self):
        name = self.combo.currentText()
        reply = QMessageBox.question(self, "Supprimer", f"Supprimer la disposition '{name}' ?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            lm.delete_layout(name)
            self._refresh_layouts()

    def set_default(self):
        name = self.combo.currentText()
        try:
            lm.set_default_layout(name)
        except Exception as e:
            QMessageBox.warning(self, "Erreur", str(e))

    def save_new_layout(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Nom requis", "Veuillez entrer un nom.")
            return
        lm.save_layout(name, self.main_window)
        self.name_input.clear()
        self._refresh_layouts()
