import json
from typing import List
from models import CurveData
from serializers import dict_to_curve
from import_utils import load_curves_from_file
import struct
from collections import namedtuple
import numpy as np
from curve_selection_dialog import CurveSelectionDialog


def load_curve_by_format(path: str, fmt: str) -> List[CurveData]:
    if fmt == "internal_json":
        return [load_internal_json(path)]
    elif fmt == "keysight_bin":
        return load_keysight_bin(path)
    elif fmt == "csv_standard":
        return load_curves_from_file(path)
    elif fmt == "keysight_json_v5":
        return load_keysight_json_v5(path)
    elif fmt == "tektro_json_v1_2":
        return load_tektro_json_v1_2(path)
    else:
        raise ValueError(f"Format inconnu : {fmt}")


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

    # Affichage du sélecteur de courbes
    dlg = CurveSelectionDialog(curves)
    if dlg.exec_() == dlg.Accepted:
        return dlg.get_selected_curves()
    return []