from PyQt5 import QtWidgets, QtCore
import logging

logger = logging.getLogger(__name__)

class AdvancedPlotContainer(QtWidgets.QWidget):
    def __init__(self, plot_widget, parent=None):
        logger.debug("[AdvancedPlotContainer.py > __init__()] ▶️ Entrée dans __init__()")
        super().__init__(parent)

        self.layout = QtWidgets.QGridLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.top_box = QtWidgets.QWidget()
        self.left_box = QtWidgets.QWidget()
        self.right_box = QtWidgets.QWidget()
        self.bottom_box = QtWidgets.QWidget()

        for box_name, box in zip(["top", "left", "right", "bottom"],
                                 [self.top_box, self.left_box, self.right_box, self.bottom_box]):
            layout = QtWidgets.QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(2)
            box.setLayout(layout)
            logger.debug(f"[INIT] Zone {box_name}_box initialisée avec layout {layout}")

        self.left_box.layout().setAlignment(QtCore.Qt.AlignTop)
        self.right_box.layout().setAlignment(QtCore.Qt.AlignTop)

        # #debug
        # label = QtWidgets.QLabel("TEST ⟵")
        # label.setStyleSheet("background: orange; border: 2px solid black;")
        # self.left_box.layout().addWidget(label)

        self.layout.addWidget(self.top_box,    0, 1)
        self.layout.addWidget(self.left_box,   1, 0)
        self.layout.addWidget(plot_widget,     1, 1)
        self.layout.addWidget(self.right_box,  1, 2)
        self.layout.addWidget(self.bottom_box, 2, 1)

        self.layout.setColumnStretch(1, 1)
        self.layout.setRowStretch(1, 1)
        #self.layout.setColumnMinimumWidth(0, 100)
        #self.layout.setColumnMinimumWidth(2, 60)
        self.layout.setColumnMinimumWidth(0, 0)
        self.layout.setColumnMinimumWidth(2, 0)


        self.top_box.setStyleSheet("background-color: rgba(0, 0, 255, 0.05);")
        self.left_box.setStyleSheet("background-color: rgba(0, 0, 255, 0.05);")
        self.right_box.setStyleSheet("background-color: rgba(0, 0, 255, 0.05);")
        self.bottom_box.setStyleSheet("background-color: rgba(0, 0, 255, 0.05);")

        #self.left_box.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)

        logger.debug("[AdvancedPlotContainer] ✅ Initialisation terminée")

    def add_to_top(self, widget):
        logger.debug("[AdvancedPlotContainer.py > add_to_top()] ▶️ Entrée dans add_to_top()")
        self.top_box.layout().addWidget(widget)
        logger.debug(f"[AdvancedPlotContainer] ➕ Widget ajouté en haut: {widget}")

    def add_to_left(self, widget):
        logger.debug("[AdvancedPlotContainer.py > add_to_left()] ▶️ Entrée dans add_to_left()")
        logger.debug(f"[AdvancedPlotContainer] ✅ Widget reçu: {widget}, visible={widget.isVisible()}, size={widget.size()}")

        self.left_box.setVisible(True)
        self.left_box.setMinimumWidth(120)

        widget.setVisible(True)
        widget.setMinimumSize(120, 100)
        widget.setStyleSheet(widget.styleSheet() + " border: 2px dashed green;")

        self.left_box.layout().addWidget(widget)
        logger.debug(f"[AdvancedPlotContainer] 🧩 Widget inséré dans left_box → {widget}, taille: {widget.size()}, visible: {widget.isVisible()}")

    def add_to_right(self, widget):
        logger.debug("[AdvancedPlotContainer.py > add_to_right()] ▶️ Entrée dans add_to_right()")
        self.right_box.layout().addWidget(widget)
        logger.debug(f"[AdvancedPlotContainer] ➕ Widget ajouté à droite: {widget}")

    def add_to_bottom(self, widget):
        logger.debug("[AdvancedPlotContainer.py > add_to_bottom()] ▶️ Entrée dans add_to_bottom()")
        self.bottom_box.layout().addWidget(widget)
        logger.debug(f"[AdvancedPlotContainer] ➕ Widget ajouté en bas: {widget}")





























