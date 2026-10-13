# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application  : openDataAgent
# Script       : test_search.py
# Version      : 1
# Date         : 12-10-2026
# Design       : TSC
# Build        : Mistral Vibe
# ---------------------------------------------------------------------
"""Tests unitaires du flux complet rechercher_jeux (src/core/search.py, T3.1.4).

Sans reseau (`responses`) : couvre le filtre de licence, la consignation
au registre et la reponse normalisee. Reponse HTTP simulee a partir de
la fixture reelle de recherche.
"""
import json
from pathlib import Path

import pytest
import responses

from src.core.search import rechercher_jeux
from src.utils.registry import RegistreSourcesInaccessibles

REPERTOIRE_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "api"
URL_RECHERCHE = "https://www.data.gouv.fr/api/1/datasets/"


@pytest.fixture
def fixture_recherche() -> dict:
    with open(REPERTOIRE_FIXTURES / "recherche_jeux_reussite.json", encoding="utf-8") as flux:
        return json.load(flux)


@pytest.fixture
def registre(tmp_path) -> RegistreSourcesInaccessibles:
    return RegistreSourcesInaccessibles(chemin=tmp_path / "registry.json")


def _jeu(id_: str, licence_id: str, organisation: str = "Insee") -> dict:
    return {
        "id": id_,
        "title": f"Jeu {id_}",
        "slug": f"jeu-{id_}",
        "page": f"https://www.data.gouv.fr/datasets/jeu-{id_}",
        "created_at": "2020-07-15T09:21:35.147000+00:00",
        "last_modified": "2026-09-30T16:42:11.000000+00:00",
        "license": licence_id,
        "organization": {"name": organisation},
        "resources": [{"id": "res1", "title": "Fichier CSV", "url": "https://static.data.gouv.fr/res1.csv"}],
    }


def test_mots_cles_vide_erreur_parametres(registre):
    # Réf. tests/plan_tests.md : TU-12 (mots_cles vide -> erreur_parametres, jamais d'appel HTTP)
    reponse = rechercher_jeux([], registre=registre)
    assert reponse["statut"] == "erreur_parametres"
    assert reponse["donnees"] == {}


@responses.activate
def test_limite_hors_bornes_corrigee(fixture_recherche, registre):
    # Réf. tests/plan_tests.md : TU-14 (limite au-delà du maximum -> corrigée, pas d'exception)
    responses.add(responses.GET, URL_RECHERCHE, json=fixture_recherche, status=200)

    reponse = rechercher_jeux(["dette"], limite=50, registre=registre)

    assert reponse["statut"] == "succes"
    assert "page_size=10" in responses.calls[0].request.url


@responses.activate
def test_filtre_licence_et_registre(registre):
    # Réf. tests/plan_tests.md : invariant CA-1 (aucun jeu de licence incompatible dans jeux)
    # + TU-21 (exclusion juridique consignée au registre)
    reponse_api = {
        "data": [
            _jeu("ouvert1", "lov2"),
            _jeu("ferme1", "other-closed"),
            _jeu("ferme2", "notspecified"),
            _jeu("ouvert2", "cc-by"),
        ],
        "total": 4,
        "page": 1,
        "next_page": None,
        "previous_page": None,
    }
    responses.add(responses.GET, URL_RECHERCHE, json=reponse_api, status=200)

    reponse = rechercher_jeux(["dette"], registre=registre)

    assert reponse["statut"] == "succes"
    ids = [j["id"] for j in reponse["donnees"]["jeux"]]
    assert ids == ["ouvert1", "ouvert2"]
    assert reponse["donnees"]["exclus_licence"] == 2
    assert reponse["donnees"]["total_trouves"] == 4

    rapports = registre.rapport_pour_agent()["sources_inaccessibles"]
    assert len(rapports) == 2
    motifs = {e["id_jeu"]: e["motif"] for e in rapports}
    assert motifs == {"ferme1": "licence_incompatible", "ferme2": "licence_incompatible"}


@responses.activate
def test_licence_absente_exclue(fixture_recherche, registre):
    # Réf. tests/plan_tests.md : TU-03 via le flux (licence absente -> comportement sûr par défaut)
    donnees = json.loads(json.dumps(fixture_recherche))
    donnees["data"][0]["license"] = None
    responses.add(responses.GET, URL_RECHERCHE, json=donnees, status=200)

    reponse = rechercher_jeux(["dette"], registre=registre)

    assert reponse["donnees"]["jeux"] == []
    assert reponse["donnees"]["exclus_licence"] == 1
    assert registre.rapport_pour_agent()["sources_inaccessibles"][0]["licence"] == "notspecified"


@responses.activate
def test_succes_aucune_exclusion(fixture_recherche, registre):
    # Réf. tests/plan_tests.md : TI-14 (succès -> total_trouves, jeux_retournes, exclus_licence exacts)
    responses.add(responses.GET, URL_RECHERCHE, json=fixture_recherche, status=200)

    reponse = rechercher_jeux(["dette", "publique"], tri="vues", limite=10, registre=registre)

    assert reponse["statut"] == "succes"
    assert reponse["message"] == ""
    assert reponse["donnees"]["total_trouves"] == 1
    assert reponse["donnees"]["exclus_licence"] == 0
    assert reponse["donnees"]["jeux"][0]["licence"] == "lov2"
    assert registre.rapport_pour_agent()["sources_inaccessibles"] == []


@responses.activate
def test_echec_http_500_echec_technique(registre):
    # Réf. tests/plan_tests.md : TU-17 (erreur HTTP 500 -> echec_technique, pas d'exception)
    responses.add(responses.GET, URL_RECHERCHE, json={"erreur": "interne"}, status=500)

    reponse = rechercher_jeux(["dette"], registre=registre)

    assert reponse["statut"] == "echec_technique"
    assert reponse["donnees"]["suggestion"] == "réessayer"
    assert registre.rapport_pour_agent()["sources_inaccessibles"] == []
