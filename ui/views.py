from core.app_state import AppState
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QTimer
import time
import pyqtgraph as pg
from signal_bus import signal_bus
from PyQt5.QtGui import QColor
    
class MyPlotView:
    def __init__(self, graph_data):
        print("[views.py > __init__()] ▶️ Entrée dans __init__()")

        self.graph_data = graph_data
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.useOpenGL(True)
        self.curves = {}
        self.labels = {}
        self.legend = None
        self.satellites = []

        self.left_indicator_plot = None  # ← AJOUT ICI ✅

        self.plot_widget.scene().sigMouseClicked.connect(self._on_mouse_click)


    def update_graph_properties(self):
        print("[views.py > update_graph_properties()] ▶️ Entrée dans update_graph_properties()")

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
        print("[views.py > refresh_curves()] ▶️ Entrée dans refresh_curves()")

    
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
    
        curves_with_legend = [c for c in self.graph_data.curves if c.label_mode == "legend" and c.visible]
        if curves_with_legend:
            self.legend = pg.LegendItem(offset=(30, 30))
            self.legend.setParentItem(self.plot_widget.plotItem)
    
        legend_items_added = set()
        self.zero_arrows = []
    
        for curve in self.graph_data.curves:
            print(f"[DEBUG] Courbe '{curve.name}' → id={id(curve)} zero_indicator = {curve.zero_indicator}")
    
            if not curve.visible:
                continue
    
            x = curve.x[::curve.downsampling_ratio] if curve.downsampling_mode == "manual" else curve.x
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
                item = pg.ScatterPlotItem(x=x, y=y, pen=pen, brush=pg.mkBrush(qcolor),
                                          symbol=curve.symbol or 'o', size=curve.width * 2)
            elif curve.display_mode == "bar":
                item = pg.BarGraphItem(x=x, height=y, width=0.1, brush=pg.mkBrush(qcolor))
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
                zero_line = pg.InfiniteLine(angle=0, pen=pg.mkPen(curve.color, style=QtCore.Qt.DashLine))
                zero_line.setPos(curve.offset)
                self.plot_widget.addItem(zero_line)
    
            # Optimisation
            if hasattr(item, 'setClipToView'):
                item.setClipToView(True)
            if hasattr(item, 'setDownsampling'):
                if curve.downsampling_mode == "off":
                    item.setDownsampling(auto=False)
                elif curve.downsampling_mode == "auto":
                    item.setDownsampling(auto=True)
    
        end = time.perf_counter()
        print(f"[PROFILER] refresh_curves took {end - start:.4f} seconds")



    def _on_mouse_click(self, event):
        print("[views.py > _on_mouse_click()] ▶️ Entrée dans _on_mouse_click()")

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
            signal_bus.curve_selected.emit(self.graph_data.name, selected_curve)

    def _format_axis(self, axis, unit: str, fmt: str):
        print("[views.py > _format_axis()] ▶️ Entrée dans _format_axis()")

        from pyqtgraph import siFormat

        axis.setLabel(text=unit)

        if fmt == "scientific":
            try:
                axis.setTickFormat("e", precision=2)
            except AttributeError:
                axis.tickStrings = lambda values, scale, spacing: [f"{v:.2e} {unit}" for v in values]

        elif fmt == "scaled":
            axis.tickStrings = lambda values, scale, spacing: [siFormat(v, suffix=unit) for v in values]

        else:
            if hasattr(axis, "setTickFormat"):
                axis.setTickFormat(None)
            if hasattr(axis, "tickStrings"):
                axis.tickStrings = lambda values, scale, spacing: [str(v) for v in values]

    def auto_range(self):
        print("[views.py > auto_range()] ▶️ Entrée dans auto_range()")

        self.plot_widget.enableAutoRange()