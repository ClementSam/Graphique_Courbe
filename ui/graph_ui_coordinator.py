# ui/graph_ui_coordinator.py

from core.app_state import AppState
from ui.views import MyPlotView
from ui.PropertiesPanel import PropertiesPanel
import logging

logger = logging.getLogger(__name__)


class GraphUICoordinator:
    def __init__(self, state: AppState, views: dict, central_area, properties_panel: PropertiesPanel | None = None):
        logger.debug("[GraphUICoordinator.__init__] Initialisation")
        self.state = state
        self.views = views
        self.central_area = central_area  # 🆕 pour gérer dynamiquement les widgets
        self.properties_panel = properties_panel
        logger.debug(f"[GraphUICoordinator.__init__] Vues disponibles : {list(self.views.keys())}")
        
    def refresh_curve_ui(self):
        logger.debug("[graph_ui_coordinator > refresh_curve_ui()] ▶️ Rafraîchissement des propriétés de courbe")
        if self.state.current_curve:
            logger.debug(f"🔍 Courbe courante : {self.state.current_curve.name}")
        else:
            logger.debug("ℹ️ Aucune courbe sélectionnée")

        if self.properties_panel:
            self.properties_panel.update_curve_ui()

    def refresh_plot(self):
        logger.debug("\n[GraphUICoordinator.refresh_plot] ▶️ Début du rafraîchissement des graphes")
        logger.debug(f"[refresh_plot] Graphiques connus dans l'état : {list(self.state.graphs.keys())}")
        #logger.debug(f"📌 [refresh_plot] Vérification de la vue pour : {name}")
        
        # 🔄 Création des vues manquantes
        for name, graph in self.state.graphs.items():
            logger.debug(f"📌 [refresh_plot] Vérification de la vue pour : {name}")
            if name not in self.views:
                logger.debug(f"🆕 [refresh_plot] Création de la vue pour le graphique : {name}")
                view = MyPlotView(graph)
                self.views[name] = view
                if self.central_area:
                    logger.debug(f"📤 [refresh_plot] Tentative d’ajout du widget à la zone centrale")
                    self.central_area.add_plot_widget(view.container)
                    logger.debug(f"✅ Widget ajouté à la zone centrale pour : {name}")
            else:
                logger.debug(f"♻️ [refresh_plot] Mise à jour de la vue existante : {name}")
                self.views[name].graph_data = graph
        
        # 🧹 Suppression des vues obsolètes
        to_remove = [name for name in self.views if name not in self.state.graphs]
        for name in to_remove:
            logger.debug(f"🗑️ [refresh_plot] Suppression de la vue orpheline : {name}")
            view = self.views[name]
            if self.central_area:
                self.central_area.remove_plot_widget(view.container)
                logger.debug(f"🗑️ Widget retiré de la zone centrale : {name}")
            del self.views[name]

        # 🔁 Mise à jour de toutes les vues visibles
        for name, view in self.views.items():
            logger.debug(f"🔄 [refresh_plot] Mise à jour de : {name}")
            graph = self.state.graphs.get(name)
            if not graph:
                logger.debug(f"⚠️ [refresh_plot] Graphique '{name}' absent de l'état malgré la vue.")
                continue
            view.graph_data = graph
            view.container.set_graph_name(graph.name)
            logger.debug(f"🔧 [refresh_plot] Appel de update_graph_properties() pour : {name}")
            view.update_graph_properties()
            logger.debug(f"🔄 [refresh_plot] Appel de refresh_curves() pour : {name}")
            view.refresh_curves()
            view.refresh_satellites()
            logger.debug(f"✅ [refresh_plot] Vue mise à jour : {name}")
            
    def reset_zoom(self):
        logger.debug("[graph_ui_coordinator > reset_zoom()] ▶️ Réinitialisation du zoom sur toutes les vues")
        for name, view in self.views.items():
            logger.debug(f"  🔍 [reset_zoom] Vue : {name}")
            view.reset_zoom()

    def reset_zoom_x(self):
        logger.debug("[graph_ui_coordinator > reset_zoom_x()] ▶️ Réinitialisation du zoom X")
        for name, view in self.views.items():
            view.reset_zoom_x()

    def reset_zoom_y(self):
        logger.debug("[graph_ui_coordinator > reset_zoom_y()] ▶️ Réinitialisation du zoom Y")
        for name, view in self.views.items():
            view.reset_zoom_y()
