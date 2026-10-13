# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application  : openDataAgent
# Script       : test_integration.py
# Version      : 1
# Date         : 13-10-2026
# Design       : TSC
# Build        : Mistral Vibe
# ---------------------------------------------------------------------
"""Tests d'integration du flux complet (T3.4.3, embryon de T5.2.1).

Chaine recherche -> inventaire -> telechargement, sans reseau
(`responses`), registre injecte sur tmp_path. Couvre TI-08 : registre
final avec deux entrees de motifs distincts en ordre chronologique.
"""
import json
from pathlib import Path

import pytest
import responses

from src.core.search import rechercher_jeux
from src.core.resources import lister_ressources
from src.core.download import telecharger_brut
from src.utils.registry import RegistreSourcesInaccessibles

URL_RECHERCHE = "https://www.data.gouv.fr/api/1/datasets/"
def url_jeu(id_jeu: str) -> str:
    return f"https://www.data.gouv.fr/api/1/datasets/{id_jeu}/"
URL_FICHIER = "https://exemple.org/donnees/budget.csv"


@pytest.fixture
def registre(tmp_path) -> RegistreSourcesInaccessibles:
    return RegistreSourcesInaccessibles(chemin=tmp_path / "registry.json")


def _jeu(id_: str, titre: str, licence: str, organisation: str = "Org") -> dict:
    return {
        "id": id_,
        "title": titre,
        "slug": id_,
        "page": f"https://www.data.gouv.fr/datasets/{id_}",
        "created_at": "2024-01-01T00:00:00+00:00",
        "last_modified": "2026-09-01T00:00:00+00:00",
        "license": licence,
        "organization": {"name": organisation},
        "resources": [
            {"id": f"res-{id_}", "title": f"Fichier {id_}", "url": URL_FICHIER, "format": "csv", "mime": "text/csv", "filesize": 10}
        ],
    }


@responses.activate
def test_ti08_flux_complet_exclusion_et_echec(registre, tmp_path, monkeypatch):
    # Réf. tests/plan_tests.md : TI-08 (flux complet : exclusion licence + échec téléchargement → registre : deux entrées, motifs exacts, ordre chronologique)
    monkeypatch.chdir(tmp_path)

    # Etape 1 : recherche — un jeu ouvert, un jeu de licence refusee
    reponse_recherche = {
        "data": [
            _jeu("jeu-ouvert", "Jeu ouvert", "lov2", organisation="Insee"),
            _jeu("jeu-ferme", "Jeu ferme", "other-closed", organisation="Ministere X"),
        ],
        "total": 2,
        "page": 1,
        "next_page": None,
        "previous_page": None,
    }
    responses.add(responses.GET, URL_RECHERCHE, json=reponse_recherche, status=200)

    recherche = rechercher_jeux(["budget"], registre=registre)
    assert recherche["statut"] == "succes"
    assert [j["id"] for j in recherche["donnees"]["jeux"]] == ["jeu-ouvert"]
    assert recherche["donnees"]["exclus_licence"] == 1

    # Etape 2 : inventaire du jeu ouvert
    reponse_inventaire = {
        "id": "jeu-ouvert",
        "title": "Jeu ouvert",
        "license": "lov2",
        "organization": {"name": "Insee"},
        "resources": [
            {"id": "res-telecharge", "title": "Budget", "url": URL_FICHIER, "format": "csv", "mime": "text/csv", "filesize": 10}
        ],
    }
    responses.add(responses.GET, url_jeu("jeu-ouvert"), json=reponse_inventaire, status=200)

    inventaire = lister_ressources("jeu-ouvert", registre=registre)
    assert inventaire["statut"] == "succes"

    # Etape 3 : telechargement refuse par le serveur d'origine
    responses.add(responses.GET, URL_FICHIER, body=b"acces refuse", status=403)

    telechargement = telecharger_brut("res-telecharge", id_execution="20261013_160000_xyz789", registre=registre)
    assert telechargement["statut"] == "echec_technique"
    assert telechargement["donnees"]["suggestion"] == "fichier_heberge_exterieurement"

    # Registre final : deux entrees, motifs exacts, ordre chronologique
    entrees = registre.rapport_pour_agent()["sources_inaccessibles"]
    assert len(entrees) == 2

    premiere, seconde = entrees
    assert premiere["motif"] == "licence_incompatible"
    assert premiere["id_jeu"] == "jeu-ferme"
    assert premiere["licence"] == "other-closed"
    assert premiere["organisation"] == "Ministere X"

    assert seconde["motif"] == "serveur_origine_bloque"
    assert seconde["id_jeu"] == "jeu-ouvert"
    assert seconde["licence"] == "lov2"
    assert seconde["organisation"] == "Insee"
    assert seconde["detail"] == "Statut HTTP 403"

    assert premiere["timestamp"] <= seconde["timestamp"]

    # Registre persiste au format JSON valide
    chemin_registre = tmp_path / "registry.json"
    assert chemin_registre.exists()
    json.loads(chemin_registre.read_text(encoding="utf-8"))


