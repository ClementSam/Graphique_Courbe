# application_coordinator.py

from controllers import GraphController
from ui.GraphCurvePanel import GraphCurvePanel
from ui.CentralPlotArea import CentralPlotArea
from ui.PropertiesPanel import PropertiesPanel
from signal_bus import signal_bus
from core.models import GraphData
from ui.views import MyPlotView
from core.app_state import AppState
from signal_bus import signal_bus
from ui.graph_ui_coordinator import GraphUICoordinator
import logging

logger = logging.getLogger(__name__)


class ApplicationCoordinator:
    def __init__(self, main_window):
        logger.debug("[ApplicationCoordinator] ▶️ Initialisation du coordinateur")

        self.main_window = main_window
        self.state = AppState.get_instance()

        self.graph_panel = GraphCurvePanel()
        self.properties_panel = PropertiesPanel()
        self.center_area = CentralPlotArea()
        self.views = {}

        # 👇 Coordinateur UI des graphes
        self.graph_ui_coordinator = GraphUICoordinator(self.state, self.views, self.center_area)

        self._setup_controller()
        self._connect_signals()

        logger.debug("[ApplicationCoordinator] ✅ Initialisation terminée")

    def _setup_controller(self):
        self.controller = GraphController(self.views, self.center_area)
        logger.debug("[ApplicationCoordinator] 🧠 Contrôleur initialisé")

    def _connect_signals(self):
        # ➕ Ajout de graphes ou courbes
        signal_bus.add_graph_requested.connect(lambda _: self._handle_add_requested("graph"))
        signal_bus.add_curve_requested.connect(self._handle_add_requested)

        # 🎯 Sélections
        signal_bus.graph_selected.connect(self.controller.select_graph)
        signal_bus.curve_selected.connect(lambda g, c: self.controller.select_curve(c))

        # 🔄 Mise à jour des panneaux de propriétés
        signal_bus.graph_updated.connect(self.properties_panel.refresh_graph_tab)
        signal_bus.curve_updated.connect(self.properties_panel.refresh_curve_tab)
        signal_bus.curve_list_updated.connect(self.properties_panel.refresh_curve_tab)

        # 🧠 Mise à jour de l’état interne
        signal_bus.graph_selected.connect(self.on_graph_selected)
        signal_bus.graph_updated.connect(self.on_graph_updated)

        # ✅ ➕ Connexions vers l'UI passive (nouvelle logique)
        signal_bus.graph_updated.connect(self._on_graph_updated)
        signal_bus.curve_updated.connect(self._on_curve_updated)
        signal_bus.curve_selected.connect(self._on_curve_selected)
        signal_bus.graph_selected.connect(self._on_graph_selected)
        signal_bus.rename_requested.connect(self._handle_rename_requested)
        signal_bus.remove_requested.connect(self._handle_remove_requested)

    def _handle_add_requested(self, kind_or_graphname):
        if kind_or_graphname == "graph":
            self.controller.add_graph(None)
        else:
            self.controller.add_curve(kind_or_graphname)

    def on_graph_selected(self, name):
        logger.debug(f"📥 [ApplicationCoordinator] Signal graph_selected reçu pour : {name}")
        graph = self.state.graphs.get(name)
        if graph:
            self.state.current_graph = graph
            logger.debug(f"🧠 [on_graph_selected] current_graph mis à jour : {graph.name}")
            if self.properties_panel:
                self.properties_panel.update_graph_ui()
        self.graph_ui_coordinator.refresh_plot()

    def on_graph_updated(self):
        logger.debug("📥 [ApplicationCoordinator] Signal graph_updated reçu")
        self.graph_ui_coordinator.refresh_plot()

    # 🆕 Méthodes pour pilotage de l’UI
    def _on_graph_updated(self):
        self.main_window.show_graph_tab()

    def _on_curve_updated(self):
        self.main_window.show_curve_tab()

    def _on_graph_selected(self, graph_name):
        self.main_window.show_graph_tab()

    def _on_curve_selected(self, graph_name, curve_name):
        self.main_window.show_curve_tab(graph_name, curve_name)

    def _handle_rename_requested(self, kind, old_name, new_name):
        if kind == "graph":
            self.controller.rename_graph(old_name, new_name)
            signal_bus.graph_updated.emit()
        elif kind == "curve":
            self.controller.rename_curve(old_name, new_name)
            signal_bus.curve_updated.emit()
        self.graph_ui_coordinator.refresh_plot()

    def _handle_remove_requested(self, kind, name):
        if kind == "graph":
            self.controller.remove_graph(name)
        elif kind == "curve":
            self.controller.remove_curve(name)
            self.graph_ui_coordinator.refresh_plot()

