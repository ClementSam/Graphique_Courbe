from PyQt5 import QtCore
from PyQt5.QtCore import QObject, pyqtSignal

class SignalBus(QtCore.QObject):
    graph_selected = QtCore.pyqtSignal(str)
    curve_selected = QtCore.pyqtSignal(str, str)  # graph_name, curve_name
    curve_list_updated = QtCore.pyqtSignal()
    curve_updated = QtCore.pyqtSignal()
    graph_updated = QtCore.pyqtSignal()

    # Visible state toggles
    graph_visibility_changed = QtCore.pyqtSignal(str, bool)
    curve_visibility_changed = QtCore.pyqtSignal(str, str, bool)

    remove_requested = QtCore.pyqtSignal(str, str)
    rename_requested = QtCore.pyqtSignal(str, str, str)  # kind, old_name, new_name

    # 🚨 Deux signaux séparés !
    add_graph_requested = pyqtSignal(str)  # "graph"
    add_curve_requested = pyqtSignal(str)  # "NomGraphique"
    bit_curve_requested = pyqtSignal(str, object)  # curve_name, bit_count

signal_bus = SignalBus()
