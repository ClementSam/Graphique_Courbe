from app_state import AppState
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer
import time
import pyqtgraph as pg

class MyPlotView:
    def __init__(self, graph_data):
        self.graph_data = graph_data
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.useOpenGL(True)
        self.curves = {}

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
