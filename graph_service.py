# graph_service.py

from app_state import AppState
from models import CurveData
import numpy as np
from PyQt5 import QtCore

class GraphService:
    """
    Gère la logique métier liée aux graphes et aux courbes.
    """

    def __init__(self, state: AppState):
        self.state = state

    # Gestion des Graphes
    def create_graph(self):
        name = self._generate_unique_graph_name()
        self.state.add_graph(name)
        return name

    def delete_graph(self, name: str):
        self.state.remove_graph(name)

    def rename_graph(self, old_name: str, new_name: str):
        self.state.rename_graph(old_name, new_name)

    def select_graph(self, name: str):
        self.state.select_graph(name)

    # Gestion des Courbes
    def add_curve(self, graph_name: str, curve: CurveData):
        graph = self.state.graphs.get(graph_name)
        if not graph:
            raise ValueError(f"Graphique '{graph_name}' introuvable.")
        graph.add_curve(curve)
    
    def add_random_curve(self):
        graph = self.state.current_graph
        if graph is None:
            raise ValueError("Aucun graphique sélectionné.")
        
        x = np.linspace(0, 2*np.pi, 1000)
        y = np.sin(np.random.uniform(1, 5) * x)
        curve_name = self._generate_unique_curve_name(graph)
        curve = CurveData(
            name=curve_name,
            x=x,
            y=y,
            color=np.random.choice(['r', 'g', 'b', 'm', 'c', 'y']),
            style=QtCore.Qt.SolidLine
        )
        graph.add_curve(curve)
        return curve.name

    def remove_curve(self, curve_name: str):
        graph = self.state.current_graph
        if graph is None:
            raise ValueError("Aucun graphique sélectionné.")
        graph.remove_curve_by_name(curve_name)
        if self.state.current_curve and self.state.current_curve.name == curve_name:
            self.state.current_curve = None

    def rename_curve(self, old_name: str, new_name: str):
        graph = self.state.current_graph
        if graph is None:
            raise ValueError("Aucun graphique sélectionné.")
        if any(c.name == new_name for c in graph.curves):
            raise ValueError(f"Une courbe '{new_name}' existe déjà.")
        curve = next((c for c in graph.curves if c.name == old_name), None)
        if curve is None:
            raise KeyError(f"La courbe '{old_name}' n'existe pas.")
        curve.name = new_name

    def clear_curves(self):
        graph = self.state.current_graph
        if graph:
            graph.clear_curves()
            self.state.current_curve = None

    def select_curve(self, curve_name: str):
        self.state.select_curve(curve_name)

    # Méthodes privées d'aide
    def _generate_unique_graph_name(self):
        base_name = "Graphique"
        index = 1
        while f"{base_name} {index}" in self.state.graphs:
            index += 1
        return f"{base_name} {index}"

    def _generate_unique_curve_name(self, graph):
        base_name = "Courbe"
        index = 1
        existing_names = {curve.name for curve in graph.curves}
        while f"{base_name} {index}" in existing_names:
            index += 1
        return f"{base_name} {index}"
