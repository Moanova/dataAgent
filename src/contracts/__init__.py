# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application  : openDataAgent
# Script       : __init__.py
# Version      : 1
# Date         : 12-10-2026
# Design       : TSC
# Build        : Mistral Vibe
# ---------------------------------------------------------------------
"""Package des contrats Pydantic pour les outils exposes aux agents.

Re-exporte tous les modeles pour un import facilite :
    from src.contracts import RechercherJeuxInput, StatutEnum, ReponseBase
"""

from src.contracts.base import (
    ClasseRessource,
    JeuResume,
    ReponseBase,
    RessourceResume,
    StatutEnum,
    valider_coherence_contrat,
)
from src.contracts.rechercher_jeux import (
    FenetreMaj,
    RechercherJeuxInput,
    RechercherJeuxOutput,
    TriRecherche,
)
from src.contracts.lister_ressources import (
    ListerRessourcesInput,
    ListerRessourcesOutput,
)
from src.contracts.interroger_ressource import (
    FiltreColonne,
    InterrogerRessourceInput,
    InterrogerRessourceOutput,
    OperateurFiltre,
    OrdreTri,
    TriColonne,
)
from src.contracts.telecharger_brut import (
    TelechargerBrutInput,
    TelechargerBrutOutput,
)

__all__ = [
    # Base
    "StatutEnum",
    "ClasseRessource",
    "ReponseBase",
    "JeuResume",
    "RessourceResume",
    "valider_coherence_contrat",
    # rechercher_jeux
    "TriRecherche",
    "FenetreMaj",
    "RechercherJeuxInput",
    "RechercherJeuxOutput",
    # lister_ressources
    "ListerRessourcesInput",
    "ListerRessourcesOutput",
    # interroger_ressource
    "OperateurFiltre",
    "OrdreTri",
    "FiltreColonne",
    "TriColonne",
    "InterrogerRessourceInput",
    "InterrogerRessourceOutput",
    # telecharger_brut
    "TelechargerBrutInput",
    "TelechargerBrutOutput",
]
