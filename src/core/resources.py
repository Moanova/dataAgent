# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application  : openDataAgent
# Script       : resources.py
# Version      : 1
# Date         : 13-10-2026
# Design       : TSC
# Build        : Mistral Vibe
# ---------------------------------------------------------------------
"""Inventaire des ressources d'un jeu de donnees (lister_ressources, T3.2.1).

L'appel enregistre les metadonnees de chaque ressource (invariant du
contrat) dans un inventaire en memoire : c'est ce qui arme
`telecharger_brut` et `interroger_ressource` ensuite, et qui permet de
refuser tout identifiant jamais delivre par la chaine.
"""
from typing import Any, Dict, Optional

from src.utils.logging import get_logger, bind_context, log_to_file
from src.utils.http import lister_ressources_api
from src.utils.registry import RegistreSourcesInaccessibles
from src.core.classification import classer_ressource

logger = get_logger("openDataAgent.core.resources")

_registre_par_defaut = RegistreSourcesInaccessibles()

# Inventaire en memoire : id_ressource -> metadonnees normalisees.
# Peuple a chaque appel de lister_ressources, consomme par telecharger_brut
# (T3.4.1) et interroger_ressource (T3.3.1).
_inventaire: Dict[str, Dict[str, Any]] = {}


def inventaire() -> Dict[str, Dict[str, Any]]:
    """Retourne une copie de l'inventaire des ressources deja vues."""
    return dict(_inventaire)


def _normaliser_ressource(ressource: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise une ressource v1 vers le format RessourceResume du contrat."""
    classe, _ = classer_ressource(
        format_ressource=ressource.get("format"),
        mime=ressource.get("mime"),
        url=ressource.get("url"),
    )
    return {
        "id": ressource["id"],
        "titre": ressource["title"],
        "format": ressource.get("format"),
        "taille_octets": ressource.get("filesize"),
        "classe": classe,
        # Detection API tabulaire : T3.3.x ; provisoirement faux.
        "api_tabulaire": False,
        # v1 : filetype "file" = heberge sur la plateforme, "remote" sinon.
        "heberge_sur_plateforme": ressource.get("filetype") == "file",
        "url": ressource["url"],
    }


def lister_ressources(
    id_jeu: str,
    id_execution: Optional[str] = None,
    registre: Optional[RegistreSourcesInaccessibles] = None,
) -> Dict[str, Any]:
    """
    Inventorie les ressources d'un jeu de donnees data.gouv.fr.

    Args:
        id_jeu (str): Identifiant du jeu, issu de `rechercher_jeux`.
        id_execution (Optional[str]): Identifiant unique pour tracer l'execution.
        registre (Optional[RegistreSourcesInaccessibles]): Registre des sources
            inaccessibles ; par defaut, l'instance globale sur data/registry.json.

    Returns:
        Dict[str, Any]: Resultat au format normalise (statut/message/donnees).
    """
    if registre is None:
        registre = _registre_par_defaut

    if id_execution:
        bind_context(id_execution=id_execution)

    logger.info("Appel de lister_ressources", id_jeu=id_jeu)
    log_to_file("Appel de lister_ressources", id_jeu=id_jeu)

    if not id_jeu:
        logger.error("Erreur de parametres : id_jeu est vide")
        return {
            "statut": "erreur_parametres",
            "message": "Le paramètre 'id_jeu' est obligatoire et ne peut être vide.",
            "donnees": {},
        }

    logger.debug("Appel HTTP à l'API data.gouv.fr", id_jeu=id_jeu)
    log_to_file("Appel HTTP à l'API data.gouv.fr", id_jeu=id_jeu)

    resultat = lister_ressources_api(id_jeu=id_jeu)

    if not resultat.reussi:
        logger.error(
            "Échec de l'appel HTTP à data.gouv.fr",
            statut=resultat.statut,
            erreur=resultat.erreur,
            id_jeu=id_jeu,
        )
        log_to_file(
            "Échec de l'appel HTTP à data.gouv.fr",
            statut=resultat.statut,
            erreur=resultat.erreur,
            id_jeu=id_jeu,
        )
        return {
            "statut": resultat.statut,
            "message": f"Échec de l'inventaire du jeu {id_jeu} : {resultat.erreur or resultat.statut}",
            "donnees": {
                "suggestion": "reprendre à rechercher_jeux" if resultat.statut == "jeu_introuvable" else "réessayer",
            },
        }

    data = resultat.donnees
    ressources_normalisees = [_normaliser_ressource(r) for r in data.get("resources", [])]

    # Invariant du contrat : l'appel enregistre les metadonnees de chaque
    # ressource ; c'est ce qui rend telecharger_brut possible ensuite.
    for ressource in ressources_normalisees:
        _inventaire[ressource["id"]] = ressource

    indetermination = [r["id"] for r in ressources_normalisees if r["classe"] == "indetermine"]

    logger.info(
        "Inventaire terminé",
        id_jeu=id_jeu,
        ressources=len(ressources_normalisees),
        indeterminees=len(indetermination),
    )
    log_to_file(
        "Inventaire terminé",
        id_jeu=id_jeu,
        ressources=len(ressources_normalisees),
        indeterminees=len(indetermination),
    )

    return {
        "statut": "succes",
        "message": "",
        "donnees": {
            "ressources": ressources_normalisees,
            "indetermination": indetermination,
        },
    }
