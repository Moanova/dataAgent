# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application  : openDataAgent
# Script       : licence.py
# Version      : 1
# Date         : 12-10-2026
# Design       : Mistral Vibe
# Build        : Mistral Vibe
# ---------------------------------------------------------------------
"""Filtre de licence du projet openDataAgent (T3.1.2).

Deterministe : aucune decision agentique. Une licence absente, nulle
ou vide est refusee (comportement sur par defaut). L'evaluation est
insensible a la casse et aux espaces parasites.
"""
from typing import Optional

LICENCES_ACCEPTES = frozenset({
    "lov2",
    "fr-lo",
    "odc-odbl",
    "cc-by",
    "cc-by-sa",
    "cc-zero",
    "other-open",
})


def licence_est_acceptable(licence: Optional[str]) -> bool:
    """Retourne True si la licence est compatible avec la politique du projet.

    Politique (docs/architecture/contrat_global.md) : licences acceptees
    `lov2`, `fr-lo`, `odc-odbl`, `cc-by`, `cc-by-sa`, `cc-zero`, `other-open` ; toute
    autre valeur — y compris absente, nulle ou vide — est refusee.
    """
    if not isinstance(licence, str):
        return False
    return licence.strip().lower() in LICENCES_ACCEPTES
