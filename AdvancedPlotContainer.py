from PyQt5 import QtWidgets

class AdvancedPlotContainer(QtWidgets.QWidget):
    def __init__(self, plot_widget, parent=None):
        super().__init__(parent)

        self.layout = QtWidgets.QGridLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Zones satellites
        self.top_box = QtWidgets.QWidget()
        self.left_box = QtWidgets.QWidget()
        self.right_box = QtWidgets.QWidget()
        self.bottom_box = QtWidgets.QWidget()

        # Layouts pour pouvoir ajouter des éléments plus tard
        self.top_box.setLayout(QtWidgets.QVBoxLayout())
        self.left_box.setLayout(QtWidgets.QVBoxLayout())
        self.right_box.setLayout(QtWidgets.QVBoxLayout())
        self.bottom_box.setLayout(QtWidgets.QVBoxLayout())

        for box in [self.top_box, self.left_box, self.right_box, self.bottom_box]:
            box.layout().setContentsMargins(0, 0, 0, 0)
            box.layout().setSpacing(2)

        # Ajout dans la grille
        self.layout.addWidget(self.top_box,    0, 1)
        self.layout.addWidget(self.left_box,   1, 0)
        self.layout.addWidget(plot_widget,     1, 1)
        self.layout.addWidget(self.right_box,  1, 2)
        self.layout.addWidget(self.bottom_box, 2, 1)

        self.layout.setColumnStretch(1, 1)
        self.layout.setRowStretch(1, 1)
        self.layout.setColumnMinimumWidth(0, 60)  # largeur pour la colonne gauche

        
        #debug
        self.left_box.setStyleSheet("background-color: rgba(0, 0, 255, 0.05);")

    def add_to_top(self, widget):
        self.top_box.layout().addWidget(widget)

    def add_to_left(self, widget):
        self.left_box.layout().addWidget(widget)

    def add_to_right(self, widget):
        self.right_box.layout().addWidget(widget)

    def add_to_bottom(self, widget):
        self.bottom_box.layout().addWidget(widget)
