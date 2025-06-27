from PyQt5 import QtWidgets, QtCore, QtGui


class SatelliteZoneView(QtWidgets.QGraphicsView):
    """View to display and optionally edit satellite items."""

    def __init__(self, parent=None, editable: bool = False):
        super().__init__(parent)
        self.setScene(QtWidgets.QGraphicsScene(self))
        self._editable = editable
        self.setAcceptDrops(editable)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

    def clear_items(self):
        self.scene().clear()

    def create_item(self, typ: str, pos: QtCore.QPointF, text: str = ""):
        typ = typ.lower()
        if typ in {"text", "texte"}:
            item = QtWidgets.QGraphicsTextItem(text or "Texte")
            if self._editable:
                item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
            self.scene().addItem(item)
        elif typ in {"button", "bouton"}:
            btn = QtWidgets.QPushButton(text or "Bouton")
            item = self.scene().addWidget(btn)
            if self._editable:
                item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        else:  # image placeholder
            rect = QtWidgets.QGraphicsRectItem(0, 0, 50, 50)
            rect.setBrush(QtGui.QBrush(QtGui.QColor("lightgray")))
            rect.setData(0, text)
            item = rect
            if self._editable:
                item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
            self.scene().addItem(item)
        item.setPos(pos)
        return item

    def load_items(self, items: list):
        self.clear_items()
        for it in items:
            pos = QtCore.QPointF(it.get("x", 0), it.get("y", 0))
            self.create_item(it.get("type", "text"), pos, it.get("text", ""))

    def set_editable(self, editable: bool):
        self._editable = editable
        self.setAcceptDrops(editable)
        for item in self.scene().items():
            item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, editable)

    def dragEnterEvent(self, event):
        if self._editable and event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if self._editable and event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if self._editable and event.mimeData().hasText():
            typ = event.mimeData().text()
            pos = self.mapToScene(event.pos())
            self.create_item(typ, pos)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def get_items(self) -> list:
        """Return a list of item descriptors from the scene."""
        result = []
        for it in self.scene().items():
            if isinstance(it, QtWidgets.QGraphicsTextItem):
                result.append(
                    {
                        "type": "text",
                        "text": it.toPlainText(),
                        "x": it.pos().x(),
                        "y": it.pos().y(),
                    }
                )
            elif isinstance(it, QtWidgets.QGraphicsProxyWidget):
                w = it.widget()
                if isinstance(w, QtWidgets.QPushButton):
                    result.append(
                        {
                            "type": "button",
                            "text": w.text(),
                            "x": it.pos().x(),
                            "y": it.pos().y(),
                        }
                    )
            elif isinstance(it, QtWidgets.QGraphicsRectItem):
                result.append(
                    {
                        "type": "image",
                        "text": it.data(0) or "",
                        "x": it.pos().x(),
                        "y": it.pos().y(),
                    }
                )
        result.reverse()
        return result
