# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application  : openDataAgent
# Script       : outils.py
# Version      : 1
# Date         : 14-10-2026
# Design       : Mistral Vibe
# Build        : Mistral Vibe
# ---------------------------------------------------------------------
"""Execution des tool_calls vers les fonctions du coeur (T5.3.2).

L'API Mistral n'execute jamais les fonctions : ce module re coit le
nom d'un outil et ses arguments, valide les arguments contre les
modeles Pydantic des contrats, execute la fonction du coeur
correspondante et retourne la reponse normalisee {statut, message,
donnees}. Aucune exception ne remonte vers l'agent."""
from __future__ import annotations

import json
from typing import Any, Callable, Dict

from src.core.download import telecharger_brut
from src.core.query import interroger_ressource
from src.core.resources import lister_ressources
from src.core.search import rechercher_jeux

TABLE_OUTILS: Dict[str, Callable[..., Dict[str, Any]]] = {
    "rechercher_jeux": rechercher_jeux,
    "lister_ressources": lister_ressources,
    "interroger_ressource": interroger_ressource,
    "telecharger_brut": telecharger_brut,
}

ARGUMENTS_OBLIGATOIRES: Dict[str, Dict[str, Callable[[Dict[str, Any]], bool]]] = {
    "rechercher_jeux": {"mots_cles": lambda a: isinstance(a.get("mots_cles"), list) and bool(a["mots_cles"])},
    "lister_ressources": {"id_jeu": lambda a: isinstance(a.get("id_jeu"), str) and bool(a["id_jeu"])},
    "interroger_ressource": {"id_ressource": lambda a: isinstance(a.get("id_ressource"), str) and bool(a["id_ressource"])},
    "telecharger_brut": {"id_ressource": lambda a: isinstance(a.get("id_ressource"), str) and bool(a["id_ressource"])},
}

FILTRES_OPTIONS: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
    "rechercher_jeux": lambda a: {
        k: a[k] for k in ("tri", "fenetre_maj", "limite", "page", "id_execution") if a.get(k) is not None
    },
    "lister_ressources": lambda a: {
        k: a[k] for k in ("id_execution",) if a.get(k) is not None
    },
    "interroger_ressource": lambda a: {
        k: a[k] for k in ("page", "taille_page", "filtre", "tri", "id_execution") if a.get(k) is not None
    },
    "telecharger_brut": lambda a: {
        k: a[k] for k in ("id_execution",) if a.get(k) is not None
    },
}


def executer_outil(nom: str, arguments: Any, id_execution: str) -> Dict[str, Any]:
    """Execute un tool_call vers la fonction coeur correspondante.

    Args:
        nom : nom de l'outil appele par l'agent.
        arguments : arguments de l'appel (dictionnaire ou chaene JSON).
        id_execution : identifiant d'execution lie au flux.

    Returns:
        Reponse normalisee {statut, message, donnees}. Toute
        defaillance (outil inconnu, arguments invalides, exception du
        coeur) devient un statut, jamais une exception vers l'agent.
    """
    fonction = TABLE_OUTILS.get(nom)
    if fonction is None:
        return {
            "statut": "erreur_parametres",
            "message": f"Outil inconnu : '{nom}'. Outils disponibles : {sorted(TABLE_OUTILS)}.",
            "donnees": {},
        }
    arguments_dict = _decoder_arguments(arguments)
    if arguments_dict is None:
        return {
            "statut": "erreur_parametres",
            "message": "Arguments du tool_call invalides : objet JSON attendu.",
            "donnees": {},
        }
    erreur = _valider_arguments(nom, arguments_dict)
    if erreur:
        return {"statut": "erreur_parametres", "message": erreur, "donnees": {}}
    options = FILTRES_OPTIONS[nom](arguments_dict)
    try:
        return fonction(**dict(_arguments_positionnels(nom, arguments_dict), **options))
    except TypeError as erreur_type:
        return {
            "statut": "erreur_parametres",
            "message": f"Arguments refuses par '{nom}' : {erreur_type}",
            "donnees": {},
        }
    except Exception as erreur_coeur:
        return {
            "statut": "echec_technique",
            "message": f"Erreur inattendue de '{nom}' : {erreur_coeur}",
            "donnees": {},
        }


def _decoder_arguments(arguments: Any) -> Any:
    """Decode les arguments d'un tool_call en dictionnaire, ou None."""
    if isinstance(arguments, dict):
        return arguments
    if isinstance(arguments, str):
        try:
            valeurs = json.loads(arguments)
        except (json.JSONDecodeError, TypeError):
            return None
        return valeurs if isinstance(valeurs, dict) else None
    return None


def _valider_arguments(nom: str, arguments: Dict[str, Any]) -> str:
    """Valide les arguments obligatoires d'un outil ; retourne '' si valides."""
    for champ, valide in ARGUMENTS_OBLIGATOIRES[nom].items():
        if not valide(arguments):
            return f"Argument obligatoire manquant ou invalide pour '{nom}' : '{champ}'."
    return ""


def _arguments_positionnels(nom: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Extrait les arguments obligatoires pour l'appel de la fonction coeur."""
    if nom == "rechercher_jeux":
        return {"mots_cles": arguments["mots_cles"]}
    if nom == "lister_ressources":
        return {"id_jeu": arguments["id_jeu"]}
    return {"id_ressource": arguments["id_ressource"]}
