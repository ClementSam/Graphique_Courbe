
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
        rp.zero_line_checkbox.toggled.connect(self._on_show_zero_line_toggled)
        
        rp.bring_to_front_button.clicked.connect(self._on_bring_curve_to_front)


    def _connect_signals(self):
        signal_bus.graph_selected.connect(self.refresh_graph_ui)
        signal_bus.curve_selected.connect(self.refresh_curve_ui)
        signal_bus.curve_selected.connect(self._on_curve_selected_by_click)
        signal_bus.curve_list_updated.connect(lambda: self.w.left_panel.refresh_tree(self.state.graphs))
        signal_bus.curve_updated.connect(self._refresh_plot)
        signal_bus.graph_updated.connect(self._refresh_plot)
        signal_bus.remove_requested.connect(self._handle_remove_requested)
        signal_bus.rename_requested.connect(self._handle_rename_requested)

    def _handle_remove_requested(self, kind, name):
        self._remove_item(kind, name)

    def _on_tree_selection_changed(self, current: QtCore.QModelIndex, previous: QtCore.QModelIndex):
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
                signal_bus.curve_selected.emit(name)

    def add_graph(self):
        name = self.service.create_graph()
        graph_data = self.state.graphs[name]
        view = MyPlotView(graph_data)
        self.views[name] = view
        container = PlotContainerWidget(name, view.plot_widget)
        self.w.center_area_widget.add_plot_widget(container)
        self.w.left_panel.refresh_tree(self.state.graphs)
        
    def add_curve(self):
        try:
            self.service.add_random_curve()
            signal_bus.curve_list_updated.emit()
            signal_bus.curve_updated.emit()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self.w, "Erreur", str(e))

    def _remove_item(self, kind, name):
        confirm = QtWidgets.QMessageBox.question(self.w, "Confirmer", f"Supprimer {kind} '{name}' ?")
        if confirm != QtWidgets.QMessageBox.Yes:
            return
        try:
            if kind == "graph":
                self.service.delete_graph(name)
                view = self.views.pop(name, None)
                if view:
                    container = view.plot_widget.parent()
                    self.w.center_area_widget.remove_plot_widget(container)
            elif kind == "curve":
                self.service.remove_curve(name)
            self.w.left_panel.refresh_tree(self.state.graphs)
            signal_bus.curve_updated.emit()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self.w, "Erreur", str(e))

    def refresh_graph_ui(self):
        graph = self.state.current_graph
        if not graph:
            return
        self._block_ui_sync = True
        try:
            rp = self.w.right_panel
            rp.label_graph_name.setText(graph.name)
            rp.grid_checkbox.setChecked(graph.grid_visible)
            rp.darkmode_checkbox.setChecked(graph.dark_mode)
            rp.logx_checkbox.setChecked(graph.log_x)
            rp.logy_checkbox.setChecked(graph.log_y)
            rp.font_combo.setCurrentFont(QFont(graph.font))
            rp.fix_y_checkbox.setChecked(graph.fix_y_range)
            rp.ymin_input.setValue(graph.y_min)
            rp.ymax_input.setValue(graph.y_max)
            self.w.right_panel.setTabEnabled(0, True)
        finally:
            self._block_ui_sync = False

    def refresh_curve_ui(self):
        rp = self.w.right_panel
        
        curve = self.state.current_curve
        if not curve:
            return

        index = rp.downsampling_combo.findData(curve.downsampling_mode)
        rp.downsampling_combo.setCurrentIndex(index)
        
        rp.label_curve_name.setText(curve.name)
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
        rp.zero_line_checkbox.setChecked(curve.show_zero_line)

        self.w.right_panel.setTabEnabled(1, True)

    def _on_graph_props_changed(self, *_):
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


    def _on_curve_width_changed(self, value):
        curve = self.state.current_curve
        if curve:
            curve.width = value
            signal_bus.curve_updated.emit()

    def _on_curve_style_changed(self, index):
        curve = self.state.current_curve
        if curve:
            style = self.w.right_panel.style_combo.itemData(index)
            curve.style = style
            signal_bus.curve_updated.emit()

    def _on_curve_color_changed(self):
        curve = self.state.current_curve
        if curve:
            color = QtWidgets.QColorDialog.getColor()
            if color.isValid():
                curve.color = color.name()
                signal_bus.curve_updated.emit()

    def _refresh_plot(self):
        for name, view in self.views.items():
            graph = self.state.graphs.get(name)
            if graph:
                view.graph_data = graph
                view.plot_widget.setVisible(graph.visible)
                view.update_graph_properties()
                view.refresh_curves()
        view = self.get_current_view()
        if view:
            view.graph_data = self.state.current_graph
            view.update_graph_properties()
            view.refresh_curves()

    def get_current_view(self):
        graph = self.state.current_graph
        if not graph:
            return None
        return self.views.get(graph.name)

    def reset_zoom(self):
        view = self.get_current_view()
        if view:
            view.auto_range()

    def _handle_rename_requested(self, kind, old_name, new_name):
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
                    if view:
                        container = view.plot_widget.parent()
                        if hasattr(container, 'setTitle'):
                            container.setTitle(new_name)

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
        name = graph_data.name
        self.state.graphs[name] = graph_data
        view = MyPlotView(graph_data)
        self.views[name] = view
        container = PlotContainerWidget(name, view.plot_widget)
        self.w.center_area_widget.add_plot_widget(container)
        self.w.left_panel.refresh_tree(self.state.graphs)
        self._refresh_plot()

    def _on_downsampling_mode_changed(self, index):
        mode = self.w.right_panel.downsampling_combo.itemData(index)
        is_manual = (mode == "manual")
        self.w.right_panel.downsampling_ratio_input.setEnabled(is_manual)
        self.w.right_panel.downsampling_apply_btn.setEnabled(is_manual)
    
        curve = self.state.current_curve
        if curve:
            curve.downsampling_mode = mode
            signal_bus.curve_updated.emit()
            
    def _on_apply_downsampling_ratio(self):
        curve = self.state.current_curve
        if curve and curve.downsampling_mode == "manual":
            ratio = self.w.right_panel.downsampling_ratio_input.value()
            curve.downsampling_ratio = max(1, ratio)
            signal_bus.curve_updated.emit()

    def _on_graph_selected(self, name):
        # Empêche double déclenchement si déjà sélectionné
        if self.state.current_graph and self.state.current_graph.name == name:
            return
        self._select_graph_from_name(name)
    
    def _select_graph_from_name(self, name):
        self.service.select_graph(name)
        self._highlight_selected_graph_view(name)
        self._select_in_tree(name)
        signal_bus.graph_selected.emit(name)
    
    def _highlight_selected_graph_view(self, name):
        for graph_name, view in self.views.items():
            container = view.plot_widget.parent()
            if hasattr(container, 'set_selected'):
                container.set_selected(graph_name == name)
    
    def _select_in_tree(self, graph_name):
        model = self.w.left_panel.model
        for i in range(model.rowCount()):
            index = model.index(i, 0)
            item = model.itemFromIndex(index)
            if item.text() == graph_name:
                self.w.left_panel.tree.setCurrentIndex(index)
                break

    def _on_curve_selected_by_click(self, curve_name):
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
    
    def _select_curve_in_tree(self, curve_name):
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
        curve = self.state.current_curve
        if curve:
            curve.opacity = value
            signal_bus.curve_updated.emit()
    
    def _on_symbol_changed(self, index):
        curve = self.state.current_curve
        if curve:
            symbol = self.w.right_panel.symbol_combo.itemData(index)
            curve.symbol = symbol
            signal_bus.curve_updated.emit()
    
    def _on_fill_toggled(self, checked):
        curve = self.state.current_curve
        if curve:
            curve.fill = checked
            signal_bus.curve_updated.emit()
    
    def _on_display_mode_changed(self, index):
        curve = self.state.current_curve
        if curve:
            mode = self.w.right_panel.display_mode_combo.itemData(index)
            curve.display_mode = mode
            signal_bus.curve_updated.emit()

    def _on_gain_changed(self, value):
        curve = self.state.current_curve
        if curve:
            curve.gain = value / 100.0
            signal_bus.curve_updated.emit()
    
    def _on_offset_changed(self, value):
        curve = self.state.current_curve
        if curve:
            curve.offset = value / 100.0
            signal_bus.curve_updated.emit()
    
    def _on_show_zero_line_toggled(self, checked):
        curve = self.state.current_curve
        if curve:
            curve.show_zero_line = checked
            signal_bus.curve_updated.emit()
            
    def _on_bring_curve_to_front(self):
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
