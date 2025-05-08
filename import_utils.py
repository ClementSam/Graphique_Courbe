
import pandas as pd
from typing import List
from models import CurveData


def load_curves_from_file(path: str) -> List[CurveData]:
    """Charge des courbes à partir d'un fichier CSV, Excel ou JSON."""
    ext = path.lower().split('.')[-1]
    if ext == "csv":
        df = pd.read_csv(path)
    elif ext in ["xls", "xlsx"]:
        df = pd.read_excel(path)
    elif ext == "json":
        df = pd.read_json(path)
    else:
        raise ValueError(f"Format de fichier non supporté: {ext}")

    if df.shape[1] < 2:
        raise ValueError("Le fichier doit contenir au moins deux colonnes pour x et y.")

    x_col = df.columns[0]
    y_cols = df.columns[1:]

    curves = []
    for col in y_cols:
        curves.append(CurveData(
            name=col,
            x=df[x_col].to_numpy(),
            y=df[col].to_numpy()
        ))
    return curves
