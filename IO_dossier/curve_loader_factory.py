import json
from typing import List
from core.models import CurveData
from .serializers import dict_to_curve
from .import_utils import (
    load_curves_from_file,
    import_curves_from_csv,
    import_curves_from_excel,
    TimeMode,
)
import struct
from collections import namedtuple
import numpy as np
from ui.dialogs.curve_selection_dialog import CurveSelectionDialog
from .RTxReadBin import RTxReadBin


def _select_curves(curves: List[CurveData]) -> List[CurveData]:
    """Display dialog to let the user pick which curves to import."""
    if not curves:
        return []
    dlg = CurveSelectionDialog(curves)
    if dlg.exec_() == dlg.Accepted:
        return dlg.get_selected_curves()
    return []


def load_curve_by_format(
    path: str, fmt: str, *, sep: str = ",", mode: TimeMode = TimeMode.NUMERIC
) -> List[CurveData]:
    """Load curves according to the given format and ask the user which ones to keep."""
    if isinstance(mode, str):
        mode = TimeMode(mode)
    if fmt == "internal_json":
        curves = [load_internal_json(path)]
    elif fmt == "keysight_bin":
        curves = load_keysight_bin(path)
    elif fmt == "csv_standard":
        curves = import_curves_from_csv(path, sep=sep, mode=mode)
    elif fmt == "excel":
        curves = import_curves_from_excel(path, mode=mode)
    elif fmt == "csv_or_excel":  # backward compatibility
        curves = load_curves_from_file(path, sep=sep, mode=mode)
    elif fmt == "keysight_json_v5":
        curves = load_keysight_json_v5(path)
    elif fmt == "tektro_json_v1_2":
        curves = load_tektro_json_v1_2(path)
    elif fmt == "rohde_schwarz_bin":
        curves = load_rohde_schwarz_bin(path)
    else:
        raise ValueError(f"Format inconnu : {fmt}")

    return _select_curves(curves)


def load_internal_json(path: str) -> CurveData:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return dict_to_curve(data)


def load_keysight_json_v5(path: str) -> List[CurveData]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict) or "samples" not in data:
        raise ValueError("Fichier Keysight V5 invalide")

    x = [pt[0] for pt in data["samples"]]
    y = [pt[1] for pt in data["samples"]]
    name = data.get("label", "Keysight")
    curve = CurveData(name=name, x=x, y=y)
    return [curve]


def load_tektro_json_v1_2(path: str) -> List[CurveData]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    metadata = data.get("meta", {})
    waveform = data.get("waveform", {})

    if not waveform or "X" not in waveform or "Y" not in waveform:
        raise ValueError("Fichier TEKTRO V1.2 invalide")

    x = waveform["X"]
    y = waveform["Y"]
    name = metadata.get("name", "Tektro")
    curve = CurveData(name=name, x=x, y=y)
    return [curve]


def load_keysight_bin(path: str) -> List[CurveData]:
    with open(path, "rb") as f:
        magic = f.read(2)
        version = int(f.read(2).decode("utf-8"))
        size = int.from_bytes(f.read(8 if version == 3 else 4), byteorder="little")
        count = int.from_bytes(f.read(4), byteorder="little")

        if magic not in (b"AG", b"RG"):
            raise ValueError("Fichier Keysight .bin non reconnu")

        curves = []

        for i in range(count):
            # Waveform header
            length = int.from_bytes(f.read(1), "little")
            data = bytes([length]) + f.read(length - 1)
            fields = struct.unpack("5if3d2i16s16s24s16sdI", data)
            WaveformHeader = namedtuple("WaveformHeader", [
                "size", "wave_type", "buffers", "points", "average",
                "x_d_range", "x_d_origin", "x_increment", "x_origin",
                "x_units", "y_units", "date", "time", "frame", "label",
                "time_tags", "segment"
            ])
            header = WaveformHeader(*fields)

            # Data header
            length = int.from_bytes(f.read(1), "little")
            data_header = bytes([length]) + f.read(length - 1)
            if version == 3:
                fields = struct.unpack("i2hQ", data_header)
            else:
                fields = struct.unpack("i2hi", data_header)
            _, data_type, _, data_len = fields

            raw = f.read(data_len)
            dtype = np.float32 if data_type in [1, 2, 3] else np.uint8
            y = np.frombuffer(raw, dtype=dtype)

            x = np.linspace(header.x_d_origin, header.x_d_origin + header.x_d_range, len(y))
            label = header.label.decode().strip("\x00") or f"Waveform {i + 1}"

            curves.append(CurveData(name=label, x=x, y=y))

    return curves


def load_rohde_schwarz_bin(path: str) -> List[CurveData]:
    """Load waveform exported by Rohde & Schwarz oscilloscopes."""
    y, x, _ = RTxReadBin(path)
    y_arr = np.asarray(y)
    x_arr = np.asarray(x)

    if y_arr.ndim == 1:
        y_arr = y_arr[:, np.newaxis, np.newaxis]
    elif y_arr.ndim == 2:
        # assume (samples, channels) or (samples, acquisitions)
        y_arr = y_arr[:, np.newaxis, :]

    if x_arr.ndim == 1:
        x_arr = x_arr[:, np.newaxis]

    n_samples, n_acq, n_ch = y_arr.shape
    curves = []
    for ch in range(n_ch):
        curves.append(
            CurveData(
                name=f"Channel {ch + 1}",
                x=x_arr[:, 0],
                y=y_arr[:, 0, ch],
            )
        )

    return curves
