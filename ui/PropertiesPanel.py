# PropertiesPanel.py

from core.app_state import AppState
from PyQt5 import QtWidgets, QtCore, QtGui
from ui.widgets import BitGroupWidget
from ui.satellite_zone_builder import Toolbox
from signal_bus import signal_bus
from core.utils import generate_random_color
import logging

logger = logging.getLogger(__name__)

# Available zone types and their placeholders for the "Zones personnalisées" table
ZONE_TYPES = {
    "linear": "début, fin",
    "rect": "x, y, largeur, hauteur",
    "path": "x1, y1, x2, y2, ...",
}


class ZoneParamsWidget(QtWidgets.QWidget):
    """Widget to edit parameters of a custom zone."""

    changed = QtCore.pyqtSignal()

    def __init__(self, ztype: str = "linear", zone: dict | None = None, parent=None):
        super().__init__(parent)
        self._layout = QtWidgets.QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
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

        if ztype == "linear":
            for name in ["x départ", "x de fin"]:
                spin = self._create_spin(name)
                self._fields.append(spin)
                self._layout.addWidget(spin)
        elif ztype == "rect":
            for name in ["x", "y", "largeur", "hauteur"]:
                spin = self._create_spin(name)
                self._fields.append(spin)
                self._layout.addWidget(spin)
        else:  # path
            self._add_btn = QtWidgets.QPushButton("+")
            self._add_btn.clicked.connect(self._add_point)
            self._layout.addWidget(self._add_btn)
            # start with two points
            self._add_point()
            self._add_point()

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
        if self._add_btn:
            self._layout.insertWidget(self._layout.count() - 1, cont)
        else:
            self._layout.addWidget(cont)
        self._points.append((cont, sx, sy))
        self.changed.emit()

    def _remove_point(self, widget: QtWidgets.QWidget):
        if len(self._points) <= 2:
            return
        for i, (w, sx, sy) in enumerate(self._points):
            if w is widget:
                self._points.pop(i)
                w.deleteLater()
                break
        self.changed.emit()

    def set_zone(self, zone: dict):
        self.blockSignals(True)
        self.set_type(zone.get("type", "linear"))
        if self._type == "linear":
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
            if not pts:
                self._add_point()
                self._add_point()
        self.blockSignals(False)

    def get_zone(self) -> dict:
        if self._type == "linear":
            vals = [f.value() for f in self._fields]
            return {"type": "linear", "bounds": vals}
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

        for zone, chk in self.satellite_edit_checks.items():
            chk.toggled.connect(
                lambda val, z=zone: self._call_graph_controller(
                    self.controller.set_satellite_edit_mode, z, val
                )
            )

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
        def create_satellite_group(title):
            group = QtWidgets.QGroupBox(title)
            v = QtWidgets.QVBoxLayout(group)
            checkbox = QtWidgets.QCheckBox("Afficher")
            color_btn = QtWidgets.QPushButton("Couleur")
            size_spin = QtWidgets.QSpinBox()
            size_spin.setRange(20, 500)
            table = QtWidgets.QTableWidget(0, 10)
            table.setHorizontalHeaderLabels(
                [
                    "Type",
                    "Name",
                    "Paramètre",
                    "Size X",
                    "Size Y",
                    "X",
                    "Y",
                    "Ordre",
                    "Suppr.",
                    "Modifié",
                ]
            )
            edit_chk = QtWidgets.QCheckBox("Éditer")

            def toggle(enabled):
                color_btn.setEnabled(enabled)
                size_spin.setEnabled(enabled)
                table.setEnabled(enabled)
                edit_chk.setEnabled(enabled)

            checkbox.toggled.connect(toggle)
            v.addWidget(checkbox)
            h = QtWidgets.QHBoxLayout()
            h.addWidget(color_btn)
            h.addWidget(size_spin)
            v.addLayout(h)
            v.addWidget(table)
            v.addWidget(edit_chk)
            toggle(False)
            return group, checkbox, color_btn, size_spin, table, edit_chk

        (
            self.sat_left_group,
            self.satellite_left_checkbox,
            self.satellite_left_color,
            self.satellite_left_size,
            self.satellite_left_table,
            self.satellite_left_edit,
        ) = create_satellite_group("Zone gauche")
        layout.addWidget(self.sat_left_group)

        (
            self.sat_right_group,
            self.satellite_right_checkbox,
            self.satellite_right_color,
            self.satellite_right_size,
            self.satellite_right_table,
            self.satellite_right_edit,
        ) = create_satellite_group("Zone droite")
        layout.addWidget(self.sat_right_group)

        (
            self.sat_top_group,
            self.satellite_top_checkbox,
            self.satellite_top_color,
            self.satellite_top_size,
            self.satellite_top_table,
            self.satellite_top_edit,
        ) = create_satellite_group("Zone haut")
        layout.addWidget(self.sat_top_group)

        (
            self.sat_bottom_group,
            self.satellite_bottom_checkbox,
            self.satellite_bottom_color,
            self.satellite_bottom_size,
            self.satellite_bottom_table,
            self.satellite_bottom_edit,
        ) = create_satellite_group("Zone bas")
        layout.addWidget(self.sat_bottom_group)

        self.satellite_tables = {
            "left": self.satellite_left_table,
            "right": self.satellite_right_table,
            "top": self.satellite_top_table,
            "bottom": self.satellite_bottom_table,
        }
        self.satellite_edit_checks = {
            "left": self.satellite_left_edit,
            "right": self.satellite_right_edit,
            "top": self.satellite_top_edit,
            "bottom": self.satellite_bottom_edit,
        }

        # Palette of draggable objects
        self.toolbox = Toolbox()
        layout.addWidget(self.toolbox)

        # Zone objects in the plot
        zone_group = QtWidgets.QGroupBox("Zones personnalisées")
        v_z = QtWidgets.QVBoxLayout(zone_group)
        self.zone_table = QtWidgets.QTableWidget(0, 4)
        self.zone_table.setHorizontalHeaderLabels(["Type", "Paramètres", "Couleur", ""])
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

    def _choose_zone_color(self, row: int):
        btn = self.zone_table.cellWidget(row, 2)
        if not isinstance(btn, QtWidgets.QPushButton):
            return
        color = QtWidgets.QColorDialog.getColor(parent=self)
        if color.isValid():
            btn.setStyleSheet(f"background-color: {color.name()}")
            self._update_zone_from_row(row)

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

        name_edit = QtWidgets.QLineEdit(f"item{row}")
        name_edit.editingFinished.connect(
            lambda z=zone, r=row: self._satellite_cell_changed(z, r)
        )
        table.setCellWidget(row, 1, name_edit)

        param_widget = QtWidgets.QLineEdit("" if choice != "Bouton" else "Bouton")
        param_widget.editingFinished.connect(
            lambda z=zone, r=row: self._satellite_cell_changed(z, r)
        )
        table.setCellWidget(row, 2, param_widget)

        for col in range(3, 7):
            spin = QtWidgets.QSpinBox()
            spin.setRange(-1000, 1000)
            if col in {3, 4}:
                spin.setRange(1, 1000)
                spin.setValue(50)
            spin.valueChanged.connect(
                lambda _, z=zone, r=row: self._satellite_cell_changed(z, r)
            )
            table.setCellWidget(row, col, spin)

        btns = QtWidgets.QWidget()
        hb = QtWidgets.QHBoxLayout(btns)
        hb.setContentsMargins(0, 0, 0, 0)
        for text, action in [("⬆", "front"), ("⬇", "back"), ("+", "up"), ("-", "down")]:
            b = QtWidgets.QPushButton(text)
            b.setFixedWidth(20)
            b.clicked.connect(
                lambda _, r=row, z=zone, a=action: self._move_satellite_item(z, r, a)
            )
            hb.addWidget(b)
        table.setCellWidget(row, 7, btns)

        del_btn = QtWidgets.QPushButton("X")
        del_btn.clicked.connect(lambda _, r=row, z=zone: self._remove_satellite_item(z, r))
        table.setCellWidget(row, 8, del_btn)

        table.setItem(row, 9, QtWidgets.QTableWidgetItem(""))

        if self.controller:
            item = {
                "type": choice.lower(),
                "name": f"item{row}",
                "text": "" if choice != "Bouton" else "Bouton",
                "width": 50,
                "height": 50,
                "x": 0,
                "y": 0,
            }
            self._call_graph_controller(self.controller.add_satellite_item, zone, item)
        self.update_graph_ui()

    def _edit_satellite_zone(self, zone: str):
        from ui.satellite_zone_builder import SatelliteZoneBuilder

        state = AppState.get_instance()
        graph = state.current_graph
        if not graph:
            return

        items = graph.satellite_settings[zone]["items"]
        dlg = SatelliteZoneBuilder(items, parent=self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            new_items = dlg.items()
            if self.controller:
                self._call_graph_controller(
                    self.controller.set_satellite_items, zone, new_items
                )
            self.update_graph_ui()

    def _apply_satellite_table(self, zone: str):
        table = self.satellite_tables[zone]
        items = []
        for row in range(table.rowCount()):
            typ_item = table.item(row, 0)
            if typ_item is None:
                continue
            typ = typ_item.text().lower()
            name_edit = table.cellWidget(row, 1)
            param_widget = table.cellWidget(row, 2)
            w_spin = table.cellWidget(row, 3)
            h_spin = table.cellWidget(row, 4)
            x_spin = table.cellWidget(row, 5)
            y_spin = table.cellWidget(row, 6)

            text = ""
            if isinstance(param_widget, QtWidgets.QLineEdit):
                text = param_widget.text()
            item = {
                "type": typ,
                "name": (
                    name_edit.text()
                    if isinstance(name_edit, QtWidgets.QLineEdit)
                    else f"item{row}"
                ),
                "text": text,
                "width": (
                    w_spin.value() if isinstance(w_spin, QtWidgets.QSpinBox) else 50
                ),
                "height": (
                    h_spin.value() if isinstance(h_spin, QtWidgets.QSpinBox) else 50
                ),
                "x": x_spin.value() if isinstance(x_spin, QtWidgets.QSpinBox) else 0,
                "y": y_spin.value() if isinstance(y_spin, QtWidgets.QSpinBox) else 0,
            }
            items.append(item)
        if self.controller:
            self._call_graph_controller(
                self.controller.set_satellite_items, zone, items
            )

    def _mark_satellite_row_modified(self, zone: str, row: int):
        table = self.satellite_tables.get(zone)
        if not table:
            return
        table.setItem(row, 9, QtWidgets.QTableWidgetItem("✓"))

    def _satellite_cell_changed(self, zone: str, row: int):
        self._mark_satellite_row_modified(zone, row)
        self._apply_satellite_table(zone)

    def _move_satellite_item(self, zone: str, row: int, action: str):
        state = AppState.get_instance()
        graph = state.current_graph
        if not graph:
            return
        items = list(graph.satellite_settings[zone]["items"])
        if row < 0 or row >= len(items):
            return
        item = items.pop(row)
        if action == "front":
            items.append(item)
        elif action == "back":
            items.insert(0, item)
        elif action == "up":
            items.insert(min(row + 1, len(items)), item)
        elif action == "down":
            items.insert(max(row - 1, 0), item)
        if self.controller:
            self._call_graph_controller(
                self.controller.set_satellite_items, zone, items
            )
        self.update_graph_ui()
        for r in range(len(items)):
            self._mark_satellite_row_modified(zone, r)

    def _remove_satellite_item(self, zone: str, row: int):
        if self.controller:
            self._call_graph_controller(
                self.controller.remove_satellite_item, zone, row
            )
        self.update_graph_ui()

    def _on_view_items_moved(self, zone: str, view):
        """Update table values and graph data when items are moved in a view."""
        items = view.get_items()
        table = self.satellite_tables.get(zone)
        if not table:
            return
        table.blockSignals(True)
        for row, item in enumerate(items):
            if row >= table.rowCount():
                break
            x_spin = table.cellWidget(row, 5)
            y_spin = table.cellWidget(row, 6)
            if isinstance(x_spin, QtWidgets.QSpinBox):
                x_spin.setValue(int(item.get("x", 0)))
            if isinstance(y_spin, QtWidgets.QSpinBox):
                y_spin.setValue(int(item.get("y", 0)))
        table.blockSignals(False)
        if self.controller:
            self._call_graph_controller(
                self.controller.set_satellite_items, zone, items
            )
        for r in range(len(items)):
            self._mark_satellite_row_modified(zone, r)

    def _add_zone_item(self):
        """Add a new custom zone with default parameters directly."""
        # Default to a linear region. The user can change the type later
        # using the table's combobox.
        zone = {
            "type": "linear",
            "bounds": [0.0, 1.0],
            "color": generate_random_color(),
        }

        if self.controller:
            self._call_graph_controller(self.controller.add_zone, zone)
        self.update_graph_ui()

    def _create_zone_row(self, row: int, zone: dict):
        """Insert a row describing *zone* and setup widgets."""
        self.zone_table.insertRow(row)

        combo = QtWidgets.QComboBox()
        combo.addItem("LinearRegion", "linear")
        combo.addItem("Rectangle", "rect")
        combo.addItem("Path", "path")
        index = combo.findData(zone.get("type", "linear"))
        if index != -1:
            combo.setCurrentIndex(index)
        combo.currentIndexChanged.connect(
            lambda _, r=row: self._on_zone_type_changed(r)
        )
        self.zone_table.setCellWidget(row, 0, combo)

        params = ZoneParamsWidget(zone.get("type", "linear"))
        params.set_zone(zone)
        params.changed.connect(lambda r=row: self._update_zone_from_row(r))
        self.zone_table.setCellWidget(row, 1, params)

        color_btn = QtWidgets.QPushButton()
        color = zone.get("color", "#FF0000")
        color_btn.setStyleSheet(f"background-color: {color}")
        color_btn.clicked.connect(lambda _, r=row: self._choose_zone_color(r))
        self.zone_table.setCellWidget(row, 2, color_btn)

        btn = QtWidgets.QPushButton("Supprimer")
        btn.clicked.connect(lambda _, r=row: self._remove_zone_row(r))
        self.zone_table.setCellWidget(row, 3, btn)

    def _on_zone_type_changed(self, row: int):
        combo = self.zone_table.cellWidget(row, 0)
        params = self.zone_table.cellWidget(row, 1)
        if not isinstance(combo, QtWidgets.QComboBox) or not isinstance(
            params, ZoneParamsWidget
        ):
            return
        params.set_type(combo.currentData())

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
        params = self.zone_table.cellWidget(row, 1)
        combo = self.zone_table.cellWidget(row, 0)
        color_btn = self.zone_table.cellWidget(row, 2)

        if not isinstance(params, ZoneParamsWidget) or not isinstance(
            combo, QtWidgets.QComboBox
        ):
            return

        zone = params.get_zone()
        if isinstance(color_btn, QtWidgets.QPushButton):
            style = color_btn.styleSheet()
            if "background-color" in style:
                color = style.split(":")[-1].strip()
                zone["color"] = color

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

        for zone, chk in self.satellite_edit_checks.items():
            chk.blockSignals(True)
            chk.setChecked(graph.satellite_edit_mode[zone])
            chk.blockSignals(False)

        for zone, widgets in {
            "left": (
                self.satellite_left_color,
                self.satellite_left_size,
                self.satellite_left_table,
                self.satellite_left_edit,
            ),
            "right": (
                self.satellite_right_color,
                self.satellite_right_size,
                self.satellite_right_table,
                self.satellite_right_edit,
            ),
            "top": (
                self.satellite_top_color,
                self.satellite_top_size,
                self.satellite_top_table,
                self.satellite_top_edit,
            ),
            "bottom": (
                self.satellite_bottom_color,
                self.satellite_bottom_size,
                self.satellite_bottom_table,
                self.satellite_bottom_edit,
            ),
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

                name_edit = QtWidgets.QLineEdit(item.get("name", f"item{row}"))
                name_edit.editingFinished.connect(
                    lambda z=zone, r=row: self._satellite_cell_changed(z, r)
                )
                table.setCellWidget(row, 1, name_edit)

                if typ == "text":
                    param_widget = QtWidgets.QLineEdit(item.get("text", ""))
                    param_widget.editingFinished.connect(
                        lambda z=zone, r=row: self._satellite_cell_changed(z, r)
                    )
                elif typ in {"button", "bouton"}:
                    param_widget = QtWidgets.QLineEdit(item.get("text", "Bouton"))
                    param_widget.editingFinished.connect(
                        lambda z=zone, r=row: self._satellite_cell_changed(z, r)
                    )
                else:
                    param_widget = QtWidgets.QLineEdit(item.get("text", ""))
                    param_widget.editingFinished.connect(
                        lambda z=zone: self._apply_satellite_table(z)
                    )
                table.setCellWidget(row, 2, param_widget)

                w_spin = QtWidgets.QSpinBox()
                w_spin.setRange(1, 1000)
                w_spin.setValue(int(item.get("width", 50)))
                w_spin.valueChanged.connect(
                    lambda _, z=zone, r=row: self._satellite_cell_changed(z, r)
                )
                table.setCellWidget(row, 3, w_spin)

                h_spin = QtWidgets.QSpinBox()
                h_spin.setRange(1, 1000)
                h_spin.setValue(int(item.get("height", 50)))
                h_spin.valueChanged.connect(
                    lambda _, z=zone, r=row: self._satellite_cell_changed(z, r)
                )
                table.setCellWidget(row, 4, h_spin)

                x_spin = QtWidgets.QSpinBox()
                x_spin.setRange(-1000, 1000)
                x_spin.setValue(int(item.get("x", 0)))
                x_spin.valueChanged.connect(
                    lambda _, z=zone, r=row: self._satellite_cell_changed(z, r)
                )
                table.setCellWidget(row, 5, x_spin)

                y_spin = QtWidgets.QSpinBox()
                y_spin.setRange(-1000, 1000)
                y_spin.setValue(int(item.get("y", 0)))
                y_spin.valueChanged.connect(
                    lambda _, z=zone, r=row: self._satellite_cell_changed(z, r)
                )
                table.setCellWidget(row, 6, y_spin)

                btns = QtWidgets.QWidget()
                hb = QtWidgets.QHBoxLayout(btns)
                hb.setContentsMargins(0, 0, 0, 0)
                to_front = QtWidgets.QPushButton("⬆")
                to_back = QtWidgets.QPushButton("⬇")
                up = QtWidgets.QPushButton("+")
                down = QtWidgets.QPushButton("-")
                for b in (to_front, to_back, up, down):
                    b.setFixedWidth(20)
                to_front.clicked.connect(
                    lambda _, r=row, z=zone: self._move_satellite_item(z, r, "front")
                )
                to_back.clicked.connect(
                    lambda _, r=row, z=zone: self._move_satellite_item(z, r, "back")
                )
                up.clicked.connect(
                    lambda _, r=row, z=zone: self._move_satellite_item(z, r, "up")
                )
                down.clicked.connect(
                    lambda _, r=row, z=zone: self._move_satellite_item(z, r, "down")
                )
                for b in (to_front, to_back, up, down):
                    hb.addWidget(b)
                table.setCellWidget(row, 7, btns)

                del_btn = QtWidgets.QPushButton("X")
                del_btn.clicked.connect(
                    lambda _, r=row, z=zone: self._remove_satellite_item(z, r)
                )
                table.setCellWidget(row, 8, del_btn)

                table.setItem(row, 9, QtWidgets.QTableWidgetItem(""))

            table.blockSignals(False)

        # Connect view movement signals to update tables
        if self.controller and hasattr(self.controller, "ui"):
            coord = self.controller.ui
            view = coord.views.get(graph.name)
            if view:
                for zone, table in self.satellite_tables.items():
                    zview = getattr(view, "satellites", {}).get(zone)
                    if not zview:
                        continue
                    handler = getattr(zview, "_pp_handler", None)
                    if handler:
                        try:
                            zview.itemsMoved.disconnect(handler)
                        except Exception:
                            pass
                    handler = lambda v=zview, z=zone: self._on_view_items_moved(z, v)
                    zview.itemsMoved.connect(handler)
                    zview._pp_handler = handler

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
