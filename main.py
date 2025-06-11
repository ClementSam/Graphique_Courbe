#main.py

from PyQt5 import QtWidgets
from core.startup import check_expiry_date
from core.app import launch_app
import sys
from signal_bus import SignalBus, signal_bus
from core.app_state import AppState

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    check_expiry_date()
    state = AppState.get_instance()
    bus = signal_bus
    launch_app(state, bus)
