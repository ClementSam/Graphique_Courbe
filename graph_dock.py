
from PyQt5.QtWidgets import QDockWidget

class GraphDockWidget(QDockWidget):
    def __init__(self, graph_name, plot_widget, parent=None):
        super().__init__(graph_name, parent)
        self.setObjectName(graph_name)
        self.setWidget(plot_widget)
        self.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)
        self.graph_name = graph_name
