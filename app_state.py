# app_state.py

from models import GraphData

class AppState:
    """
    Singleton centralisant l'état global de l'application (graphes et courbes).
    Utiliser AppState.get_instance() pour accéder à l'instance.
    """

    _instance = None

    def __init__(self):
        if AppState._instance is not None:
            raise RuntimeError("Utiliser AppState.get_instance() au lieu d'instancier directement.")
        self.graphs = {}  # nom → GraphData
        self.current_graph = None  # GraphData ou None
        self.current_curve = None  # CurveData ou None
        AppState._instance = self

    @staticmethod
    def get_instance():
        if AppState._instance is None:
            AppState()
        return AppState._instance

    # Gestion des graphes
    def add_graph(self, name: str):
        if name in self.graphs:
            raise ValueError(f"Le graphique '{name}' existe déjà.")
        self.graphs[name] = GraphData(name)

    def remove_graph(self, name: str):
        if name not in self.graphs:
            raise KeyError(f"Le graphique '{name}' n'existe pas.")
        del self.graphs[name]
        if self.current_graph and self.current_graph.name == name:
            self.current_graph = None
            self.current_curve = None

    def rename_graph(self, old_name: str, new_name: str):
        if old_name not in self.graphs:
            raise KeyError(f"Le graphique '{old_name}' n'existe pas.")
        if new_name in self.graphs:
            raise ValueError(f"Le graphique '{new_name}' existe déjà.")
        graph = self.graphs.pop(old_name)
        graph.name = new_name
        self.graphs[new_name] = graph
        if self.current_graph and self.current_graph.name == old_name:
            self.current_graph = graph

    def select_graph(self, name: str):
        self.current_graph = self.graphs.get(name, None)
        self.current_curve = None

    # Gestion des courbes
    def select_curve(self, curve_name: str):
        if not self.current_graph:
            self.current_curve = None
            return
        self.current_curve = next((c for c in self.current_graph.curves if c.name == curve_name), None)

    def clear_selection(self):
        self.current_graph = None
        self.current_curve = None