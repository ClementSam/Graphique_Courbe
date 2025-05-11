# models.py

import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class CurveData:
    name: str
    x: np.ndarray
    y: np.ndarray
    color: str = 'b'
    width: int = 2
    style: Optional[int] = None
    visible: bool = True
    downsampling_mode: str = "auto"
    downsampling_ratio: int = 1

    def __post_init__(self):
        self.x = np.array(self.x)
        self.y = np.array(self.y)
        if not self.name:
            raise ValueError("Le nom de la courbe ne peut pas être vide.")
        if len(self.x) != len(self.y):
            raise ValueError("x et y doivent avoir la même longueur.")
        if self.width < 1:
            raise ValueError("L'épaisseur de la ligne doit être >= 1.")

@dataclass
class GraphData:
    name: str
    curves: List[CurveData] = field(default_factory=list)
    grid_visible: bool = False
    dark_mode: bool = False
    log_x: bool = False
    log_y: bool = False
    font: str = "Arial"
    visible: bool = True

    def add_curve(self, curve: CurveData):
        self.curves.append(curve)

    def remove_curve_by_name(self, curve_name: str):
        self.curves = [c for c in self.curves if c.name != curve_name]

    def clear_curves(self):
        self.curves.clear()

    def apply_to_view(self, plot_view):
        plot_view.update_graph_properties()