#controllers.py

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from app_state import AppState
from graph_service import GraphService
from views import MyPlotView
from plot_container import PlotContainerWidget
from signal_bus import signal_bus

class GraphController:
    def load_project(self, graphs):
        print("[controllers.py > load_project()] ▶️ Entrée dans load_project()")

        # Nettoyer la vue existante
        for name, view in self.views.items():
            container = view.plot_widget.parent()
            self.w.center_area_widget.remove_plot_widget(container)
        self.views.clear()

        # Charger les nouveaux graphes
        self.state.graphs = graphs
        self.state.current_graph = None
        self.state.current_curve = None

        for name, graph in graphs.items():
            view = MyPlotView(graph)
            self.views[name] = view
            container = PlotContainerWidget(name, view.plot_widget)
            self.w.center_area_widget.add_plot_widget(container)

        self.w.left_panel.refresh_tree(graphs)
        self._refresh_plot()


    def __init__(self, main_window):
        print("[GraphController.__init__] Initialisation du contrôleur")

        signal_bus.graph_selected.connect(self._on_graph_selected)

        self._renaming = False  # Flag explicite pour ignorer les sélections pendant un renommage
        self.w = main_window
        self.state = AppState.get_instance()
        self.service = GraphService(self.state)
        self.views = {}
        self._last_save_path = None
        self._block_ui_sync = False

        self._connect_ui()
        self._connect_signals()
        self.w.left_panel.refresh_tree(self.state.graphs)

    def _connect_ui(self):
        print("[GraphController._connect_ui] Connexion des éléments UI")

        p = self.w.left_panel
        rp = self.w.right_panel

        p.tree.selectionModel().currentChanged.connect(self._on_tree_selection_changed)

        rp.width_spin.valueChanged.connect(self._on_curve_width_changed)
        rp.style_combo.currentIndexChanged.connect(self._on_curve_style_changed)
        rp.color_button.clicked.connect(self._on_curve_color_changed)

        rp.grid_checkbox.toggled.connect(self._on_graph_props_changed)
        rp.darkmode_checkbox.toggled.connect(self._on_graph_props_changed)
        rp.logx_checkbox.toggled.connect(self._on_graph_props_changed)
        rp.logy_checkbox.toggled.connect(self._on_graph_props_changed)
        rp.font_combo.currentFontChanged.connect(self._on_graph_props_changed)
        rp.button_reset_zoom.clicked.connect(self.reset_zoom)
        
        rp.downsampling_combo.currentIndexChanged.connect(self._on_downsampling_mode_changed)
        rp.downsampling_apply_btn.clicked.connect(self._on_apply_downsampling_ratio)
        
        rp.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        rp.symbol_combo.currentIndexChanged.connect(self._on_symbol_changed)
        rp.fill_checkbox.toggled.connect(self._on_fill_toggled)
        rp.display_mode_combo.currentIndexChanged.connect(self._on_display_mode_changed)
        
        rp.fix_y_checkbox.toggled.connect(self._on_graph_props_changed)
        rp.ymin_input.valueChanged.connect(self._on_graph_props_changed)
        rp.ymax_input.valueChanged.connect(self._on_graph_props_changed)
        
        rp.gain_slider.valueChanged.connect(self._on_gain_changed)
        rp.offset_slider.valueChanged.connect(self._on_offset_changed)
        
        rp.bring_to_front_button.clicked.connect(self._on_bring_curve_to_front)
        
        rp.x_unit_input.textChanged.connect(self._on_graph_props_changed)
        rp.y_unit_input.textChanged.connect(self._on_graph_props_changed)
        rp.x_format_combo.currentIndexChanged.connect(self._on_graph_props_changed)
        rp.y_format_combo.currentIndexChanged.connect(self._on_graph_props_changed)

        rp.label_mode_combo.currentIndexChanged.connect(self._on_label_mode_changed)

        rp.zero_indicator_combo.currentIndexChanged.connect(self._on_zero_indicator_changed)
        
        rp.satellite_left_combo.currentIndexChanged.connect(lambda _: self._refresh_satellite_zone("left"))
        rp.satellite_right_combo.currentIndexChanged.connect(lambda _: self._refresh_satellite_zone("right"))
        rp.satellite_top_combo.currentIndexChanged.connect(lambda _: self._refresh_satellite_zone("top"))
        rp.satellite_bottom_combo.currentIndexChanged.connect(lambda _: self._refresh_satellite_zone("bottom"))


    def _connect_signals(self):
        print("[GraphController._connect_signals] Connexion des signaux internes")

        signal_bus.graph_selected.connect(self.refresh_graph_ui)
        signal_bus.curve_selected.connect(self.refresh_curve_ui)
        signal_bus.curve_selected.connect(self._on_curve_selected)
        signal_bus.curve_list_updated.connect(lambda: self.w.left_panel.refresh_tree(self.state.graphs))
        signal_bus.curve_updated.connect(self._refresh_plot)
        signal_bus.graph_updated.connect(self._refresh_plot)
        signal_bus.remove_requested.connect(self._handle_remove_requested)
        signal_bus.rename_requested.connect(self._handle_rename_requested)

    def _handle_remove_requested(self, kind, name):
        print("[controllers.py > _handle_remove_requested()] ▶️ Entrée dans _handle_remove_requested()")

        self._remove_item(kind, name)

    def _on_tree_selection_changed(self, current: QtCore.QModelIndex, previous: QtCore.QModelIndex):
        print("[controllers.py > _on_tree_selection_changed()] ▶️ Entrée dans _on_tree_selection_changed()")

        if self._renaming:
            return
        if not current.isValid():
            return
        kind = current.data(QtCore.Qt.UserRole + 3)
        name = current.data(QtCore.Qt.UserRole + 4)

        if kind == "action":
            if name == "add_graph":
                self.add_graph()
            elif name.startswith("add_curve:"):
                graph_name = name.split(":", 1)[1]
                self.service.select_graph(graph_name)
                self.w.import_curve()
        elif kind == "graph":
            self._select_graph_from_name(name)
        elif kind == "curve":
            parent = current.parent()
            if parent.isValid():
                graph_name = parent.data(QtCore.Qt.DisplayRole)
                self.service.select_graph(graph_name)
                signal_bus.graph_selected.emit(graph_name)
                self.service.select_curve(name)
                signal_bus.curve_selected.emit(graph_name, name)

    def add_graph(self):
        print("[GraphController.add_graph] Création d'un nouveau graphe")

        name = self.service.create_graph()
        graph_data = self.state.graphs[name]
        view = MyPlotView(graph_data)
        self.views[name] = view
        container = PlotContainerWidget(name, view.plot_widget)
        self.w.center_area_widget.add_plot_widget(container)
        self.w.left_panel.refresh_tree(self.state.graphs)
        
    def add_curve(self):
        print("[GraphController.add_curve] Ajout d'une courbe aléatoire")

        try:
            self.service.add_random_curve()
            signal_bus.curve_list_updated.emit()
            signal_bus.curve_updated.emit()
        except Exception as e:
            print(f"[ERROR] Exception dans add_curve: {e}")
            QtWidgets.QMessageBox.warning(self.w, "Erreur", str(e))
            
        curve = self.state.current_graph.curves[-1]
        curve.zero_indicator = "arrow"

    def _remove_item(self, kind, name):
        print("[controllers.py > _remove_item()] ▶️ Entrée dans _remove_item()")

        confirm = QtWidgets.QMessageBox.question(self.w, "Confirmer", f"Supprimer {kind} '{name}' ?")
        if confirm != QtWidgets.QMessageBox.Yes:
            return
        try:
            print(f"[DEBUG] Suppression demandée pour {kind}: {name}")
            if kind == "graph":
                self.service.delete_graph(name)
                view = self.views.pop(name, None)
                if view:
                    container = view.plot_widget
                    while container is not None and not isinstance(container, PlotContainerWidget):
                        container = container.parent()
                    if container:
                        self.w.center_area_widget.remove_plot_widget(container)
            elif kind == "curve":
                self.service.remove_curve(name)
    
            self.w.left_panel.refresh_tree(self.state.graphs)
            signal_bus.curve_updated.emit()
        except Exception as e:
            import traceback
            print("[ERROR] Exception lors de la suppression :", traceback.format_exc())
            QtWidgets.QMessageBox.warning(self.w, "Erreur", str(e))

    def refresh_graph_ui(self):
        print("[controllers.py > refresh_graph_ui()] ▶️ Entrée dans refresh_graph_ui()")
    
        graph = self.state.current_graph
        if not graph:
            return
    
        rp = self.w.right_panel
    
        # ✅ Synchronisation des zones satellites (checkboxes + menus)
        for zone in ["left", "right", "top", "bottom"]:
            visible = graph.satellite_visibility.get(zone, False)
            checkbox = getattr(rp, f"satellite_{zone}_checkbox")
            combo = getattr(rp, f"satellite_{zone}_combo")
    
            # ⛔ Bloque les signaux pour ne pas déclencher les handlers
            checkbox.blockSignals(True)
            checkbox.setChecked(visible)
            checkbox.blockSignals(False)
    
            value = graph.satellite_content.get(zone, None)
            index = combo.findData(value)
            combo.blockSignals(True)
            combo.setCurrentIndex(index if index >= 0 else 0)
            combo.blockSignals(False)
    
        self._block_ui_sync = True
        try:
            rp.label_graph_name.setText(graph.name)
            rp.grid_checkbox.setChecked(graph.grid_visible)
            rp.darkmode_checkbox.setChecked(graph.dark_mode)
            rp.logx_checkbox.setChecked(graph.log_x)
            rp.logy_checkbox.setChecked(graph.log_y)
            rp.font_combo.setCurrentFont(QFont(graph.font))
            rp.fix_y_checkbox.setChecked(graph.fix_y_range)
            rp.ymin_input.setValue(graph.y_min)
            rp.ymax_input.setValue(graph.y_max)
            rp.x_unit_input.setText(graph.x_unit)
            rp.y_unit_input.setText(graph.y_unit)
            rp.x_format_combo.setCurrentIndex(rp.x_format_combo.findData(graph.x_format))
            rp.y_format_combo.setCurrentIndex(rp.y_format_combo.findData(graph.y_format))
            self.w.right_panel.setTabEnabled(0, True)
        finally:
            self._block_ui_sync = False



    def refresh_curve_ui(self):
        print("[controllers.py > refresh_curve_ui()] ▶️ Entrée dans refresh_curve_ui()")

        rp = self.w.right_panel
        
        curve = self.state.current_curve
        if not curve:
            return

        index = rp.downsampling_combo.findData(curve.downsampling_mode)
        rp.downsampling_combo.setCurrentIndex(index)
        
        rp.label_curve_name.setText(curve.name)
        rp.label_mode_combo.setCurrentIndex(rp.label_mode_combo.findData(curve.label_mode))
        rp.width_spin.setValue(curve.width)
        rp.style_combo.setCurrentIndex(rp.style_combo.findData(curve.style))
        
        rp.downsampling_ratio_input.setValue(curve.downsampling_ratio)
        is_manual = curve.downsampling_mode == "manual"
        rp.downsampling_ratio_input.setEnabled(is_manual)
        rp.downsampling_apply_btn.setEnabled(is_manual)
        
        rp.opacity_slider.setValue(int(curve.opacity))
        rp.symbol_combo.setCurrentIndex(rp.symbol_combo.findData(curve.symbol))
        rp.fill_checkbox.setChecked(curve.fill)
        rp.display_mode_combo.setCurrentIndex(rp.display_mode_combo.findData(curve.display_mode))
        
        rp.gain_slider.setValue(int(curve.gain * 100))
        rp.offset_slider.setValue(int(curve.offset * 100))
        rp.zero_indicator_combo.setCurrentIndex(rp.zero_indicator_combo.findData(curve.zero_indicator))
        
        self.w.right_panel.setTabEnabled(1, True)

    def _on_graph_props_changed(self, *_):
        print("[controllers.py > _on_graph_props_changed()] ▶️ Entrée dans _on_graph_props_changed()")

        if self._block_ui_sync:
            return
        graph = self.state.current_graph
        if not graph:
            return
        rp = self.w.right_panel
        graph.grid_visible = rp.grid_checkbox.isChecked()
        graph.dark_mode = rp.darkmode_checkbox.isChecked()
        graph.log_x = rp.logx_checkbox.isChecked()
        graph.log_y = rp.logy_checkbox.isChecked()
        graph.font = rp.font_combo.currentFont().family()
        signal_bus.graph_updated.emit()
        
        graph.fix_y_range = rp.fix_y_checkbox.isChecked()
        graph.y_min = rp.ymin_input.value()
        graph.y_max = rp.ymax_input.value()
        signal_bus.graph_updated.emit()
        
        graph.x_unit = rp.x_unit_input.text().strip()
        graph.y_unit = rp.y_unit_input.text().strip()
        graph.x_format = rp.x_format_combo.currentData()
        graph.y_format = rp.y_format_combo.currentData()
        signal_bus.graph_updated.emit()

    def _on_curve_width_changed(self, value):
        print("[controllers.py > _on_curve_width_changed()] ▶️ Entrée dans _on_curve_width_changed()")

        curve = self.state.current_curve
        if curve:
            curve.width = value
            signal_bus.curve_updated.emit()

    def _on_curve_style_changed(self, index):
        print("[controllers.py > _on_curve_style_changed()] ▶️ Entrée dans _on_curve_style_changed()")

        curve = self.state.current_curve
        if curve:
            style = self.w.right_panel.style_combo.itemData(index)
            curve.style = style
            signal_bus.curve_updated.emit()

    def _on_curve_color_changed(self):
        print("[controllers.py > _on_curve_color_changed()] ▶️ Entrée dans _on_curve_color_changed()")

        curve = self.state.current_curve
        if curve:
            color = QtWidgets.QColorDialog.getColor()
            if color.isValid():
                curve.color = color.name()
                signal_bus.curve_updated.emit()

    
    def _refresh_plot(self):
        print("\n[GraphController._refresh_plot] ▶️ Début du rafraîchissement des graphes")
        for name, view in self.views.items():
            print(f"  [INFO] Rafraîchissement de {name}")
            graph = self.state.graphs.get(name)
            if not graph:
                print(f"  [WARN] Graphe {name} non trouvé dans l'état")
                continue
            view.graph_data = graph
            view.plot_widget.setVisible(graph.visible)
            view.update_graph_properties()
            view.refresh_curves()

        for graph_name, view in self.views.items():
            print(f"\n[SATELLITES] pour {graph_name} = {[type(s).__name__ for s in view.satellites]}")
            
            # 🔍 Recherche récursive du bon parent
            container = view.plot_widget
            while container is not None and not hasattr(container, "get_advanced_container"):
                container = container.parent()
            
            if container is None:
                print("  [ERROR] Aucun parent avec get_advanced_container trouvé")
                continue
            
            adv = container.get_advanced_container()
            print(f"  [SUCCESS] Advanced container trouvé: {adv}")

            for zone in ['left', 'right', 'top', 'bottom']:
                layout = getattr(adv, f"{zone}_box").layout()
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget:
                        print(f"    [CLEAR] Suppression widget: {widget}")
                        widget.deleteLater()
            
            #ajout satellite            
            for zone in ['left', 'right', 'top', 'bottom']:
                if not graph.satellite_visibility.get(zone):
                    continue
                content = graph.satellite_content.get(zone)
                if not content:
                    continue
                widget = self._create_satellite_widget(zone, content)
                if widget:
                    getattr(adv, f"add_to_{zone}")(widget)
            
            for satellite in view.satellites:
                try:
                    zone = satellite.get_zone()
                    widget = satellite.get_widget()
                    print(f"  [ADD] Satellite {satellite} vers zone {zone}, visible={widget.isVisible()}, size={widget.size()}")
                    getattr(adv, f"add_to_{zone}")(widget)
                    widget.setVisible(True)
                    widget.setFixedSize(120, 200)
                    #widget.setStyleSheet(widget.styleSheet() + " background-color: magenta;")
                    print(f"  [✔] Widget inséré: {widget}, visible={widget.isVisible()}, size={widget.size()}")
                except Exception as e:
                    import traceback
                    print("  [EXCEPTION] Erreur lors de l'injection de satellite:", traceback.format_exc())

                      

    def get_current_view(self):
        print("[controllers.py > get_current_view()] ▶️ Entrée dans get_current_view()")

        graph = self.state.current_graph
        if not graph:
            return None
        return self.views.get(graph.name)

    def reset_zoom(self):
        print("[controllers.py > reset_zoom()] ▶️ Entrée dans reset_zoom()")

        view = self.get_current_view()
        if view:
            view.auto_range()

    def _find_dock_for_view(self, widget):
        print("[controllers.py > _find_dock_for_view()] ▶️ Entrée dans _find_dock_for_view()")

        parent = widget.parent()
        while parent:
            if isinstance(parent, QtWidgets.QDockWidget):
                return parent
            parent = parent.parent()
        return None



    def _handle_rename_requested(self, kind, old_name, new_name):
        print("[controllers.py > _handle_rename_requested()] ▶️ Entrée dans _handle_rename_requested()")

        print("old_name", old_name)
        print("new_name", new_name)

        
        # Annuler si aucun changement
        if old_name == new_name:
            return

        # Vérification des doublons avant toute modification
        if kind == "graph" and new_name in self.state.graphs:
            QtWidgets.QMessageBox.warning(self.w, "Erreur", f"Le graphique '{new_name}' existe déjà.")
            self._restore_item_name(old_name)
            return
        elif kind == "curve" and self.state.current_graph and any(c.name == new_name for c in self.state.current_graph.curves):
            QtWidgets.QMessageBox.warning(self.w, "Erreur", f"La courbe '{new_name}' existe déjà.")
            self._restore_item_name(old_name)
            return
        sel_model = self.w.left_panel.tree.selectionModel()
        try:
            try:
                self._renaming = True
                sel_model.blockSignals(True)

                if kind == "graph":
                    self._block_ui_sync = True
                    self.service.rename_graph(old_name, new_name)

                    if old_name in self.views:
                        self.views[new_name] = self.views.pop(old_name)

                    view = self.views.get(new_name)

                    # Trouver le PlotContainerWidget parent réel
                    container = view.plot_widget
                    while container is not None and not isinstance(container, PlotContainerWidget):
                        container = container.parent()
                    
                    if isinstance(container, PlotContainerWidget):
                        print("[DEBUG] ✅ PlotContainerWidget trouvé, renommage appliqué")
                        container.set_graph_name(new_name)
                    else:
                        print("[DEBUG] ❌ PlotContainerWidget introuvable")

                    

                    self._block_ui_sync = False
                    self._refresh_plot()

                elif kind == "curve":
                    self.service.rename_curve(old_name, new_name)

                self.w.left_panel.refresh_tree(self.state.graphs)

            finally:
                sel_model.blockSignals(False)
                self._renaming = False

        except Exception as e:
            QtWidgets.QMessageBox.warning(self.w, "Erreur", str(e))


 
    def _restore_item_name(self, name):
        print("[controllers.py > _restore_item_name()] ▶️ Entrée dans _restore_item_name()")

        # Rétablit le nom dans l'arbre si le renommage a échoué
        model = self.w.left_panel.model
        for i in range(model.rowCount()):
            parent_item = model.item(i)
            if parent_item.data(QtCore.Qt.UserRole + 4) == name:
                parent_item.setText(name)
                return
            for j in range(parent_item.rowCount()):
                child_item = parent_item.child(j)
                if child_item.data(QtCore.Qt.UserRole + 4) == name:
                    child_item.setText(name)
                    return

    def import_graph(self, graph_data):
        print("[controllers.py > import_graph()] ▶️ Entrée dans import_graph()")

        name = graph_data.name
        self.state.graphs[name] = graph_data
        view = MyPlotView(graph_data)
        self.views[name] = view
        container = PlotContainerWidget(name, view.plot_widget)
        self.w.center_area_widget.add_plot_widget(container)
        self.w.left_panel.refresh_tree(self.state.graphs)
        self._refresh_plot()

    def _on_downsampling_mode_changed(self, index):
        print("[controllers.py > _on_downsampling_mode_changed()] ▶️ Entrée dans _on_downsampling_mode_changed()")

        mode = self.w.right_panel.downsampling_combo.itemData(index)
        is_manual = (mode == "manual")
        self.w.right_panel.downsampling_ratio_input.setEnabled(is_manual)
        self.w.right_panel.downsampling_apply_btn.setEnabled(is_manual)
    
        curve = self.state.current_curve
        if curve:
            curve.downsampling_mode = mode
            signal_bus.curve_updated.emit()
            
    def _on_apply_downsampling_ratio(self):
        print("[controllers.py > _on_apply_downsampling_ratio()] ▶️ Entrée dans _on_apply_downsampling_ratio()")

        curve = self.state.current_curve
        if curve and curve.downsampling_mode == "manual":
            ratio = self.w.right_panel.downsampling_ratio_input.value()
            curve.downsampling_ratio = max(1, ratio)
            signal_bus.curve_updated.emit()

    def _on_graph_selected(self, name):
        print("[controllers.py > _on_graph_selected()] ▶️ Entrée dans _on_graph_selected()")

        # Empêche double déclenchement si déjà sélectionné
        if self.state.current_graph and self.state.current_graph.name == name:
            return
        self._select_graph_from_name(name)
    
    def _select_graph_from_name(self, name):
        print("[controllers.py > _select_graph_from_name()] ▶️ Entrée dans _select_graph_from_name()")

        self.service.select_graph(name)
        self._highlight_selected_graph_view(name)
        self._select_in_tree(name)
        signal_bus.graph_selected.emit(name)
    
    def _highlight_selected_graph_view(self, name):
        print("[controllers.py > _highlight_selected_graph_view()] ▶️ Entrée dans _highlight_selected_graph_view()")

        for graph_name, view in self.views.items():
            print(f"[controllers.py > _refresh_plot()] 📡 satellites pour {graph_name} = {[type(s).__name__ for s in view.satellites]}")
            container = view.plot_widget.parent()
            if hasattr(container, 'set_selected'):
                container.set_selected(graph_name == name)
    
    def _select_in_tree(self, graph_name):
        print("[controllers.py > _select_in_tree()] ▶️ Entrée dans _select_in_tree()")

        model = self.w.left_panel.model
        for i in range(model.rowCount()):
            index = model.index(i, 0)
            item = model.itemFromIndex(index)
            if item.text() == graph_name:
                self.w.left_panel.tree.setCurrentIndex(index)
                break

    def _on_curve_selected_by_click_old_function(self, curve_name):
        print("[controllers.py > _on_curve_selected_by_click()] ▶️ Entrée dans _on_curve_selected_by_click()")

        graph = self.state.current_graph
    
        if not graph:
            # Si aucun graphe n’est sélectionné, essaie de le retrouver à partir des courbes
            for g_name, g in self.state.graphs.items():
                if any(c.name == curve_name for c in g.curves):
                    self._select_graph_from_name(g_name)
                    break
            graph = self.state.current_graph
    
        if not graph:
            return
    
        self.service.select_curve(curve_name)
        self._select_curve_in_tree(curve_name)
        
        
    def _on_curve_selected(self, graph_name, curve_name):
        graph = self.state.graphs.get(graph_name)
        if not graph:
            print(f"[ERREUR] Graphique '{graph_name}' introuvable.")
            return
        for c in graph.curves:
             if c.name == curve_name:
                 self.state.current_curve = c
                 print(f"[INFO] Courbe sélectionnée : {c.name} dans {graph_name}")
                 return
        print(f"[ERREUR] Courbe '{curve_name}' non trouvée dans '{graph_name}'")        
        
    
    def _select_curve_in_tree(self, curve_name):
        print("[controllers.py > _select_curve_in_tree()] ▶️ Entrée dans _select_curve_in_tree()")

        model = self.w.left_panel.model
        for i in range(model.rowCount()):
            graph_item = model.item(i)
            for j in range(graph_item.rowCount()):
                curve_item = graph_item.child(j)
                if curve_item.data(QtCore.Qt.UserRole + 4) == curve_name:
                    index = model.indexFromItem(curve_item)
                    self.w.left_panel.tree.setCurrentIndex(index)
                    return

    def _on_opacity_changed(self, value):
        print("[controllers.py > _on_opacity_changed()] ▶️ Entrée dans _on_opacity_changed()")

        curve = self.state.current_curve
        if curve:
            curve.opacity = value
            signal_bus.curve_updated.emit()
    
    def _on_symbol_changed(self, index):
        print("[controllers.py > _on_symbol_changed()] ▶️ Entrée dans _on_symbol_changed()")

        curve = self.state.current_curve
        if curve:
            symbol = self.w.right_panel.symbol_combo.itemData(index)
            curve.symbol = symbol
            signal_bus.curve_updated.emit()
    
    def _on_fill_toggled(self, checked):
        print("[controllers.py > _on_fill_toggled()] ▶️ Entrée dans _on_fill_toggled()")

        curve = self.state.current_curve
        if curve:
            curve.fill = checked
            signal_bus.curve_updated.emit()
    
    def _on_display_mode_changed(self, index):
        print("[controllers.py > _on_display_mode_changed()] ▶️ Entrée dans _on_display_mode_changed()")

        curve = self.state.current_curve
        if curve:
            mode = self.w.right_panel.display_mode_combo.itemData(index)
            curve.display_mode = mode
            signal_bus.curve_updated.emit()

    def _on_gain_changed(self, value):
        print("[controllers.py > _on_gain_changed()] ▶️ Entrée dans _on_gain_changed()")

        curve = self.state.current_curve
        if curve:
            curve.gain = value / 100.0
            signal_bus.curve_updated.emit()
    
    def _on_offset_changed(self, value):
        print("[controllers.py > _on_offset_changed()] ▶️ Entrée dans _on_offset_changed()")

        curve = self.state.current_curve
        if curve:
            curve.offset = value / 100.0
            signal_bus.curve_updated.emit()
            
    def _on_bring_curve_to_front(self):
        print("[controllers.py > _on_bring_curve_to_front()] ▶️ Entrée dans _on_bring_curve_to_front()")

        graph = self.state.current_graph
        curve = self.state.current_curve
        if not graph or not curve:
            return
    
        # Réorganise la liste en mettant la courbe sélectionnée en premier
        if curve in graph.curves:
            graph.curves.remove(curve)
            graph.curves.insert(0, curve)
    
            # Met à jour les vues
            signal_bus.curve_list_updated.emit()
            signal_bus.curve_updated.emit()

    def _on_show_label_toggled(self, checked):
        print("[controllers.py > _on_show_label_toggled()] ▶️ Entrée dans _on_show_label_toggled()")

        curve = self.state.current_curve
        if curve:
            curve.show_label = checked
            signal_bus.curve_updated.emit()

    def _on_label_mode_changed(self, index):
        print("[controllers.py > _on_label_mode_changed()] ▶️ Entrée dans _on_label_mode_changed()")

        curve = self.state.current_curve
        if curve:
            rp = self.w.right_panel
            mode = rp.label_mode_combo.itemData(index)
            curve.label_mode = mode
            signal_bus.curve_updated.emit()

    def _on_zero_indicator_changed(self, index):
        print("[controllers.py > _on_zero_indicator_changed()] ▶️ Entrée dans _on_zero_indicator_changed()")
    
        value = self.w.right_panel.zero_indicator_combo.itemData(index)
        curve = self.state.current_curve
        if curve:
            curve.zero_indicator = value
            signal_bus.curve_updated.emit()

    def _toggle_satellite_zone(self, zone, visible):
        print(f"[GraphController] ▶️ Zone satellite '{zone}' → visible={visible}")
    
        graph = self.state.current_graph
        if graph:
            graph.satellite_visibility[zone] = visible
    
        view = self.get_current_view()
        if not view:
            return
    
        container = view.plot_widget
        while container and not hasattr(container, "get_advanced_container"):
            container = container.parent()
    
        if not container:
            print("[ERROR] Impossible de localiser AdvancedPlotContainer")
            return
    
        adv = container.get_advanced_container()
        box = getattr(adv, f"{zone}_box", None)
        if box:
            if visible:
                box.show()
            else:
                box.hide()
                # Variante B : supprimer les widgets si besoin
                while box.layout().count():
                    item = box.layout().takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()


    def _refresh_satellite_zone(self, zone):
        print(f"[Satellite] Rafraîchissement de la zone {zone}")
    
        view = self.get_current_view()
        if not view:
            return
    
        container = view.plot_widget
        while container and not hasattr(container, "get_advanced_container"):
            container = container.parent()
        if not container:
            return
    
        adv = container.get_advanced_container()
        box = getattr(adv, f"{zone}_box", None)
        if not box:
            return
    
        # Nettoyage
        while box.layout().count():
            item = box.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
        # Choix de contenu
        combo = getattr(self.w.right_panel, f"satellite_{zone}_combo")
        key = combo.currentData()
    
        # ⬇️ Enregistrer la sélection dans les données du graphique
        graph = self.state.current_graph
        if graph:
            graph.satellite_content[zone] = key
    
        # Créer le widget
        if key == "label":
            from PyQt5.QtWidgets import QLabel
            widget = QLabel(f"Label dans zone {zone}")
        elif key == "button":
            from PyQt5.QtWidgets import QPushButton
            widget = QPushButton(f"Bouton dans zone {zone}")
        else:
            widget = None
    
        # Affichage ou masquage
        if widget:
            box.layout().addWidget(widget)
            box.show()
        else:
            box.hide()
    


    def _create_satellite_widget(self, zone, content_key):
        if content_key == "label":
            from PyQt5.QtWidgets import QLabel
            return QLabel(f"[{zone}] Label")
        elif content_key == "button":
            from PyQt5.QtWidgets import QPushButton
            return QPushButton(f"[{zone}] Bouton")
        return None
