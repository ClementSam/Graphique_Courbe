# core/startup.py
from core.app_state import AppState
from controllers import GraphController
from core.graph_service import GraphService
from ui.graph_ui_coordinator import GraphUICoordinator
from datetime import datetime
import sys
from PyQt5 import QtWidgets

def initialize_application(center_area_widget):
    state = AppState.get_instance()
    default_graph_name = "Graphique"
    graph_service = GraphService(state)
    graph_service.add_graph(default_graph_name)
    
    # Prépare les vues associées
    from ui.views import MyPlotView
    
    graph = state.graphs[default_graph_name]
    plot_view = MyPlotView(graph)
    center_area_widget.add_plot_widget(plot_view.plot_widget)
    
    views = {default_graph_name: plot_view}
    controller = GraphController(views)

    return controller, plot_view


def check_expiry_date():
    expiry = datetime(2025, 6, 30)
    if datetime.now() > expiry:
        QtWidgets.QMessageBox.critical(
            None,
            "Accès expiré",
            f"Cette version a expiré le {expiry.strftime('%d/%m/%Y')}. Veuillez contacter l’auteur."
        )
        sys.exit(0)
