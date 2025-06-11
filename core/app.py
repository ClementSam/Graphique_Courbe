#app.py

from PyQt5 import QtWidgets
from ui.ui_main_window import MainWindow
from layout_manager import get_default_layout, load_layout
import sys
from ui.application_coordinator import ApplicationCoordinator
from core.app_state import AppState
from signal_bus import SignalBus, signal_bus

def launch_app(state: AppState = None, bus: SignalBus = signal_bus):
    state = state or AppState.get_instance()
    bus = bus or signal_bus
    window = MainWindow(state, bus)

    # Coordination de l'application
    app_coordinator = ApplicationCoordinator(window, state, bus)

    # Connecte la zone centrale de tracé
    window.center_area_widget = app_coordinator.center_area
    window.dock_center.setWidget(window.center_area_widget)

    # Chargement du layout s'il existe
    try:
        default = get_default_layout()
        if default:
            load_layout(default, window)
    except Exception as e:
        print(f"[launch_app] ⚠️ Erreur lors du chargement du layout : {e}")

    window.show()
    sys.exit(QtWidgets.QApplication.instance().exec_())