from PyQt5 import QtCore

class SignalBus(QtCore.QObject):
    graph_selected = QtCore.pyqtSignal(str)
    curve_selected = QtCore.pyqtSignal(str)
    curve_list_updated = QtCore.pyqtSignal()
    curve_updated = QtCore.pyqtSignal()
    graph_updated = QtCore.pyqtSignal()
    remove_requested = QtCore.pyqtSignal(str, str)
    rename_requested = QtCore.pyqtSignal(str, str, str)  # kind, old_name, new_name

signal_bus = SignalBus()