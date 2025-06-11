
# CentralPlotArea.py

from PyQt5 import QtWidgets
import logging

logger = logging.getLogger(__name__)

class CentralPlotArea(QtWidgets.QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setWidgetResizable(True)
        self.widget = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout(self.widget)
        self.setWidget(self.widget)

    def add_plot_widget(self, widget):
        logger.debug(f"[CentralPlotArea] ➕ Ajout du widget : {widget}")
        self.layout.addWidget(widget)
    
    def remove_plot_widget(self, widget):
        logger.debug(f"[CentralPlotArea] ➖ Retrait du widget : {widget}")
        self.layout.removeWidget(widget)
        widget.deleteLater()

