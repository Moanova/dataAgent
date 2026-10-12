# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application  : openDataAgent
# Script       : interroger_ressource.py
# Version      : 1
# Date         : 12-10-2026
# Design       : TSC
# Build        : Mistral Vibe
# ---------------------------------------------------------------------
"""Contrat Pydantic pour l'outil `interroger_ressource`.

Miroir du fichier JSON `contrats/interroger_ressource.json` et de la documentation
`docs/architecture/interroger_ressource.md`.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class OperateurFiltre(str, Enum):
    """Operateurs de filtrage disponibles pour une colonne."""

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


# ---------------------------------------------------------------------------
# Sous-modeles
# ---------------------------------------------------------------------------

class FiltreColonne(BaseModel):
    """Filtre applicable sur une colonne (une colonne a la fois)."""

    colonne: str = Field(description="Nom de la colonne a filtrer.")
    valeur: str = Field(description="Valeur de comparaison.")
    operateur: OperateurFiltre = Field(
        default=OperateurFiltre.EXACT,
        description="Operateur de comparaison (defaut : exact).",
    )


class TriColonne(BaseModel):
    """Tri applicable sur une colonne."""

    colonne: str = Field(description="Nom de la colonne a trier.")
    ordre: OrdreTri = Field(description="Ordre de tri (croissant ou decroissant).")


# ---------------------------------------------------------------------------
# Entree
# ---------------------------------------------------------------------------

class InterrogerRessourceInput(BaseModel):
    """Parametres d'entree de l'outil `interroger_ressource`."""

    id_ressource: str = Field(
        ...,
        description="Identifiant de la ressource, issu de `lister_ressources`.",
    )
    page: int = Field(
        default=1,
        ge=1,
        description="Numero de page (defaut : 1).",
    )
    taille_page: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Nombre d'elements par page (defaut : 20, max : 100).",
    )
    filtre: FiltreColonne | None = Field(
        default=None,
        description="Filtre optionnel sur une colonne.",
    )
    tri: TriColonne | None = Field(
        default=None,
        description="Tri optionnel sur une colonne.",
    )


# ---------------------------------------------------------------------------
# Sortie
# ---------------------------------------------------------------------------

class InterrogerRessourceOutput(BaseModel):
    """Donnees retournees en cas de succes par `interroger_ressource`."""

    total_lignes: int = Field(description="Nombre total de lignes de la ressource.")
    colonnes: list[str] = Field(description="Schema detecte (noms des colonnes).")
    lignes: list[dict[str, Any]] = Field(description="Page courante de donnees.")
    page: int = Field(description="Numero de la page retournee.")
    recommandation: str | None = Field(
        default=None,
        description="Recommandation pour les volumes eleves "
                    "(ex : 'volume_eleve_telechargement_brut_suggere').",
    )
