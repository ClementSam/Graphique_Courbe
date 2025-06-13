#GraphCurvePanel.py

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QTreeView, QStyledItemDelegate, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPainter, QFont
from PyQt5.QtCore import Qt, QRect, QSize
from core.app_state import AppState
from signal_bus import signal_bus
import logging

logger = logging.getLogger(__name__)

class CombinedDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        painter.save()
        if option.state & QtWidgets.QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        rect = option.rect
        y = rect.top()
        h = rect.height()
        x = rect.left() + 5

        name = index.data(Qt.DisplayRole)
        visible = index.data(Qt.UserRole + 1)
        kind = index.data(Qt.UserRole + 3)

        if kind != "action":
            eye = "👁" if visible else "🙈"
            painter.drawText(QRect(x, y, 20, h), Qt.AlignCenter, eye)
            painter.setFont(QFont(option.font))
            painter.setPen(option.palette.text().color())
            painter.drawText(QRect(x + 25, y, 150, h), Qt.AlignVCenter, name)
            self.draw_icon(painter, QRect(x + 190, y, 24, h), "⚙️")
            self.draw_icon(painter, QRect(x + 220, y, 24, h), "🗑")
        else:
            bold_font = QtGui.QFont(option.font)
            bold_font.setBold(True)
            painter.setFont(bold_font)
            painter.setPen(option.palette.text().color())
            painter.drawText(rect.adjusted(-20, 0, 0, 0), Qt.AlignVCenter, name)

        painter.restore()

    def draw_icon(self, painter, rect, symbol):
        painter.drawText(rect, Qt.AlignCenter, symbol)
        
    def editorEvent(self, event, model, option, index):
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            pos = event.pos()
            rect = option.rect
            h = rect.height()
            y = rect.top()
            x = rect.left() + 5
    
            eye_rect = QRect(x, rect.top(), 20, h)
            delete_rect = QRect(x + 220, y, 24, h)
    
            kind = index.data(Qt.UserRole + 3)
            name = index.data(Qt.UserRole + 4)
    
            logger.debug(f"🖱️ [editorEvent] Clic détecté à la position {pos}")
            logger.debug(f"   ⤷ Type : {kind}, Nom : {name}")
            logger.debug(f"   ⤷ Rect oeil : {eye_rect}, Rect poubelle : {delete_rect}")
    
            if eye_rect.contains(pos) and kind in ("graph", "curve"):
                val = index.data(Qt.UserRole + 1)
                new_val = not val
                logger.debug(f"👁️ [Toggle Visibility] {name} → {new_val}")
                model.setData(index, new_val, Qt.UserRole + 1)
                if kind == "graph":
                    signal_bus.graph_visibility_changed.emit(name, new_val)
                else:
                    parent_index = index.parent()
                    if parent_index.data(Qt.UserRole + 3) == "curve":
                        parent_index = parent_index.parent()
                    graph_name = parent_index.data(Qt.UserRole + 4) if parent_index.isValid() else None
                    signal_bus.curve_visibility_changed.emit(graph_name, name, new_val)
                return True
    
            if delete_rect.contains(pos) and kind in ("graph", "curve"):
                logger.debug(f"🗑️ [Suppression demandée] {kind} '{name}'")
                confirm = QMessageBox.question(None, "Supprimer", f"Supprimer {kind} '{name}' ?", QMessageBox.Yes | QMessageBox.No)
                if confirm == QMessageBox.Yes:
                    logger.debug(f"✅ [Confirmé] Suppression de {kind} '{name}'")
                    signal_bus.remove_requested.emit(kind, name)
                else:
                    logger.debug(f"❌ [Annulé] Suppression de {kind} '{name}'")
                return True
    
            if kind == "action" and name == "add_graph":
                logger.debug("➕ [Delegate] Demande d'ajout de graphique")
                signal_bus.add_graph_requested.emit("graph")
                return True
    
            if kind == "action" and name.startswith("add_curve:"):
                graph_name = name.split(":")[1]
                logger.debug(f"➕ [Delegate] Demande d'ajout de courbe au graphique : {graph_name}")
                signal_bus.add_curve_requested.emit(graph_name)
                return True

    
        return super().editorEvent(event, model, option, index)

    def sizeHint(self, option, index):
        return QSize(280, 24)

