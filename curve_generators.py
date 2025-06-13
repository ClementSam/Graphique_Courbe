# curve_generators.py
import numpy as np
from core.models import CurveData
from PyQt5.QtCore import Qt
from core.utils import generate_random_color

def generate_random_curve(index=1) -> CurveData:
    x = np.linspace(0, 2 * np.pi, 1000)
    y = np.sin(np.random.uniform(1, 5) * x)
    name = f"Courbe {index}"
    color = generate_random_color()
    return CurveData(
        name=name,
        x=x,
        y=y,
        color=color,
        style=Qt.SolidLine
    )
