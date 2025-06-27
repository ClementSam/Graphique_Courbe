# models.py

import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class DataType(str, Enum):
    """Supported data storage types for curves."""

    FLOAT64 = "float64"
    UINT8 = "uint8"
    UINT16 = "uint16"
    UINT32 = "uint32"

@dataclass
class CurveData:
    name: str
    x: np.ndarray
    y: np.ndarray
    dtype: DataType = DataType.FLOAT64
    color: str = 'b'
    width: int = 2
    style: Optional[int] = None
    visible: bool = True
    downsampling_mode: str = "auto"
    downsampling_ratio: int = 1
    opacity: float = 100.0  # en pourcentage (0 à 100)
    symbol: Optional[str] = None  # ex: 'o', 't', 's', 'd'
    fill: bool = False
    display_mode: str = "line"  # 'line', 'scatter', 'bar'
    gain: float = 1.0
    units_per_grid: float = 1.0
    gain_mode: str = "multiplier"  # "multiplier" or "unit"
    offset: float = 0.0
    time_offset: float = 0.0
    zero_indicator: str = "none"  # "none", "line"
    label_mode: str = "none"  # valeurs possibles : "none", "inline", "legend"
    # When this curve represents a single bit extracted from another curve,
    # *bit_index* stores the index (0 = LSB) and *parent_curve* references the
    # source curve name. These fields remain ``None`` for normal curves.
    bit_index: Optional[int] = None
    parent_curve: Optional[str] = None


    def __post_init__(self):
        self.x = np.array(self.x, dtype=np.float64)
        self.y = np.array(self.y)
        if self.dtype != DataType.FLOAT64:
            self.y = self.y.astype(self.dtype.value)
        if not self.name:
            raise ValueError("Le nom de la courbe ne peut pas être vide.")
        if len(self.x) != len(self.y):
            raise ValueError("x et y doivent avoir la même longueur.")
        if self.width < 1:
            raise ValueError("L'épaisseur de la ligne doit être >= 1.")

        # Keep gain and units_per_grid consistent depending on gain_mode
        if self.gain_mode == "unit":
            if self.units_per_grid:
                self.gain = 1.0 / self.units_per_grid
        else:
            if self.gain:
                self.units_per_grid = 1.0 / self.gain

    @property
    def is_bit_curve(self) -> bool:
        return self.bit_index is not None

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
    fix_y_range: bool = False
    y_min: float = -5.0
    y_max: float = 5.0
    x_unit: str = ""
    y_unit: str = ""
    x_format: str = "normal"  # valeurs possibles : "normal", "scientific", "scaled"
    y_format: str = "normal"
    mode: str = "standard"  # mode d'affichage spécifique au graphique
    satellite_zones_visible: dict[str, bool] = field(
        default_factory=lambda: {
            "left": True,
            "right": True,
            "top": True,
            "bottom": True,
        }
    )

    satellite_visibility: dict[str, bool] = field(
        default_factory=lambda: {
            "left": False,
            "right": False,
            "top": False,
            "bottom": False,
        }
    )

    satellite_content: dict[str, Optional[str]] = field(
        default_factory=lambda: {
            "left": None,
            "right": None,
            "top": None,
            "bottom": None,
        }
    )

    satellite_settings: dict[str, dict] = field(
        default_factory=lambda: {
            "left": {"color": "#ffffff", "size": 100, "items": []},
            "right": {"color": "#ffffff", "size": 100, "items": []},
            "top": {"color": "#ffffff", "size": 100, "items": []},
            "bottom": {"color": "#ffffff", "size": 100, "items": []},
        }
    )

    satellite_edit_mode: dict[str, bool] = field(
        default_factory=lambda: {
            "left": False,
            "right": False,
            "top": False,
            "bottom": False,
        }
    )

    zones: List[dict] = field(default_factory=list)


    def add_curve(self, curve: CurveData):
        self.curves.append(curve)

    def remove_curve_by_name(self, curve_name: str):
        self.curves = [c for c in self.curves if c.name != curve_name]

    def clear_curves(self):
        self.curves.clear()

    def apply_to_view(self, plot_view):
        plot_view.update_graph_properties()
