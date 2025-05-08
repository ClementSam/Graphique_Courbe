import json
import base64
from PyQt5.QtWidgets import QMainWindow
from pathlib import Path

LAYOUT_FILE = Path("layouts.json")


def _load_data():
    if not LAYOUT_FILE.exists():
        return {"default": None, "presets": {}}
    with open(LAYOUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_data(data):
    with open(LAYOUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def save_layout(name: str, main_window: QMainWindow):
    data = _load_data()
    state_bytes = main_window.saveState()
    encoded = base64.b64encode(state_bytes).decode("utf-8")
    data["presets"][name] = encoded
    _save_data(data)


def load_layout(name: str, main_window: QMainWindow):
    data = _load_data()
    encoded = data["presets"].get(name)
    if not encoded:
        raise ValueError(f"Disposition '{name}' non trouvée.")
    state_bytes = base64.b64decode(encoded)
    main_window.restoreState(state_bytes)


def delete_layout(name: str):
    data = _load_data()
    if name in data["presets"]:
        del data["presets"][name]
        _save_data(data)


def list_layouts():
    data = _load_data()
    return list(data["presets"].keys())


def set_default_layout(name: str):
    data = _load_data()
    if name not in data["presets"]:
        raise ValueError(f"Disposition '{name}' non trouvée.")
    data["default"] = name
    _save_data(data)


def get_default_layout():
    data = _load_data()
    return data.get("default")
