# core/naming.py

from core.app_state import AppState

def get_next_graph_name():
    print("🔍 [get_next_graph_name] Début de génération de nom...")
    state = AppState.get_instance()

    if not state.graphs:
        print("📭 Aucun graphique existant, on commence à Graphique 1")
    else:
        print(f"📦 Graphiques existants : {[g.name for g in state.graphs.values()]}")

    existing_names = {g.name for g in state.graphs.values()}
    base = "Graphique"
    index = 1
    proposed_name = f"{base} {index}"

    while proposed_name in existing_names:
        print(f"⛔️ Nom déjà utilisé : {proposed_name}")
        index += 1
        proposed_name = f"{base} {index}"

    print(f"✅ Nom disponible généré : {proposed_name}")
    return proposed_name
