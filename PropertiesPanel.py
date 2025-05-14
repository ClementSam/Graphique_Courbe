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
        self.downsampling_combo = QtWidgets.QComboBox()
        self.downsampling_combo.addItem("Automatique", "auto")
        self.downsampling_combo.addItem("Manuel", "manual")
        self.downsampling_combo.addItem("Désactivé", "off")
        self.downsampling_ratio_input = QtWidgets.QSpinBox()
        self.downsampling_ratio_input.setRange(1, 1000)
        self.downsampling_ratio_input.setValue(10)
        self.downsampling_ratio_input.setEnabled(False)
        self.downsampling_apply_btn = QtWidgets.QPushButton("Appliquer")
        self.downsampling_apply_btn.setEnabled(False)

        layout.addWidget(QtWidgets.QLabel("Courbe sélectionnée :"))
        layout.addWidget(self.label_curve_name)
        layout.addSpacing(8)
        layout.addWidget(QtWidgets.QLabel("Épaisseur :"))
        layout.addWidget(self.width_spin)
        layout.addWidget(QtWidgets.QLabel("Style :"))
        layout.addWidget(self.style_combo)
        layout.addWidget(self.color_button)

        ds_layout = QtWidgets.QHBoxLayout()
        ds_layout.addWidget(QtWidgets.QLabel("Ratio :"))
        ds_layout.addWidget(self.downsampling_ratio_input)
        ds_layout.addWidget(self.downsampling_apply_btn)
        
        layout.addWidget(QtWidgets.QLabel("Downsampling :"))
        layout.addWidget(self.downsampling_combo)
        layout.addLayout(ds_layout)

        # Opacité
        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        layout.addWidget(QtWidgets.QLabel("Opacité (%) :"))
        layout.addWidget(self.opacity_slider)
        
        # Symbole
        self.symbol_combo = QtWidgets.QComboBox()
        self.symbol_combo.addItem("Aucun", None)
        self.symbol_combo.addItem("Cercle", "o")
        self.symbol_combo.addItem("Carré", "s")
        self.symbol_combo.addItem("Triangle", "t")
        self.symbol_combo.addItem("Diamant", "d")
        layout.addWidget(QtWidgets.QLabel("Symbole :"))
        layout.addWidget(self.symbol_combo)
        
        # Remplissage
        self.fill_checkbox = QtWidgets.QCheckBox("Remplir sous la courbe")
        layout.addWidget(self.fill_checkbox)
        
        # Mode d'affichage
        self.display_mode_combo = QtWidgets.QComboBox()
        self.display_mode_combo.addItem("Ligne", "line")
        self.display_mode_combo.addItem("Points (scatter)", "scatter")
        self.display_mode_combo.addItem("Histogramme (barres)", "bar")
        layout.addWidget(QtWidgets.QLabel("Type d'affichage :"))
        layout.addWidget(self.display_mode_combo)

        layout.addStretch()

        self.addTab(tab_curve, "Propriétés de la courbe")
