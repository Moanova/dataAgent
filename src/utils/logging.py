# -*- coding: utf-8 -*-
"""
Module de configuration du logging pour openDataAgent.
Utilise `structlog` pour produire des logs structurés au format JSON.
"""

import structlog
import logging
from typing import Optional, Dict, Any, TextIO
import sys
from datetime import datetime
import json
import os

# Configuration par défaut pour les métadonnées dynamiques
_default_context: Dict[str, Any] = {
    "id_execution": None,
}

# Fichier de logs pour le JSON
_log_file: Optional[TextIO] = None


def configure_logging(id_execution: Optional[str] = None) -> None:
    """
    Configure `structlog` pour produire des logs JSON.
    
    Args:
        id_execution (Optional[str]): Identifiant unique pour tracer une exécution.
            Si non fourni, un horodatage est généré.
    """
    global _log_file
    
    if id_execution is None:
        id_execution = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Mettre à jour le contexte par défaut
    _default_context["id_execution"] = id_execution
    
    # Créer le dossier de logs s'il n'existe pas
    os.makedirs("logs", exist_ok=True)
    
    # Ouvrir le fichier de logs en mode append
    _log_file = open(f"logs/openDataAgent_{id_execution}.log", "a", encoding="utf-8")
    
    # Configuration des processors pour structlog
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Configuration pour la console (format clé-valeur)
    console_processors = [
        *shared_processors,
        structlog.dev.ConsoleRenderer(),
    ]
    
    # Configuration pour le fichier (format JSON)
    file_processors = [
        *shared_processors,
        structlog.processors.JSONRenderer(),
    ]
    
    # Configuration de structlog pour la console
    structlog.configure(
        processors=console_processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configuration du logger racine pour la console
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Retourne un logger configuré pour le module spécifié.
    
    Args:
        name (str): Nom du module (ex : "openDataAgent.core.search").
    
    Returns:
        structlog.stdlib.BoundLogger: Logger configuré.
    """
    logger = structlog.get_logger(name)
    return logger.bind(**_default_context)


def bind_context(**kwargs: Any) -> None:
    """
    Met à jour le contexte global pour tous les loggers.
    
    Args:
        **kwargs: Paires clé-valeur à ajouter au contexte (ex : id_jeu="12345").
    """
    _default_context.update(kwargs)


def log_to_file(event: str, **kwargs: Any) -> None:
    """
    Écrit un log directement dans le fichier JSON.
    
    Args:
        event (str): Message de log.
        **kwargs: Champs supplémentaires à logger.
    """
    global _log_file
    if _log_file is None:
        return
    
    # Créer le log structuré
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event": event,
        **_default_context,
        **kwargs,
    }
    
    # Écrire dans le fichier
    _log_file.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    _log_file.flush()