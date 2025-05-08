from app_state import AppState
from PyQt5 import QtWidgets, QtCore

class PropertiesPanel(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setup_graph_tab()
        self.setup_curve_tab()
        self.setTabEnabled(0, False)
        self.setTabEnabled(1, False)

    def setup_graph_tab(self):
        tab_graph = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab_graph)

        self.label_graph_name = QtWidgets.QLabel("—")
        self.label_graph_name.setStyleSheet("font-weight:bold")
        self.grid_checkbox = QtWidgets.QCheckBox("Afficher la grille")
        self.darkmode_checkbox = QtWidgets.QCheckBox("Mode sombre")
        self.logx_checkbox = QtWidgets.QCheckBox("Échelle X logarithmique")
        self.logy_checkbox = QtWidgets.QCheckBox("Échelle Y logarithmique")
        self.font_combo = QtWidgets.QFontComboBox()
        self.button_reset_zoom = QtWidgets.QPushButton("🔍 Réinitialiser le zoom")

        layout.addWidget(QtWidgets.QLabel("Graphique sélectionné :"))
        layout.addWidget(self.label_graph_name)
        layout.addSpacing(8)
        layout.addWidget(self.grid_checkbox)
        layout.addWidget(self.darkmode_checkbox)
        layout.addWidget(self.logx_checkbox)
        layout.addWidget(self.logy_checkbox)
        layout.addWidget(QtWidgets.QLabel("Police :"))
        layout.addWidget(self.font_combo)
        layout.addWidget(self.button_reset_zoom)
        layout.addStretch()

        self.addTab(tab_graph, "Propriétés du graphique")

    def setup_curve_tab(self):
        tab_curve = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab_curve)

        self.label_curve_name = QtWidgets.QLabel("—")
        self.label_curve_name.setStyleSheet("font-weight:bold")
        self.color_button = QtWidgets.QPushButton("Changer couleur")
        self.width_spin = QtWidgets.QSpinBox()
        self.width_spin.setRange(1, 10)
        self.style_combo = QtWidgets.QComboBox()
        self.style_combo.addItem("Ligne continue", QtCore.Qt.SolidLine)
        self.style_combo.addItem("Pointillé", QtCore.Qt.DotLine)
        self.style_combo.addItem("Tiret", QtCore.Qt.DashLine)
        self.style_combo.addItem("Tiret-point", QtCore.Qt.DashDotLine)
        self.style_combo.addItem("Tiret-point-point", QtCore.Qt.DashDotDotLine)

        layout.addWidget(QtWidgets.QLabel("Courbe sélectionnée :"))
        layout.addWidget(self.label_curve_name)
        layout.addSpacing(8)
        layout.addWidget(QtWidgets.QLabel("Épaisseur :"))
        layout.addWidget(self.width_spin)
        layout.addWidget(QtWidgets.QLabel("Style :"))
        layout.addWidget(self.style_combo)
        layout.addWidget(self.color_button)
        layout.addStretch()

        self.addTab(tab_curve, "Propriétés de la courbe")
