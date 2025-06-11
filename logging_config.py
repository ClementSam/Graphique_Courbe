import logging

def setup_logging(level=logging.INFO):
    """Configure standard logging for the application."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

