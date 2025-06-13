
import pandas as pd
from typing import List
from core.models import CurveData
import logging

logger = logging.getLogger(__name__)


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
    logger.debug(f"📂 [import_curves_from_csv] Lecture du fichier: {path} (sep='{sep}')")
    df = pd.read_csv(path, sep=sep, decimal=',')
    logger.debug(f"📝 [import_curves_from_csv] Colonnes détectées: {list(df.columns)}")
    logger.debug(f"🔢 [import_curves_from_csv] Nombre de lignes: {len(df)}")

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
        x_data = df[x_col].to_numpy()
        y_data = df[col].to_numpy()
        logger.debug(
            f"📈 [import_curves_from_csv] Courbe '{col}' avec {len(x_data)} points"
        )
        curves.append(
            CurveData(
                name=col,
                x=x_data,
                y=y_data,
            )
        )
    return curves


def import_curves_from_excel(path: str) -> List[CurveData]:
    """Import curves from an Excel file (.xls or .xlsx)."""
    logger.debug(f"📂 [import_curves_from_excel] Lecture du fichier: {path}")
    df = pd.read_excel(path)
    logger.debug(f"📝 [import_curves_from_excel] Colonnes détectées: {list(df.columns)}")
    logger.debug(f"🔢 [import_curves_from_excel] Nombre de lignes: {len(df)}")

    if df.shape[1] < 2:
        raise ValueError("Le fichier doit contenir au moins deux colonnes pour x et y.")

    x_col = df.columns[0]
    y_cols = df.columns[1:]

    curves = []
    for col in y_cols:
        x_data = pd.to_numeric(df[x_col], errors="coerce").to_numpy()
        y_data = pd.to_numeric(df[col], errors="coerce").to_numpy()
        logger.debug(
            f"📈 [import_curves_from_excel] Courbe '{col}' avec {len(x_data)} points"
        )
        curves.append(CurveData(name=col, x=x_data, y=y_data))

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
    logger.debug(f"📂 [load_curves_from_file] Lecture du fichier: {path}")
    ext = path.lower().split('.')[-1]
    if ext == "csv":
        return import_curves_from_csv(path, sep=sep)
    elif ext in ["xls", "xlsx"]:
        return import_curves_from_excel(path)
    elif ext == "json":
        df = pd.read_json(path)
        for column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    else:
        raise ValueError(f"Format de fichier non supporté: {ext}")

    if df.shape[1] < 2:
        raise ValueError("Le fichier doit contenir au moins deux colonnes pour x et y.")

    x_col = df.columns[0]
    y_cols = df.columns[1:]

    curves = []
    for col in y_cols:
        x_data = df[x_col].to_numpy()
        y_data = df[col].to_numpy()
        logger.debug(
            f"📈 [load_curves_from_file] Courbe '{col}' avec {len(x_data)} points"
        )
        curves.append(
            CurveData(
                name=col,
                x=x_data,
                y=y_data,
            )
        )
    return curves

