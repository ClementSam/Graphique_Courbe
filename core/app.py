#app.py

from PyQt5 import QtWidgets
from ui.ui_main_window import MainWindow
from ui.layout_manager import get_default_layout, load_layout
import sys
from ui.application_coordinator import ApplicationCoordinator
import logging

logger = logging.getLogger(__name__)

def launch_app():
    window = MainWindow()

    # Coordination de l'application
    app_coordinator = ApplicationCoordinator(window)

    # Connecte la zone centrale de tracé
    window.center_area_widget = app_coordinator.center_area
    window.dock_center.setWidget(window.center_area_widget)

    # Injecte les panneaux gérés par le coordinateur
    window.left_panel = app_coordinator.graph_panel
    window.dock_left.setWidget(window.left_panel)
    window.right_panel = app_coordinator.properties_panel
    window.dock_right.setWidget(window.right_panel)

    # Chargement du layout s'il existe
    try:
        default = get_default_layout()
        if default:
            load_layout(default, window)
    except Exception as e:
        logger.debug(f"[launch_app] ⚠️ Erreur lors du chargement du layout : {e}")

    window.show()
    sys.exit(QtWidgets.QApplication.instance().exec_())
