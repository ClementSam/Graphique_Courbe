import logging

def setup_logging(level=logging.INFO):
    """
    Configure le système de logging de l'application.

    Les niveaux de log disponibles sont (du moins au plus verbeux) :
        - CRITICAL : erreurs très graves, l'application ne peut pas continuer
        - ERROR    : erreurs qui empêchent une action
        - WARNING  : avertissements, comportement inattendu mais l'application continue
        - INFO     : informations générales sur le déroulement normal
        - DEBUG    : informations détaillées pour le débogage

    Le niveau choisi affiche tous les messages de ce niveau et des niveaux plus graves.
    Par exemple, level=logging.INFO affichera INFO, WARNING, ERROR et CRITICAL.

    Args:
        level (int, optional): Le niveau de log à utiliser (ex: logging.INFO, logging.DEBUG).
            Par défaut : logging.INFO.

    Returns:
        None
    """
    logging.basicConfig(level=level,
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