@responses.activate
def test_flux_complet_telechargement_reussi(registre, tmp_path, monkeypatch):
    # Réf. tests/plan_tests.md : TI-05/T5.2.1 (flux complet simulé avec téléchargement réussi)
    monkeypatch.chdir(tmp_path)

    responses.add(responses.GET, URL_RECHERCHE, json={
        "data": [_jeu("jeu-ok", "Jeu OK", "fr-lo")],
        "total": 1, "page": 1, "next_page": None, "previous_page": None,
    }, status=200)
    recherche = rechercher_jeux(["budget"], registre=registre)
    assert recherche["donnees"]["jeux"][0]["id"] == "jeu-ok"

    responses.add(responses.GET, url_jeu("jeu-ok"), json={
        "id": "jeu-ok",
        "title": "Jeu OK",
        "license": "fr-lo",
        "organization": {"name": "Org"},
        "resources": [
            {"id": "res-ok", "title": "Fichier", "url": URL_FICHIER, "format": "csv", "mime": "text/csv", "filesize": 5}
        ],
    }, status=200)
    inventaire = lister_ressources("jeu-ok", registre=registre)
    assert inventaire["statut"] == "succes"

    responses.add(responses.GET, URL_FICHIER, body=b"a,b\n1,2\n", status=200)
    telechargement = telecharger_brut("res-ok", id_execution="20261013_170000_aaa000", registre=registre)

    assert telechargement["statut"] == "succes"
    chemin = Path(telechargement["donnees"]["chemin_local"])
    assert chemin.read_bytes() == b"a,b\n1,2\n"
    assert telechargement["donnees"]["licence"] == "fr-lo"

    # Aucune entree au registre : tout a reussi
    assert registre.rapport_pour_agent()["sources_inaccessibles"] == []


@responses.activate
def test_entree_exclusion_non_alteree_par_echec(registre, tmp_path, monkeypatch):
    # Réf. tests/plan_tests.md : invariants du registre (aucune entrée modifiée après écriture)
    monkeypatch.chdir(tmp_path)

    responses.add(responses.GET, URL_RECHERCHE, json={
        "data": [_jeu("jeu-ferme", "Jeu ferme", "notspecified")],
        "total": 1, "page": 1, "next_page": None, "previous_page": None,
    }, status=200)
    rechercher_jeux(["x"], registre=registre)
    avant = registre.rapport_pour_agent()["sources_inaccessibles"][0]

    # Un echec de telechargement sur une autre source n'altere pas l'entree existante
    responses.add(responses.GET, url_jeu("jeu-autre"), json={
        "id": "jeu-autre",
        "title": "Jeu autre",
        "license": "lov2",
        "organization": {"name": "Autre"},
        "resources": [
            {"id": "res-autre", "title": "F", "url": URL_FICHIER, "format": "csv", "mime": "text/csv", "filesize": 1}
        ],
    }, status=200)
    lister_ressources("jeu-autre", registre=registre)
    responses.add(responses.GET, URL_FICHIER, body=b"non", status=503)
    responses.add(responses.GET, URL_FICHIER, body=b"non", status=503)
    responses.add(responses.GET, URL_FICHIER, body=b"non", status=503)
    telecharger_brut("res-autre", id_execution="20261013_180000_bbb111", registre=registre)

    entrees = registre.rapport_pour_agent()["sources_inaccessibles"]
    assert len(entrees) == 2
    assert entrees[0] == avant
