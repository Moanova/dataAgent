# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application  : openDataAgent
# Script       : classification.py
# Version      : 1
# Date         : 13-10-2026
# Design       : Mistral Vibe
# Build        : Mistral Vibe
# ---------------------------------------------------------------------
"""Classificateur deterministe des ressources (B3, T3.2.2/T3.2.3).

Fonction pure, sans I/O. Trois signaux independants peuvent entrer en
conflit (format declare, mime detecte, URL) ; l'ordre de priorite fixe
est : HTML > API distante > tabulaire > autre format > indetermine.

Distinction fondamentale (T3.2.3) : des signaux CONTRADICTOIRES sont
tranches par l'ordre de priorite (ex. format csv + mime text/html ->
page_web) ; seuls des signaux ABSENTS ou INCONNUS produisent
`indetermine`. L'agent (etape A3) ne voit donc dans
`donnees.indetermination` que de l'inconnu, jamais du contradictoire
deja tranche, et dispose pour chaque id du titre et de l'URL dans
`donnees.ressources` (autoportance, sans appel d'outil supplementaire).

Piste d'evolution (pas dans le perimetre) : l'API v1 propose un
parametre `format` de pre-filtrage des recherches, utilisable par
l'etape A1 ; il ne remplace pas cette classification (le format
declare n'est pas fiable, cf. conflits format/mime).
"""
from typing import Optional, Tuple

FORMATS_TABULAIRES = frozenset({"csv", "xlsx", "xls", "tsv"})
MIMES_TABULAIRES = frozenset({
    "text/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/tab-separated-values",
})
FORMATS_AUTRES = frozenset({"zip", "geojson", "json", "shp", "pdf", "parquet"})
MIMES_AUTRES = frozenset({
    "application/zip",
    "application/geo+json",
    "application/json",
    "application/octet-stream",
    "application/pdf",
})
FORMATS_HTML = frozenset({"html", "htm"})
MIMES_HTML = frozenset({"text/html"})
FORMAT_API = "api"


def _normaliser(valeur: Optional[str]) -> str:
    return (valeur or "").strip().lower()


def classer_ressource(
    format_ressource: Optional[str],
    mime: Optional[str],
    url: Optional[str],
) -> Tuple[str, bool]:
    """Classe une ressource a partir de ses trois signaux.

    Retourne (classe, indetermine) ou classe vaut l'une des cinq valeurs
    de l'enum ClasseRessource. Priorite : HTML > api_distante >
    fichier_tabulaire > fichier_autre_format > indetermine. Le defaut
    est sur : toute ressource non classee est `indetermine`.
    """
    format_ = _normaliser(format_ressource)
    mime_ = _normaliser(mime)
    url_ = _normaliser(url)

    # 1. HTML : contenu trompeur le plus couteux (le fichier declare
    #    n'est pas ce qui est servi) -> priorite maximale.
    if format_ in FORMATS_HTML or mime_ in MIMES_HTML:
        return "page_web", False

    # 2. API distante : URL stable dans le temps, signal structurant
    #    pour la voie d'acquisition.
    if format_ == FORMAT_API or "/api" in url_:
        return "api_distante", False

    # 3. Tabulaire.
    if format_ in FORMATS_TABULAIRES or mime_ in MIMES_TABULAIRES:
        return "fichier_tabulaire", False

    # 4. Autre format connu (liste fermee).
    if format_ in FORMATS_AUTRES or mime_ in MIMES_AUTRES:
        return "fichier_autre_format", False

    # 5. Defaut sur : jamais de classification erronnee silencieuse.
    return "indetermine", True
