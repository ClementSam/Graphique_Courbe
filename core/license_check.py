# core/license_check.py

"""
Vérification de la date d'expiration de l'application.
Affiche un message d'erreur et bloque l'accès si la date est dépassée.
"""

from datetime import datetime
from PyQt5 import QtWidgets

def check_expiry_date():
    """
    Vérifie si la date d'expiration de l'application est dépassée.
    Affiche un message d'erreur si la licence est expirée.

    Returns:
        bool: True si la licence est valide, False sinon.
    """
    expiry = datetime(2027, 6, 30)
    if datetime.now() > expiry:
        QtWidgets.QMessageBox.critical(
            None,
            "Accès expiré",
            f"Cette version a expiré le {expiry.strftime('%d/%m/%Y')}. Veuillez contacter l’auteur."
        )
        return False
    return True