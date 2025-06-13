
import pandas as pd
from typing import List
from core.models import CurveData


def import_curves_from_csv(path: str, sep: str = ",") -> List[CurveData]:
    """Import curves from a CSV file.

    Parameters
    ----------
    path:
        Path to the CSV file.
    sep:
        Column separator used in the file (default is comma).

    The first column is used as the X axis and all subsequent columns are
    interpreted as Y values for individual curves. Each curve name is taken
    from the corresponding column header.
    """
    df = pd.read_csv(path, sep=sep)

    # Ensure numeric types for all columns, converting invalid entries to NaN
    for column in df.columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    if df.shape[1] < 2:
        raise ValueError(
            "Le fichier doit contenir au moins deux colonnes pour x et y."
        )

    x_col = df.columns[0]
    y_cols = df.columns[1:]

    curves = []
    for col in y_cols:
        curves.append(
            CurveData(
                name=col,
                x=df[x_col].to_numpy(),
                y=df[col].to_numpy(),
            )
        )
    return curves


def load_curves_from_file(path: str, sep: str = ",") -> List[CurveData]:
    """Charge des courbes à partir d'un fichier CSV, Excel ou JSON.

    Parameters
    ----------
    path:
        Path to the file to load.
    sep:
        Column separator when reading CSV files.
    """
    ext = path.lower().split('.')[-1]
    if ext == "csv":
        return import_curves_from_csv(path, sep=sep)
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
        curves.append(
            CurveData(
                name=col,
                x=df[x_col].to_numpy(),
                y=df[col].to_numpy(),
            )
        )
    return curves

