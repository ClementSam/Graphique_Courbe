from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from GraphCurvePanel import GraphCurvePanel
from CentralPlotArea import CentralPlotArea
from PropertiesPanel import PropertiesPanel
from controllers import GraphController
from signal_bus import signal_bus
from layout_manager_dialog import LayoutManagerDialog
import layout_manager as lm
from app_state import AppState
from project_io import export_project_to_json, import_project_from_json
from graph_io import export_graph_to_json, import_graph_from_json
from curve_io import export_curve_to_json, import_curve_from_json
from import_curve_dialog import ImportCurveDialog
from curve_loader_factory import load_curve_by_format
from curve_generators import generate_random_curve
import os
import json

RECENT_FILE = "recent_projects.json"

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestionnaire de courbes")
        self.setGeometry(100, 100, 1200, 700)
        self._current_project_path = None
        self._setup_menu()
        self._setup_ui()
        self._setup_toolbar()
        self._connect_signals()
        self.controller = GraphController(self)

        try:
            default = lm.get_default_layout()
            if default:
                lm.load_layout(default, self)
        except Exception as e:
            print("[Layout] Impossible de charger la disposition par défaut:", e)

    def _setup_ui(self):
        self.center_area_widget = CentralPlotArea()
        self.dock_center = QtWidgets.QDockWidget("Zone centrale", self)
        self.dock_center.setWidget(self.center_area_widget)
        self.dock_center.setFeatures(QtWidgets.QDockWidget.AllDockWidgetFeatures)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_center)
        self.add_graph_to_view_menu("Zone centrale", self.dock_center)

        self.left_panel = GraphCurvePanel()
        self.dock_left = QtWidgets.QDockWidget("Graphiques et courbes", self)
        self.dock_left.setWidget(self.left_panel)
        self.dock_left.setFeatures(QtWidgets.QDockWidget.AllDockWidgetFeatures)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_left)
        self.add_graph_to_view_menu("Graphiques et courbes", self.dock_left)

        self.right_panel = PropertiesPanel()
        self.dock_right = QtWidgets.QDockWidget("Propriétés", self)
        self.dock_right.setWidget(self.right_panel)
        self.dock_right.setFeatures(QtWidgets.QDockWidget.AllDockWidgetFeatures)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_right)
        self.tabifyDockWidget(self.dock_left, self.dock_right)
        self.dock_left.raise_()
        self.add_graph_to_view_menu("Propriétés", self.dock_right)

    def _setup_menu(self):
        menu_bar = self.menuBar()
        self.view_menu = menu_bar.addMenu("Affichage")

        file_menu = menu_bar.addMenu("Fichier")
        self.save_action = file_menu.addAction("Sauvegarder")
        self.save_action.triggered.connect(self.save_project)
        self.save_as_action = file_menu.addAction("Sauvegarder sous...")
        self.save_as_action.triggered.connect(self.save_project_as)
        self.load_action = file_menu.addAction("Charger un projet")
        self.load_action.triggered.connect(self.load_project)

        self.recent_menu = file_menu.addMenu("Charger récent")
        self._populate_recent_projects()

        file_menu.addSeparator()
        self.export_graph_csv_action = file_menu.addAction("Exporter graphique en CSV")
        self.export_project_csv_action = file_menu.addAction("Exporter projet en CSV")
        file_menu.addSeparator()
        quit_action = file_menu.addAction("Quitter")
        quit_action.triggered.connect(self.close)

        
        self.import_export_menu = menu_bar.addMenu("Exporter / Importer")
        self.export_graph_action = self.import_export_menu.addAction("📤 Exporter graphique")
        self.export_graph_action.triggered.connect(self.export_graph)
        self.export_curve_action = self.import_export_menu.addAction("📤 Exporter courbe")
        self.export_curve_action.triggered.connect(self.export_curve)
        self.import_graph_action = self.import_export_menu.addAction("📥 Importer graphique")
        self.import_graph_action.triggered.connect(self.import_graph)
        self.import_curve_action = self.import_export_menu.addAction("📥 Importer courbe")
        self.import_curve_action.triggered.connect(self.import_curve)
    

        help_menu = menu_bar.addMenu("Aide")
        about_action = help_menu.addAction("À propos")
        about_action.triggered.connect(self._show_about)

    def _setup_toolbar(self):
        self.toolbar = self.addToolBar("Outils")

        save_btn = QtWidgets.QAction("💾 Sauver projet", self)
        save_btn.triggered.connect(self.save_project)
        save_as_btn = QtWidgets.QAction("💾 Sauver sous...", self)
        save_as_btn.triggered.connect(self.save_project_as)
        load_btn = QtWidgets.QAction("📂 Charger projet", self)
        load_btn.triggered.connect(self.load_project)

        self.toolbar.addAction(save_btn)
        self.toolbar.addAction(save_as_btn)
        self.toolbar.addAction(load_btn)
        self.toolbar.addSeparator()

        export_graph_btn = QtWidgets.QAction("📤 Exporter graphique", self)
        export_graph_btn.triggered.connect(self.export_graph)
        export_curve_btn = QtWidgets.QAction("📈 Exporter courbe", self)
        export_curve_btn.triggered.connect(self.export_curve)
        import_graph_btn = QtWidgets.QAction("📥 Importer graphique", self)
        import_graph_btn.triggered.connect(self.import_graph)
        import_curve_btn = QtWidgets.QAction("📈 Importer courbe", self)
        import_curve_btn.triggered.connect(self.import_curve)        
        
        self.toolbar.addAction(export_graph_btn)
        self.toolbar.addAction(export_curve_btn)
        self.toolbar.addAction(import_graph_btn)
        self.toolbar.addAction(import_curve_btn)        
        self.toolbar.addSeparator()

        layout_btn = QtWidgets.QAction("🗂 Dispositions", self)
        layout_btn.triggered.connect(self.open_layout_dialog)
        self.toolbar.addAction(layout_btn)

    def open_layout_dialog(self):
        dlg = LayoutManagerDialog(self)
        dlg.exec_()

    def save_project(self):
        if not self._current_project_path:
            self.save_project_as()
            return
        export_project_to_json(AppState.get_instance().graphs, self._current_project_path)

    def save_project_as(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Sauvegarder le projet", "", "Fichiers JSON (*.json)")
        if path:
            self._current_project_path = path
            export_project_to_json(AppState.get_instance().graphs, path)
            self._add_to_recent(path)

    def load_project(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Charger un projet", "", "Fichiers JSON (*.json)")
        if path:
            graphs = import_project_from_json(path)
            self.controller.load_project(graphs)
            self._current_project_path = path
            self._add_to_recent(path)

    def import_graph(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Importer graphique", "", "Fichiers JSON (*.json)")
        if path:
            graph = import_graph_from_json(path)
            self.controller.import_graph(graph)
            QtWidgets.QMessageBox.information(self, "Import réussi", f"Graphique '{graph.name}' importé.")

    def import_curve(self):
        state = AppState.get_instance()
        graph = state.current_graph
        if not graph:
            QtWidgets.QMessageBox.warning(self, "Aucun graphique sélectionné", "Veuillez sélectionner un graphique pour y ajouter la courbe.")
            return

        dlg = ImportCurveDialog(self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            path, fmt = dlg.get_selected_path_and_format()
            try:
                if fmt == "random_curve":
                    # Utilise AppState pour savoir quel graph est actif
                    existing_names = [c.name for c in graph.curves]
                    index = 1
                    while f"Courbe {index}" in existing_names:
                        index += 1
                    curve = generate_random_curve(index)
                    curves = [curve]
                else:
                    curves = load_curve_by_format(path, fmt)

                for curve in curves:
                    self.controller.service.add_curve(graph.name, curve)
                signal_bus.curve_list_updated.emit()
                signal_bus.curve_updated.emit()
                QtWidgets.QMessageBox.information(self, "Import réussi", f"{len(curves)} courbe(s) importée(s) dans '{graph.name}'.")
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Erreur", str(e))

    def _populate_recent_projects(self):
            self.recent_menu.clear()
            if not os.path.exists(RECENT_FILE):
                return
            try:
                with open(RECENT_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for path in data.get("recent", [])[:5]:
                    action = self.recent_menu.addAction(path)
                    action.triggered.connect(lambda checked, p=path: self._load_recent_project(p))
            except Exception as e:
                print("Erreur chargement projets récents:", e)

    def _add_to_recent(self, path):
        data = {"recent": []}
        if os.path.exists(RECENT_FILE):
            try:
                with open(RECENT_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass
        if path in data["recent"]:
            data["recent"].remove(path)
        data["recent"].insert(0, path)
        data["recent"] = data["recent"][:10]
        with open(RECENT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        self._populate_recent_projects()

    def _load_recent_project(self, path):
        if os.path.exists(path):
            graphs = import_project_from_json(path)
            self.controller.load_project(graphs)
            self._current_project_path = path
        else:
            QtWidgets.QMessageBox.warning(self, "Fichier introuvable", f"Le fichier '{path}' n'existe plus.")
            self._populate_recent_projects()

    def export_graph(self):
        state = AppState.get_instance()
        graph = state.current_graph
        if not graph:
            QtWidgets.QMessageBox.warning(self, "Aucun graphique", "Veuillez sélectionner un graphique.")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Exporter graphique", f"{graph.name}.json", "Fichiers JSON (*.json)")
        if path:
            export_graph_to_json(graph, path)

    def export_curve(self):
        state = AppState.get_instance()
        curve = state.current_curve
        if not curve:
            QtWidgets.QMessageBox.warning(self, "Aucune courbe", "Veuillez sélectionner une courbe.")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Exporter courbe", f"{curve.name}.json", "Fichiers JSON (*.json)")
        if path:
            export_curve_to_json(curve, path)

    def _connect_signals(self):
        signal_bus.graph_selected.connect(self._enable_graph_props)
        signal_bus.curve_selected.connect(self._enable_curve_props)

    def _enable_graph_props(self, *_):
        self.right_panel.setTabEnabled(0, True)

    def _enable_curve_props(self, *_):
        self.right_panel.setTabEnabled(1, True)

    def _show_about(self):
        QtWidgets.QMessageBox.information(
            self,
            "À propos",
            "Application de gestion de courbes conçue avec PyQt5 et pyqtgraph"
        )

    def add_graph_to_view_menu(self, name, dock):
        action = self.view_menu.addAction(name)
        action.setCheckable(True)
        action.setChecked(True)
        action.triggered.connect(lambda checked: dock.setVisible(checked))
        dock.visibilityChanged.connect(lambda visible: action.setChecked(visible))

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())