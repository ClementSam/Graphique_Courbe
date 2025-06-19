#plot_container.py

from PyQt5 import QtWidgets
from signal_bus import signal_bus
from .AdvancedPlotContainer import AdvancedPlotContainer
import logging

logger = logging.getLogger(__name__)

class PlotContainerWidget(QtWidgets.QGroupBox):
    def __init__(self, graph_name, plot_widget, parent=None):
        logger.debug("[plot_container.py > __init__()] ▶️ Entrée dans __init__()")

        super().__init__(graph_name, parent)
        self.setObjectName(graph_name)
        self.setLayout(QtWidgets.QVBoxLayout())

        self.advanced_container = AdvancedPlotContainer(plot_widget)
        self.layout().addWidget(self.advanced_container)

        self.plot_widget = plot_widget  # garde pour compatibilité
        self.graph_name = graph_name
        self.removed = False
        
        # Forcer taille minimale pour laisser place aux satellites
        self.setMinimumWidth(400)
        self.advanced_container.setMinimumWidth(400)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.MinimumExpanding)




    def mark_removed(self):
        logger.debug("[plot_container.py > mark_removed()] ▶️ Entrée dans mark_removed()")

        self.removed = True
        self.setTitle(f"{self.graph_name} (supprimé)")
        self.setDisabled(True)

    def mousePressEvent(self, event):
        logger.debug("[plot_container.py > mousePressEvent()] ▶️ Entrée dans mousePressEvent()")

        if not self.removed:
            signal_bus.graph_selected.emit(self.graph_name)
        super().mousePressEvent(event)
    
    def set_selected(self, selected: bool):
        logger.debug("[plot_container.py > set_selected()] ▶️ Entrée dans set_selected()")

        if selected:
            self.setStyleSheet("QGroupBox { border: 2px solid #0078d7; }")  # bleu pro
        else:
            self.setStyleSheet("")
            
    def get_advanced_container(self):
        logger.debug("[plot_container.py > get_advanced_container()] ▶️ Entrée dans get_advanced_container()")

        return self.advanced_container

    def set_graph_name(self, new_name):
        logger.debug("[plot_container.py > set_graph_name()] ▶️ Entrée dans set_graph_name()")

        logger.debug(f"[DEBUG_plot_container] set_graph_name appelé avec: {new_name}")
        self.graph_name = new_name
        self.setTitle(new_name)
        self.setObjectName(new_name)
