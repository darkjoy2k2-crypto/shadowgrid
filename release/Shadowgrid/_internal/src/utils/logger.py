import logging
import sys
import traceback
from pathlib import Path

def setup_logger() -> logging.Logger:
    """Konfiguriert den globalen Logger, der in game.log schreibt."""
    log_file = Path("game.log")
    
    # Logger-Konfiguration
    logger = logging.getLogger("Shadowgrid")
    logger.setLevel(logging.DEBUG)
    
    # File Handler
    file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    
    # Globaler Exception Hook um unhandled exceptions in die Log-Datei zu schreiben
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger.critical("Unbehandelte Exception", exc_info=(exc_type, exc_value, exc_traceback))
        
    sys.excepthook = handle_exception
    
    return logger

logger = setup_logger()
