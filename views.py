from app_state import AppState
from PyQt5 import QtWidgets
import pyqtgraph as pg

class MyPlotView:
    def __init__(self, graph_data):
        self.graph_data = graph_data
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.curves = {}

    def update_graph_properties(self):
        g = self.graph_data
        self.plot_widget.showGrid(g.grid_visible, g.grid_visible)
        self.plot_widget.setLogMode(g.log_x, g.log_y)
        self.plot_widget.setBackground('k' if g.dark_mode else 'w')

    def refresh_curves(self):
        self.plot_widget.clear()
        self.curves.clear()
        for curve in self.graph_data.curves:
            print('[VIEW] Drawing:', curve.name, '| Visible:', curve.visible)
            if not curve.visible:
                continue
            pen = pg.mkPen(color=curve.color, width=curve.width, style=curve.style)
            item = self.plot_widget.plot(curve.x, curve.y, pen=pen, name=curve.name)
            self.curves[curve.name] = item

    def auto_range(self):
        self.plot_widget.enableAutoRange()
