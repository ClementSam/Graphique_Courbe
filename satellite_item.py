# satellite_item.py
from abc import ABC, abstractmethod
from PyQt5.QtWidgets import QWidget

class SatelliteItem(ABC):
    @abstractmethod
    def get_widget(self) -> QWidget:
        print("[satellite_item.py > get_widget()] ▶️ Méthode abstraite appelée")
        """Retourne le widget à afficher (QLabel, QPushButton, etc.)"""
        pass

    @abstractmethod
    def get_zone(self) -> str:
        print("[satellite_item.py > get_zone()] ▶️ Méthode abstraite appelée")
        """Retourne 'left', 'right', 'top' ou 'bottom'"""
        pass
