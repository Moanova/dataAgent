# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application  : openDataAgent
# Script       : telecharger_brut.py
# Version      : 1
# Date         : 12-10-2026
# Design       : TSC
# Build        : Mistral Vibe
# ---------------------------------------------------------------------
"""Contrat Pydantic pour l'outil `telecharger_brut`.

Miroir du fichier JSON `contrats/telecharger_brut.json` et de la documentation
`docs/architecture/telecharger_brut.md`.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Entree
# ---------------------------------------------------------------------------

class TelechargerBrutInput(BaseModel):
    """Parametres d'entree de l'outil `telecharger_brut`."""

    id_ressource: str = Field(
        ...,
        description="Identifiant de la ressource, issu de `lister_ressources`.",
    )


# ---------------------------------------------------------------------------
# Sortie
# ---------------------------------------------------------------------------

class TelechargerBrutOutput(BaseModel):
    """Donnees retournees en cas de succes par `telecharger_brut`."""

    chemin_local: str = Field(description="Chemin relatif du fichier telecharge.")
    format: str = Field(description="Format du fichier telecharge.")
    licence: str = Field(description="Licence du jeu de donnees.")
    suggestion: str | None = Field(
        default=None,
        description="Suggestion en cas d'echec (ex : 'fichier_heberge_exterieurement').",
    )
