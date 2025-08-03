from core.app_state import AppState
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QTimer
import time
import pyqtgraph as pg
from signal_bus import signal_bus
from PyQt5.QtGui import QColor, QPainterPath
from ui.custom_regions import LinearRegion, HLinearRegion
from ui.widgets.plot_container import PlotContainerWidget
import logging

logger = logging.getLogger(__name__)


class MyPlotView:
    def __init__(self, graph_data):
        logger.debug("[views.py > __init__()] ▶️ Entrée dans __init__()")

        self.graph_data = graph_data
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("w")
        self.plot_widget.useOpenGL(True)
        # Container widget that will host the plot and the satellite zones
        self.container = PlotContainerWidget(graph_data.name, self.plot_widget)
        self.curves = {}
        self.labels = {}
        self.legend = None
        self.satellites = {}

        self.left_indicator_plot = None  # ← AJOUT ICI ✅

        self.plot_widget.scene().sigMouseClicked.connect(self._on_mouse_click)

    def update_graph_properties(self):
        logger.debug(
            "[views.py > update_graph_properties()] ▶️ Entrée dans update_graph_properties()"
        )

        g = self.graph_data
        self.plot_widget.showGrid(g.grid_visible, g.grid_visible)
        self.plot_widget.setLogMode(g.log_x, g.log_y)
        self.plot_widget.setBackground("k" if g.dark_mode else "w")

        x_auto = g.auto_range_x
        y_auto = g.auto_range_y and not g.fix_y_range
        self.plot_widget.enableAutoRange(x=x_auto, y=y_auto)
        if g.fix_y_range:
            self.plot_widget.setYRange(g.y_min, g.y_max)

        vb = self.plot_widget.getViewBox()
        vb.setMouseEnabled(x=g.mouse_enabled_x, y=g.mouse_enabled_y)

        self._format_axis(self.plot_widget.getAxis("bottom"), g.x_unit, g.x_format)
        self._format_axis(self.plot_widget.getAxis("left"), g.y_unit, g.y_format)

    def refresh_curves(self):
        logger.debug("[views.py > refresh_curves()] ▶️ Entrée dans refresh_curves()")

        start = time.perf_counter()

        self.plot_widget.clear()
        self.curves.clear()
        self.labels.clear()
        self.satellites.clear()

        # Supprimer les anciens éléments personnalisés (TextItem, ArrowItem, etc.)
        for item in self.plot_widget.items():
            if isinstance(item, (pg.TextItem, pg.ArrowItem)):
                self.plot_widget.removeItem(item)

        # Réinitialise la légende si elle existait
        if self.legend:
            for sample, label in self.legend.items[:]:
                self.legend.removeItem(label.text)
            self.plot_widget.removeItem(self.legend)
            self.legend = None

        curves_with_legend = [
            c for c in self.graph_data.curves if c.label_mode == "legend" and c.visible
        ]
        if curves_with_legend:
            self.legend = pg.LegendItem(offset=(30, 30))
            self.legend.setParentItem(self.plot_widget.plotItem)

        legend_items_added = set()
        self.zero_arrows = []

        for curve in self.graph_data.curves:
            logger.debug(
                f"[DEBUG] Courbe '{curve.name}' → id={id(curve)} zero_indicator = {curve.zero_indicator}"
            )

            if not curve.visible:
                continue

            base_x = (
                curve.x[:: curve.downsampling_ratio]
                if curve.downsampling_mode == "manual"
                else curve.x
            )
            x = base_x + curve.time_offset
            y = curve.gain * curve.y + curve.offset

            qcolor = QColor(curve.color)
            qcolor.setAlphaF(curve.opacity / 100.0)
            pen = pg.mkPen(color=qcolor, width=curve.width, style=curve.style)

            if curve.display_mode == "line":
                item = pg.PlotDataItem(x, y, pen=pen, symbol=curve.symbol)
                if curve.fill:
                    item.setFillLevel(0)
                    item.setBrush(pg.mkBrush(qcolor))
            elif curve.display_mode == "scatter":
                item = pg.ScatterPlotItem(
                    x=x,
                    y=y,
                    pen=pen,
                    brush=pg.mkBrush(qcolor),
                    symbol=curve.symbol or "o",
                    size=curve.width * 2,
                )
            elif curve.display_mode == "bar":
                item = pg.BarGraphItem(
                    x=x, height=y, width=0.1, brush=pg.mkBrush(qcolor)
                )
            else:
                continue

            item.curve_name = curve.name
            self.plot_widget.addItem(item)
            self.curves[curve.name] = item

            # Étiquette inline
            if curve.label_mode == "inline" and len(x) and len(y):
                text = pg.TextItem(text=curve.name, anchor=(1, 0), color=qcolor)
                text.setPos(x[-1], y[-1])
                self.plot_widget.addItem(text)
                self.labels[curve.name] = text

            # Légende
            if curve.label_mode == "legend" and self.legend:
                if curve.name not in legend_items_added:
                    self.legend.addItem(item, curve.name)
                    legend_items_added.add(curve.name)

            # Indicateur zéro (ligne ou flèche)
            if curve.zero_indicator == "line":
                zero_line = pg.InfiniteLine(
                    angle=0, pen=pg.mkPen(curve.color, style=QtCore.Qt.DashLine)
                )
                zero_line.setPos(curve.offset)
                self.plot_widget.addItem(zero_line)

            # Optimisation
            if hasattr(item, "setClipToView"):
                item.setClipToView(True)
            if hasattr(item, "setDownsampling"):
                if curve.downsampling_mode == "off":
                    item.setDownsampling(auto=False)
                elif curve.downsampling_mode == "auto":
                    item.setDownsampling(auto=True)

        # Add custom zones
        for zone in getattr(self.graph_data, "zones", []):
            ztype = zone.get("type")
            line_color = zone.get("line_color", "#FF0000")
            line_alpha = float(zone.get("line_alpha", 100)) / 100.0
            line_width = int(zone.get("line_width", 1))
            fill_color = zone.get("fill_color", line_color)
            fill_alpha = float(zone.get("fill_alpha", 40)) / 100.0
            line_qcolor = QColor(line_color)
            line_qcolor.setAlphaF(line_alpha)
            pen = pg.mkPen(line_qcolor, width=line_width)

            fill_qcolor = QColor(fill_color)
            fill_qcolor.setAlphaF(fill_alpha)

            if ztype in {"hlinear", "vlinear"}:
                bounds = zone.get("bounds", [0, 1])
                region_cls = HLinearRegion if ztype == "hlinear" else LinearRegion
                item = region_cls(
                    values=bounds,
                    brush=QtGui.QBrush(fill_qcolor),
                    pen=pen,
                )
                item.setMovable(False)
                item.setHoverBrush(item.brush)
                item.setAcceptedMouseButtons(QtCore.Qt.NoButton)
                item.setZValue(100)
            elif ztype == "rect":
                x, y, w, h = zone.get("rect", [0, 0, 1, 1])
                item = QtWidgets.QGraphicsRectItem(x, y, w, h)
                # mkBrush may return tuples on some platforms if given an
                # unrecognized color specification. Construct the QBrush
                # explicitly to avoid "unexpected type 'tuple'" errors on
                # setBrush().
                brush = QtGui.QBrush(fill_qcolor)
                item.setPen(pen)
                item.setBrush(brush)
            elif ztype == "path":
                pts = zone.get("points", [])
                path = QPainterPath()
                if pts:
                    path.moveTo(*pts[0])
                    for pt in pts[1:]:
                        path.lineTo(*pt)
                item = QtWidgets.QGraphicsPathItem(path)
                item.setPen(pen)
            else:
                continue
            item.setAcceptedMouseButtons(QtCore.Qt.NoButton)
            item.setZValue(100)
            self.plot_widget.addItem(item)

        end = time.perf_counter()
        logger.debug(f"[PROFILER] refresh_curves took {end - start:.4f} seconds")

    def _on_mouse_click(self, event):
        logger.debug("[views.py > _on_mouse_click()] ▶️ Entrée dans _on_mouse_click()")

        scene_pos = event.scenePos()
        view_pos = self.plot_widget.plotItem.vb.mapSceneToView(scene_pos)
        x_click, y_click = view_pos.x(), view_pos.y()

        min_distance = float("inf")
        selected_curve = None

        for curve_name, item in self.curves.items():
            x_data, y_data = item.getData()
            if x_data is None or y_data is None:
                continue

            distances = (x_data - x_click) ** 2 + (y_data - y_click) ** 2
            idx_min = distances.argmin()
            distance = distances[idx_min] ** 0.5

            if distance < 10 and distance < min_distance:
                min_distance = distance
                selected_curve = curve_name

        if selected_curve:
            logger.debug(f"[CLICK] Courbe cliquée (par distance) : {selected_curve}")
            signal_bus.curve_selected.emit(self.graph_data.name, selected_curve)

    def _format_axis(self, axis, unit: str, fmt: str):
        logger.debug("[views.py > _format_axis()] ▶️ Entrée dans _format_axis()")

        from pyqtgraph import siFormat

        axis.setLabel(text=unit)

        if fmt == "scientific":
            try:
                axis.setTickFormat("e", precision=2)
            except AttributeError:
                axis.tickStrings = lambda values, scale, spacing: [
                    f"{v:.2e} {unit}" for v in values
                ]

        elif fmt == "scaled":
            axis.tickStrings = lambda values, scale, spacing: [
                siFormat(v, suffix=unit) for v in values
            ]

        else:
            if hasattr(axis, "setTickFormat"):
                axis.setTickFormat(None)
            if hasattr(axis, "tickStrings"):
                axis.tickStrings = lambda values, scale, spacing: [
                    str(v) for v in values
                ]

    def auto_range(self):
        logger.debug("[views.py > auto_range()] ▶️ Entrée dans auto_range()")

        self.plot_widget.enableAutoRange()

    def reset_zoom(self):
        """Reset both axes to show all data."""
        vb = self.plot_widget.getViewBox()
        vb.autoRange()
        if self.graph_data.fix_y_range:
            vb.setYRange(self.graph_data.y_min, self.graph_data.y_max, padding=0)

    def reset_zoom_x(self):
        """Reset only the X axis."""
        vb = self.plot_widget.getViewBox()
        bounds = vb.childrenBoundingRect()
        if bounds is not None:
            vb.setXRange(bounds.left(), bounds.right(), padding=0)

    def reset_zoom_y(self):
        """Reset only the Y axis."""
        vb = self.plot_widget.getViewBox()
        if self.graph_data.fix_y_range:
            vb.setYRange(self.graph_data.y_min, self.graph_data.y_max, padding=0)
        else:
            bounds = vb.childrenBoundingRect()
            if bounds is not None:
                vb.setYRange(bounds.top(), bounds.bottom(), padding=0)

    def refresh_satellites(self):
        """Update visibility and content of satellite zones around the plot."""
        zones = {
            "left": self.container.advanced_container.left_box,
            "right": self.container.advanced_container.right_box,
            "top": self.container.advanced_container.top_box,
            "bottom": self.container.advanced_container.bottom_box,
        }

        for zone, box in zones.items():
            settings = self.graph_data.satellite_settings.get(zone)
            visible = settings.visible if settings else False
            box.setVisible(visible)
            if not visible:
                continue

            color = settings.color if settings else "#ffffff"
            size = settings.size if settings else 100

            if zone in {"left", "right"}:
                box.setFixedWidth(size)
            else:
                box.setFixedHeight(size)

            box.setStyleSheet(f"background-color: {color};")

            layout = box.layout()
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    if item and item.widget():
                        item.widget().deleteLater()
            for child in box.findChildren(QtWidgets.QWidget):
                if layout is None or layout.indexOf(child) == -1:
                    child.deleteLater()

            for obj in self.graph_data.satellite_objects.get(zone, []):
                widget = self._create_satellite_widget(obj)
                anchor = getattr(obj, "anchor", "grid")
                if anchor == "grid" and layout is not None:
                    if isinstance(layout, QtWidgets.QGridLayout):
                        row = max(0, obj.y)
                        col = max(0, obj.x)
                        layout.addWidget(widget, row, col)
                    else:
                        layout.addWidget(widget)
                else:
                    widget.setParent(box)
                    zone_w = box.width()
                    zone_h = box.height()
                    anchor_map = {
                        "top-left": (0, 0),
                        "top": (0.5, 0),
                        "top-right": (1, 0),
                        "left": (0, 0.5),
                        "center": (0.5, 0.5),
                        "right": (1, 0.5),
                        "bottom-left": (0, 1),
                        "bottom": (0.5, 1),
                        "bottom-right": (1, 1),
                    }
                    ax, ay = anchor_map.get(anchor, (0, 0))
                    x = int(ax * zone_w) + obj.x
                    y = int(ay * zone_h) + obj.y
                    widget.move(x, y)
                    widget.show()

    def _create_satellite_widget(self, obj):
        if obj.obj_type == "text":
            label = QtWidgets.QLabel(obj.config.get("value", ""))
            return label
        if obj.obj_type == "button":
            btn = QtWidgets.QToolButton()
            btn.setText(obj.config.get("value", ""))
            width = int(obj.config.get("width", 24))
            height = int(obj.config.get("height", 24))
            btn.setFixedSize(width, height)
            return btn
        if obj.obj_type == "image":
            label = QtWidgets.QLabel()
            path = obj.config.get("value")
            if path:
                pix = QtGui.QPixmap(path)
                if not pix.isNull():
                    w = int(obj.config.get("width", pix.width()))
                    h = int(obj.config.get("height", pix.height()))
                    label.setPixmap(pix.scaled(w, h))
            return label
        return QtWidgets.QLabel(obj.name)
