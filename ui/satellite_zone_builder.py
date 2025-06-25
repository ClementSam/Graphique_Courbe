from PyQt5 import QtWidgets, QtCore, QtGui

class Toolbox(QtWidgets.QListWidget):
    """Simple list widget used as a palette of items."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        for name in ["Texte", "Image", "Bouton"]:
            item = QtWidgets.QListWidgetItem(name)
            item.setData(QtCore.Qt.UserRole, name.lower())
            self.addItem(item)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item is None:
            return
        drag = QtGui.QDrag(self)
        mime = QtCore.QMimeData()
        mime.setText(item.data(QtCore.Qt.UserRole))
        drag.setMimeData(mime)
        drag.exec_(QtCore.Qt.CopyAction)

class DropView(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QtWidgets.QGraphicsScene(self))
        self.setAcceptDrops(True)
        self.setRenderHint(QtGui.QPainter.Antialiasing)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasText():
            typ = event.mimeData().text()
            pos = self.mapToScene(event.pos())
            self.create_item(typ, pos)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def create_item(self, typ: str, pos: QtCore.QPointF, text: str = ""):
        typ = typ.lower()
        if typ in {"text", "texte"}:
            item = QtWidgets.QGraphicsTextItem(text or "Texte")
            item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        elif typ in {"button", "bouton"}:
            btn = QtWidgets.QPushButton(text or "Bouton")
            item = self.scene().addWidget(btn)
            item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        else:  # image placeholder
            rect = QtWidgets.QGraphicsRectItem(0, 0, 50, 50)
            rect.setBrush(QtGui.QBrush(QtGui.QColor("lightgray")))
            rect.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
            rect.setData(0, text)
            item = rect
        item.setPos(pos)
        self.scene().addItem(item)

    def load_items(self, items: list):
        for it in items:
            pos = QtCore.QPointF(it.get("x", 0), it.get("y", 0))
            self.create_item(it.get("type", "text"), pos, it.get("text", ""))

    def get_items(self) -> list:
        result = []
        for it in self.scene().items():
            if isinstance(it, QtWidgets.QGraphicsTextItem):
                result.append({
                    "type": "text",
                    "text": it.toPlainText(),
                    "x": it.pos().x(),
                    "y": it.pos().y(),
                })
            elif isinstance(it, QtWidgets.QGraphicsProxyWidget):
                w = it.widget()
                if isinstance(w, QtWidgets.QPushButton):
                    result.append({
                        "type": "button",
                        "text": w.text(),
                        "x": it.pos().x(),
                        "y": it.pos().y(),
                    })
            elif isinstance(it, QtWidgets.QGraphicsRectItem):
                result.append({
                    "type": "image",
                    "text": it.data(0) or "",
                    "x": it.pos().x(),
                    "y": it.pos().y(),
                })
        result.reverse()
        return result

class SatelliteZoneBuilder(QtWidgets.QDialog):
    """Dialog to arrange items inside a satellite zone."""

    def __init__(self, items: list | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Éditeur de zone")
        layout = QtWidgets.QHBoxLayout(self)
        self.toolbox = Toolbox()
        layout.addWidget(self.toolbox)
        self.view = DropView()
        layout.addWidget(self.view, 1)
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        if items:
            self.view.load_items(items)

    def items(self) -> list:
        return self.view.get_items()
