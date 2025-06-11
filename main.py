#main.py

from PyQt5 import QtWidgets
from core.startup import check_expiry_date
from core.app import launch_app
import sys

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    check_expiry_date()
    launch_app()
