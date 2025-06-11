# controllers.py

from core.app_state import AppState
from core.graph_service import GraphService
from ui.graph_ui_coordinator import GraphUICoordinator
from signal_bus import signal_bus

class GraphController:
    def __init__(self, views: dict, central_area):
        print("🧠 [GraphController.__init__] Initialisation du contrôleur")
        self.state = AppState.get_instance()
        self.service = GraphService(self.state)
        self.ui = GraphUICoordinator(self.state, views, central_area)

    def load_project(self, graphs: dict):
        print("📂 [GraphController.load_project] Chargement du projet...")
        print(f"📊 [GraphController.load_project] Graphiques reçus : {list(graphs.keys())}")
        self.state.graphs = graphs
        self.state.current_graph = None
        self.state.current_curve = None
        self.ui.refresh_plot()

    def add_graph(self, name: str = None):
        print(f"➕ [GraphController.add_graph] Requête d'ajout de graphique : {name}")
        created_name = self.service.add_graph(name)
        print(f"✅ [GraphController.add_graph] Graphique '{created_name}' ajouté via service.")
        signal_bus.graph_selected.emit(created_name)
        signal_bus.graph_updated.emit()
        self.ui.refresh_plot()
        
    def add_curve(self, graph_name: str):
        print(f"➕ [GraphController.add_curve] Requête d'ajout de courbe à : {graph_name}")
        from curve_generators import generate_random_curve
        graph = self.state.graphs.get(graph_name)
        if not graph:
            print(f"❌ [GraphController.add_curve] Graphique introuvable : {graph_name}")
            return
    
        existing_names = [c.name for c in graph.curves]
        index = 1
        while f"Courbe {index}" in existing_names:
            index += 1
    
        curve = generate_random_curve(index)
        created_curve_name = self.service.add_curve(graph_name, curve)
        print(f"✅ [GraphController.add_curve] Courbe '{created_curve_name}' ajoutée à '{graph_name}'")
        signal_bus.curve_selected.emit(graph_name, created_curve_name)
        signal_bus.curve_list_updated.emit()
        signal_bus.curve_updated.emit()
        self.ui.refresh_plot()

    def select_graph(self, name: str):
        print(f"🎯 [GraphController.select_graph] Sélection du graphique : {name}")
        self.service.select_graph(name)
        self.ui.refresh_plot()

    def select_curve(self, curve_name: str):
        print(f"🎯 [GraphController.select_curve] Sélection de la courbe : {curve_name}")
        self.service.select_curve(curve_name)
        self.ui.refresh_curve_ui()

    def remove_graph(self, name: str):
        print(f"🗑 [GraphController.remove_graph] Suppression du graphique : {name}")
        self.service.remove_graph(name)
        signal_bus.graph_updated.emit()
        self.ui.refresh_plot()
        
    def remove_curve(self, name: str):
        print(f"🗑 [GraphController.remove_curve] Suppression de la courbe : {name}")
        self.service.remove_curve(name)
        signal_bus.curve_updated.emit()
        self.ui.refresh_curve_ui()

    def rename_graph(self, old_name: str, new_name: str):
        print(f"✏️ [GraphController.rename_graph] Renommage graphique : {old_name} → {new_name}")
        self.service.rename_graph(old_name, new_name)
        self.ui.refresh_plot()

    def rename_curve(self, old_name: str, new_name: str):
        print(f"✏️ [GraphController.rename_curve] Renommage courbe : {old_name} → {new_name}")
        self.service.rename_curve(old_name, new_name)
        self.ui.refresh_curve_ui()

    def import_graph(self, graph_data):
        print(f"📥 [GraphController.import_graph] Import du graphique : {graph_data.name}")
        self.service.import_graph(graph_data)
        self.ui.refresh_plot()

    def bring_curve_to_front(self):
        print("🔝 [GraphController.bring_curve_to_front] Priorisation de la courbe")
        self.service.bring_curve_to_front()
        self.ui.refresh_plot()

    def set_opacity(self, value: float):
        print(f"🎨 [GraphController.set_opacity] Opacité = {value}")
        self.service.set_opacity(value)
        self.ui.refresh_curve_ui()

    def set_gain(self, value: float):
        print(f"📈 [GraphController.set_gain] Gain = {value}")
        self.service.set_gain(value)
        self.ui.refresh_curve_ui()

    def set_offset(self, value: float):
        print(f"📏 [GraphController.set_offset] Offset = {value}")
        self.service.set_offset(value)
        self.ui.refresh_curve_ui()

    def set_style(self, style: int):
        print(f"🖌 [GraphController.set_style] Style = {style}")
        self.service.set_style(style)
        self.ui.refresh_curve_ui()

    def set_symbol(self, symbol: str):
        print(f"🔣 [GraphController.set_symbol] Symbole = {symbol}")
        self.service.set_symbol(symbol)
        self.ui.refresh_curve_ui()

    def set_fill(self, fill: bool):
        print(f"🧱 [GraphController.set_fill] Remplissage = {fill}")
        self.service.set_fill(fill)
        self.ui.refresh_curve_ui()

    def set_display_mode(self, mode: str):
        print(f"🖥 [GraphController.set_display_mode] Mode d'affichage = {mode}")
        self.service.set_display_mode(mode)
        self.ui.refresh_curve_ui()

    def set_label_mode(self, mode: str):
        print(f"🏷 [GraphController.set_label_mode] Mode étiquette = {mode}")
        self.service.set_label_mode(mode)
        self.ui.refresh_curve_ui()

    def set_zero_indicator(self, mode: str):
        print(f"🎯 [GraphController.set_zero_indicator] Indicateur zéro = {mode}")
        self.service.set_zero_indicator(mode)
        self.ui.refresh_curve_ui()

    def set_color(self, color: str):
        print(f"🌈 [GraphController.set_color] Couleur = {color}")
        self.service.set_color(color)
        self.ui.refresh_curve_ui()

    def set_show_label(self, visible: bool):
        print(f"👁 [GraphController.set_show_label] Étiquette visible = {visible}")
        self.service.set_show_label(visible)
        self.ui.refresh_curve_ui()

    def reset_zoom(self):
        print("🔍 [GraphController.reset_zoom] Réinitialisation du zoom")
        self.ui.reset_zoom()
