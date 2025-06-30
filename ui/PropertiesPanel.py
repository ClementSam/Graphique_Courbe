# PropertiesPanel.py

from core.app_state import AppState
from PyQt5 import QtWidgets, QtCore, QtGui
from ui.widgets import BitGroupWidget
from signal_bus import signal_bus
from core.utils import generate_random_color
from core import SatelliteObjectData
import logging

logger = logging.getLogger(__name__)

# Available zone types and their placeholders for the "Zones personnalisées" table
ZONE_TYPES = {
    "hlinear": "début, fin",
    "vlinear": "début, fin",
    "rect": "x, y, largeur, hauteur",
    "path": "x1, y1, x2, y2, ...",
}


class ZoneParamsWidget(QtWidgets.QWidget):
    """Widget to edit parameters of a custom zone."""

    changed = QtCore.pyqtSignal()

    def __init__(self, ztype: str = "vlinear", zone: dict | None = None, parent=None):
        super().__init__(parent)
        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._points_layout: QtWidgets.QVBoxLayout | None = None
        self._type = None
        self._fields: list[QtWidgets.QDoubleSpinBox] = []
        self._points: list[
            tuple[QtWidgets.QWidget, QtWidgets.QDoubleSpinBox, QtWidgets.QDoubleSpinBox]
        ] = []
        self._add_btn: QtWidgets.QPushButton | None = None
        self.set_type(ztype)
        if zone:
            self.set_zone(zone)

    def _clear_layout(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._points_layout = None

    def _create_spin(self, placeholder: str = ""):
        spin = QtWidgets.QDoubleSpinBox()
        spin.setRange(-1e9, 1e9)
        spin.setDecimals(6)
        spin.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        if placeholder:
            spin.setPrefix(placeholder + " ")
        spin.valueChanged.connect(self.changed.emit)
        return spin

    def set_type(self, ztype: str):
        if ztype == self._type:
            return
        self._type = ztype
        self._fields.clear()
        self._points.clear()
        self._clear_layout()

        if ztype in {"hlinear", "vlinear"}:
            row = QtWidgets.QHBoxLayout()
            for name in ["x départ", "x de fin"]:
                spin = self._create_spin(name)
                self._fields.append(spin)
                row.addWidget(spin)
            self._layout.addLayout(row)
        elif ztype == "rect":
            row = QtWidgets.QHBoxLayout()
            for name in ["x", "y", "largeur", "hauteur"]:
                spin = self._create_spin(name)
                self._fields.append(spin)
                row.addWidget(spin)
            self._layout.addLayout(row)
        else:  # path
            self._points_layout = QtWidgets.QVBoxLayout()
            self._layout.addLayout(self._points_layout)
            self._add_btn = QtWidgets.QPushButton("+")
            self._add_btn.clicked.connect(self._add_point)
            self._layout.addWidget(self._add_btn)

    def _add_point(self, x: float = 0.0, y: float = 0.0):
        cont = QtWidgets.QWidget()
        lay = QtWidgets.QHBoxLayout(cont)
        lay.setContentsMargins(0, 0, 0, 0)
        sx = self._create_spin("x")
        sy = self._create_spin("y")
        sx.setValue(x)
        sy.setValue(y)
        rm = QtWidgets.QPushButton("-")
        rm.setFixedWidth(20)
        rm.clicked.connect(lambda *_: self._remove_point(cont))
        for w in (sx, sy, rm):
            lay.addWidget(w)
        if self._points_layout is not None:
            self._points_layout.addWidget(cont)
        else:
            self._layout.addWidget(cont)
        self._points.append((cont, sx, sy))
        self.changed.emit()

    def _remove_point(self, widget: QtWidgets.QWidget):
        for i, (w, sx, sy) in enumerate(self._points):
            if w is widget:
                self._points.pop(i)
                w.deleteLater()
                break
        self.changed.emit()

    def set_zone(self, zone: dict):
        self.blockSignals(True)
        self.set_type(zone.get("type", "vlinear"))
        if self._type in {"hlinear", "vlinear"}:
            vals = zone.get("bounds", [0.0, 1.0])
            for spin, val in zip(self._fields, vals):
                spin.setValue(val)
        elif self._type == "rect":
            vals = zone.get("rect", [0.0, 0.0, 1.0, 1.0])
            for spin, val in zip(self._fields, vals):
                spin.setValue(val)
        else:
            pts = zone.get("points", [])
            # clear existing points except add button
            for w, _, _ in list(self._points):
                w.deleteLater()
            self._points.clear()
            for x, y in pts:
                self._add_point(x, y)
        self.blockSignals(False)

    def get_zone(self) -> dict:
        if self._type in {"hlinear", "vlinear"}:
            vals = [f.value() for f in self._fields]
            return {"type": self._type, "bounds": vals}
        if self._type == "rect":
            vals = [f.value() for f in self._fields]
            return {"type": "rect", "rect": vals}
        pts = [(sx.value(), sy.value()) for _, sx, sy in self._points]
        return {"type": "path", "points": pts}


class PropertiesPanel(QtWidgets.QTabWidget):

    def __init__(self, controller=None, parent=None):
        logger.debug("[PropertiesPanel.py > __init__()] ▶️ Entrée dans __init__()")

        super().__init__(parent)
        self.controller = controller
        # Allow the panel to expand to fill the available dock area
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
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
            lambda i: self._call_controller(
                self.controller.set_style, self.style_combo.itemData(i)
            )
        )
        self.symbol_combo.currentIndexChanged.connect(
            lambda i: self._call_controller(
                self.controller.set_symbol, self.symbol_combo.itemData(i)
            )
        )
        self.fill_checkbox.toggled.connect(
            lambda val: self._call_controller(self.controller.set_fill, val)
        )
        self.display_mode_combo.currentIndexChanged.connect(
            lambda i: self._call_controller(
                self.controller.set_display_mode, self.display_mode_combo.itemData(i)
            )
        )
        self.label_mode_combo.currentIndexChanged.connect(
            lambda i: self._call_controller(
                self.controller.set_label_mode, self.label_mode_combo.itemData(i)
            )
        )
        self.zero_indicator_combo.currentIndexChanged.connect(
            lambda i: self._call_controller(
                self.controller.set_zero_indicator,
                self.zero_indicator_combo.itemData(i),
            )
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
            lambda val: self._call_graph_controller(
                self.controller.set_grid_visible, val
            )
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
            lambda val: self._call_graph_controller(
                self.controller.set_fix_y_range, val
            )
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

        # Add satellite object buttons
        self.add_zone_btn.clicked.connect(self._add_zone_item)
        for zone, btn in {
            "left": self.satellite_left_add_btn,
            "right": self.satellite_right_add_btn,
            "top": self.satellite_top_add_btn,
            "bottom": self.satellite_bottom_add_btn,
        }.items():
            btn.clicked.connect(lambda _, z=zone: self._add_satellite_object(z))

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
        logger.debug(
            "[PropertiesPanel.py > setup_graph_tab()] ▶️ Entrée dans setup_graph_tab()"
        )

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
        def create_satellite_group(title, zone):
            group = QtWidgets.QGroupBox(title)
            v = QtWidgets.QVBoxLayout(group)
            checkbox = QtWidgets.QCheckBox("Afficher")
            color_btn = QtWidgets.QPushButton("Couleur")
            size_spin = QtWidgets.QSpinBox()
            size_spin.setRange(20, 500)

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

            table = QtWidgets.QTableWidget(0, 10)
            table.setHorizontalHeaderLabels(
                [
                    "Type",
                    "Nom",
                    "Param",
                    "Largeur",
                    "Hauteur",
                    "X",
                    "Y",
                    "Ancre",
                    "Calque",
                    "",
                ]
            )
            # Stretch columns so the content remains visible
            header = table.horizontalHeader()
            header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
            header.setStretchLastSection(True)
            table.setMinimumHeight(150)
            add_btn = QtWidgets.QPushButton("Ajouter")
            v.addWidget(table)
            v.addWidget(add_btn)

            table.setEnabled(False)
            add_btn.setEnabled(False)
            toggle(False)

            return group, checkbox, color_btn, size_spin, table, add_btn

        (
            self.sat_left_group,
            self.satellite_left_checkbox,
            self.satellite_left_color,
            self.satellite_left_size,
            self.satellite_left_table,
            self.satellite_left_add_btn,
        ) = create_satellite_group("Zone gauche", "left")
        layout.addWidget(self.sat_left_group)

        (
            self.sat_right_group,
            self.satellite_right_checkbox,
            self.satellite_right_color,
            self.satellite_right_size,
            self.satellite_right_table,
            self.satellite_right_add_btn,
        ) = create_satellite_group("Zone droite", "right")
        layout.addWidget(self.sat_right_group)

        (
            self.sat_top_group,
            self.satellite_top_checkbox,
            self.satellite_top_color,
            self.satellite_top_size,
            self.satellite_top_table,
            self.satellite_top_add_btn,
        ) = create_satellite_group("Zone haut", "top")
        layout.addWidget(self.sat_top_group)

        (
            self.sat_bottom_group,
            self.satellite_bottom_checkbox,
            self.satellite_bottom_color,
            self.satellite_bottom_size,
            self.satellite_bottom_table,
            self.satellite_bottom_add_btn,
        ) = create_satellite_group("Zone bas", "bottom")
        layout.addWidget(self.sat_bottom_group)

        # Palette no longer used

        # Zone objects in the plot
        zone_group = QtWidgets.QGroupBox("Zones personnalisées")
        v_z = QtWidgets.QVBoxLayout(zone_group)
        self.zone_table = QtWidgets.QTableWidget(0, 9)
        self.zone_table.setHorizontalHeaderLabels(
            [
                "Type",
                "Nom",
                "Paramètres",
                "Couleur trait",
                "trait : alpha",
                "trait : épaisseur",
                "Couleur plein",
                "Plein : alpha",
                "",
            ]
        )
        header = self.zone_table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        header.setStretchLastSection(True)
        self.zone_table.setMinimumHeight(150)
        self.add_zone_btn = QtWidgets.QPushButton("Ajouter une zone")
        v_z.addWidget(self.zone_table)
        v_z.addWidget(self.add_zone_btn)
        layout.addWidget(zone_group)

        scroll_graph = QtWidgets.QScrollArea()
        scroll_graph.setWidgetResizable(True)
        scroll_graph.setWidget(tab_graph)

        self.addTab(scroll_graph, "Propriétés du graphique")

    def setup_curve_tab(self):
        logger.debug(
            "[PropertiesPanel.py > setup_curve_tab()] ▶️ Entrée dans setup_curve_tab()"
        )

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
        logger.debug(
            "[PropertiesPanel.py > setup_mode_tab()] ▶️ Entrée dans setup_mode_tab()"
        )

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

    def _choose_zone_color(self, row: int, column: int):
        btn = self.zone_table.cellWidget(row, column)
        if not isinstance(btn, QtWidgets.QPushButton):
            return
        color = QtWidgets.QColorDialog.getColor(parent=self)
        if color.isValid():
            btn.setStyleSheet(f"background-color: {color.name()}")
            self._update_zone_from_row(row)


    def _add_zone_item(self):
        """Add a new custom zone with default parameters directly."""
        # Default to a linear region. The user can change the type later
        # using the table's combobox.
        zone = {
            "type": "vlinear",
            "name": "",
            "bounds": [0.0, 1.0],
            "line_color": generate_random_color(),
            "line_alpha": 100,
            "line_width": 1,
            "fill_color": generate_random_color(),
            "fill_alpha": 40,
        }

        if self.controller:
            self._call_graph_controller(self.controller.add_zone, zone)
        self.update_graph_ui()

    def _add_satellite_object(self, zone: str):
        obj = SatelliteObjectData(obj_type="text", name="Objet", anchor="grid")
        if self.controller:
            self._call_graph_controller(
                self.controller.add_satellite_object, zone, obj
            )
        self.update_graph_ui()

    def _create_zone_row(self, row: int, zone: dict):
        """Insert a row describing *zone* and setup widgets."""
        self.zone_table.insertRow(row)

        combo = QtWidgets.QComboBox()
        combo.addItem("HLinearRegion", "hlinear")
        combo.addItem("VLinearRegion", "vlinear")
        combo.addItem("Rectangle", "rect")
        combo.addItem("Path", "path")
        index = combo.findData(zone.get("type", "vlinear"))
        if index != -1:
            combo.setCurrentIndex(index)
        combo.currentIndexChanged.connect(
            lambda _, r=row: self._on_zone_type_changed(r)
        )
        self.zone_table.setCellWidget(row, 0, combo)

        name_edit = QtWidgets.QLineEdit(zone.get("name", ""))
        name_edit.editingFinished.connect(lambda r=row: self._update_zone_from_row(r))
        self.zone_table.setCellWidget(row, 1, name_edit)

        params = ZoneParamsWidget(zone.get("type", "vlinear"))
        params.set_zone(zone)
        params.changed.connect(lambda r=row: self._update_zone_from_row(r))
        self.zone_table.setCellWidget(row, 2, params)

        line_btn = QtWidgets.QPushButton()
        line_color = zone.get("line_color", "#FF0000")
        line_btn.setStyleSheet(f"background-color: {line_color}")
        line_btn.clicked.connect(lambda _, r=row: self._choose_zone_color(r, 3))
        self.zone_table.setCellWidget(row, 3, line_btn)

        line_alpha = QtWidgets.QSpinBox()
        line_alpha.setRange(0, 100)
        line_alpha.setValue(int(zone.get("line_alpha", 100)))
        line_alpha.valueChanged.connect(lambda _, r=row: self._update_zone_from_row(r))
        self.zone_table.setCellWidget(row, 4, line_alpha)

        line_width = QtWidgets.QSpinBox()
        line_width.setRange(1, 10)
        line_width.setValue(int(zone.get("line_width", 1)))
        line_width.valueChanged.connect(lambda _, r=row: self._update_zone_from_row(r))
        self.zone_table.setCellWidget(row, 5, line_width)

        fill_btn = QtWidgets.QPushButton()
        fill_color = zone.get("fill_color", "#FF0000")
        fill_btn.setStyleSheet(f"background-color: {fill_color}")
        fill_btn.clicked.connect(lambda _, r=row: self._choose_zone_color(r, 6))
        fill_btn.setEnabled(zone.get("type", "vlinear") != "path")
        self.zone_table.setCellWidget(row, 6, fill_btn)

        fill_alpha = QtWidgets.QSpinBox()
        fill_alpha.setRange(0, 100)
        fill_alpha.setValue(int(zone.get("fill_alpha", 40)))
        fill_alpha.valueChanged.connect(lambda _, r=row: self._update_zone_from_row(r))
        fill_alpha.setEnabled(zone.get("type", "vlinear") != "path")
        self.zone_table.setCellWidget(row, 7, fill_alpha)

        btn = QtWidgets.QPushButton("Supprimer")
        btn.clicked.connect(lambda _, r=row: self._remove_zone_row(r))
        self.zone_table.setCellWidget(row, 8, btn)

    # ------------------------------------------------------------------
    # Satellite objects helpers
    # ------------------------------------------------------------------
    def _create_satellite_row(self, zone: str, row: int, obj: SatelliteObjectData):
        table = self._get_sat_table(zone)
        if table is None:
            return
        table.insertRow(row)

        type_combo = QtWidgets.QComboBox()
        for t in ["text", "button", "image"]:
            type_combo.addItem(t.capitalize(), t)
        idx = type_combo.findData(obj.obj_type)
        if idx != -1:
            type_combo.setCurrentIndex(idx)
        type_combo.currentIndexChanged.connect(
            lambda _, z=zone, r=row: self._on_sat_type_changed(z, r)
        )
        table.setCellWidget(row, 0, type_combo)

        name_edit = QtWidgets.QLineEdit(obj.name)
        name_edit.editingFinished.connect(
            lambda z=zone, r=row: self._update_sat_row(z, r)
        )
        table.setCellWidget(row, 1, name_edit)

        param_widget = self._create_sat_param_widget(
            zone, row, obj.obj_type, obj.config.get("value", "")
        )
        table.setCellWidget(row, 2, param_widget)

        spin_w = QtWidgets.QSpinBox()
        spin_w.setRange(1, 1000)
        spin_w.setValue(int(obj.config.get("width", 24)))
        spin_w.valueChanged.connect(
            lambda _, z=zone, r=row: self._update_sat_row(z, r)
        )
        table.setCellWidget(row, 3, spin_w)

        spin_h = QtWidgets.QSpinBox()
        spin_h.setRange(1, 1000)
        spin_h.setValue(int(obj.config.get("height", 24)))
        spin_h.valueChanged.connect(
            lambda _, z=zone, r=row: self._update_sat_row(z, r)
        )
        spin_h.setEnabled(obj.obj_type != "text")
        table.setCellWidget(row, 4, spin_h)

        spin_x = QtWidgets.QSpinBox()
        spin_x.setRange(-9999, 9999)
        spin_x.setValue(obj.x)
        spin_x.valueChanged.connect(
            lambda _, z=zone, r=row: self._update_sat_row(z, r)
        )
        table.setCellWidget(row, 5, spin_x)

        spin_y = QtWidgets.QSpinBox()
        spin_y.setRange(-9999, 9999)
        spin_y.setValue(obj.y)
        spin_y.valueChanged.connect(
            lambda _, z=zone, r=row: self._update_sat_row(z, r)
        )
        table.setCellWidget(row, 6, spin_y)

        anchor_combo = QtWidgets.QComboBox()
        options = [
            "grid",
            "top-left",
            "top",
            "top-right",
            "left",
            "center",
            "right",
            "bottom-left",
            "bottom",
            "bottom-right",
        ]
        for opt in options:
            anchor_combo.addItem(opt, opt)
        idx = anchor_combo.findData(getattr(obj, "anchor", "grid"))
        if idx != -1:
            anchor_combo.setCurrentIndex(idx)
        anchor_combo.currentIndexChanged.connect(
            lambda _, z=zone, r=row: self._update_sat_row(z, r)
        )
        table.setCellWidget(row, 7, anchor_combo)

        btns = QtWidgets.QWidget()
        h = QtWidgets.QHBoxLayout(btns)
        h.setContentsMargins(0, 0, 0, 0)
        up_btn = QtWidgets.QToolButton()
        up_btn.setText("▲")
        down_btn = QtWidgets.QToolButton()
        down_btn.setText("▼")
        top_btn = QtWidgets.QToolButton()
        top_btn.setText("⤒")
        bottom_btn = QtWidgets.QToolButton()
        bottom_btn.setText("⤓")
        for b in (up_btn, down_btn, top_btn, bottom_btn):
            h.addWidget(b)
            b.setFixedWidth(18)

        up_btn.clicked.connect(lambda _, z=zone, r=row: self._move_sat_row(z, r, r-1))
        down_btn.clicked.connect(lambda _, z=zone, r=row: self._move_sat_row(z, r, r+1))
        top_btn.clicked.connect(lambda _, z=zone, r=row: self._move_sat_row(z, r, 0))
        bottom_btn.clicked.connect(
            lambda _, z=zone, r=row: self._move_sat_row(z, r, 1e9)
        )
        table.setCellWidget(row, 8, btns)

        del_btn = QtWidgets.QPushButton("✖")
        del_btn.clicked.connect(lambda _, z=zone, r=row: self._remove_sat_row(z, r))
        table.setCellWidget(row, 9, del_btn)

    def _create_sat_param_widget(self, zone: str, row: int, obj_type: str, value: str):
        if obj_type == "image":
            cont = QtWidgets.QWidget()
            lay = QtWidgets.QHBoxLayout(cont)
            lay.setContentsMargins(0, 0, 0, 0)
            edit = QtWidgets.QLineEdit(value)
            btn = QtWidgets.QToolButton()
            btn.setText("…")
            btn.setFixedWidth(24)
            btn.clicked.connect(
                lambda _, e=edit, z=zone, r=row: self._choose_image_file(e, z, r)
            )
            edit.editingFinished.connect(
                lambda z=zone, r=row: self._update_sat_row(z, r)
            )
            lay.addWidget(edit)
            lay.addWidget(btn)
            cont.line_edit = edit
            return cont
        edit = QtWidgets.QLineEdit(value)
        edit.editingFinished.connect(
            lambda z=zone, r=row: self._update_sat_row(z, r)
        )
        return edit

    def _choose_image_file(self, line_edit: QtWidgets.QLineEdit, zone: str, row: int):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Sélectionner une image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif);;Tous les fichiers (*)",
        )
        if path:
            line_edit.setText(path)
            self._update_sat_row(zone, row)

    def _on_sat_type_changed(self, zone: str, row: int):
        table = self._get_sat_table(zone)
        if table is None:
            return
        combo = table.cellWidget(row, 0)
        current = table.cellWidget(row, 2)
        if not isinstance(combo, QtWidgets.QComboBox):
            return
        if isinstance(current, QtWidgets.QLineEdit):
            val = current.text()
        elif hasattr(current, "line_edit"):
            val = current.line_edit.text()
        else:
            val = ""
        new_widget = self._create_sat_param_widget(zone, row, combo.currentData(), val)
        table.setCellWidget(row, 2, new_widget)
        spin_h = table.cellWidget(row, 4)
        if isinstance(spin_h, QtWidgets.QSpinBox):
            spin_h.setEnabled(combo.currentData() != "text")
        self._update_sat_row(zone, row)

    def _get_sat_table(self, zone: str):
        return {
            "left": self.satellite_left_table,
            "right": self.satellite_right_table,
            "top": self.satellite_top_table,
            "bottom": self.satellite_bottom_table,
        }.get(zone)

    def _update_sat_row(self, zone: str, row: int):
        table = self._get_sat_table(zone)
        if table is None:
            return
        type_combo = table.cellWidget(row, 0)
        name_edit = table.cellWidget(row, 1)
        param_edit = table.cellWidget(row, 2)
        spin_w = table.cellWidget(row, 3)
        spin_h = table.cellWidget(row, 4)
        spin_x = table.cellWidget(row, 5)
        spin_y = table.cellWidget(row, 6)
        anchor_combo = table.cellWidget(row, 7)
        if not all(
            isinstance(w, QtWidgets.QWidget)
            for w in [type_combo, name_edit, param_edit, spin_w, spin_h, spin_x, spin_y, anchor_combo]
        ):
            return
        if isinstance(param_edit, QtWidgets.QLineEdit):
            param_value = param_edit.text()
        elif hasattr(param_edit, "line_edit"):
            param_value = param_edit.line_edit.text()
        else:
            param_value = ""

        obj = SatelliteObjectData(
            obj_type=type_combo.currentData(),
            name=name_edit.text(),
            config={
                "value": param_value,
                "width": int(spin_w.value()),
                "height": int(spin_h.value()),
            },
            x=spin_x.value(),
            y=spin_y.value(),
            anchor=anchor_combo.currentData() if isinstance(anchor_combo, QtWidgets.QComboBox) else "grid",
        )
        if self.controller:
            self._call_graph_controller(
                self.controller.update_satellite_object, zone, row, obj
            )

    def _remove_sat_row(self, zone: str, row: int):
        if self.controller:
            self._call_graph_controller(
                self.controller.remove_satellite_object, zone, row
            )
        self.update_graph_ui()

    def _move_sat_row(self, zone: str, row: int, new_index: int):
        if self.controller:
            self._call_graph_controller(
                self.controller.move_satellite_object, zone, row, new_index
            )
        self.update_graph_ui()

    def _on_zone_type_changed(self, row: int):
        combo = self.zone_table.cellWidget(row, 0)
        params = self.zone_table.cellWidget(row, 2)
        fill_btn = self.zone_table.cellWidget(row, 6)
        fill_alpha = self.zone_table.cellWidget(row, 7)
        if not isinstance(combo, QtWidgets.QComboBox) or not isinstance(
            params, ZoneParamsWidget
        ):
            return
        params.set_type(combo.currentData())
        enabled = combo.currentData() != "path"
        if isinstance(fill_btn, QtWidgets.QPushButton):
            fill_btn.setEnabled(enabled)
        if isinstance(fill_alpha, QtWidgets.QSpinBox):
            fill_alpha.setEnabled(enabled)

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
        params = self.zone_table.cellWidget(row, 2)
        combo = self.zone_table.cellWidget(row, 0)
        name_edit = self.zone_table.cellWidget(row, 1)
        line_btn = self.zone_table.cellWidget(row, 3)
        line_alpha = self.zone_table.cellWidget(row, 4)
        line_width = self.zone_table.cellWidget(row, 5)
        fill_btn = self.zone_table.cellWidget(row, 6)
        fill_alpha = self.zone_table.cellWidget(row, 7)

        if not isinstance(params, ZoneParamsWidget) or not isinstance(
            combo, QtWidgets.QComboBox
        ):
            return

        zone = params.get_zone()
        current_type = combo.currentData()
        if current_type in {"hlinear", "vlinear"}:
            zone["type"] = current_type
        if isinstance(name_edit, QtWidgets.QLineEdit):
            zone["name"] = name_edit.text()
        if isinstance(line_btn, QtWidgets.QPushButton):
            style = line_btn.styleSheet()
            if "background-color" in style:
                color = style.split(":")[-1].strip()
                zone["line_color"] = color
        if isinstance(line_alpha, QtWidgets.QSpinBox):
            zone["line_alpha"] = line_alpha.value()
        if isinstance(line_width, QtWidgets.QSpinBox):
            zone["line_width"] = line_width.value()
        if isinstance(fill_btn, QtWidgets.QPushButton):
            style = fill_btn.styleSheet()
            if "background-color" in style:
                color = style.split(":")[-1].strip()
                zone["fill_color"] = color
        if isinstance(fill_alpha, QtWidgets.QSpinBox):
            zone["fill_alpha"] = fill_alpha.value()

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
            QtWidgets.QMessageBox.warning(
                self, "Erreur", "Les données ne sont pas entières"
            )
            self.bits_checkbox.setChecked(False)
            return

        if finite_values.size and int(finite_values.min()) < 0:
            QtWidgets.QMessageBox.warning(
                self, "Erreur", "Les valeurs négatives ne sont pas prises en charge"
            )
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

        logger.debug(
            f"[PropertiesPanel] 🔄 Mise à jour des champs pour le graphique '{graph.name}'"
        )

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
        self.x_format_combo.setCurrentIndex(
            index_x_format if index_x_format != -1 else 0
        )

        index_y_format = self.y_format_combo.findData(graph.y_format)
        self.y_format_combo.setCurrentIndex(
            index_y_format if index_y_format != -1 else 0
        )

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
            checkbox.setChecked(graph.satellite_settings[zone].visible)
            checkbox.blockSignals(False)

        for zone, btn in {
            "left": self.satellite_left_color,
            "right": self.satellite_right_color,
            "top": self.satellite_top_color,
            "bottom": self.satellite_bottom_color,
        }.items():
            color = graph.satellite_settings[zone].color
            btn.setStyleSheet(f"background-color: {color}")
        for zone, widgets in {
            "left": (
                self.satellite_left_color,
                self.satellite_left_size,
            ),
            "right": (
                self.satellite_right_color,
                self.satellite_right_size,
            ),
            "top": (
                self.satellite_top_color,
                self.satellite_top_size,
            ),
            "bottom": (
                self.satellite_bottom_color,
                self.satellite_bottom_size,
            ),
        }.items():
            enabled = graph.satellite_settings[zone].visible
            for w in widgets:
                w.setEnabled(enabled)

        for zone, spin in {
            "left": self.satellite_left_size,
            "right": self.satellite_right_size,
            "top": self.satellite_top_size,
            "bottom": self.satellite_bottom_size,
        }.items():
            spin.blockSignals(True)
            spin.setValue(graph.satellite_settings[zone].size)
            spin.blockSignals(False)

        # Satellite objects tables
        for zone, table in {
            "left": self.satellite_left_table,
            "right": self.satellite_right_table,
            "top": self.satellite_top_table,
            "bottom": self.satellite_bottom_table,
        }.items():
            table.blockSignals(True)
            table.setRowCount(0)
            for idx, obj in enumerate(graph.satellite_objects.get(zone, [])):
                self._create_satellite_row(zone, idx, obj)
            table.blockSignals(False)



        # Zones table
        self.zone_table.blockSignals(True)
        self.zone_table.setRowCount(0)
        for idx, zone in enumerate(getattr(graph, "zones", [])):
            self._create_zone_row(idx, zone)
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

        logger.debug(
            f"[PropertiesPanel] 🔄 Mise à jour des champs pour la courbe '{curve.name}'"
        )

        self.label_curve_name.setText(curve.name)
        self.color_button.setStyleSheet(f"background-color: {curve.color}")

        index_style = self.style_combo.findData(curve.style)
        self.style_combo.setCurrentIndex(index_style if index_style != -1 else 0)

        self.width_spin.setValue(curve.width)

        index_symbol = self.symbol_combo.findData(curve.symbol)
        self.symbol_combo.setCurrentIndex(index_symbol if index_symbol != -1 else 0)

        index_display = self.display_mode_combo.findData(curve.display_mode)
        self.display_mode_combo.setCurrentIndex(
            index_display if index_display != -1 else 0
        )

        index_label = self.label_mode_combo.findData(curve.label_mode)
        self.label_mode_combo.setCurrentIndex(index_label if index_label != -1 else 0)

        self.opacity_slider.setValue(int(curve.opacity))
        self.fill_checkbox.setChecked(curve.fill)

        mode_index = self.gain_mode_combo.findData(
            getattr(curve, "gain_mode", "multiplier")
        )
        self.gain_mode_combo.blockSignals(True)
        self.gain_mode_combo.setCurrentIndex(mode_index if mode_index != -1 else 0)
        self.gain_mode_combo.blockSignals(False)
        self._update_gain_mode_ui(self.gain_mode_combo.currentData())

        self.gain_slider.setValue(int(curve.gain * 100))  # gain 1.0 → slider 100
        self.gain_input.setValue(curve.gain)
        self.units_per_grid_input.setValue(getattr(curve, "units_per_grid", 1.0))
        self.offset_slider.setValue(int(curve.offset))  # offset en pixels/valeur
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
