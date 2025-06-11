# core/graph_service.py

from core.app_state import AppState
from core.models import GraphData, CurveData
from signal_bus import signal_bus
from core.utils.naming import get_next_graph_name


class GraphService:
    """
    Fournit les opérations métier sur les graphes et courbes,
    indépendamment de l'interface utilisateur.
    """

    def __init__(self, state: AppState):
        print("🧠 [GraphService.__init__] Initialisation du service avec AppState")
        self.state = state

    def create_graph(self):
        print("🧱 [GraphService.create_graph] Création d'un nouveau graphique...")
        name = self._generate_unique_graph_name()
        print(f"📛 [GraphService.create_graph] Nom généré : {name}")
        self.state.add_graph(name)
        print(f"✅ [GraphService.create_graph] Graphique '{name}' ajouté à l'état.")
        return name

    def _generate_unique_graph_name(self):
        print("🔄 [GraphService._generate_unique_graph_name] Recherche d'un nom unique...")
        index = 1
        while f"Graphique {index}" in self.state.graphs:
            print(f"🔁 [GraphService._generate_unique_graph_name] Graphique {index} existe déjà")
            index += 1
        result = f"Graphique {index}"
        print(f"🎯 [GraphService._generate_unique_graph_name] Nom unique trouvé : {result}")
        return result

    def select_graph(self, name: str):
        print(f"🖱 [GraphService.select_graph] Sélection du graphique : {name}")
        if name not in self.state.graphs:
            print(f"❌ [GraphService.select_graph] Graphique '{name}' introuvable dans AppState.")
        self.state.select_graph(name)
        print(f"🎯 [GraphService.select_graph] Graphique sélectionné : {self.state.current_graph.name if self.state.current_graph else 'None'}")
        print(f"📢 [GraphService.select_graph] Emission du signal graph_selected")
        #signal_bus.graph_selected.emit(name)
    
    def select_curve(self, curve_name: str):
        print(f"🖱 [GraphService.select_curve] Sélection de la courbe : {curve_name}")
        self.state.select_curve(curve_name)

    def rename_graph(self, old_name: str, new_name: str):
        print(f"✏️ [GraphService.rename_graph] Renommage du graphique : {old_name} → {new_name}")
        self.state.rename_graph(old_name, new_name)

    def rename_curve(self, old_name: str, new_name: str):
        print(f"✏️ [GraphService.rename_curve] Renommage de courbe : {old_name} → {new_name}")
        graph = self.state.current_graph
        if not graph:
            print("⚠️ [GraphService.rename_curve] Aucun graphique sélectionné !")
            raise ValueError("Aucun graphique sélectionné")

        if any(c.name == new_name for c in graph.curves):
            print(f"❌ [GraphService.rename_curve] Une courbe nommée '{new_name}' existe déjà.")
            raise ValueError(f"Une courbe nommée '{new_name}' existe déjà.")

        for curve in graph.curves:
            if curve.name == old_name:
                print(f"🔁 [GraphService.rename_curve] Mise à jour du nom dans le modèle")
                curve.name = new_name
                return

        print(f"❌ [GraphService.rename_curve] Courbe '{old_name}' non trouvée")
        raise ValueError(f"Courbe '{old_name}' introuvable dans le graphique courant")

    def add_graph(self, name: str = None):
        print(f"📥 [GraphService.add_graph] Appel avec nom = {name}")
    
        if not name or name.strip() == "":
            name = get_next_graph_name()
            print(f"🆕 [GraphService.add_graph] Nom généré automatiquement : {name}")
        else:
            print(f"🏷️ [GraphService.add_graph] Nom spécifié : {name}")
    
        if name in self.state.graphs:
            print(f"❌ [GraphService.add_graph] Le graphique '{name}' existe déjà !")
            raise ValueError(f"Le graphique '{name}' existe déjà.")
    
        self.state.graphs[name] = GraphData(name)
        self.state.current_graph = self.state.graphs[name]
    
        print(f"✅ [GraphService.add_graph] Graphique '{name}' ajouté dans AppState.")
        print(f"🔎 [GraphService.add_graph] État courant après ajout :")
        print(f"    - Graphiques : {list(self.state.graphs.keys())}")
        print(f"    - Graphique actif : {self.state.current_graph.name}")    
        
        # 👇 Signaler qu’un graphique a été sélectionné (utile pour afficher les propriétés)
        print(f"📢 [GraphService.add_graph] Emission du signal graph_selected pour '{name}'")
        signal_bus.graph_selected.emit(name)
    
        print(f"📢 [GraphService.add_graph] Emission du signal graph_updated")
        signal_bus.graph_updated.emit()


    def add_curve(self, graph_name: str, curve: CurveData = None):
        graph = self.state.graphs.get(graph_name)
        if not graph:
            print(f"❌ [GraphService.add_curve] Graphique '{graph_name}' introuvable dans AppState")
            return
    
        print(f"🧩 [GraphService.add_curve] Graphique trouvé → {graph.name}")
        print(f"📊 [GraphService.add_curve] Courbes existantes : {[c.name for c in graph.curves]}")    
        
        existing_names = [c.name for c in graph.curves]
        index = 1
        while f"Courbe {index}" in existing_names:
            index += 1
        curve_name = f"Courbe {index}"
    
        if curve is None:
            print(f"🔧 [GraphService.add_curve] Génération d'une courbe vide nommée '{curve_name}'")
            curve = CurveData(name=curve_name)
        else:
            print(f"📥 [GraphService.add_curve] Courbe fournie nommée '{curve.name}', renommée '{curve_name}'")
            curve.name = curve_name
    
        graph.curves.append(curve)
        self.state.current_graph = graph
        self.state.current_curve = curve
    
        print(f"🔎 [GraphService.add_curve] État après ajout de courbe :")
        print(f"    - Courbes du graphique '{graph.name}' : {[c.name for c in graph.curves]}")
        print(f"    - Courbe courante : {self.state.current_curve.name if self.state.current_curve else 'None'}")
    
        # 👇 Sélectionne automatiquement la courbe ajoutée
        print(f"📢 [GraphService.add_curve] Emission du signal curve_selected pour '{curve.name}' dans '{graph.name}'")
        signal_bus.curve_selected.emit(graph.name, curve.name)
    
        print(f"📢 [GraphService.add_curve] Emission des signaux curve_list_updated et curve_updated")
        signal_bus.curve_list_updated.emit()
        signal_bus.curve_updated.emit()
            

    def remove_graph(self, name: str):
        print(f"🗑 [GraphService.remove_graph] Suppression du graphique '{name}'")
        if name not in self.state.graphs:
            print(f"❌ [GraphService.remove_graph] Graphique '{name}' introuvable")
            raise KeyError(f"Le graphique '{name}' n'existe pas.")
        del self.state.graphs[name]
        print(f"✅ [GraphService.remove_graph] Supprimé")
        if self.state.current_graph and self.state.current_graph.name == name:
            print("🔄 [GraphService.remove_graph] Réinitialisation de current_graph et current_curve")
            self.state.current_graph = None
            self.state.current_curve = None
            
        print(f"📢 [GraphService.remove_graph] Emission du signal graph_updated")
        signal_bus.graph_updated.emit()

            
    def remove_curve(self, curve_name: str):
        graph = self.state.current_graph
        if not graph:
            print("❌ [GraphService.remove_curve] Aucun graphique sélectionné.")
            return
    
        print(f"🗑 [GraphService.remove_curve] Suppression de la courbe '{curve_name}' dans le graphique '{graph.name}'")
    
        curve_to_remove = next((c for c in graph.curves if c.name == curve_name), None)
        if not curve_to_remove:
            print(f"❌ [GraphService.remove_curve] Courbe '{curve_name}' introuvable.")
            return
    
        graph.curves.remove(curve_to_remove)
        if self.state.current_curve == curve_to_remove:
            self.state.current_curve = None
    
        print(f"✅ [GraphService.remove_curve] Courbe '{curve_name}' supprimée.")
        print(f"📢 [GraphService.remove_curve] Emission du signal curve_updated")
        signal_bus.curve_updated.emit()


    def import_graph(self, graph_data: GraphData):
        print(f"📥 [GraphService.import_graph] Import du graphique '{graph_data.name}'")
        self.state.graphs[graph_data.name] = graph_data

    def bring_curve_to_front(self):
        print(f"🔝 [GraphService.bring_curve_to_front] Remonter la courbe courante en tête")
        graph = self.state.current_graph
        curve = self.state.current_curve
        if not graph or not curve:
            print("⚠️ [GraphService.bring_curve_to_front] Aucune courbe ou graphique sélectionné")
            return
        if curve in graph.curves:
            graph.curves.remove(curve)
            graph.curves.insert(0, curve)
            print(f"✅ [GraphService.bring_curve_to_front] Courbe '{curve.name}' déplacée en tête")

    # ----- Méthodes métier explicites sur les courbes -----
    def set_opacity(self, value: float):
        print(f"🎨 [GraphService.set_opacity] Opacité = {value}")
        if self.state.current_curve:
            self.state.current_curve.opacity = value

    def set_gain(self, value: float):
        print(f"🔊 [GraphService.set_gain] Gain = {value}")
        if self.state.current_curve:
            self.state.current_curve.gain = value

    def set_offset(self, value: float):
        print(f"📏 [GraphService.set_offset] Offset = {value}")
        if self.state.current_curve:
            self.state.current_curve.offset = value

    def set_style(self, style: int):
        print(f"🖌 [GraphService.set_style] Style = {style}")
        if self.state.current_curve:
            self.state.current_curve.style = style

    def set_symbol(self, symbol: str):
        print(f"🔣 [GraphService.set_symbol] Symbole = {symbol}")
        if self.state.current_curve:
            self.state.current_curve.symbol = symbol

    def set_fill(self, fill: bool):
        print(f"🧱 [GraphService.set_fill] Remplissage = {fill}")
        if self.state.current_curve:
            self.state.current_curve.fill = fill

    def set_display_mode(self, mode: str):
        print(f"🖥 [GraphService.set_display_mode] Mode d'affichage = {mode}")
        if self.state.current_curve:
            self.state.current_curve.display_mode = mode

    def set_label_mode(self, mode: str):
        print(f"🏷 [GraphService.set_label_mode] Mode d’étiquetage = {mode}")
        if self.state.current_curve:
            self.state.current_curve.label_mode = mode

    def set_zero_indicator(self, mode: str):
        print(f"🎯 [GraphService.set_zero_indicator] Indicateur zéro = {mode}")
        if self.state.current_curve:
            self.state.current_curve.zero_indicator = mode

    def set_color(self, color: str):
        print(f"🌈 [GraphService.set_color] Couleur = {color}")
        if self.state.current_curve:
            self.state.current_curve.color = color

    def set_show_label(self, visible: bool):
        print(f"👁 [GraphService.set_show_label] Étiquette visible = {visible}")
        if self.state.current_curve:
            self.state.current_curve.show_label = visible
