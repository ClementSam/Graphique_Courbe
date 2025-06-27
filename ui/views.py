from core.app_state import AppState
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QTimer
import time
import pyqtgraph as pg
from signal_bus import signal_bus
from PyQt5.QtGui import QColor, QPainterPath
from ui.widgets.plot_container import PlotContainerWidget
from ui.satellite_zone_view import SatelliteZoneView
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
        self.satellites = []

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

        if g.fix_y_range:
            self.plot_widget.enableAutoRange(False, False)
            self.plot_widget.setYRange(g.y_min, g.y_max)
        else:
            self.plot_widget.enableAutoRange(True, True)

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
            color = zone.get("color", "#FF0000")
            if ztype == "linear":
                bounds = zone.get("bounds", [0, 1])
                orientation = zone.get("orientation", "vertical")
                item = pg.LinearRegionItem(
                    values=bounds,
                    orientation=orientation,
                    brush=pg.mkBrush(QColor(color + "40")),
                    pen=pg.mkPen(color),
                )
            elif ztype == "rect":
                x, y, w, h = zone.get("rect", [0, 0, 1, 1])
                item = QtWidgets.QGraphicsRectItem(x, y, w, h)
                pen = pg.mkPen(color)
                brush = pg.mkBrush(QColor(color + "40"))
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
                item.setPen(pg.mkPen(color))
            else:
                continue
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
        """Convenience wrapper used by GraphUICoordinator."""
        self.plot_widget.enableAutoRange()

    def refresh_satellites(self):
        """Update visibility and content of satellite zones around the plot."""
        zones = {
            "left": self.container.advanced_container.left_box,
            "right": self.container.advanced_container.right_box,
            "top": self.container.advanced_container.top_box,
            "bottom": self.container.advanced_container.bottom_box,
        }

        for zone, box in zones.items():
            visible = self.graph_data.satellite_visibility.get(zone, False)
            box.setVisible(visible)
            if not visible:
                continue

            settings = self.graph_data.satellite_settings.get(zone, {})
            color = settings.get("color", "#ffffff")
            size = settings.get("size", 100)

            if zone in {"left", "right"}:
                box.setFixedWidth(size)
            else:
                box.setFixedHeight(size)

            box.setStyleSheet(f"background-color: {color};")

            layout = box.layout()
            old_view = None
            if layout.count():
                w = layout.itemAt(0).widget()
                if isinstance(w, SatelliteZoneView):
                    old_view = w
            while layout.count():
                item = layout.takeAt(0)
                if item and item.widget():
                    item.widget().deleteLater()

            if old_view:
                self.graph_data.satellite_settings[zone]["items"] = old_view.get_items()

            edit_mode = self.graph_data.satellite_edit_mode.get(zone, False)
            view = SatelliteZoneView(editable=edit_mode)
            layout.addWidget(view)
            view.setSceneRect(0, 0, box.width(), box.height())
            view.load_items(settings.get("items", []))
