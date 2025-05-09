# curve_generators.py
import numpy as np
from models import CurveData
from PyQt5.QtCore import Qt
import random

def generate_random_curve(index=1) -> CurveData:
    x = np.linspace(0, 2 * np.pi, 1000)
    y = np.sin(np.random.uniform(1, 5) * x)
    name = f"Courbe {index}"
    color = random.choice(['r', 'g', 'b', 'm', 'c', 'y'])
    return CurveData(
        name=name,
        x=x,
        y=y,
        color=color,
        style=Qt.SolidLine
    )