# Fichier : GraphCurvePanel.py


class GraphCurvePanel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("🔧 [GraphCurvePanel.__init__] Initialisation du panneau graphique")
        self.controller = None
        self.setup_ui()
        signal_bus.graph_updated.connect(self.refresh_tree)
        signal_bus.curve_updated.connect(self.refresh_tree)

    def set_controller(self, controller):
        """Expose le contrôleur pour déclencher des actions directement."""
        self.controller = controller

    def setup_ui(self):
        logger.debug("🛠 [GraphCurvePanel.setup_ui] Construction de l'UI")
        layout = QtWidgets.QVBoxLayout(self)

        self.tree = QTreeView()
        self.tree.setHeaderHidden(True)
        self.tree.setItemDelegate(CombinedDelegate())
        self.tree.setEditTriggers(QtWidgets.QAbstractItemView.EditKeyPressed | QtWidgets.QAbstractItemView.SelectedClicked | QtWidgets.QAbstractItemView.DoubleClicked)

        self.model = QStandardItemModel()
        self.model.itemChanged.connect(self.on_item_renamed)
        self.tree.setModel(self.model)
        layout.addWidget(self.tree)
        layout.addStretch()

        self.tree.expanded.connect(self.on_item_expanded)

        self.populate_from_state()
        
        self.tree.selectionModel().currentChanged.connect(self.on_selection_changed)

    def populate_from_state(self):
        logger.debug("🧠 [populate_from_state] Début de la reconstruction de l'arbre")
        state = AppState.get_instance()
        logger.debug(f"📦 [AppState] Graphs détectés : {list(state.graphs.keys())}")
        
        expanded_names = set()
        for i in range(self.model.rowCount()):
            idx = self.model.index(i, 0)
            if self.tree.isExpanded(idx):
                item = self.model.itemFromIndex(idx)
                expanded_names.add(item.text())

        selected_index = self.tree.currentIndex()
        selected_name = selected_index.data(Qt.UserRole + 4) if selected_index.isValid() else None

        self.model.clear()

        for graph in state.graphs.values():
            logger.debug(f"➕ Ajout du graphique : {graph.name}, visible = {graph.visible}")
            graph_item = self.create_item(graph.name, "graph", visible=graph.visible, active=True)

            curve_items: dict[str, QStandardItem] = {}
            for curve in graph.curves:
                logger.debug(f"    ➕ Ajout de la courbe : {curve.name}, visible = {curve.visible}")
                item = self.create_item(curve.name, "curve", visible=curve.visible, active=False)
                curve_items[curve.name] = item
                if getattr(curve, "parent_curve", None):
                    parent_item = curve_items.get(curve.parent_curve)
                    if parent_item is not None:
                        parent_item.appendRow(item)
                    else:
                        graph_item.appendRow(item)
                else:
                    graph_item.appendRow(item)
                    has_bits = any(c.parent_curve == curve.name for c in graph.curves)
                    if not has_bits and not getattr(curve, "parent_curve", None):
                        placeholder = QStandardItem("<bits>")
                        placeholder.setEditable(False)
                        placeholder.setData("placeholder", Qt.UserRole + 3)
                        item.appendRow(placeholder)

            logger.debug(f"    ➕ Ajout du bouton 'Ajouter une courbe' pour : {graph.name}")
            add_curve_item = QStandardItem("➕ Ajouter une courbe")
            add_curve_item.setEditable(False)
            add_curve_item.setData("action", Qt.UserRole + 3)
            add_curve_item.setData(f"add_curve:{graph.name}", Qt.UserRole + 4)
            graph_item.appendRow(add_curve_item)

            self.model.appendRow(graph_item)

        logger.debug("➕ Ajout du bouton 'Ajouter graphique'")
        add_graph_item = QStandardItem("➕ Ajouter graphique")
        add_graph_item.setEditable(False)
        add_graph_item.setData("action", Qt.UserRole + 3)
        add_graph_item.setData("add_graph", Qt.UserRole + 4)
        self.model.appendRow(add_graph_item)

        for i in range(self.model.rowCount()):
            idx = self.model.index(i, 0)
            item = self.model.itemFromIndex(idx)
            if item.text() in expanded_names:
                self.tree.setExpanded(idx, True)

        if selected_name and not selected_name.startswith("add_graph") and not selected_name.startswith("add_curve"):
            for i in range(self.model.rowCount()):
                idx = self.model.index(i, 0)
                if idx.data(Qt.UserRole + 4) == selected_name:
                    self.tree.setCurrentIndex(idx)
                    break

    def refresh_tree(self, *args):
        logger.debug("🔁 [refresh_tree] Rafraîchissement demandé depuis signal_bus")
        self.populate_from_state()

    def on_item_renamed(self, item):
        logger.debug("✏️ [on_item_renamed] Item modifié")
        kind = item.data(Qt.UserRole + 3)
        old_name = item.data(Qt.UserRole + 4)
        new_name = item.text().strip()
        logger.debug(f"   ⤷ Type : {kind}, Ancien nom : {old_name}, Nouveau : {new_name}")

        if not new_name or new_name == old_name:
            item.setText(old_name)
            return

        item.setData(new_name, Qt.UserRole + 4)

        if kind == "graph":
            signal_bus.rename_requested.emit("graph", old_name, new_name)
        elif kind == "curve":
            signal_bus.rename_requested.emit("curve", old_name, new_name)

    def create_item(self, name, kind, visible, active):
        item = QStandardItem(name)
        editable = kind in ("graph", "curve")
        item.setEditable(editable)
        item.setData(visible, Qt.UserRole + 1)
        item.setData(active, Qt.UserRole + 2)
        item.setData(kind, Qt.UserRole + 3)
        item.setData(name, Qt.UserRole + 4)
        return item


    def on_selection_changed(self, current, previous):
        kind = current.data(Qt.UserRole + 3)
        name = current.data(Qt.UserRole + 4)
        
        logger.debug(f"📌 [on_selection_changed] Type = {kind}, Nom = {name}")
    
        if kind == "graph":
            logger.debug(f"📌 [GraphCurvePanel] Graphique sélectionné: {name}")
            signal_bus.graph_selected.emit(name)
        elif kind == "curve":
            parent_index = current.parent()
            if parent_index.data(Qt.UserRole + 3) == "curve":
                parent_index = parent_index.parent()
            graph_name = parent_index.data(Qt.UserRole + 4) if parent_index.isValid() else None
            logger.debug(f"📌 [GraphCurvePanel] Courbe sélectionnée: {name} dans {graph_name}")
            signal_bus.curve_selected.emit(graph_name, name)

    def on_item_expanded(self, index):
        if not self.controller:
            return

        kind = index.data(Qt.UserRole + 3)
        if kind != "curve":
            return

        item = self.model.itemFromIndex(index)
        if item.rowCount() == 0:
            return
        first_child = item.child(0)
        if first_child.data(Qt.UserRole + 3) != "placeholder":
            return

        parent_index = index.parent()
        if parent_index.data(Qt.UserRole + 3) == "curve":
            return  # ignore expansion of bit curves

        graph_name = parent_index.data(Qt.UserRole + 4) if parent_index.isValid() else None
        curve_name = index.data(Qt.UserRole + 4)

        state = AppState.get_instance()
        graph = state.graphs.get(graph_name)
        curve = next((c for c in graph.curves if c.name == curve_name), None) if graph else None
        if curve is None:
            return

        import numpy as np
        if not np.allclose(curve.y, np.round(curve.y)):
            QtWidgets.QMessageBox.warning(self, "Erreur", "Les données ne sont pas entières")
            return

        values = curve.y.astype(np.int64)
        min_bits = max(int(values.max()).bit_length(), 1)
        bit_count, ok = QtWidgets.QInputDialog.getInt(
            self,
            "Décomposer la courbe",
            f"Nombre de bits à générer (minimum {min_bits})",
            min_bits,
            min_bits,
            64,
            1,
        )
        if not ok:
            return

        item.removeRows(0, item.rowCount())
        try:
            self.controller.select_graph(graph_name)
            self.controller.select_curve(curve_name)
            self.controller.create_bit_curves(curve_name, bit_count)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Erreur", str(e))
