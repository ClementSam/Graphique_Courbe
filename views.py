from app_state import AppState
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer
import time
import pyqtgraph as pg
from signal_bus import signal_bus

class MyPlotView:
    def __init__(self, graph_data):
        self.graph_data = graph_data
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.useOpenGL(True)
        self.curves = {}
        self.plot_widget.scene().sigMouseClicked.connect(self._on_mouse_click)


    def update_graph_properties(self):
        g = self.graph_data
        self.plot_widget.showGrid(g.grid_visible, g.grid_visible)
        self.plot_widget.setLogMode(g.log_x, g.log_y)
        self.plot_widget.setBackground('k' if g.dark_mode else 'w')

    def refresh_curves(self):
        import time
        start = time.perf_counter()
    
        self.plot_widget.clear()
        self.curves.clear()
    
        for curve in self.graph_data.curves:
            print('[VIEW] Drawing:', curve.name, '| Visible:', curve.visible)
            if not curve.visible:
                continue
    
            pen = pg.mkPen(color=curve.color, width=curve.width, style=curve.style)
    
            if curve.downsampling_mode == "manual":
                x = curve.x[::curve.downsampling_ratio]
                y = curve.y[::curve.downsampling_ratio]
                item = pg.PlotDataItem(x, y, pen=pen, name=curve.name)
            else:
                item = pg.PlotDataItem(curve.x, curve.y, pen=pen, name=curve.name)

            item.curve_name = curve.name  # Ajout d'un attribut custom
    
            self.plot_widget.addItem(item)
            item.setClipToView(True)
    
            if curve.downsampling_mode == "off":
                item.setDownsampling(auto=False)
            elif curve.downsampling_mode == "auto":
                item.setDownsampling(auto=True)
            # pas besoin de downsampling pour "manual" car déjà sous-échantillonné
    
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
    
            # Recherche du point le plus proche du clic
            distances = ((x_data - x_click)**2 + (y_data - y_click)**2)
            idx_min = distances.argmin()
            distance = distances[idx_min]**0.5
    
            if distance < 10:  # seuil en pixels (adaptable)
                if distance < min_distance:
                    min_distance = distance
                    selected_curve = curve_name
    
        if selected_curve:
            print(f"[CLICK] Courbe cliquée (par distance) : {selected_curve}")
            signal_bus.curve_selected.emit(selected_curve)
