# core/app_state.py

from core.models import GraphData, CurveData
import logging

logger = logging.getLogger(__name__)


class AppState:
    """
    Singleton centralisant l'état global de l'application (graphes et courbes).
    Utiliser AppState.get_instance() pour accéder à l'instance.
    """

    _instance = None

    def __init__(self):
        if AppState._instance is not None:
            raise RuntimeError("Utiliser AppState.get_instance() au lieu d'instancier directement.")
        self.graphs: dict[str, GraphData] = {}
        self.current_graph: GraphData | None = None
        self.current_curve: CurveData | None = None
        AppState._instance = self
        logger.debug("🧠 [AppState.__init__] Nouvelle instance créée")

    @staticmethod
    def get_instance() -> "AppState":
        if AppState._instance is None:
            logger.debug("🔁 [AppState.get_instance] Instance inexistante, création...")
            AppState()
        else:
            logger.debug("📦 [AppState.get_instance] Instance existante récupérée")
        return AppState._instance

    # ----- Gestion des graphes -----

    def add_graph(self, name: str):
        logger.debug(f"➕ [AppState.add_graph] Tentative d'ajout du graphique '{name}'")
        if name in self.graphs:
            logger.warning(f"⛔️ [AppState.add_graph] Graphique '{name}' déjà présent !")
            raise ValueError(f"Le graphique '{name}' existe déjà.")
        self.graphs[name] = GraphData(name)
        logger.debug(f"✅ [AppState.add_graph] Graphique '{name}' ajouté avec succès.")
        self._debug_state()

    def remove_graph(self, name: str):
        logger.warning(f"❌ [AppState.remove_graph] Suppression du graphique '{name}'")
        if name not in self.graphs:
            raise KeyError(f"Le graphique '{name}' n'existe pas.")
        del self.graphs[name]
        if self.current_graph and self.current_graph.name == name:
            logger.warning(f"⚠️ [AppState.remove_graph] Graphique supprimé était actif, nettoyage de la sélection.")
            self.current_graph = None
            self.current_curve = None
        self._debug_state()

    def rename_graph(self, old_name: str, new_name: str):
        logger.debug(f"✏️ [AppState.rename_graph] Renommage '{old_name}' -> '{new_name}'")
        if old_name not in self.graphs:
            raise KeyError(f"Le graphique '{old_name}' n'existe pas.")
        if new_name in self.graphs:
            raise ValueError(f"Le graphique '{new_name}' existe déjà.")
        graph = self.graphs.pop(old_name)
        graph.name = new_name
        self.graphs[new_name] = graph
        if self.current_graph and self.current_graph.name == old_name:
            self.current_graph = graph
        self._debug_state()

    def select_graph(self, name: str):
        logger.debug(f"🎯 [AppState.select_graph] Sélection du graphique '{name}'")
        logger.debug(f"   ➖ Avant : current_graph = {self.current_graph.name if self.current_graph else 'None'}")
        self.current_graph = self.graphs.get(name, None)
        logger.debug(f"   ➕ Après : current_graph = {self.current_graph.name if self.current_graph else 'None'}")
        self.current_curve = None
        self._debug_state()

    # ----- Gestion des courbes -----

    def select_curve(self, curve_name: str):
        logger.debug(f"🎯 [AppState.select_curve] Sélection de la courbe '{curve_name}'")
        if not self.current_graph:
            logger.warning("⚠️ [AppState.select_curve] Aucun graphique sélectionné")
            self.current_curve = None
            return
        self.current_curve = next(
            (c for c in self.current_graph.curves if c.name == curve_name),
            None
        )
        if self.current_curve:
            logger.debug(f"✅ [AppState.select_curve] Courbe sélectionnée : {self.current_curve.name}")
        else:
            logger.debug(f"❓ [AppState.select_curve] Courbe '{curve_name}' introuvable")

    def clear_selection(self):
        logger.debug("🧹 [AppState.clear_selection] Réinitialisation des sélections")
        self.current_graph = None
        self.current_curve = None

    def _debug_state(self):
        logger.debug("🔎 [AppState] État actuel :")
        logger.debug(f"   - Graphiques : {[g for g in self.graphs]}")
        logger.debug(f"   - Graphique actif : {self.current_graph.name if self.current_graph else 'None'}")
        logger.debug(f"   - Courbe active : {self.current_curve.name if self.current_curve else 'None'}")

