# core/naming.py

from core.app_state import AppState
import logging

logger = logging.getLogger(__name__)

def get_next_graph_name():
    logger.debug("🔍 [get_next_graph_name] Début de génération de nom...")
    state = AppState.get_instance()

    if not state.graphs:
        logger.debug("📭 Aucun graphique existant, on commence à Graphique 1")
    else:
        logger.debug(f"📦 Graphiques existants : {[g.name for g in state.graphs.values()]}")

    existing_names = {g.name for g in state.graphs.values()}
    base = "Graphique"
    index = 1
    proposed_name = f"{base} {index}"

    while proposed_name in existing_names:
        logger.debug(f"⛔️ Nom déjà utilisé : {proposed_name}")
        index += 1
        proposed_name = f"{base} {index}"

    logger.debug(f"✅ Nom disponible généré : {proposed_name}")
    return proposed_name


def get_unique_curve_name(base_name: str, existing_names: set[str]) -> str:
    """Return a unique curve name based on *base_name* not present in *existing_names*.

    If *base_name* is already used, the function appends ``" (n)"`` where ``n``
    is the smallest integer ensuring uniqueness.
    """
    logger.debug(
        f"🔍 [get_unique_curve_name] base='{base_name}' existing={list(existing_names)}"
    )
    if base_name not in existing_names:
        logger.debug(f"✅ Nom disponible généré : {base_name}")
        return base_name

    index = 1
    proposed = f"{base_name} ({index})"
    while proposed in existing_names:
        logger.debug(f"⛔️ Nom déjà utilisé : {proposed}")
        index += 1
        proposed = f"{base_name} ({index})"

    logger.debug(f"✅ Nom disponible généré : {proposed}")
    return proposed
