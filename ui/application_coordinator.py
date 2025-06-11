# application_coordinator.py

from controllers import GraphController
from ui.GraphCurvePanel import GraphCurvePanel
from ui.CentralPlotArea import CentralPlotArea
from ui.PropertiesPanel import PropertiesPanel
from signal_bus import SignalBus, signal_bus
from core.models import GraphData
from ui.views import MyPlotView
from core.app_state import AppState
from ui.graph_ui_coordinator import GraphUICoordinator


class ApplicationCoordinator:
    def __init__(self, main_window, state: AppState = None, bus: SignalBus = signal_bus):
        print("[ApplicationCoordinator] ▶️ Initialisation du coordinateur")

        self.main_window = main_window
        self.state = state or AppState.get_instance()
        self.bus = bus

        self.graph_panel = GraphCurvePanel(self.state, self.bus)
        self.properties_panel = PropertiesPanel(self.state)
        self.center_area = CentralPlotArea()
        self.views = {}

        # 👇 Coordinateur UI des graphes
        self.graph_ui_coordinator = GraphUICoordinator(self.state, self.views, self.center_area, self.bus)

        self._setup_controller()
        self._connect_signals()

        print("[ApplicationCoordinator] ✅ Initialisation terminée")

    def _setup_controller(self):
        self.controller = GraphController(self.state, self.bus, self.views, self.center_area)
        print("[ApplicationCoordinator] 🧠 Contrôleur initialisé")

    def _connect_signals(self):
        # ➕ Ajout de graphes ou courbes
        self.bus.add_graph_requested.connect(lambda _: self._handle_add_requested("graph"))
        self.bus.add_curve_requested.connect(self._handle_add_requested)

        # 🎯 Sélections
        self.bus.graph_selected.connect(self.controller.select_graph)
        self.bus.curve_selected.connect(lambda g, c: self.controller.select_curve(c))

        # 🔄 Mise à jour des panneaux de propriétés
        self.bus.graph_updated.connect(self.properties_panel.refresh_graph_tab)
        self.bus.curve_updated.connect(self.properties_panel.refresh_curve_tab)
        self.bus.curve_list_updated.connect(self.properties_panel.refresh_curve_tab)

        # 🧠 Mise à jour de l’état interne
        self.bus.graph_selected.connect(self.on_graph_selected)
        self.bus.graph_updated.connect(self.on_graph_updated)

        # ✅ ➕ Connexions vers l'UI passive (nouvelle logique)
        self.bus.graph_updated.connect(self._on_graph_updated)
        self.bus.curve_updated.connect(self._on_curve_updated)
        self.bus.curve_selected.connect(self._on_curve_selected)
        self.bus.graph_selected.connect(self._on_graph_selected)

    def _handle_add_requested(self, kind_or_graphname):
        if kind_or_graphname == "graph":
            self.controller.add_graph(None)
        else:
            self.controller.add_curve(kind_or_graphname)

    def on_graph_selected(self, name):
        print(f"📥 [ApplicationCoordinator] Signal graph_selected reçu pour : {name}")
        graph = self.state.graphs.get(name)
        if graph:
            self.state.current_graph = graph
            print(f"🧠 [on_graph_selected] current_graph mis à jour : {graph.name}")
            if self.properties_panel:
                self.properties_panel.update_graph_ui()
        self.graph_ui_coordinator.refresh_plot()

    def on_graph_updated(self):
        print("📥 [ApplicationCoordinator] Signal graph_updated reçu")
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
