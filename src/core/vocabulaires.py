# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application  : openDataAgent
# Script       : vocabulaires.py
# Version      : 1
# Date         : 15-10-2026
# Design       : Mistral Vibe
# Build        : Mistral Vibe
# ---------------------------------------------------------------------
"""Vocabulaires fermés du projet (T10.5) — source unique de vérité.

Les valeurs fermées échangées entre la CLI, l'agent et le cœur
(critères de tri, fenêtres de mise à jour, opérateurs de filtre,
ordres de tri) sont définies ici une seule fois. Les contrats
(src/contracts/) et la CLI (src/main.py) importent ces StrEnum ;
toute évolution du vocabulaire se fait dans ce module.
"""
from __future__ import annotations

from enum import Enum

APERCU_DEFAUT = 5


class TriRecherche(str, Enum):
    """Ordre de tri des résultats de recherche."""

    PERTINENCE = "pertinence"
    RECENT = "recent"
    VUES = "vues"
    REUTILISATIONS = "reutilisations"


class FenetreMaj(str, Enum):
    """Restriction temporelle sur la dernière mise à jour."""

    TOUTES = "toutes"
    TRENTE_JOURS = "30_jours"
    DOUZE_MOIS = "12_mois"
    TROIS_ANS = "3_ans"


class OperateurFiltre(str, Enum):
    """Opérateurs de filtrage disponibles pour une colonne."""

    EXACT = "exact"
    CONTIENT = "contient"
    INFERIEUR = "inferieur"
    SUPERIEUR = "superieur"
    STRICTEMENT_INFERIEUR = "strictement_inferieur"
    STRICTEMENT_SUPERIEUR = "strictement_superieur"


class OrdreTri(str, Enum):
    """Ordre de tri pour une colonne."""

    CROISSANT = "croissant"
    DECROISSANT = "decroissant"


def valeurs(enum: type[Enum]) -> list[str]:
    """Retourne les valeurs acceptées d'un vocabulaire fermé."""
    return [membre.value for membre in enum]
