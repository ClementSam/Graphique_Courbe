# core/graph_service.py

from core.app_state import AppState
from core.models import GraphData, CurveData
from core.utils.naming import get_next_graph_name, get_unique_curve_name
from core.utils import generate_random_color
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def apply_logic_analyzer_layout(graph: GraphData) -> None:
    """Position curves like a logic analyzer view and add background zones."""

    # Clear any previously defined zones so we start from a clean state
    graph.zones.clear()

    offset = 0
    curve_offset = 0.05
    for curve in reversed(graph.curves):
        if not curve.visible:
            continue

        # Apply consistent gain and offset for logic analyzer readability
        curve.gain_mode = "multiplier"
        curve.gain = 0.9
        curve.units_per_grid = 1.0 / 0.9
        curve.offset = offset + curve_offset

        # Alternate background colors for each curve lane
        fill = "#eeeeee" if offset % 2 == 0 else "#dddddd"
        graph.zones.append(
            {
                "type": "hlinear",
                "bounds": [offset, offset + 1],
                "fill_color": fill,
                "fill_alpha": 50,
                "line_color": "#000000",
                "line_alpha": 100,
                "line_width": 1,
            }
        )

        offset += 1


class GraphService:
    """
    Fournit les opérations métier sur les graphes et courbes,
    indépendamment de l'interface utilisateur.
    """

    def __init__(self, state: AppState):
        logger.debug("🧠 [GraphService.__init__] Initialisation du service avec AppState")
        self.state = state

    def select_graph(self, name: str):
        logger.debug(f"🖱 [GraphService.select_graph] Sélection du graphique : {name}")
        if name not in self.state.graphs:
            logger.debug(f"❌ [GraphService.select_graph] Graphique '{name}' introuvable dans AppState.")
        self.state.select_graph(name)
        logger.debug(f"🎯 [GraphService.select_graph] Graphique sélectionné : {self.state.current_graph.name if self.state.current_graph else 'None'}")
    
    def select_curve(self, curve_name: str):
        logger.debug(f"🖱 [GraphService.select_curve] Sélection de la courbe : {curve_name}")
        self.state.select_curve(curve_name)
        logger.debug(
            f"🔎 [GraphService.select_curve] Courbe active : {self.state.current_curve.name if self.state.current_curve else 'None'}"
        )

    def rename_graph(self, old_name: str, new_name: str):
        logger.debug(f"✏️ [GraphService.rename_graph] Renommage du graphique : {old_name} → {new_name}")
        self.state.rename_graph(old_name, new_name)

    def rename_curve(self, old_name: str, new_name: str):
        logger.debug(f"✏️ [GraphService.rename_curve] Renommage de courbe : {old_name} → {new_name}")
        graph = self.state.current_graph
        if not graph:
            logger.debug("⚠️ [GraphService.rename_curve] Aucun graphique sélectionné !")
            raise ValueError("Aucun graphique sélectionné")

        if any(c.name == new_name for c in graph.curves):
            logger.debug(f"❌ [GraphService.rename_curve] Une courbe nommée '{new_name}' existe déjà.")
            raise ValueError(f"Une courbe nommée '{new_name}' existe déjà.")

        for curve in graph.curves:
            if curve.name == old_name:
                logger.debug(f"🔁 [GraphService.rename_curve] Mise à jour du nom dans le modèle")
                curve.name = new_name
                return

        logger.debug(f"❌ [GraphService.rename_curve] Courbe '{old_name}' non trouvée")
        raise ValueError(f"Courbe '{old_name}' introuvable dans le graphique courant")

    def add_graph(self, name: str = None):
        logger.debug(f"📥 [GraphService.add_graph] Appel avec nom = {name}")
    
        if not name or name.strip() == "":
            name = get_next_graph_name()
            logger.debug(f"🆕 [GraphService.add_graph] Nom généré automatiquement : {name}")
        else:
            logger.debug(f"🏷️ [GraphService.add_graph] Nom spécifié : {name}")
    
        if name in self.state.graphs:
            logger.debug(f"❌ [GraphService.add_graph] Le graphique '{name}' existe déjà !")
            raise ValueError(f"Le graphique '{name}' existe déjà.")
    
        self.state.graphs[name] = GraphData(name)
        self.state.current_graph = self.state.graphs[name]
    
        logger.debug(f"✅ [GraphService.add_graph] Graphique '{name}' ajouté dans AppState.")
        logger.debug(f"🔎 [GraphService.add_graph] État courant après ajout :")
        logger.debug(f"    - Graphiques : {list(self.state.graphs.keys())}")
        logger.debug(f"    - Graphique actif : {self.state.current_graph.name}")    
        
        # Le contrôleur d'interface se chargera d'émettre les signaux appropriés
        # après la création du graphique.

        return name


    def add_curve(self, graph_name: str, curve: CurveData = None):
        graph = self.state.graphs.get(graph_name)
        if not graph:
            logger.debug(f"❌ [GraphService.add_curve] Graphique '{graph_name}' introuvable dans AppState")
            return
    
        logger.debug(f"🧩 [GraphService.add_curve] Graphique trouvé → {graph.name}")
        logger.debug(f"📊 [GraphService.add_curve] Courbes existantes : {[c.name for c in graph.curves]}")    
        
        existing_names = [c.name for c in graph.curves]

        if curve is None:
            # When no curve data is provided, create a new one with an
            # automatically generated name "Courbe X" that does not collide
            # with existing names.
            index = 1
            while f"Courbe {index}" in existing_names:
                index += 1
            curve_name = f"Courbe {index}"
            logger.debug(
                f"🔧 [GraphService.add_curve] Génération d'une courbe vide nommée '{curve_name}'"
            )
            curve = CurveData(name=curve_name, color=generate_random_color())
        else:
            # Keep the provided curve name when importing. If it already exists
            # in the target graph, append " (x)" where x is the smallest index
            # making the name unique.
            base_name = curve.name or "Courbe"
            curve_name = get_unique_curve_name(base_name, set(existing_names))
            logger.debug(
                f"📥 [GraphService.add_curve] Courbe fournie nommée '{curve.name}', renommée '{curve_name}'"
            )
            curve.name = curve_name
            if curve.color.lower() in {"#000000", "black", "#ffffff", "white", "b", "w"}:
                curve.color = generate_random_color()
    
        graph.curves.append(curve)
        self.state.current_graph = graph
        self.state.current_curve = curve
    
        logger.debug(f"🔎 [GraphService.add_curve] État après ajout de courbe :")
        logger.debug(f"    - Courbes du graphique '{graph.name}' : {[c.name for c in graph.curves]}")
        logger.debug(f"    - Courbe courante : {self.state.current_curve.name if self.state.current_curve else 'None'}")
    
        # Le contrôleur d'interface émettra les signaux nécessaires

        return curve_name
            

    def remove_graph(self, name: str):
        logger.debug(f"🗑 [GraphService.remove_graph] Suppression du graphique '{name}'")
        if name not in self.state.graphs:
            logger.debug(f"❌ [GraphService.remove_graph] Graphique '{name}' introuvable")
            raise KeyError(f"Le graphique '{name}' n'existe pas.")
        del self.state.graphs[name]
        logger.debug(f"✅ [GraphService.remove_graph] Supprimé")
        if self.state.current_graph and self.state.current_graph.name == name:
            logger.debug("🔄 [GraphService.remove_graph] Réinitialisation de current_graph et current_curve")
            self.state.current_graph = None
            self.state.current_curve = None
            
        # Les signaux d'interface seront émis par le contrôleur

        return name

            
    def remove_curve(self, curve_name: str):
        graph = self.state.current_graph
        if not graph:
            logger.debug("❌ [GraphService.remove_curve] Aucun graphique sélectionné.")
            return
    
        logger.debug(f"🗑 [GraphService.remove_curve] Suppression de la courbe '{curve_name}' dans le graphique '{graph.name}'")
    
        curve_to_remove = next((c for c in graph.curves if c.name == curve_name), None)
        if not curve_to_remove:
            logger.debug(f"❌ [GraphService.remove_curve] Courbe '{curve_name}' introuvable.")
            return
    
        graph.curves.remove(curve_to_remove)
        if self.state.current_curve == curve_to_remove:
            self.state.current_curve = None
    
        logger.debug(f"✅ [GraphService.remove_curve] Courbe '{curve_name}' supprimée.")

        # Les signaux seront émis par la couche contrôleur

        return curve_name


    def import_graph(self, graph_data: GraphData):
        logger.debug(f"📥 [GraphService.import_graph] Import du graphique '{graph_data.name}'")
        self.state.graphs[graph_data.name] = graph_data

    def bring_curve_to_front(self):
        logger.debug(f"🔝 [GraphService.bring_curve_to_front] Remonter la courbe courante en tête")
        graph = self.state.current_graph
        curve = self.state.current_curve
        if not graph or not curve:
            logger.debug("⚠️ [GraphService.bring_curve_to_front] Aucune courbe ou graphique sélectionné")
            return
        if curve in graph.curves:
            graph.curves.remove(curve)
            graph.curves.append(curve)
            logger.debug(f"✅ [GraphService.bring_curve_to_front] Courbe '{curve.name}' déplacée en tête")

    def create_bit_curves(self, curve_name: str, bit_count: Optional[int] = None) -> list[str]:
        """Generate bit curves from the given curve.

        Parameters
        ----------
        curve_name: str
            Name of the curve to decompose.
        bit_count: int | None
            Number of bits to generate. If ``None``, the minimal bit width able
            to represent all values is used.
        Returns
        -------
        list[str]
            Names of the created curves in order from LSB to MSB.
        """
        graph = self.state.current_graph
        if not graph:
            raise ValueError("Aucun graphique sélectionné")

        curve = next((c for c in graph.curves if c.name == curve_name), None)
        if not curve:
            raise ValueError(f"Courbe '{curve_name}' introuvable")

        import numpy as np

        values = curve.y
        mask = np.isnan(values)
        finite_values = values[~mask]

        if not np.allclose(finite_values, np.round(finite_values)):
            raise ValueError("Les données ne sont pas entières")

        if finite_values.size:
            max_val = int(finite_values.max())
            min_val = int(finite_values.min())
        else:
            max_val = 0
            min_val = 0

        if min_val < 0:
            raise ValueError("Les valeurs négatives ne sont pas prises en charge")

        values_int = np.nan_to_num(values, nan=0).astype(np.int64)
        min_bits = max(max_val.bit_length(), 1)

        if bit_count is None:
            bit_count = min_bits
        else:
            if max_val >= 2 ** bit_count:
                raise ValueError("La plage de valeurs dépasse le nombre de bits spécifié")

        bits = ((values_int[:, None] >> np.arange(bit_count)) & 1).astype(float)
        bits[mask, :] = np.nan

        from core.utils.naming import get_unique_curve_name
        existing = {c.name for c in graph.curves}
        insert_index = graph.curves.index(curve) + 1
        created = []

        for i in range(bit_count):
            base_name = f"{curve.name}[{i}]"
            name = get_unique_curve_name(base_name, existing)
            existing.add(name)
            bit_curve = CurveData(
                name=name,
                x=curve.x.copy(),
                y=bits[:, i],
                color=curve.color,
                width=curve.width,
                style=curve.style,
            )
            bit_curve.bit_index = i
            bit_curve.parent_curve = curve.name
            graph.curves.insert(insert_index, bit_curve)
            insert_index += 1
            created.append(name)

        return created

    def create_bit_group_curve(
        self, curve_name: str, bit_indices: list[int], group_name: Optional[str] = None
    ) -> str:
        """Generate a grouped bit curve using *bit_indices*.

        The resulting curve represents the integer value composed of the
        specified bits, ordered from LSB to MSB according to ``bit_indices``.

        Parameters
        ----------
        curve_name: str
            Name of the source curve.
        bit_indices: list[int]
            Indices of the bits to combine (e.g. ``[0, 1, 2]``).
        group_name: str | None
            If provided, use this as base name for the new curve.
        Returns
        -------
        str
            Name of the created curve.
        """
        graph = self.state.current_graph
        if not graph:
            raise ValueError("Aucun graphique sélectionné")

        curve = next((c for c in graph.curves if c.name == curve_name), None)
        if not curve:
            raise ValueError(f"Courbe '{curve_name}' introuvable")

        import numpy as np

        values = curve.y
        mask = np.isnan(values)
        finite_values = values[~mask]

        if not np.allclose(finite_values, np.round(finite_values)):
            raise ValueError("Les données ne sont pas entières")

        if finite_values.size:
            max_val = int(finite_values.max())
            min_val = int(finite_values.min())
        else:
            max_val = 0
            min_val = 0

        if min_val < 0:
            raise ValueError("Les valeurs négatives ne sont pas prises en charge")

        values_int = np.nan_to_num(values, nan=0).astype(np.int64)
        needed_bits = max(max_val.bit_length(), max(bit_indices) + 1)

        bits = ((values_int[:, None] >> np.arange(needed_bits)) & 1).astype(int)

        group = np.zeros(len(values_int), dtype=float)
        for pos, idx in enumerate(bit_indices):
            group += (bits[:, idx] << pos)
        group = group.astype(float)
        group[mask] = np.nan

        from core.utils.naming import get_unique_curve_name
        existing = {c.name for c in graph.curves}
        insert_index = graph.curves.index(curve) + 1

        if group_name:
            base_name = group_name
        else:
            base_name = f"{curve.name}[{'-'.join(map(str, bit_indices))}]"
        name = get_unique_curve_name(base_name, existing)

        bit_curve = CurveData(
            name=name,
            x=curve.x.copy(),
            y=group,
            color=curve.color,
            width=curve.width,
            style=curve.style,
        )
        bit_curve.parent_curve = curve.name
        graph.curves.insert(insert_index, bit_curve)
        return name

    # ----- Méthodes métier pour les propriétés du graphique -----
    def set_grid_visible(self, visible: bool):
        logger.debug(f"📐 [GraphService.set_grid_visible] {visible}")
        if self.state.current_graph:
            self.state.current_graph.grid_visible = visible

    def set_dark_mode(self, enabled: bool):
        logger.debug(f"🌒 [GraphService.set_dark_mode] {enabled}")
        if self.state.current_graph:
            self.state.current_graph.dark_mode = enabled

    def set_log_x(self, enabled: bool):
        logger.debug(f"📈 [GraphService.set_log_x] {enabled}")
        if self.state.current_graph:
            self.state.current_graph.log_x = enabled

    def set_log_y(self, enabled: bool):
        logger.debug(f"📉 [GraphService.set_log_y] {enabled}")
        if self.state.current_graph:
            self.state.current_graph.log_y = enabled

    def set_opacity(self, value: float):
        logger.debug(f"🎨 [GraphService.set_opacity] Opacité = {value}")
        if self.state.current_curve:
            self.state.current_curve.opacity = value

    def set_gain(self, value: float):
        logger.debug(f"🔊 [GraphService.set_gain] Gain = {value}")
        c = self.state.current_curve
        if c:
            c.gain = value
            if getattr(c, "gain_mode", "multiplier") == "unit" and value != 0:
                c.units_per_grid = 1.0 / value

    def set_units_per_grid(self, value: float):
        logger.debug(f"📐 [GraphService.set_units_per_grid] units = {value}")
        c = self.state.current_curve
        if c:
            c.units_per_grid = value
            if value != 0:
                c.gain = 1.0 / value

    def set_gain_mode(self, mode: str):
        logger.debug(f"🏳️ [GraphService.set_gain_mode] mode = {mode}")
        c = self.state.current_curve
        if c:
            c.gain_mode = mode

    def set_offset(self, value: float):
        logger.debug(f"📏 [GraphService.set_offset] Offset = {value}")
        if self.state.current_curve:
            self.state.current_curve.offset = value

    def set_time_offset(self, value: float):
        logger.debug(f"⏱ [GraphService.set_time_offset] Time offset = {value}")
        if self.state.current_curve:
            self.state.current_curve.time_offset = value

    def set_width(self, value: int):
        logger.debug(f"📏 [GraphService.set_width] Width = {value}")
        if self.state.current_curve:
            self.state.current_curve.width = value

    def set_style(self, style: int):
        logger.debug(f"🖌 [GraphService.set_style] Style = {style}")
        if self.state.current_curve:
            self.state.current_curve.style = style

    def set_symbol(self, symbol: str):
        logger.debug(f"🔣 [GraphService.set_symbol] Symbole = {symbol}")
        if self.state.current_curve:
            self.state.current_curve.symbol = symbol

    def set_fill(self, fill: bool):
        logger.debug(f"🧱 [GraphService.set_fill] Remplissage = {fill}")
        if self.state.current_curve:
            self.state.current_curve.fill = fill

    def set_display_mode(self, mode: str):
        logger.debug(f"🖥 [GraphService.set_display_mode] Mode d'affichage = {mode}")
        if self.state.current_curve:
            self.state.current_curve.display_mode = mode

    def set_label_mode(self, mode: str):
        logger.debug(f"🏷 [GraphService.set_label_mode] Mode d’étiquetage = {mode}")
        if self.state.current_curve:
            self.state.current_curve.label_mode = mode

    def set_zero_indicator(self, mode: str):
        logger.debug(f"🎯 [GraphService.set_zero_indicator] Indicateur zéro = {mode}")
        if self.state.current_curve:
            self.state.current_curve.zero_indicator = mode

    def set_color(self, color: str):
        logger.debug(f"🌈 [GraphService.set_color] Couleur = {color}")
        if self.state.current_curve:
            self.state.current_curve.color = color

    def set_show_label(self, visible: bool):
        logger.debug(f"👁 [GraphService.set_show_label] Étiquette visible = {visible}")
        if self.state.current_curve:
            self.state.current_curve.show_label = visible

    def set_graph_visible(self, graph_name: str, visible: bool):
        logger.debug(f"👁 [GraphService.set_graph_visible] {graph_name} → {visible}")
        graph = self.state.graphs.get(graph_name)
        if graph:
            graph.visible = visible

    def set_curve_visible(self, graph_name: str, curve_name: str, visible: bool):
        logger.debug(f"👁 [GraphService.set_curve_visible] {curve_name} in {graph_name} → {visible}")
        graph = self.state.graphs.get(graph_name)
        if not graph:
            return
        for curve in graph.curves:
            if curve.name == curve_name:
                curve.visible = visible
                break

    # ----- Nouvelles options d'axe -----

    def set_x_unit(self, unit: str):
        logger.debug(f"📏 [GraphService.set_x_unit] unité X = {unit}")
        if self.state.current_graph:
            self.state.current_graph.x_unit = unit

    def set_y_unit(self, unit: str):
        logger.debug(f"📏 [GraphService.set_y_unit] unité Y = {unit}")
        if self.state.current_graph:
            self.state.current_graph.y_unit = unit

    def set_x_format(self, fmt: str):
        logger.debug(f"🔢 [GraphService.set_x_format] format X = {fmt}")
        if self.state.current_graph:
            self.state.current_graph.x_format = fmt

    def set_y_format(self, fmt: str):
        logger.debug(f"🔢 [GraphService.set_y_format] format Y = {fmt}")
        if self.state.current_graph:
            self.state.current_graph.y_format = fmt

    def set_auto_range_x(self, enabled: bool):
        logger.debug(f"📏 [GraphService.set_auto_range_x] {enabled}")
        if self.state.current_graph:
            self.state.current_graph.auto_range_x = enabled

    def set_auto_range_y(self, enabled: bool):
        logger.debug(f"📏 [GraphService.set_auto_range_y] {enabled}")
        if self.state.current_graph:
            self.state.current_graph.auto_range_y = enabled
            if enabled:
                self.state.current_graph.fix_y_range = False

    def set_fix_y_range(self, fix: bool):
        logger.debug(f"📊 [GraphService.set_fix_y_range] {fix}")
        if self.state.current_graph:
            self.state.current_graph.fix_y_range = fix
            self.state.current_graph.auto_range_y = not fix

    def set_y_limits(self, y_min: float, y_max: float):
        logger.debug(f"📉 [GraphService.set_y_limits] {y_min} → {y_max}")
        if self.state.current_graph:
            self.state.current_graph.y_min = y_min
            self.state.current_graph.y_max = y_max

    def set_mouse_enabled_x(self, enabled: bool):
        logger.debug(f"🖱️ [GraphService.set_mouse_enabled_x] {enabled}")
        if self.state.current_graph:
            self.state.current_graph.mouse_enabled_x = enabled

    def set_mouse_enabled_y(self, enabled: bool):
        logger.debug(f"🖱️ [GraphService.set_mouse_enabled_y] {enabled}")
        if self.state.current_graph:
            self.state.current_graph.mouse_enabled_y = enabled

    def set_satellite_content(self, zone: str, content: Optional[str]):
        """Define which widget content should appear in the given satellite zone."""
        logger.debug(
            f"🛰 [GraphService.set_satellite_content] zone={zone} content={content}"
        )
        graph = self.state.current_graph
        if not graph:
            return
        if zone in graph.satellite_content:
            graph.satellite_content[zone] = content
            if zone in graph.satellite_settings:
                graph.satellite_settings[zone].visible = bool(content)

    def set_satellite_visible(self, zone: str, visible: bool):
        logger.debug(
            f"🛰 [GraphService.set_satellite_visible] zone={zone} visible={visible}"
        )
        graph = self.state.current_graph
        if not graph:
            return
        if zone in graph.satellite_settings:
            graph.satellite_settings[zone].visible = visible

    def set_satellite_color(self, zone: str, color: str):
        logger.debug(
            f"🛰 [GraphService.set_satellite_color] zone={zone} color={color}"
        )
        graph = self.state.current_graph
        if not graph:
            return
        if zone in graph.satellite_settings:
            graph.satellite_settings[zone].color = color

    def set_satellite_size(self, zone: str, size: int):
        logger.debug(
            f"🛰 [GraphService.set_satellite_size] zone={zone} size={size}"
        )
        graph = self.state.current_graph
        if not graph:
            return
        if zone in graph.satellite_settings:
            graph.satellite_settings[zone].size = size


    def add_zone(self, zone: dict):
        """Add a graphic zone description to the current graph."""
        logger.debug(f"🗒 [GraphService.add_zone] zone={zone}")
        graph = self.state.current_graph
        if not graph:
            return
        graph.zones.append(zone)

    def update_zone(self, index: int, zone: dict):
        """Update a zone at the given index."""
        logger.debug(f"🗒 [GraphService.update_zone] index={index} zone={zone}")
        graph = self.state.current_graph
        if not graph:
            return
        if 0 <= index < len(graph.zones):
            graph.zones[index] = zone

    def remove_zone(self, index: int):
        """Remove the zone at the given index."""
        logger.debug(f"🗒 [GraphService.remove_zone] index={index}")
        graph = self.state.current_graph
        if not graph:
            return
        if 0 <= index < len(graph.zones):
            graph.zones.pop(index)

    # ------------------------------------------------------------------
    # Satellite objects management
    # ------------------------------------------------------------------
    def add_satellite_object(self, zone: str, obj):
        """Add an object description to the given satellite zone."""
        logger.debug(f"🛰 [GraphService.add_satellite_object] zone={zone} obj={obj}")
        graph = self.state.current_graph
        if not graph:
            return
        if zone in graph.satellite_objects:
            graph.satellite_objects[zone].append(obj)

    def update_satellite_object(self, zone: str, index: int, obj):
        """Replace an object at *index* in the given zone."""
        logger.debug(
            f"🛰 [GraphService.update_satellite_object] zone={zone} index={index} obj={obj}"
        )
        graph = self.state.current_graph
        if not graph:
            return
        if zone in graph.satellite_objects and 0 <= index < len(graph.satellite_objects[zone]):
            graph.satellite_objects[zone][index] = obj

    def remove_satellite_object(self, zone: str, index: int):
        """Remove object at *index* from the given zone."""
        logger.debug(
            f"🛰 [GraphService.remove_satellite_object] zone={zone} index={index}"
        )
        graph = self.state.current_graph
        if not graph:
            return
        if zone in graph.satellite_objects and 0 <= index < len(graph.satellite_objects[zone]):
            graph.satellite_objects[zone].pop(index)

    def move_satellite_object(self, zone: str, index: int, new_index: int):
        """Move object to *new_index* in the list for the zone."""
        logger.debug(
            f"🛰 [GraphService.move_satellite_object] zone={zone} index={index} → {new_index}"
        )
        graph = self.state.current_graph
        if not graph:
            return
        objs = graph.satellite_objects.get(zone)
        if objs is None or not (0 <= index < len(objs)):
            return
        obj = objs.pop(index)
        new_index = max(0, min(new_index, len(objs)))
        objs.insert(new_index, obj)

    def apply_mode(self, graph_name: str, mode: str):
        """Apply a predefined configuration to the given graph."""
        logger.debug(f"🎛 [GraphService.apply_mode] graph={graph_name} mode={mode}")
        graph = self.state.graphs.get(graph_name)
        if not graph:
            return

        graph.mode = mode

        if mode == "logic_analyzer":
            apply_logic_analyzer_layout(graph)
