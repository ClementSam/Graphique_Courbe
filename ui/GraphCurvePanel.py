#GraphCurvePanel.py

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QTreeView, QStyledItemDelegate, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPainter, QFont
from PyQt5.QtCore import Qt, QRect, QSize
from core.app_state import AppState
from signal_bus import signal_bus

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
    
            print(f"🖱️ [editorEvent] Clic détecté à la position {pos}")
            print(f"   ⤷ Type : {kind}, Nom : {name}")
            print(f"   ⤷ Rect oeil : {eye_rect}, Rect poubelle : {delete_rect}")
    
            if eye_rect.contains(pos) and kind in ("graph", "curve"):
                val = index.data(Qt.UserRole + 1)
                print(f"👁️ [Toggle Visibility] {name} → {not val}")
                model.setData(index, not val, Qt.UserRole + 1)
                signal_bus.curve_updated.emit()
                signal_bus.graph_updated.emit()
                return True
    
            if delete_rect.contains(pos) and kind in ("graph", "curve"):
                print(f"🗑️ [Suppression demandée] {kind} '{name}'")
                confirm = QMessageBox.question(None, "Supprimer", f"Supprimer {kind} '{name}' ?", QMessageBox.Yes | QMessageBox.No)
                if confirm == QMessageBox.Yes:
                    print(f"✅ [Confirmé] Suppression de {kind} '{name}'")
                    signal_bus.remove_requested.emit(kind, name)
                else:
                    print(f"❌ [Annulé] Suppression de {kind} '{name}'")
                return True
    
            if kind == "action" and name == "add_graph":
                print("➕ [Delegate] Demande d'ajout de graphique")
                signal_bus.add_graph_requested.emit("graph")
                return True
    
            if kind == "action" and name.startswith("add_curve:"):
                graph_name = name.split(":")[1]
                print(f"➕ [Delegate] Demande d'ajout de courbe au graphique : {graph_name}")
                signal_bus.add_curve_requested.emit(graph_name)
                return True

    
        return super().editorEvent(event, model, option, index)

    def sizeHint(self, option, index):
        return QSize(280, 24)

# Fichier : GraphCurvePanel.py


class GraphCurvePanel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        print("🔧 [GraphCurvePanel.__init__] Initialisation du panneau graphique")
        self.setup_ui()
        signal_bus.graph_updated.connect(self.refresh_tree)
        signal_bus.curve_updated.connect(self.refresh_tree)

    def setup_ui(self):
        print("🛠 [GraphCurvePanel.setup_ui] Construction de l'UI")
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

        self.populate_from_state()
        
        self.tree.selectionModel().currentChanged.connect(self.on_selection_changed)

    def populate_from_state(self):
        print("🧠 [populate_from_state] Début de la reconstruction de l'arbre")
        state = AppState.get_instance()
        print(f"📦 [AppState] Graphs détectés : {list(state.graphs.keys())}")
        
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
            print(f"➕ Ajout du graphique : {graph.name}, visible = {graph.visible}")
            graph_item = self.create_item(graph.name, "graph", visible=graph.visible, active=True)

            for curve in graph.curves:
                print(f"    ➕ Ajout de la courbe : {curve.name}, visible = {curve.visible}")
                curve_item = self.create_item(curve.name, "curve", visible=curve.visible, active=False)
                graph_item.appendRow(curve_item)

            print(f"    ➕ Ajout du bouton 'Ajouter une courbe' pour : {graph.name}")
            add_curve_item = QStandardItem("➕ Ajouter une courbe")
            add_curve_item.setEditable(False)
            add_curve_item.setData("action", Qt.UserRole + 3)
            add_curve_item.setData(f"add_curve:{graph.name}", Qt.UserRole + 4)
            graph_item.appendRow(add_curve_item)

            self.model.appendRow(graph_item)

        print("➕ Ajout du bouton 'Ajouter graphique'")
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
        print("🔁 [refresh_tree] Rafraîchissement demandé depuis signal_bus")
        self.populate_from_state()

    def on_item_renamed(self, item):
        print("✏️ [on_item_renamed] Item modifié")
        kind = item.data(Qt.UserRole + 3)
        old_name = item.data(Qt.UserRole + 4)
        new_name = item.text().strip()
        print(f"   ⤷ Type : {kind}, Ancien nom : {old_name}, Nouveau : {new_name}")

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
        
        print(f"📌 [on_selection_changed] Type = {kind}, Nom = {name}")
    
        if kind == "graph":
            print(f"📌 [GraphCurvePanel] Graphique sélectionné: {name}")
            signal_bus.graph_selected.emit(name)
        elif kind == "curve":
            parent_index = current.parent()
            graph_name = parent_index.data(Qt.UserRole + 4) if parent_index.isValid() else None
            print(f"📌 [GraphCurvePanel] Courbe sélectionnée: {name} dans {graph_name}")
            signal_bus.curve_selected.emit(graph_name, name)
