# main.py

import sys
import logging
from PyQt5 import QtWidgets
from core.license_check import check_expiry_date
from core.app import launch_app
from logging_config import setup_logging

def main():
    app = QtWidgets.QApplication(sys.argv)
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting application...")
    if not check_expiry_date():
        logger.error("Application expired. Exiting now.")
        sys.exit(1)
    logger.info("Application started successfully.")
    launch_app() # launch_app() will not return because it calls sys.exit() internally.

if __name__ == "__main__":
    main()