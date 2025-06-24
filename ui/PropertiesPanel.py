#PropertiesPanel.py

from core.app_state import AppState
from PyQt5 import QtWidgets, QtCore, QtGui
from ui.widgets import BitGroupWidget
from signal_bus import signal_bus
import logging

logger = logging.getLogger(__name__)

class PropertiesPanel(QtWidgets.QTabWidget):

    def __init__(self, controller=None, parent=None):
        logger.debug("[PropertiesPanel.py > __init__()] ▶️ Entrée dans __init__()")

        super().__init__(parent)
        self.controller = controller
        # Limit the overall height so the dock doesn't occupy too much space
        self.setMaximumHeight(400)
        self.setup_ui()
        self._connect_signals()

    def set_controller(self, controller):
        """Expose le contrôleur au panneau après initialisation."""
        self.controller = controller
        self.bit_group_box.set_controller(controller)
        self._connect_signals()

    def _connect_signals(self):
        """Connecte les interactions utilisateur aux méthodes du contrôleur."""
        if not self.controller:
            return

        self.color_button.clicked.connect(self._choose_color)
        self.width_spin.valueChanged.connect(
            lambda v: self._call_controller(self.controller.set_width, int(v))
        )
        self.gain_slider.valueChanged.connect(self._on_gain_slider)
        self.gain_apply_btn.clicked.connect(self._apply_gain)
        self.gain_mode_combo.currentIndexChanged.connect(self._on_gain_mode_changed)
        self.unit_gain_apply_btn.clicked.connect(self._apply_units_per_grid)
        self.offset_slider.valueChanged.connect(self._on_offset_slider)
        self.offset_apply_btn.clicked.connect(self._apply_offset)
        self.time_offset_apply_btn.clicked.connect(
            lambda: self._call_controller(
                self.controller.set_time_offset,
                float(self.time_offset_input.value()),
            )
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
        self.bits_checkbox.toggled.connect(self._on_bits_toggled)
        self.bits_checkbox.toggled.connect(self.bit_group_box.setEnabled)

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

        # Nouvelles connexions pour les options d'axe
        self.x_unit_input.editingFinished.connect(
            lambda: self._call_graph_controller(
                self.controller.set_x_unit, self.x_unit_input.text()
            )
        )
        self.y_unit_input.editingFinished.connect(
            lambda: self._call_graph_controller(
                self.controller.set_y_unit, self.y_unit_input.text()
            )
        )
        self.x_format_combo.currentIndexChanged.connect(
            lambda i: self._call_graph_controller(
                self.controller.set_x_format, self.x_format_combo.itemData(i)
            )
        )
        self.y_format_combo.currentIndexChanged.connect(
            lambda i: self._call_graph_controller(
                self.controller.set_y_format, self.y_format_combo.itemData(i)
            )
        )
        self.fix_y_checkbox.toggled.connect(
            lambda val: self._call_graph_controller(self.controller.set_fix_y_range, val)
        )
        self.ymin_input.valueChanged.connect(
            lambda v: self._call_graph_controller(
                self.controller.set_y_limits, float(v), self.ymax_input.value()
            )
        )
        self.ymax_input.valueChanged.connect(
            lambda v: self._call_graph_controller(
                self.controller.set_y_limits, self.ymin_input.value(), float(v)
            )
        )

        # Satellite zones
        self.satellite_left_checkbox.toggled.connect(
            lambda val: self._call_graph_controller(
                self.controller.set_satellite_visible, "left", val
            )
        )
        self.satellite_right_checkbox.toggled.connect(
            lambda val: self._call_graph_controller(
                self.controller.set_satellite_visible, "right", val
            )
        )
        self.satellite_top_checkbox.toggled.connect(
            lambda val: self._call_graph_controller(
                self.controller.set_satellite_visible, "top", val
            )
        )
        self.satellite_bottom_checkbox.toggled.connect(
            lambda val: self._call_graph_controller(
                self.controller.set_satellite_visible, "bottom", val
            )
        )

        for zone, btn in {
            "left": self.satellite_left_color,
            "right": self.satellite_right_color,
            "top": self.satellite_top_color,
            "bottom": self.satellite_bottom_color,
        }.items():
            btn.clicked.connect(
                lambda _, z=zone, b=btn: self._choose_satellite_color(z, b)
            )

        for zone, spin in {
            "left": self.satellite_left_size,
            "right": self.satellite_right_size,
            "top": self.satellite_top_size,
            "bottom": self.satellite_bottom_size,
        }.items():
            spin.valueChanged.connect(
                lambda val, z=zone: self._call_graph_controller(
                    self.controller.set_satellite_size, z, int(val)
                )
            )

        for zone, btn in self.satellite_add_buttons.items():
            btn.clicked.connect(lambda _, z=zone: self._add_satellite_item(z))

        self.add_zone_btn.clicked.connect(self._add_zone_item)

        signal_bus.graph_updated.connect(self.update_mode_tab)
        self.update_mode_tab()

    def setup_ui(self):
        logger.debug("[PropertiesPanel.py > setup_ui()] ▶️ Entrée dans setup_ui()")

        self.setup_graph_tab()
        self.setup_curve_tab()
        self.setup_mode_tab()
        self.setTabEnabled(0, False)
        self.setTabEnabled(1, False)
        self.setTabEnabled(2, False)

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
        
        # Satellite zones
        def create_satellite_group(title):
            group = QtWidgets.QGroupBox(title)
            v = QtWidgets.QVBoxLayout(group)
            checkbox = QtWidgets.QCheckBox("Afficher")
            color_btn = QtWidgets.QPushButton("Couleur")
            size_spin = QtWidgets.QSpinBox()
            size_spin.setRange(20, 500)
            table = QtWidgets.QTableWidget(0, 2)
            table.setHorizontalHeaderLabels(["Type", "Texte"])
            add_btn = QtWidgets.QPushButton("Ajouter")
            def toggle(enabled):
                color_btn.setEnabled(enabled)
                size_spin.setEnabled(enabled)
                table.setEnabled(enabled)
                add_btn.setEnabled(enabled)
            checkbox.toggled.connect(toggle)
            v.addWidget(checkbox)
            h = QtWidgets.QHBoxLayout()
            h.addWidget(color_btn)
            h.addWidget(size_spin)
            v.addLayout(h)
            v.addWidget(table)
            v.addWidget(add_btn)
            toggle(False)
            return group, checkbox, color_btn, size_spin, table, add_btn

        (self.sat_left_group,
         self.satellite_left_checkbox,
         self.satellite_left_color,
         self.satellite_left_size,
         self.satellite_left_table,
         self.satellite_left_add) = create_satellite_group("Zone gauche")
        layout.addWidget(self.sat_left_group)

        (self.sat_right_group,
         self.satellite_right_checkbox,
         self.satellite_right_color,
         self.satellite_right_size,
         self.satellite_right_table,
         self.satellite_right_add) = create_satellite_group("Zone droite")
        layout.addWidget(self.sat_right_group)

        (self.sat_top_group,
         self.satellite_top_checkbox,
         self.satellite_top_color,
         self.satellite_top_size,
         self.satellite_top_table,
         self.satellite_top_add) = create_satellite_group("Zone haut")
        layout.addWidget(self.sat_top_group)

        (self.sat_bottom_group,
         self.satellite_bottom_checkbox,
         self.satellite_bottom_color,
         self.satellite_bottom_size,
         self.satellite_bottom_table,
         self.satellite_bottom_add) = create_satellite_group("Zone bas")
        layout.addWidget(self.sat_bottom_group)

        self.satellite_tables = {
            "left": self.satellite_left_table,
            "right": self.satellite_right_table,
            "top": self.satellite_top_table,
            "bottom": self.satellite_bottom_table,
        }
        self.satellite_add_buttons = {
            "left": self.satellite_left_add,
            "right": self.satellite_right_add,
            "top": self.satellite_top_add,
            "bottom": self.satellite_bottom_add,
        }

        # Zone objects in the plot
        zone_group = QtWidgets.QGroupBox("Zones personnalisées")
        v_z = QtWidgets.QVBoxLayout(zone_group)
        self.zone_table = QtWidgets.QTableWidget(0, 3)
        self.zone_table.setHorizontalHeaderLabels(["Type", "Paramètres", ""])
        self.add_zone_btn = QtWidgets.QPushButton("Ajouter une zone")
        v_z.addWidget(self.zone_table)
        v_z.addWidget(self.add_zone_btn)
        layout.addWidget(zone_group)

        scroll_graph = QtWidgets.QScrollArea()
        scroll_graph.setWidgetResizable(True)
        scroll_graph.setWidget(tab_graph)

        self.addTab(scroll_graph, "Propriétés du graphique")

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
        
        self.gain_mode_combo = QtWidgets.QComboBox()
        self.gain_mode_combo.addItem("Multiplicateur", "multiplier")
        self.gain_mode_combo.addItem("Unité par carreau", "unit")

        self.gain_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.gain_slider.setRange(1, 500)  # de 0.01 à 5.00
        self.gain_slider.setValue(100)
        self.gain_input = QtWidgets.QDoubleSpinBox()
        self.gain_input.setRange(0.01, 5.0)
        self.gain_input.setDecimals(2)
        self.gain_input.setSingleStep(0.01)
        self.gain_apply_btn = QtWidgets.QPushButton("Appliquer")

        self.units_per_grid_input = QtWidgets.QDoubleSpinBox()
        self.units_per_grid_input.setRange(0.01, 1000.0)
        self.units_per_grid_input.setDecimals(2)
        self.units_per_grid_input.setSingleStep(0.1)
        self.unit_gain_apply_btn = QtWidgets.QPushButton("Appliquer")

        self.offset_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.offset_slider.setRange(-500, 500)
        self.offset_slider.setValue(0)
        self.offset_input = QtWidgets.QDoubleSpinBox()
        self.offset_input.setRange(-500.0, 500.0)
        self.offset_input.setDecimals(2)
        self.offset_input.setSingleStep(0.1)
        self.offset_apply_btn = QtWidgets.QPushButton("Appliquer")

        self.time_offset_input = QtWidgets.QDoubleSpinBox()
        self.time_offset_input.setRange(-1000.0, 1000.0)
        self.time_offset_input.setDecimals(3)
        self.time_offset_input.setSingleStep(0.1)
        self.time_offset_apply_btn = QtWidgets.QPushButton("Appliquer")
        
        self.zero_indicator_combo = QtWidgets.QComboBox()
        self.zero_indicator_combo.addItem("Aucun", "none")
        self.zero_indicator_combo.addItem("Ligne horizontale", "line")
        layout.addWidget(QtWidgets.QLabel("Indicateur de zéro :"))
        layout.addWidget(self.zero_indicator_combo)

        # Bits display option
        self.bits_checkbox = QtWidgets.QCheckBox("Afficher les bits")
        layout.addWidget(self.bits_checkbox)
        self.bit_group_box = BitGroupWidget(self.controller)
        self.bit_group_box.setEnabled(False)
        layout.addWidget(self.bit_group_box)

        layout.addWidget(QtWidgets.QLabel("Mode de gain :"))
        layout.addWidget(self.gain_mode_combo)

        self.gain_label = QtWidgets.QLabel("Gain (x0.01 à x5.00) :")
        layout.addWidget(self.gain_label)
        gain_layout = QtWidgets.QHBoxLayout()
        gain_layout.addWidget(self.gain_slider)
        gain_layout.addWidget(self.gain_input)
        gain_layout.addWidget(self.gain_apply_btn)
        self.gain_widget = QtWidgets.QWidget()
        self.gain_widget.setLayout(gain_layout)
        layout.addWidget(self.gain_widget)

        self.unit_gain_label = QtWidgets.QLabel("Unité par carreau :")
        layout.addWidget(self.unit_gain_label)
        unit_layout = QtWidgets.QHBoxLayout()
        unit_layout.addWidget(self.units_per_grid_input)
        unit_layout.addWidget(self.unit_gain_apply_btn)
        self.unit_gain_widget = QtWidgets.QWidget()
        self.unit_gain_widget.setLayout(unit_layout)
        layout.addWidget(self.unit_gain_widget)
        self._update_gain_mode_ui("multiplier")

        layout.addWidget(QtWidgets.QLabel("Offset vertical :"))
        off_layout = QtWidgets.QHBoxLayout()
        off_layout.addWidget(self.offset_slider)
        off_layout.addWidget(self.offset_input)
        off_layout.addWidget(self.offset_apply_btn)
        layout.addLayout(off_layout)

        h_time = QtWidgets.QHBoxLayout()
        h_time.addWidget(QtWidgets.QLabel("Décalage temporel :"))
        h_time.addWidget(self.time_offset_input)
        h_time.addWidget(self.time_offset_apply_btn)
        layout.addLayout(h_time)
        
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

        scroll_curve = QtWidgets.QScrollArea()
        scroll_curve.setWidgetResizable(True)
        scroll_curve.setWidget(tab_curve)

        self.addTab(scroll_curve, "Propriétés de la courbe")

    def setup_mode_tab(self):
        logger.debug("[PropertiesPanel.py > setup_mode_tab()] ▶️ Entrée dans setup_mode_tab()")

        tab_mode = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab_mode)

        self.mode_layout = QtWidgets.QFormLayout()
        layout.addLayout(self.mode_layout)
        layout.addStretch()

        self.mode_combos = {}
        self.update_mode_tab()

        scroll_mode = QtWidgets.QScrollArea()
        scroll_mode.setWidgetResizable(True)
        scroll_mode.setWidget(tab_mode)

        self.addTab(scroll_mode, "Mode")

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

    def _choose_satellite_color(self, zone: str, button: QtWidgets.QPushButton):
        color = QtWidgets.QColorDialog.getColor(parent=self)
        if color.isValid():
            button.setStyleSheet(f"background-color: {color.name()}")
            self._call_graph_controller(
                self.controller.set_satellite_color, zone, color.name()
            )

    def _add_satellite_item(self, zone: str):
        options = ["Texte", "Bouton", "Image"]
        choice, ok = QtWidgets.QInputDialog.getItem(
            self,
            "Ajouter un objet",
            "Type d'objet :",
            options,
            0,
            False,
        )
        if not ok:
            return

        table = self.satellite_tables[zone]
        row = table.rowCount()
        table.insertRow(row)
        table.setItem(row, 0, QtWidgets.QTableWidgetItem(choice))

        if choice == "Texte":
            widget = QtWidgets.QLineEdit()
            table.setCellWidget(row, 1, widget)
            content = ""
        elif choice == "Bouton":
            widget = QtWidgets.QPushButton("Bouton")
            table.setCellWidget(row, 1, widget)
            content = "Bouton"
        else:
            widget = QtWidgets.QLabel("Image")
            table.setCellWidget(row, 1, widget)
            content = ""

        if self.controller:
            item = {"type": choice.lower(), "text": content}
            self._call_graph_controller(
                self.controller.add_satellite_item, zone, item
            )

    def _add_zone_item(self):
        options = ["LinearRegion", "Rectangle", "Path"]
        choice, ok = QtWidgets.QInputDialog.getItem(
            self,
            "Ajouter une zone",
            "Type de zone :",
            options,
            0,
            False,
        )
        if not ok:
            return

        if choice == "LinearRegion":
            zone = {"type": "linear", "bounds": [0.0, 1.0]}
            placeholder = "début, fin"
        elif choice == "Rectangle":
            zone = {"type": "rect", "rect": [0.0, 0.0, 1.0, 1.0]}
            placeholder = "x, y, largeur, hauteur"
        else:
            zone = {"type": "path", "points": [(0.0, 0.0), (1.0, 1.0)]}
            placeholder = "x1, y1, x2, y2, ..."

        row = self.zone_table.rowCount()
        self.zone_table.insertRow(row)
        self.zone_table.setItem(row, 0, QtWidgets.QTableWidgetItem(zone["type"]))

        edit = QtWidgets.QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.editingFinished.connect(lambda r=row: self._update_zone_from_row(r))
        self.zone_table.setCellWidget(row, 1, edit)

        btn = QtWidgets.QPushButton("Supprimer")
        btn.clicked.connect(lambda _, r=row: self._remove_zone_row(r))
        self.zone_table.setCellWidget(row, 2, btn)

        if self.controller:
            self._call_graph_controller(self.controller.add_zone, zone)
        self.update_graph_ui()

    def _on_gain_slider(self, value: int):
        self.gain_input.setValue(value / 100)
        self._call_controller(self.controller.set_gain, value / 100)

    def _apply_gain(self):
        val = float(self.gain_input.value())
        self.gain_slider.setValue(int(val * 100))
        self._call_controller(self.controller.set_gain, val)

    def _on_gain_mode_changed(self, index: int):
        mode = self.gain_mode_combo.itemData(index)
        self._call_controller(self.controller.set_gain_mode, mode)
        self._update_gain_mode_ui(mode)

    def _apply_units_per_grid(self):
        val = float(self.units_per_grid_input.value())
        self._call_controller(self.controller.set_units_per_grid, val)

    def _update_gain_mode_ui(self, mode: str):
        show_multiplier = mode == "multiplier"
        self.gain_label.setVisible(show_multiplier)
        self.gain_widget.setVisible(show_multiplier)
        self.unit_gain_label.setVisible(not show_multiplier)
        self.unit_gain_widget.setVisible(not show_multiplier)

    def _on_offset_slider(self, value: int):
        self.offset_input.setValue(float(value))
        self._call_controller(self.controller.set_offset, float(value))

    def _apply_offset(self):
        val = float(self.offset_input.value())
        self.offset_slider.setValue(int(val))
        self._call_controller(self.controller.set_offset, val)

    def _update_zone_from_row(self, row: int):
        edit = self.zone_table.cellWidget(row, 1)
        if not isinstance(edit, QtWidgets.QLineEdit):
            return
        text = edit.text()
        ztype_item = self.zone_table.item(row, 0)
        if ztype_item is None:
            return
        ztype = ztype_item.text()
        values = [float(v.strip()) for v in text.split(',') if v.strip()]
        if ztype == "linear" and len(values) >= 2:
            zone = {"type": "linear", "bounds": values[:2]}
        elif ztype == "rect" and len(values) >= 4:
            zone = {"type": "rect", "rect": values[:4]}
        elif ztype == "path" and len(values) >= 4 and len(values) % 2 == 0:
            pts = list(zip(values[::2], values[1::2]))
            zone = {"type": "path", "points": pts}
        else:
            return

        if self.controller:
            self._call_graph_controller(self.controller.update_zone, row, zone)

    def _remove_zone_row(self, row: int):
        if self.controller:
            self._call_graph_controller(self.controller.remove_zone, row)
        self.update_graph_ui()

    def _on_bits_toggled(self, checked: bool):
        if not checked:
            return

        state = AppState.get_instance()
        curve = state.current_curve
        if not curve:
            return

        import numpy as np

        values = curve.y
        mask = np.isnan(values)
        finite_values = values[~mask]

        if not np.allclose(finite_values, np.round(finite_values)):
            QtWidgets.QMessageBox.warning(self, "Erreur", "Les données ne sont pas entières")
            self.bits_checkbox.setChecked(False)
            return

        if finite_values.size and int(finite_values.min()) < 0:
            QtWidgets.QMessageBox.warning(self, "Erreur", "Les valeurs négatives ne sont pas prises en charge")
            self.bits_checkbox.setChecked(False)
            return
        
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
        for zone, checkbox in {
            "left": self.satellite_left_checkbox,
            "right": self.satellite_right_checkbox,
            "top": self.satellite_top_checkbox,
            "bottom": self.satellite_bottom_checkbox,
        }.items():
            checkbox.blockSignals(True)
            checkbox.setChecked(graph.satellite_visibility[zone])
            checkbox.blockSignals(False)

        for zone, btn in {
            "left": self.satellite_left_color,
            "right": self.satellite_right_color,
            "top": self.satellite_top_color,
            "bottom": self.satellite_bottom_color,
        }.items():
            color = graph.satellite_settings[zone]["color"]
            btn.setStyleSheet(f"background-color: {color}")

        for zone, widgets in {
            "left": (self.satellite_left_color, self.satellite_left_size, self.satellite_left_table, self.satellite_left_add),
            "right": (self.satellite_right_color, self.satellite_right_size, self.satellite_right_table, self.satellite_right_add),
            "top": (self.satellite_top_color, self.satellite_top_size, self.satellite_top_table, self.satellite_top_add),
            "bottom": (self.satellite_bottom_color, self.satellite_bottom_size, self.satellite_bottom_table, self.satellite_bottom_add),
        }.items():
            enabled = graph.satellite_visibility[zone]
            for w in widgets:
                w.setEnabled(enabled)

        for zone, spin in {
            "left": self.satellite_left_size,
            "right": self.satellite_right_size,
            "top": self.satellite_top_size,
            "bottom": self.satellite_bottom_size,
        }.items():
            spin.blockSignals(True)
            spin.setValue(graph.satellite_settings[zone]["size"])
            spin.blockSignals(False)

        for zone, table in self.satellite_tables.items():
            table.blockSignals(True)
            table.setRowCount(0)
            for item in graph.satellite_settings[zone]["items"]:
                row = table.rowCount()
                table.insertRow(row)
                typ = item.get("type", "")
                table.setItem(row, 0, QtWidgets.QTableWidgetItem(typ.capitalize()))
                if typ == "text":
                    widget = QtWidgets.QLineEdit(item.get("text", ""))
                elif typ in {"button", "bouton"}:
                    widget = QtWidgets.QPushButton(item.get("text", "Bouton"))
                else:
                    widget = QtWidgets.QLabel(item.get("text", ""))
                table.setCellWidget(row, 1, widget)
            table.blockSignals(False)

        # Zones table
        self.zone_table.blockSignals(True)
        self.zone_table.setRowCount(0)
        for idx, zone in enumerate(getattr(graph, "zones", [])):
            row = self.zone_table.rowCount()
            self.zone_table.insertRow(row)
            ztype = zone.get("type", "")
            self.zone_table.setItem(row, 0, QtWidgets.QTableWidgetItem(ztype))

            if ztype == "linear":
                desc = ", ".join(str(v) for v in zone.get("bounds", []))
                placeholder = "début, fin"
            elif ztype == "rect":
                desc = ", ".join(str(v) for v in zone.get("rect", []))
                placeholder = "x, y, largeur, hauteur"
            else:
                pts = zone.get("points", [])
                flat = []
                for x, y in pts:
                    flat.extend([x, y])
                desc = ", ".join(str(v) for v in flat)
                placeholder = "x1, y1, x2, y2, ..."

            edit = QtWidgets.QLineEdit(desc)
            edit.setPlaceholderText(placeholder)
            edit.editingFinished.connect(lambda r=idx: self._update_zone_from_row(r))
            self.zone_table.setCellWidget(row, 1, edit)

            btn = QtWidgets.QPushButton("Supprimer")
            btn.clicked.connect(lambda _, r=idx: self._remove_zone_row(r))
            self.zone_table.setCellWidget(row, 2, btn)
        self.zone_table.blockSignals(False)

    def update_curve_ui(self):
        """Met à jour les champs de l'onglet courbe en fonction de la courbe sélectionnée."""
        state = AppState.get_instance()
        curve = state.current_curve
        if not curve:
            logger.debug("[PropertiesPanel] ⚠️ Aucune courbe sélectionnée")
            self.label_curve_name.setText("—")
            self.color_button.setStyleSheet("")
            self.style_combo.setCurrentIndex(0)
            self.width_spin.setValue(1)
            self.symbol_combo.setCurrentIndex(0)
            self.display_mode_combo.setCurrentIndex(0)
            self.label_mode_combo.setCurrentIndex(0)
            self.opacity_slider.setValue(100)
            self.fill_checkbox.setChecked(False)
            self.gain_slider.setValue(100)
            self.gain_input.setValue(1.0)
            self.gain_mode_combo.setCurrentIndex(0)
            self.units_per_grid_input.setValue(1.0)
            self.offset_slider.setValue(0)
            self.offset_input.setValue(0.0)
            self.time_offset_input.setValue(0.0)
            self.zero_indicator_combo.setCurrentIndex(0)
            self.downsampling_combo.setCurrentIndex(0)
            self.downsampling_ratio_input.setValue(10)
            self.downsampling_ratio_input.setEnabled(False)
            self.downsampling_apply_btn.setEnabled(False)
            self.bits_checkbox.setChecked(False)
            self.bits_checkbox.setEnabled(False)
            self._update_gain_mode_ui("multiplier")
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

        mode_index = self.gain_mode_combo.findData(getattr(curve, "gain_mode", "multiplier"))
        self.gain_mode_combo.blockSignals(True)
        self.gain_mode_combo.setCurrentIndex(mode_index if mode_index != -1 else 0)
        self.gain_mode_combo.blockSignals(False)
        self._update_gain_mode_ui(self.gain_mode_combo.currentData())

        self.gain_slider.setValue(int(curve.gain * 100))  # gain 1.0 → slider 100
        self.gain_input.setValue(curve.gain)
        self.units_per_grid_input.setValue(getattr(curve, "units_per_grid", 1.0))
        self.offset_slider.setValue(int(curve.offset))    # offset en pixels/valeur
        self.offset_input.setValue(curve.offset)
        self.time_offset_input.setValue(curve.time_offset)
    
        index_zero = self.zero_indicator_combo.findData(curve.zero_indicator)
        self.zero_indicator_combo.setCurrentIndex(index_zero if index_zero != -1 else 0)
    
        # Downsampling
        index_ds = self.downsampling_combo.findData(curve.downsampling_mode)
        self.downsampling_combo.setCurrentIndex(index_ds if index_ds != -1 else 0)
    
        self.downsampling_ratio_input.setValue(curve.downsampling_ratio)
        is_manual = curve.downsampling_mode == "manual"
        self.downsampling_ratio_input.setEnabled(is_manual)
        self.downsampling_apply_btn.setEnabled(is_manual)

        has_bits = any(c.parent_curve == curve.name for c in state.current_graph.curves)
        self.bits_checkbox.blockSignals(True)
        self.bits_checkbox.setChecked(has_bits)
        self.bits_checkbox.setEnabled(True)
        self.bits_checkbox.blockSignals(False)
        self.bit_group_box.setEnabled(self.bits_checkbox.isChecked())

    def update_mode_tab(self):
        """Refresh the list of graphs available in the mode tab."""
        if not hasattr(self, "mode_layout"):
            return

        while self.mode_layout.count():
            item = self.mode_layout.takeAt(0)
            if item:
                if item.widget():
                    item.widget().deleteLater()

        self.mode_combos.clear()
        state = AppState.get_instance()

        for graph in state.graphs.values():
            combo = QtWidgets.QComboBox()
            combo.addItem("Analyseur logique", "logic_analyzer")
            combo.addItem("Standard", "standard")
            combo.addItem("Analyse", "analysis")
            combo.addItem("Sombre", "dark")

            # Position the combo box on the current mode of the graph
            index = combo.findData(graph.mode)
            combo.setCurrentIndex(index if index != -1 else 0)

            # Apply button to trigger the mode change explicitly
            apply_btn = QtWidgets.QPushButton("Appliquer")
            apply_btn.clicked.connect(
                lambda _, g=graph.name, c=combo: self._call_graph_controller(
                    self.controller.apply_mode, g, c.currentData()
                )
            )

            h_layout = QtWidgets.QHBoxLayout()
            h_layout.addWidget(combo)
            h_layout.addWidget(apply_btn)

            container = QtWidgets.QWidget()
            container.setLayout(h_layout)

            self.mode_layout.addRow(graph.name, container)
            self.mode_combos[graph.name] = combo
    
