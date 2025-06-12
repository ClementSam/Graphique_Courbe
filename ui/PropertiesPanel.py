#PropertiesPanel.py

from core.app_state import AppState
from PyQt5 import QtWidgets, QtCore, QtGui
from signal_bus import signal_bus
import logging

logger = logging.getLogger(__name__)

class PropertiesPanel(QtWidgets.QTabWidget):

    def __init__(self, controller=None, parent=None):
        logger.debug("[PropertiesPanel.py > __init__()] ▶️ Entrée dans __init__()")

        super().__init__(parent)
        self.controller = controller
        self.setup_ui()
        self._connect_signals()

    def set_controller(self, controller):
        """Expose le contrôleur au panneau après initialisation."""
        self.controller = controller
        self._connect_signals()

    def _connect_signals(self):
        """Connecte les interactions utilisateur aux méthodes du contrôleur."""
        if not self.controller:
            return

        self.color_button.clicked.connect(self._choose_color)
        self.gain_slider.valueChanged.connect(
            lambda v: self._call_controller(self.controller.set_gain, v / 100)
        )
        self.offset_slider.valueChanged.connect(
            lambda v: self._call_controller(self.controller.set_offset, float(v))
        )
        self.style_combo.currentIndexChanged.connect(
            lambda i: self._call_controller(self.controller.set_style, self.style_combo.itemData(i))
        )
        self.symbol_combo.currentIndexChanged.connect(
            lambda i: self._call_controller(self.controller.set_symbol, self.symbol_combo.itemData(i))
        )
        self.fill_checkbox.toggled.connect(
            lambda val: self._call_controller(self.controller.set_fill, val)
        )
        self.display_mode_combo.currentIndexChanged.connect(
            lambda i: self._call_controller(self.controller.set_display_mode, self.display_mode_combo.itemData(i))
        )
        self.label_mode_combo.currentIndexChanged.connect(
            lambda i: self._call_controller(self.controller.set_label_mode, self.label_mode_combo.itemData(i))
        )
        self.zero_indicator_combo.currentIndexChanged.connect(
            lambda i: self._call_controller(self.controller.set_zero_indicator, self.zero_indicator_combo.itemData(i))
        )
        self.opacity_slider.valueChanged.connect(
            lambda v: self._call_controller(self.controller.set_opacity, float(v))
        )
        self.bring_to_front_button.clicked.connect(
            lambda: self._call_controller(self.controller.bring_curve_to_front)
        )

        # Connexions pour l'onglet graphique
        self.grid_checkbox.toggled.connect(
            lambda val: self._call_graph_controller(self.controller.set_grid_visible, val)
        )
        self.darkmode_checkbox.toggled.connect(
            lambda val: self._call_graph_controller(self.controller.set_dark_mode, val)
        )
        self.logx_checkbox.toggled.connect(
            lambda val: self._call_graph_controller(self.controller.set_log_x, val)
        )
        self.logy_checkbox.toggled.connect(
            lambda val: self._call_graph_controller(self.controller.set_log_y, val)
        )

    def setup_ui(self):
        logger.debug("[PropertiesPanel.py > setup_ui()] ▶️ Entrée dans setup_ui()")

        self.setup_graph_tab()
        self.setup_curve_tab()
        self.setTabEnabled(0, False)
        self.setTabEnabled(1, False)

    def setup_graph_tab(self):
        logger.debug("[PropertiesPanel.py > setup_graph_tab()] ▶️ Entrée dans setup_graph_tab()")

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
        logger.debug("[PropertiesPanel.py > setup_curve_tab()] ▶️ Entrée dans setup_curve_tab()")

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

    def _call_controller(self, func, *args):
        if not self.controller:
            return
        func(*args)
        signal_bus.curve_updated.emit()

    def _call_graph_controller(self, func, *args):
        if not self.controller:
            return
        func(*args)
        signal_bus.graph_updated.emit()
        
    def _choose_color(self):
        color = QtWidgets.QColorDialog.getColor(parent=self)
        if color.isValid():
            self.color_button.setStyleSheet(f"background-color: {color.name()}")
            self._call_controller(self.controller.set_color, color.name())
        
    def refresh_curve_tab(self):
        logger.debug("[PropertiesPanel] 🔁 Rafraîchissement de l’onglet courbe")
        self.update_curve_ui()

    def refresh_graph_tab(self):
        logger.debug("[PropertiesPanel] 🔁 Rafraîchissement de l’onglet graphique")
        self.update_graph_ui()

    def update_graph_ui(self):
        """Met à jour les champs de l'onglet graphique en fonction du graphique sélectionné."""
        state = AppState.get_instance()
        graph = state.current_graph
        if not graph:
            logger.debug("[PropertiesPanel] ⚠️ Aucun graphique sélectionné")
            return
    
        logger.debug(f"[PropertiesPanel] 🔄 Mise à jour des champs pour le graphique '{graph.name}'")
    
        # Nom du graphique
        self.label_graph_name.setText(graph.name)
    
        # Checkboxes
        self.grid_checkbox.setChecked(graph.grid_visible)
        self.darkmode_checkbox.setChecked(graph.dark_mode)
        self.logx_checkbox.setChecked(graph.log_x)
        self.logy_checkbox.setChecked(graph.log_y)
    
        # Police
        self.font_combo.setCurrentFont(QtGui.QFont(graph.font))
    
        # Unités et formats
        self.x_unit_input.setText(graph.x_unit or "")
        self.y_unit_input.setText(graph.y_unit or "")
    
        index_x_format = self.x_format_combo.findData(graph.x_format)
        self.x_format_combo.setCurrentIndex(index_x_format if index_x_format != -1 else 0)
    
        index_y_format = self.y_format_combo.findData(graph.y_format)
        self.y_format_combo.setCurrentIndex(index_y_format if index_y_format != -1 else 0)
    
        # Échelle Y fixée
        self.fix_y_checkbox.setChecked(graph.fix_y_range)
        self.ymin_input.setValue(graph.y_min if graph.fix_y_range else -5.0)
        self.ymax_input.setValue(graph.y_max if graph.fix_y_range else 5.0)
    
        # Satellites
        self.satellite_left_checkbox.setChecked(graph.satellite_visibility["left"])
        index_left = self.satellite_left_combo.findData(graph.satellite_content["left"])
        self.satellite_left_combo.setCurrentIndex(index_left if index_left != -1 else 0)
    
        self.satellite_right_checkbox.setChecked(graph.satellite_visibility["right"])
        index_right = self.satellite_right_combo.findData(graph.satellite_content["right"])
        self.satellite_right_combo.setCurrentIndex(index_right if index_right != -1 else 0)
    
        self.satellite_top_checkbox.setChecked(graph.satellite_visibility["top"])
        index_top = self.satellite_top_combo.findData(graph.satellite_content["top"])
        self.satellite_top_combo.setCurrentIndex(index_top if index_top != -1 else 0)
    
        self.satellite_bottom_checkbox.setChecked(graph.satellite_visibility["bottom"])
        index_bottom = self.satellite_bottom_combo.findData(graph.satellite_content["bottom"])
        self.satellite_bottom_combo.setCurrentIndex(index_bottom if index_bottom != -1 else 0)

    def update_curve_ui(self):
        """Met à jour les champs de l'onglet courbe en fonction de la courbe sélectionnée."""
        state = AppState.get_instance()
        curve = state.current_curve
        if not curve:
            logger.debug("[PropertiesPanel] ⚠️ Aucune courbe sélectionnée")
            return
    
        logger.debug(f"[PropertiesPanel] 🔄 Mise à jour des champs pour la courbe '{curve.name}'")
    
        self.label_curve_name.setText(curve.name)
        self.color_button.setStyleSheet(f"background-color: {curve.color}")
    
        index_style = self.style_combo.findData(curve.style)
        self.style_combo.setCurrentIndex(index_style if index_style != -1 else 0)
    
        self.width_spin.setValue(curve.width)
    
        index_symbol = self.symbol_combo.findData(curve.symbol)
        self.symbol_combo.setCurrentIndex(index_symbol if index_symbol != -1 else 0)
    
        index_display = self.display_mode_combo.findData(curve.display_mode)
        self.display_mode_combo.setCurrentIndex(index_display if index_display != -1 else 0)
    
        index_label = self.label_mode_combo.findData(curve.label_mode)
        self.label_mode_combo.setCurrentIndex(index_label if index_label != -1 else 0)
    
        self.opacity_slider.setValue(int(curve.opacity))
        self.fill_checkbox.setChecked(curve.fill)
    
        self.gain_slider.setValue(int(curve.gain * 100))  # gain 1.0 → slider 100
        self.offset_slider.setValue(int(curve.offset))    # offset en pixels/valeur
    
        index_zero = self.zero_indicator_combo.findData(curve.zero_indicator)
        self.zero_indicator_combo.setCurrentIndex(index_zero if index_zero != -1 else 0)
    
        # Downsampling
        index_ds = self.downsampling_combo.findData(curve.downsampling_mode)
        self.downsampling_combo.setCurrentIndex(index_ds if index_ds != -1 else 0)
    
        self.downsampling_ratio_input.setValue(curve.downsampling_ratio)
        is_manual = curve.downsampling_mode == "manual"
        self.downsampling_ratio_input.setEnabled(is_manual)
        self.downsampling_apply_btn.setEnabled(is_manual)
    
