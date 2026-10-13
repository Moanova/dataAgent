# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application  : openDataAgent
# Script       : http.py
# Version      : 1
# Date         : 12-10-2026
# Design       : TSC
# Build        : Mistral Vibe
# ---------------------------------------------------------------------
"""Client HTTP generique pour l'API data.gouv.fr.

Couche unique d'acces reseau du projet (T3.1.1). Fournit :
- une session `requests` reutilisable avec `User-Agent` explicite ;
- des tentatives de reprise sur les statuts transitoires (429, 502, 503)
  et les erreurs de connexion, avec delai croissant ;
- des retours structures sans exception : aucun appel ne leve, les
  echecs sont convertis en statut `echec_technique` (ou `jeu_introuvable`
  pour un 404).
"""
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

from src.utils.logging import get_logger, log_to_file

load_dotenv()

logger = get_logger("openDataAgent.utils.http")

URL_BASE_DEFAUT = "https://www.data.gouv.fr/api/1/"
DELAIS_TENTATIVES = (1, 2)
STATUTS_TRANSITOIRES = {429, 502, 503}


@dataclass
class ResultatAppel:
    """Resultat structure d'un appel API, sans exception."""

    statut: str
    status_code: Optional[int] = None
    donnees: Dict[str, Any] = field(default_factory=dict)
    erreur: Optional[str] = None

    @property
    def reussi(self) -> bool:
        return self.statut == "succes"


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "openDataAgent/1.0 (https://github.com/Moanova/openDataAgent)"})
    return session


_SESSION = _session()


def appel_api(
    chemin: str,
    params: Optional[Dict[str, Any]] = None,
    url_base: Optional[str] = None,
    timeout: float = 10.0,
    nb_tentatives: int = 3,
) -> ResultatAppel:
    """Effectue un appel GET vers l'API data.gouv.fr avec reprise sur echec transitoire.

    Ne leve jamais d'exception : les echecs techniques (injoignable,
    expiration du delai, statut transitoire persistant) produisent un
    `ResultatAppel` de statut `echec_technique` ; un 404 produit le
    statut `jeu_introuvable`.
    """
    base = url_base or os.environ.get("DATA_GOUV_API_URL", URL_BASE_DEFAUT)
    url = f"{base.rstrip('/')}/{chemin.lstrip('/')}"

    for tentative in range(1, nb_tentatives + 1):
        try:
            reponse = _SESSION.get(url, params=params, timeout=timeout)
        except requests.exceptions.RequestException as exc:
            log_to_file(
                "Echec de l'appel HTTP a data.gouv.fr",
                url=url,
                tentative=tentative,
                erreur=str(exc),
                suggestion="Reessayer apres 30 secondes",
            )
            if tentative < nb_tentatives:
                time.sleep(DELAIS_TENTATIVES[min(tentative - 1, len(DELAIS_TENTATIVES) - 1)])
                continue
            return ResultatAppel(statut="echec_technique", erreur=str(exc))

        if reponse.status_code == 404:
            return ResultatAppel(statut="jeu_introuvable", status_code=404)

        if reponse.status_code in STATUTS_TRANSITOIRES and tentative < nb_tentatives:
            log_to_file(
                "Statut transitoire, nouvelle tentative",
                url=url,
                status_code=reponse.status_code,
                tentative=tentative,
            )
            time.sleep(DELAIS_TENTATIVES[min(tentative - 1, len(DELAIS_TENTATIVES) - 1)])
            continue

        if reponse.status_code >= 400:
            log_to_file(
                "Echec de l'appel HTTP a data.gouv.fr",
                url=url,
                status_code=reponse.status_code,
                suggestion="Reessayer apres 30 secondes",
            )
            return ResultatAppel(statut="echec_technique", status_code=reponse.status_code)

        try:
            donnees = reponse.json()
        except ValueError as exc:
            return ResultatAppel(
                statut="echec_technique",
                status_code=reponse.status_code,
                erreur=f"Reponse non parsable en JSON : {exc}",
            )
        return ResultatAppel(statut="succes", status_code=reponse.status_code, donnees=donnees)

    return ResultatAppel(statut="echec_technique", erreur="Tentatives epuisees")


def rechercher_jeux_api(
    mots_cles: list,
    tri: str = "pertinence",
    fenetre_maj: str = "toutes",
    limite: int = 10,
    **kwargs: Any,
) -> ResultatAppel:
    """Appelle l'endpoint de recherche /api/1/datasets/ (v1).

    Traduit les arguments normalises vers les parametres de l'API et
    valide la reponse contre le schema jsonschema de l'outil (T2.2) ;
    une reponse invalide produit un echec propre sans exception.
    """
    from src.contracts.validation_api import valider_reponse_api

    TRIS_API = {"recent": "-last_update", "vues": "-views", "reutilisations": "-reuses"}

    params = {
        "q": " ".join(mots_cles),
        "page_size": limite,
    }
    if tri != "pertinence":
        params["sort"] = TRIS_API[tri]
    if fenetre_maj != "toutes":
        params["last_update_range"] = fenetre_maj

    resultat = appel_api("/datasets/", params=params, **kwargs)
    if not resultat.reussi:
        return resultat

    validation = valider_reponse_api("rechercher_jeux", resultat.donnees)
    if not validation.valide:
        return ResultatAppel(
            statut="echec_technique",
            status_code=resultat.status_code,
            erreur="Reponse de recherche invalide : " + " ; ".join(validation.erreurs),
        )
    return resultat
