# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application  : openDataAgent
# Script       : rechercher_jeux.py
# Version      : 1
# Date         : 12-10-2026
# Design       : TSC
# Build        : Mistral Vibe
# ---------------------------------------------------------------------
"""Contrat Pydantic pour l'outil `rechercher_jeux`.

Miroir du fichier JSON `contrats/rechercher_jeux.json` et de la documentation
`docs/architecture/rechercher_jeux.md`.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from src.contracts.base import JeuResume


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TriRecherche(str, Enum):
    """Ordre de tri des resultats."""

    PERTINENCE = "pertinence"
    RECENT = "recent"
    VUES = "vues"
    REUTILISATIONS = "reutilisations"


class FenetreMaj(str, Enum):
    """Restriction temporelle sur la derniere mise a jour."""

    TOUTES = "toutes"
    TRENTE_JOURS = "30_jours"
    DOUZE_MOIS = "12_mois"
    TROIS_ANS = "3_ans"


# ---------------------------------------------------------------------------
# Entree
# ---------------------------------------------------------------------------

class RechercherJeuxInput(BaseModel):
    """Parametres d'entree de l'outil `rechercher_jeux`.

    La recherche applique une logique ET sur les mots-cles.
    """

    mots_cles: list[str] = Field(
        ...,
        min_length=1,
        description="Mots-cles de la recherche, combines en logique ET.",
    )
    tri: TriRecherche = Field(
        default=TriRecherche.PERTINENCE,
        description="Ordre de tri des resultats.",
    )
    fenetre_maj: FenetreMaj = Field(
        default=FenetreMaj.TOUTES,
        description="Restriction temporelle sur la derniere mise a jour.",
    )
    limite: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Nombre maximum de jeux retournes (defaut : 10, max : 20).",
    )


# ---------------------------------------------------------------------------
# Sortie
# ---------------------------------------------------------------------------

class RechercherJeuxOutput(BaseModel):
    """Donnees retournees en cas de succes par `rechercher_jeux`."""

    total_trouves: int = Field(description="Nombre total de jeux correspondant a la requete.")
    jeux: list[JeuResume] = Field(description="Liste resumee des jeux de donnees.")
    exclus_licence: int = Field(description="Nombre de jeux ecartes par le filtre de licence.")
