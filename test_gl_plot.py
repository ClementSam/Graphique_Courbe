# import sys
# import numpy as np
# from PyQt5 import QtWidgets
# import pyqtgraph.opengl as gl
# import pyqtgraph as pg
# from curve_loader_factory import load_keysight_bin

# def plot_with_glview(curves):
#     app = QtWidgets.QApplication(sys.argv)
#     w = gl.GLViewWidget()
#     w.setWindowTitle("GLView - Test Rendu GPU .bin")
#     w.setCameraPosition(distance=50)
#     w.show()

#     for curve in curves:
#         x, y = curve.x, curve.y
#         # Convertir en coordonnées 3D (z=0)
#         pts = np.vstack([x, y, np.zeros_like(x)]).T
#         color = pg.glColor(curve.color if hasattr(curve, "color") else "r")
#         item = gl.GLLinePlotItem(pos=pts, color=color, width=1.5, antialias=True)
#         w.addItem(item)

#     sys.exit(app.exec_())

# if __name__ == "__main__":
#     from PyQt5.QtWidgets import QFileDialog
#     app = QtWidgets.QApplication(sys.argv)
#     path, _ = QFileDialog.getOpenFileName(None, "Choisir un fichier .bin", "", "Fichiers bin (*.bin)")
#     if path:
#         curves = load_keysight_bin(path)
#         if curves:
#             plot_with_glview(curves)
#         else:
#             print("Aucune courbe sélectionnée.")
#     else:
#         print("Aucun fichier sélectionné.")



import sys
import plotly.graph_objects as go
from PyQt5.QtWidgets import QApplication, QFileDialog
from curve_loader_factory import load_keysight_bin
import os

def show_curves_with_plotly(curves):
    fig = go.Figure()
    for curve in curves:
        fig.add_trace(go.Scattergl(
            x=curve.x,
            y=curve.y,
            mode='lines',
            name=curve.name,
            line=dict(width=1)
        ))
    fig.update_layout(
        title="Visualisation Plotly (WebGL)",
        xaxis_title="Temps",
        yaxis_title="Amplitude",
        showlegend=True,
        height=700
    )
    fig.write_html("plot_test.html")
    os.system(f'start "" "{os.path.abspath("plot_test.html")}"')  # Windows

if __name__ == "__main__":
    app = QApplication(sys.argv)
    path, _ = QFileDialog.getOpenFileName(None, "Sélectionner un fichier .bin", "", "Fichiers bin (*.bin)")
    if path:
        curves = load_keysight_bin(path)
        if curves:
            show_curves_with_plotly(curves)
        else:
            print("Aucune courbe sélectionnée.")
    else:
        print("Aucun fichier sélectionné.")

