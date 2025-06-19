# controllers.py

from core.app_state import AppState
from core.graph_service import GraphService
from ui.graph_ui_coordinator import GraphUICoordinator
from signal_bus import signal_bus
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class GraphController:
    def __init__(self, views: dict, central_area, properties_panel=None):
        logger.debug("🧠 [GraphController.__init__] Initialisation du contrôleur")
        self.state = AppState.get_instance()
        self.service = GraphService(self.state)
        try:
            self.ui = GraphUICoordinator(
                self.state, views, central_area, properties_panel
            )
        except TypeError:
            # fallback for older coordinator stubs without properties panel
            self.ui = GraphUICoordinator(self.state, views, central_area)
            if properties_panel is not None:
                self.ui.properties_panel = properties_panel

    def load_project(self, graphs: dict):
        logger.debug("📂 [GraphController.load_project] Chargement du projet...")
        logger.debug(f"📊 [GraphController.load_project] Graphiques reçus : {list(graphs.keys())}")
        self.state.graphs = graphs
        self.state.current_graph = None
        self.state.current_curve = None
        self.ui.refresh_plot()

    def add_graph(self, name: str = None):
        logger.debug(f"➕ [GraphController.add_graph] Requête d'ajout de graphique : {name}")
        created_name = self.service.add_graph(name)
        logger.debug(f"✅ [GraphController.add_graph] Graphique '{created_name}' ajouté via service.")
        signal_bus.graph_selected.emit(created_name)
        signal_bus.graph_updated.emit()
        self.ui.refresh_plot()
        
    def add_curve(self, graph_name: str):
        logger.debug(f"➕ [GraphController.add_curve] Requête d'ajout de courbe à : {graph_name}")
        from curve_generators import generate_random_curve
        graph = self.state.graphs.get(graph_name)
        if not graph:
            logger.debug(f"❌ [GraphController.add_curve] Graphique introuvable : {graph_name}")
            return
    
        existing_names = [c.name for c in graph.curves]
        index = 1
        while f"Courbe {index}" in existing_names:
            index += 1
    
        curve = generate_random_curve(index)
        created_curve_name = self.service.add_curve(graph_name, curve)
        logger.debug(f"✅ [GraphController.add_curve] Courbe '{created_curve_name}' ajoutée à '{graph_name}'")
        signal_bus.curve_selected.emit(graph_name, created_curve_name)
        signal_bus.curve_list_updated.emit()
        signal_bus.curve_updated.emit()
        self.ui.refresh_plot()

    def select_graph(self, name: str):
        logger.debug(f"🎯 [GraphController.select_graph] Sélection du graphique : {name}")
        self.service.select_graph(name)
        logger.debug(
            f"   ➡️ Graphique courant : {self.state.current_graph.name if self.state.current_graph else 'None'}"
        )
        self.ui.refresh_plot()

    def select_curve(self, curve_name: str):
        logger.debug(f"🎯 [GraphController.select_curve] Sélection de la courbe : {curve_name}")
        self.service.select_curve(curve_name)
        logger.debug(
            f"   ➡️ Courbe courante : {self.state.current_curve.name if self.state.current_curve else 'None'}"
        )
        self.ui.refresh_curve_ui()

    def remove_graph(self, name: str):
        logger.debug(f"🗑 [GraphController.remove_graph] Suppression du graphique : {name}")
        self.service.remove_graph(name)
        signal_bus.graph_updated.emit()
        self.ui.refresh_plot()
        
    def remove_curve(self, name: str):
        logger.debug(f"🗑 [GraphController.remove_curve] Suppression de la courbe : {name}")
        self.service.remove_curve(name)
        signal_bus.curve_updated.emit()
        self.ui.refresh_curve_ui()

    def rename_graph(self, old_name: str, new_name: str):
        logger.debug(f"✏️ [GraphController.rename_graph] Renommage graphique : {old_name} → {new_name}")
        self.service.rename_graph(old_name, new_name)
        self.ui.refresh_plot()

    def rename_curve(self, old_name: str, new_name: str):
        logger.debug(f"✏️ [GraphController.rename_curve] Renommage courbe : {old_name} → {new_name}")
        self.service.rename_curve(old_name, new_name)
        self.ui.refresh_curve_ui()

    def import_graph(self, graph_data):
        logger.debug(f"📥 [GraphController.import_graph] Import du graphique : {graph_data.name}")
        self.service.import_graph(graph_data)
        self.ui.refresh_plot()

    def create_bit_curves(self, curve_name: str, bit_count: Optional[int] = None):
        logger.debug(f"🔬 [GraphController.create_bit_curves] Decomposition de {curve_name} en {bit_count or 'auto'} bits")
        names = self.service.create_bit_curves(curve_name, bit_count)
        signal_bus.curve_list_updated.emit()
        signal_bus.curve_updated.emit()
        self.ui.refresh_plot()
        return names

    def create_bit_group_curve(
        self, curve_name: str, bit_indices: list[int], group_name: Optional[str] = None
    ):
        logger.debug(
            f"🔬 [GraphController.create_bit_group_curve] Groupe {bit_indices} pour {curve_name}"
        )
        name = self.service.create_bit_group_curve(curve_name, bit_indices, group_name)
        signal_bus.curve_list_updated.emit()
        signal_bus.curve_updated.emit()
        self.ui.refresh_plot()
        return name

    def bring_curve_to_front(self):
        logger.debug("🔝 [GraphController.bring_curve_to_front] Priorisation de la courbe")
        self.service.bring_curve_to_front()
        self.ui.refresh_plot()

    # ----- Paramètres du graphique -----
    def set_grid_visible(self, visible: bool):
        logger.debug(f"📐 [GraphController.set_grid_visible] {visible}")
        self.service.set_grid_visible(visible)
        signal_bus.graph_updated.emit()
        self.ui.refresh_plot()

    def set_dark_mode(self, enabled: bool):
        logger.debug(f"🌒 [GraphController.set_dark_mode] {enabled}")
        self.service.set_dark_mode(enabled)
        signal_bus.graph_updated.emit()
        self.ui.refresh_plot()

    def set_log_x(self, enabled: bool):
        logger.debug(f"📈 [GraphController.set_log_x] {enabled}")
        self.service.set_log_x(enabled)
        signal_bus.graph_updated.emit()
        self.ui.refresh_plot()

    def set_log_y(self, enabled: bool):
        logger.debug(f"📉 [GraphController.set_log_y] {enabled}")
        self.service.set_log_y(enabled)
        signal_bus.graph_updated.emit()
        self.ui.refresh_plot()

    def set_x_unit(self, unit: str):
        logger.debug(f"📏 [GraphController.set_x_unit] {unit}")
        self.service.set_x_unit(unit)
        signal_bus.graph_updated.emit()
        self.ui.refresh_plot()

    def set_y_unit(self, unit: str):
        logger.debug(f"📏 [GraphController.set_y_unit] {unit}")
        self.service.set_y_unit(unit)
        signal_bus.graph_updated.emit()
        self.ui.refresh_plot()

    def set_x_format(self, fmt: str):
        logger.debug(f"🔢 [GraphController.set_x_format] {fmt}")
        self.service.set_x_format(fmt)
        signal_bus.graph_updated.emit()
        self.ui.refresh_plot()

    def set_y_format(self, fmt: str):
        logger.debug(f"🔢 [GraphController.set_y_format] {fmt}")
        self.service.set_y_format(fmt)
        signal_bus.graph_updated.emit()
        self.ui.refresh_plot()

    def set_fix_y_range(self, fix: bool):
        logger.debug(f"📊 [GraphController.set_fix_y_range] {fix}")
        self.service.set_fix_y_range(fix)
        signal_bus.graph_updated.emit()
        self.ui.refresh_plot()

    def set_y_limits(self, y_min: float, y_max: float):
        logger.debug(f"📉 [GraphController.set_y_limits] {y_min} → {y_max}")
        self.service.set_y_limits(y_min, y_max)
        signal_bus.graph_updated.emit()
        self.ui.refresh_plot()

    def set_satellite_content(self, zone: str, content: str | None):
        logger.debug(
            f"🛰 [GraphController.set_satellite_content] zone={zone} content={content}"
        )
        self.service.set_satellite_content(zone, content)
        signal_bus.graph_updated.emit()
        self.ui.refresh_plot()

    def set_satellite_visible(self, zone: str, visible: bool):
        logger.debug(
            f"🛰 [GraphController.set_satellite_visible] zone={zone} visible={visible}"
        )
        self.service.set_satellite_visible(zone, visible)
        signal_bus.graph_updated.emit()
        self.ui.refresh_plot()

    def set_satellite_color(self, zone: str, color: str):
        logger.debug(
            f"🛰 [GraphController.set_satellite_color] zone={zone} color={color}"
        )
        self.service.set_satellite_color(zone, color)
        signal_bus.graph_updated.emit()
        self.ui.refresh_plot()

    def set_satellite_size(self, zone: str, size: int):
        logger.debug(
            f"🛰 [GraphController.set_satellite_size] zone={zone} size={size}"
        )
        self.service.set_satellite_size(zone, size)
        signal_bus.graph_updated.emit()
        self.ui.refresh_plot()
    
    def set_graph_visible(self, graph_name: str, visible: bool):
        logger.debug(f"👁 [GraphController.set_graph_visible] {graph_name} → {visible}")
        self.service.set_graph_visible(graph_name, visible)
        signal_bus.graph_updated.emit()
        signal_bus.curve_updated.emit()
        self.ui.refresh_plot()

    def set_curve_visible(self, graph_name: str, curve_name: str, visible: bool):
        logger.debug(f"👁 [GraphController.set_curve_visible] {curve_name} in {graph_name} → {visible}")
        self.service.set_curve_visible(graph_name, curve_name, visible)
        signal_bus.graph_updated.emit()
        signal_bus.curve_updated.emit()
        self.ui.refresh_plot()

    def set_opacity(self, value: float):
        logger.debug(f"🎨 [GraphController.set_opacity] Opacité = {value}")
        self.service.set_opacity(value)
        self.ui.refresh_curve_ui()

    def set_gain(self, value: float):
        logger.debug(f"📈 [GraphController.set_gain] Gain = {value}")
        self.service.set_gain(value)
        self.ui.refresh_curve_ui()

    def set_offset(self, value: float):
        logger.debug(f"📏 [GraphController.set_offset] Offset = {value}")
        self.service.set_offset(value)
        self.ui.refresh_curve_ui()

    def set_time_offset(self, value: float):
        logger.debug(f"⏱ [GraphController.set_time_offset] Time offset = {value}")
        self.service.set_time_offset(value)
        self.ui.refresh_curve_ui()

    def set_width(self, value: int):
        logger.debug(f"📏 [GraphController.set_width] Width = {value}")
        self.service.set_width(value)
        self.ui.refresh_curve_ui()

    def set_style(self, style: int):
        logger.debug(f"🖌 [GraphController.set_style] Style = {style}")
        self.service.set_style(style)
        self.ui.refresh_curve_ui()

    def set_symbol(self, symbol: str):
        logger.debug(f"🔣 [GraphController.set_symbol] Symbole = {symbol}")
        self.service.set_symbol(symbol)
        self.ui.refresh_curve_ui()

    def set_fill(self, fill: bool):
        logger.debug(f"🧱 [GraphController.set_fill] Remplissage = {fill}")
        self.service.set_fill(fill)
        self.ui.refresh_curve_ui()

    def set_display_mode(self, mode: str):
        logger.debug(f"🖥 [GraphController.set_display_mode] Mode d'affichage = {mode}")
        self.service.set_display_mode(mode)
        self.ui.refresh_curve_ui()

    def set_label_mode(self, mode: str):
        logger.debug(f"🏷 [GraphController.set_label_mode] Mode étiquette = {mode}")
        self.service.set_label_mode(mode)
        self.ui.refresh_curve_ui()

    def set_zero_indicator(self, mode: str):
        logger.debug(f"🎯 [GraphController.set_zero_indicator] Indicateur zéro = {mode}")
        self.service.set_zero_indicator(mode)
        self.ui.refresh_curve_ui()

    def set_color(self, color: str):
        logger.debug(f"🌈 [GraphController.set_color] Couleur = {color}")
        self.service.set_color(color)
        self.ui.refresh_curve_ui()

    def set_show_label(self, visible: bool):
        logger.debug(f"👁 [GraphController.set_show_label] Étiquette visible = {visible}")
        self.service.set_show_label(visible)
        self.ui.refresh_curve_ui()

    def apply_mode(self, graph_name: str, mode: str):
        logger.debug(f"🎛 [GraphController.apply_mode] graph={graph_name} mode={mode}")
        self.service.apply_mode(graph_name, mode)
        self.ui.refresh_plot()
        self.ui.refresh_curve_ui()

    def reset_zoom(self):
        logger.debug("🔍 [GraphController.reset_zoom] Réinitialisation du zoom")
        self.ui.reset_zoom()
