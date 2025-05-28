from app_state import AppState
from PyQt5 import QtWidgets, QtCore

class PropertiesPanel(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        print("[PropertiesPanel.py > __init__()] ▶️ Entrée dans __init__()")

        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        print("[PropertiesPanel.py > setup_ui()] ▶️ Entrée dans setup_ui()")

        self.setup_graph_tab()
        self.setup_curve_tab()
        self.setTabEnabled(0, False)
        self.setTabEnabled(1, False)

    def setup_graph_tab(self):
        print("[PropertiesPanel.py > setup_graph_tab()] ▶️ Entrée dans setup_graph_tab()")

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
    
        # ✅ Ajout : unités et formats des axes
        unit_layout = QtWidgets.QFormLayout()
    
        self.x_unit_input = QtWidgets.QLineEdit()
        self.y_unit_input = QtWidgets.QLineEdit()
    
        self.x_format_combo = QtWidgets.QComboBox()
        self.y_format_combo = QtWidgets.QComboBox()
        for combo in [self.x_format_combo, self.y_format_combo]:
            combo.addItem("Normal", "normal")
            combo.addItem("Scientifique", "scientific")
            combo.addItem("Multiplicateur (n, µ, m...)", "scaled")
    
        unit_layout.addRow("Unité X :", self.x_unit_input)
        unit_layout.addRow("Format X :", self.x_format_combo)
        unit_layout.addRow("Unité Y :", self.y_unit_input)
        unit_layout.addRow("Format Y :", self.y_format_combo)
    
        layout.addSpacing(10)
        layout.addLayout(unit_layout)
    
        layout.addStretch()
    
        self.fix_y_checkbox = QtWidgets.QCheckBox("Fixer l'échelle Y")
        self.ymin_input = QtWidgets.QDoubleSpinBox()
        self.ymax_input = QtWidgets.QDoubleSpinBox()
        self.ymin_input.setRange(-1000, 1000)
        self.ymax_input.setRange(-1000, 1000)
        self.ymin_input.setValue(-5.0)
        self.ymax_input.setValue(5.0)
    
        ylayout = QtWidgets.QHBoxLayout()
        ylayout.addWidget(QtWidgets.QLabel("Y min :"))
        ylayout.addWidget(self.ymin_input)
        ylayout.addWidget(QtWidgets.QLabel("Y max :"))
        ylayout.addWidget(self.ymax_input)
    
        layout.addWidget(self.fix_y_checkbox)
        layout.addLayout(ylayout)
        
        self.satellite_left_checkbox = QtWidgets.QCheckBox("Zone gauche")
        self.satellite_left_combo = QtWidgets.QComboBox()
        self.satellite_left_combo.addItem("Aucun", None)
        self.satellite_left_combo.addItem("Exemple: Texte", "label")
        self.satellite_left_combo.addItem("Exemple: Bouton", "button")
        
        layout.addWidget(self.satellite_left_checkbox)
        layout.addWidget(self.satellite_left_combo)
        
        self.satellite_right_checkbox = QtWidgets.QCheckBox("Zone droite")
        self.satellite_right_combo = QtWidgets.QComboBox()
        self.satellite_right_combo.addItem("Aucun", None)
        self.satellite_right_combo.addItem("Exemple: Texte", "label")
        self.satellite_right_combo.addItem("Exemple: Bouton", "button")
        
        layout.addWidget(self.satellite_right_checkbox)
        layout.addWidget(self.satellite_right_combo)
        
        self.satellite_top_checkbox = QtWidgets.QCheckBox("Zone haut")
        self.satellite_top_combo = QtWidgets.QComboBox()
        self.satellite_top_combo.addItem("Aucun", None)
        self.satellite_top_combo.addItem("Exemple: Texte", "label")
        self.satellite_top_combo.addItem("Exemple: Bouton", "button")
        
        layout.addWidget(self.satellite_top_checkbox)
        layout.addWidget(self.satellite_top_combo)
        
        self.satellite_bottom_checkbox = QtWidgets.QCheckBox("Zone bas")
        self.satellite_bottom_combo = QtWidgets.QComboBox()
        self.satellite_bottom_combo.addItem("Aucun", None)
        self.satellite_bottom_combo.addItem("Exemple: Texte", "label")
        self.satellite_bottom_combo.addItem("Exemple: Bouton", "button")
        
        layout.addWidget(self.satellite_bottom_checkbox)
        layout.addWidget(self.satellite_bottom_combo)
    
        self.addTab(tab_graph, "Propriétés du graphique")

    def setup_curve_tab(self):
        print("[PropertiesPanel.py > setup_curve_tab()] ▶️ Entrée dans setup_curve_tab()")

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
        
        self.gain_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.gain_slider.setRange(1, 500)  # de 0.01 à 5.00
        self.gain_slider.setValue(100)
        
        self.offset_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.offset_slider.setRange(-500, 500)
        self.offset_slider.setValue(0)
        
        self.zero_indicator_combo = QtWidgets.QComboBox()
        self.zero_indicator_combo.addItem("Aucun", "none")
        self.zero_indicator_combo.addItem("Ligne horizontale", "line")
        layout.addWidget(QtWidgets.QLabel("Indicateur de zéro :"))
        layout.addWidget(self.zero_indicator_combo)
        
        layout.addWidget(QtWidgets.QLabel("Gain (x0.01 à x5.00) :"))
        layout.addWidget(self.gain_slider)
        layout.addWidget(QtWidgets.QLabel("Offset vertical :"))
        layout.addWidget(self.offset_slider)
        
        self.bring_to_front_button = QtWidgets.QPushButton("🔝 Mettre au premier plan")
        layout.addWidget(self.bring_to_front_button)
        
        layout.addSpacing(10)
        layout.addWidget(QtWidgets.QLabel("Affichage du nom de la courbe :"))
        self.label_mode_combo = QtWidgets.QComboBox()
        self.label_mode_combo.addItem("Aucun", "none")
        self.label_mode_combo.addItem("Texte sur la courbe", "inline")
        self.label_mode_combo.addItem("Légende", "legend")
        layout.addWidget(self.label_mode_combo)

        layout.addStretch()
        
        self.addTab(tab_curve, "Propriétés de la courbe")