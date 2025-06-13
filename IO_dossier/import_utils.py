
import pandas as pd
from typing import List
from enum import Enum


class TimeMode(Enum):
    """How the first column of imported data should be interpreted."""

    INDEX = "index"  # No X column provided; use row indices.
    NUMERIC = "numeric"  # First column already numeric X values.
    IGNORE = "ignore"  # First column ignored, X uses row indices.
    TIMESTAMP_RELATIVE = "timestamp_relative"  # Parse timestamps, first value at 0s.
    TIMESTAMP_ABSOLUTE = "timestamp_absolute"  # Parse timestamps as seconds since epoch.

from core.models import CurveData
import logging

logger = logging.getLogger(__name__)


def _curves_from_dataframe(df: pd.DataFrame, mode: TimeMode) -> List[CurveData]:
    """Convert a pandas DataFrame to CurveData objects according to time mode."""
    curves = []

    if mode == TimeMode.INDEX:
        x = df.index.to_numpy()
        y_cols = df.columns
    elif mode == TimeMode.IGNORE:
        if df.shape[1] < 2:
            raise ValueError(
                "Le fichier doit contenir au moins deux colonnes pour ignorer la première."
            )
        x = df.index.to_numpy()
        y_cols = df.columns[1:]
    else:
        if df.shape[1] < 2:
            raise ValueError(
                "Le fichier doit contenir au moins deux colonnes pour x et y."
            )
        x_series = df.iloc[:, 0]

        if mode == TimeMode.NUMERIC:
            x = pd.to_numeric(x_series, errors="coerce").to_numpy()
        else:
            dt = pd.to_datetime(x_series, errors="coerce")
            if mode == TimeMode.TIMESTAMP_RELATIVE:
                start = dt.iloc[0]
                x = (dt - start).dt.total_seconds().to_numpy()
            else:  # TIMESTAMP_ABSOLUTE
                x = (dt.astype("int64") / 1e9).to_numpy()

        y_cols = df.columns[1:]

    for col in y_cols:
        y_data = pd.to_numeric(df[col], errors="coerce").to_numpy()
        logger.debug(
            f"📈 [_curves_from_dataframe] Courbe '{col}' avec {len(x)} points"
        )
        curves.append(CurveData(name=col, x=x, y=y_data))

    return curves


def import_curves_from_csv(
    path: str, sep: str = ",", mode: TimeMode = TimeMode.NUMERIC
) -> List[CurveData]:
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

    return _curves_from_dataframe(df, mode)


def import_curves_from_excel(path: str, mode: TimeMode = TimeMode.NUMERIC) -> List[CurveData]:
    """Import curves from an Excel file (.xls or .xlsx)."""
    logger.debug(f"📂 [import_curves_from_excel] Lecture du fichier: {path}")
    df = pd.read_excel(path)
    logger.debug(f"📝 [import_curves_from_excel] Colonnes détectées: {list(df.columns)}")
    logger.debug(f"🔢 [import_curves_from_excel] Nombre de lignes: {len(df)}")

    return _curves_from_dataframe(df, mode)


def load_curves_from_file(
    path: str, sep: str = ",", mode: TimeMode = TimeMode.NUMERIC
) -> List[CurveData]:
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
        return import_curves_from_csv(path, sep=sep, mode=mode)
    elif ext in ["xls", "xlsx"]:
        return import_curves_from_excel(path, mode=mode)
    elif ext == "json":
        df = pd.read_json(path)
        for column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    else:
        raise ValueError(f"Format de fichier non supporté: {ext}")

    return _curves_from_dataframe(df, mode)

