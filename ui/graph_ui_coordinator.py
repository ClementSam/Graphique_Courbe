# ui/graph_ui_coordinator.py

from core.app_state import AppState
from ui.views import MyPlotView
from ui.PropertiesPanel import PropertiesPanel
from signal_bus import SignalBus, signal_bus


class GraphUICoordinator:
    def __init__(self, state: AppState, views: dict, central_area, bus: SignalBus = signal_bus):
        print("[GraphUICoordinator.__init__] Initialisation")
        self.state = state
        self.views = views
        self.central_area = central_area  # 🆕 pour gérer dynamiquement les widgets
        self.bus = bus
        print(f"[GraphUICoordinator.__init__] Vues disponibles : {list(self.views.keys())}")
        
    def refresh_curve_ui(self):
        print("[graph_ui_coordinator > refresh_curve_ui()] ▶️ Rafraîchissement des propriétés de courbe")
        if self.state.current_curve:
            print(f"🔍 Courbe courante : {self.state.current_curve.name}")
            # ⚠️ À adapter : Assure-toi que self.properties_panel est bien défini quelque part
            if hasattr(self, 'properties_panel') and self.properties_panel:
                self.properties_panel.update_curve_ui()
        else:
            print("ℹ️ Aucune courbe sélectionnée")

    def refresh_plot(self):
        print("\n[GraphUICoordinator.refresh_plot] ▶️ Début du rafraîchissement des graphes")
        print(f"[refresh_plot] Graphiques connus dans l'état : {list(self.state.graphs.keys())}")
        #print(f"📌 [refresh_plot] Vérification de la vue pour : {name}")
        
        # 🔄 Création des vues manquantes
        for name, graph in self.state.graphs.items():
            print(f"📌 [refresh_plot] Vérification de la vue pour : {name}")
            if name not in self.views:
                print(f"🆕 [refresh_plot] Création de la vue pour le graphique : {name}")
                view = MyPlotView(graph, self.bus)
                self.views[name] = view
                if self.central_area:
                    print(f"📤 [refresh_plot] Tentative d’ajout du widget à la zone centrale")
                    self.central_area.add_plot_widget(view.plot_widget)
                    print(f"✅ Widget ajouté à la zone centrale pour : {name}")
            else:
                print(f"♻️ [refresh_plot] Mise à jour de la vue existante : {name}")
                self.views[name].graph_data = graph
        
        # 🧹 Suppression des vues obsolètes
        to_remove = [name for name in self.views if name not in self.state.graphs]
        for name in to_remove:
            print(f"🗑️ [refresh_plot] Suppression de la vue orpheline : {name}")
            view = self.views[name]
            if self.central_area:
                self.central_area.remove_plot_widget(view.plot_widget)
                print(f"🗑️ Widget retiré de la zone centrale : {name}")
            del self.views[name]

        # 🔁 Mise à jour de toutes les vues visibles
        for name, view in self.views.items():
            print(f"🔄 [refresh_plot] Mise à jour de : {name}")
            graph = self.state.graphs.get(name)
            if not graph:
                print(f"⚠️ [refresh_plot] Graphique '{name}' absent de l'état malgré la vue.")
                continue
            view.graph_data = graph
            print(f"🔧 [refresh_plot] Appel de update_graph_properties() pour : {name}")
            view.update_graph_properties()
            print(f"🔄 [refresh_plot] Appel de refresh_curves() pour : {name}")
            view.refresh_curves()
            print(f"✅ [refresh_plot] Vue mise à jour : {name}")
            
    def reset_zoom(self):
        print("[graph_ui_coordinator > reset_zoom()] ▶️ Réinitialisation du zoom sur toutes les vues")
        for name, view in self.views.items():
            print(f"  🔍 [reset_zoom] Vue : {name}")
            view.reset_zoom()
