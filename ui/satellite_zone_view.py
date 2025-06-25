from PyQt5 import QtWidgets, QtCore, QtGui

class SatelliteZoneView(QtWidgets.QGraphicsView):
    """Read-only view to display satellite items at absolute positions."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QtWidgets.QGraphicsScene(self))
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
        elif typ in {"button", "bouton"}:
            btn = QtWidgets.QPushButton(text or "Bouton")
            item = self.scene().addWidget(btn)
        else:  # image placeholder
            rect = QtWidgets.QGraphicsRectItem(0, 0, 50, 50)
            rect.setBrush(QtGui.QBrush(QtGui.QColor("lightgray")))
            rect.setData(0, text)
            item = rect
        item.setPos(pos)
        self.scene().addItem(item)

    def load_items(self, items: list):
        self.clear_items()
        for it in items:
            pos = QtCore.QPointF(it.get("x", 0), it.get("y", 0))
            self.create_item(it.get("type", "text"), pos, it.get("text", ""))

