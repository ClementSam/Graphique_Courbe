
from PyQt5 import QtWidgets

class PlotContainerWidget(QtWidgets.QGroupBox):
    def __init__(self, graph_name, plot_widget, parent=None):
        super().__init__(graph_name, parent)
        self.setObjectName(graph_name)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.plot_widget = plot_widget
        self.graph_name = graph_name
        self.removed = False  # marque si le graphique a déjà été supprimé

        self.layout().addWidget(self.plot_widget)

    def mark_removed(self):
        self.removed = True
        self.setTitle(f"{self.graph_name} (supprimé)")
        self.setDisabled(True)
