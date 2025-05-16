from app_state import AppState
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QTimer
import time
import pyqtgraph as pg
from signal_bus import signal_bus
from PyQt5.QtGui import QColor


class MyPlotView:
    def __init__(self, graph_data):
        self.graph_data = graph_data
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.useOpenGL(True)
        self.curves = {}
        self.labels = {}
        self.plot_widget.scene().sigMouseClicked.connect(self._on_mouse_click)

    def update_graph_properties(self):
        g = self.graph_data
        self.plot_widget.showGrid(g.grid_visible, g.grid_visible)
        self.plot_widget.setLogMode(g.log_x, g.log_y)
        self.plot_widget.setBackground('k' if g.dark_mode else 'w')

        if g.fix_y_range:
            self.plot_widget.enableAutoRange(False, False)
            self.plot_widget.setYRange(g.y_min, g.y_max)
        else:
            self.plot_widget.enableAutoRange(True, True)

        self._format_axis(self.plot_widget.getAxis("bottom"), g.x_unit, g.x_format)
        self._format_axis(self.plot_widget.getAxis("left"), g.y_unit, g.y_format)

    def refresh_curves(self):
        start = time.perf_counter()

        self.plot_widget.clear()
        self.curves.clear()

        # Nettoyer anciens labels
        for label in self.labels.values():
            self.plot_widget.removeItem(label)
        self.labels.clear()

        # Nettoyer ancienne légende
        self.plot_widget.plotItem.legend = None

        # Ajouter une nouvelle légende si nécessaire
        use_legend = any(c.label_mode == "legend" for c in self.graph_data.curves)
        if use_legend:
            self.plot_widget.addLegend(offset=(30, 30))

        for curve in self.graph_data.curves:
            print('[VIEW] Drawing:', curve.name, '| Visible:', curve.visible)
            if not curve.visible:
                continue

            qcolor = QColor(curve.color)
            qcolor.setAlphaF(curve.opacity / 100.0)
            pen = pg.mkPen(color=qcolor, width=curve.width, style=curve.style)

            if curve.downsampling_mode == "manual":
                x = curve.x[::curve.downsampling_ratio]
                y = curve.y[::curve.downsampling_ratio]
            else:
                x = curve.x
                y = curve.gain * curve.y + curve.offset

            if curve.display_mode == "line":
                item = pg.PlotDataItem(x, y, pen=pen, name=curve.name, symbol=curve.symbol)
                if curve.fill:
                    item.setFillLevel(0)
                    item.setBrush(pg.mkBrush(qcolor))
            elif curve.display_mode == "scatter":
                item = pg.ScatterPlotItem(
                    x=x, y=y,
                    pen=pen,
                    brush=pg.mkBrush(qcolor),
                    symbol=curve.symbol or 'o',
                    size=curve.width * 2
                )
            elif curve.display_mode == "bar":
                item = pg.BarGraphItem(
                    x=x, height=y, width=0.1,
                    brush=pg.mkBrush(qcolor)
                )
            else:
                continue

            item.curve_name = curve.name
            self.plot_widget.addItem(item)

            # --- Affichage du label selon le mode ---
            if curve.label_mode == "inline":
                text = pg.TextItem(text=curve.name, anchor=(1, 0), color=qcolor)
                if len(x) > 0 and len(y) > 0:
                    text.setPos(x[-1], y[-1])
                self.plot_widget.addItem(text)
                self.labels[curve.name] = text

            elif curve.label_mode == "legend":
                if hasattr(self.plot_widget, 'legend') and self.plot_widget.legend:
                    self.plot_widget.legend.addItem(item, curve.name)

            if curve.show_zero_line:
                zero_line = pg.InfiniteLine(angle=0, pen=pg.mkPen(curve.color, style=QtCore.Qt.DashLine))
                zero_line.setPos(curve.offset)
                self.plot_widget.addItem(zero_line)

            if hasattr(item, 'setClipToView'):
                item.setClipToView(True)

            if hasattr(item, 'setDownsampling'):
                if curve.downsampling_mode == "off":
                    item.setDownsampling(auto=False)
                elif curve.downsampling_mode == "auto":
                    item.setDownsampling(auto=True)

            self.curves[curve.name] = item

        end = time.perf_counter()
        print(f"[PROFILER] refresh_curves took {end - start:.4f} seconds")

    def _on_mouse_click(self, event):
        scene_pos = event.scenePos()
        view_pos = self.plot_widget.plotItem.vb.mapSceneToView(scene_pos)
        x_click, y_click = view_pos.x(), view_pos.y()

        min_distance = float('inf')
        selected_curve = None

        for curve_name, item in self.curves.items():
            x_data, y_data = item.getData()
            if x_data is None or y_data is None:
                continue

            distances = ((x_data - x_click) ** 2 + (y_data - y_click) ** 2)
            idx_min = distances.argmin()
            distance = distances[idx_min] ** 0.5

            if distance < 10 and distance < min_distance:
                min_distance = distance
                selected_curve = curve_name

        if selected_curve:
            print(f"[CLICK] Courbe cliquée (par distance) : {selected_curve}")
            signal_bus.curve_selected.emit(selected_curve)

    def _format_axis(self, axis, unit: str, fmt: str):
        from pyqtgraph import siFormat

        axis.setLabel(text=unit)

        if fmt == "scientific":
            try:
                axis.setTickFormat("e", precision=2)
            except AttributeError:
                axis.tickStrings = lambda values, scale, spacing: [f"{v:.2e} {unit}" for v in values]

        elif fmt == "scaled":
            axis.tickStrings = lambda values, scale, spacing: [siFormat(v, suffix=unit) for v in values]

        else:  # normal
            if hasattr(axis, "setTickFormat"):
                axis.setTickFormat(None)
            if hasattr(axis, "tickStrings"):
                axis.tickStrings = lambda values, scale, spacing: [str(v) for v in values]

    def auto_range(self):
        self.plot_widget.enableAutoRange()
