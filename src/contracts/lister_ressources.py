# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application  : openDataAgent
# Script       : lister_ressources.py
# Version      : 1
# Date         : 12-10-2026
# Design       : Mistral Vibe
# Build        : Mistral Vibe
# ---------------------------------------------------------------------
"""Contrat Pydantic pour l'outil `lister_ressources`.

Miroir du fichier JSON `contrats/lister_ressources.json` et de la documentation
`docs/architecture/lister_ressources.md`.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.contracts.base import ClasseRessource, RessourceResume

__all__ = ["ClasseRessource", "ListerRessourcesInput", "ListerRessourcesOutput"]


# ---------------------------------------------------------------------------
# Entrée
# ---------------------------------------------------------------------------

class ListerRessourcesInput(BaseModel):
    model_config = ConfigDict(extra="ignore")
    """Paramètres d'entrée de l'outil `lister_ressources`."""

    id_jeu: str = Field(
        ...,
        description="Identifiant du jeu de données, issu de `rechercher_jeux`.",
    )


# ---------------------------------------------------------------------------
# Sortie
# ---------------------------------------------------------------------------

class ListerRessourcesOutput(BaseModel):
    """Données retournées en cas de succès par `lister_ressources`."""

    ressources: list[RessourceResume] = Field(
        description="Inventaire des ressources du jeu avec classification.",
    )
    indetermination: list[str] = Field(
        default_factory=list,
        description="Identifiants des ressources non classées automatiquement.",
    )
