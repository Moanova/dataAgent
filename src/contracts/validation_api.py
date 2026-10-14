# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application  : openDataAgent
# Script       : validation_api.py
# Version      : 1
# Date         : 12-10-2026
# Design       : Mistral Vibe
# Build        : Mistral Vibe
# ---------------------------------------------------------------------
"""Validation des reponses brutes de l'API data.gouv.fr avec jsonschema.

Tache T2.2. Ce module valide la couche entrante : les charges utiles
brutes retourn"es par l'API data.gouv.fr, avant tout traitement, contre
les schemas JSON stockés dans `contrats/schemas_api/`. Les schémas des
outils (`contrats/<outil>.json`) restent la source de verite pour le
function calling Mistral ; les modèles Pydantic (`src/contracts/`)
valident la couche sortante.

Tout "cart de sch"ma doit produire un échec propre (`echec_technique`),
jamais une exception non gérée.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema
from jsonschema.protocols import Validator

REPERTOIRE_SCHEMAS = Path(__file__).resolve().parents[2] / "contrats" / "schemas_api"

SCHEMAS_CONNUS: Dict[str, str] = {
    "rechercher_jeux": "rechercher_jeux.reponse.json",
    "lister_ressources": "lister_ressources.reponse.json",
    "interroger_ressource": "interroger_ressource.reponse.json",
}


@dataclass
class ResultatValidation:
    """Résultat d'une validation de reponse API.

    Attributs :
        valide : True si la charge utile est conforme au schema.
        erreurs : liste de messages lisibles, un par écart détécté,
                  avec le chemin JSON de l'element fautif.
    """

    valide: bool
    erreurs: List[str] = field(default_factory=list)

    @property
    def statut(self) -> str:
        """Code de statut normalisé associé au résultat."""
        return "succes" if self.valide else "echec_technique"


def charger_schema(nom_outil: str, repertoire: Optional[Path] = None) -> Dict[str, Any]:
    """Charge le schema JSON de réponse pour l'outil donné.

    Raises:
        KeyError : si le nom d'outil n'est pas réferencé dans SCHEMAS_CONNUS.
        FileNotFoundError : si le fichier de schéma est absent du repertoire.
    """
    if nom_outil not in SCHEMAS_CONNUS:
        raise KeyError(
            f"Aucun schéma de réponse API référence pour l'outil '{nom_outil}'. "
            f"Outils connus : {sorted(SCHEMAS_CONNUS)}"
        )
    chemin = (repertoire or REPERTOIRE_SCHEMAS) / SCHEMAS_CONNUS[nom_outil]
    if not chemin.is_file():
        raise FileNotFoundError(f"Schéma de réponse API introuvable : {chemin}")
    with open(chemin, encoding="utf-8") as flux:
        return json.load(flux)


def _formater_erreur(erreur: jsonschema.exceptions.ValidationError) -> str:
    """Formate une erreur jsonschema en message lisible avec chemin JSON."""
    chemin = "/".join(str(morceau) for morceau in erreur.absolute_path)
    localisation = f"/{chemin}" if chemin else "/"
    return f"{localisation} : {erreur.message}"


def valider_reponse_api(
    nom_outil: str,
    donnees: Any,
    repertoire: Optional[Path] = None,
) -> ResultatValidation:
    """Valide une charge utile brute de l'API contre le schéma de l'outil.

    Ne lève jamais d'exception pour des données non conformes ; les écarts
    sont retournés dans `ResultatValidation.erreurs`. Les erreurs de
    chargement du schéma (outil inconnu, fichier absent, JSON invalide)
    sont également converties en échec propre, sans exception.
    """
    try:
        schema = charger_schema(nom_outil, repertoire)
        validateur: Validator = jsonschema.Draft202012Validator(schema)
    except (KeyError, FileNotFoundError, json.JSONDecodeError) as exc:
        return ResultatValidation(
            valide=False,
            erreurs=[f"Erreur de chargement du schéma '{nom_outil}' : {exc}"],
        )
    erreurs = [_formater_erreur(e) for e in validateur.iter_errors(donnees)]
    return ResultatValidation(valide=not erreurs, erreurs=erreurs)


def valider_json_brut(
    nom_outil: str,
    texte: str,
    repertoire: Optional[Path] = None,
) -> ResultatValidation:
    """Valide une reponse API fournie comme texte JSON brut.

    Un texte non parsable en JSON, ou une racine non objet, produit un
    échec propre (`echec_technique`), sans exception.
    """
    try:
        donnees = json.loads(texte)
    except json.JSONDecodeError as exc:
        return ResultatValidation(
            valide=False,
            erreurs=[f"Charge utile non parsable en JSON : {exc.msg} (ligne {exc.lineno})"],
        )
    if not isinstance(donnees, dict):
        return ResultatValidation(
            valide=False,
            erreurs=[f"Racine de type {type(donnees).__name__}, objet attendu."],
        )
    return valider_reponse_api(nom_outil, donnees, repertoire)
