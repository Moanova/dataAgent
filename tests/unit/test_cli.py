# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application  : openDataAgent
# Script       : test_cli.py
# Version      : 1
# Date         : 13-10-2026
# Design       : TSC
# Build        : Mistral Vibe
# ---------------------------------------------------------------------
"""Tests unitaires de la CLI (src/main.py, T4.1/T4.2 — perimetre search).

La fonction coeur `rechercher_jeux` est simulee : la CLI se teste sans
reseau et sans connaitre le comportement du coeur.
"""
import json
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from src.main import app

runner = CliRunner()

REPONSE_SUCCES = {
    "statut": "succes",
    "message": "",
    "donnees": {
        "total_trouves": 2,
        "jeux": [
            {
                "id": "abc123",
                "titre": "Comptes des administrations publiques",
                "organisation": "Insee",
                "licence": "lov2",
                "derniere_maj": "2026-09-30",
                "nb_ressources": 2,
                "url": "https://www.data.gouv.fr/datasets/comptes-des-administrations-publiques",
            }
        ],
        "exclus_licence": 1,
    },
}


@patch("src.main.rechercher_jeux")
def test_search_appel_coeur_avec_options(mock_recherche):
    # Réf. tests/plan_tests.md : TI-13 (appels logs avec mots_cles, tri, limite — via la CLI)
    mock_recherche.return_value = REPONSE_SUCCES
    resultat = runner.invoke(app, ["search", "dette", "publique", "--tri", "vues", "--limite", "5"])
    assert resultat.exit_code == 0
    mock_recherche.assert_called_once()
    kwargs = mock_recherche.call_args.kwargs
    assert kwargs["mots_cles"] == ["dette", "publique"]
    assert kwargs["tri"] == "vues"
    assert kwargs["limite"] == 5
    assert "Comptes des administrations publiques" in resultat.output
    assert "exclu(s) licence" in resultat.output


@patch("src.main.rechercher_jeux")
def test_search_valeurs_par_defaut(mock_recherche):
    # Réf. tests/plan_tests.md : TU-13 (limite omise -> valeur par défaut 10)
    mock_recherche.return_value = REPONSE_SUCCES
    resultat = runner.invoke(app, ["search", "dette"])
    assert resultat.exit_code == 0
    kwargs = mock_recherche.call_args.kwargs
    assert kwargs["tri"] == "pertinence"
    assert kwargs["fenetre_maj"] == "toutes"
    assert kwargs["limite"] == 10
    assert kwargs["id_execution"]


@patch("src.main.rechercher_jeux")
def test_search_sortie_json(mock_recherche):
    # Test annexe : sans référence directe dans tests/plan_tests.md
    mock_recherche.return_value = REPONSE_SUCCES
    resultat = runner.invoke(app, ["search", "dette", "--json"])
    assert resultat.exit_code == 0
    charge = json.loads(resultat.output)
    assert charge["statut"] == "succes"
    assert charge["donnees"]["exclus_licence"] == 1
    assert charge["donnees"]["jeux"][0]["licence"] == "lov2"


def test_search_limite_hors_bornes():
    # Réf. tests/plan_tests.md : TU-14 (limite au-delà du maximum -> erreur, pas d'exception)
    resultat = runner.invoke(app, ["search", "dette", "--limite", "50"])
    assert resultat.exit_code != 0
    assert "limite" in (resultat.output + str(resultat.stderr)).lower()


def test_search_tri_invalide():
    # Réf. tests/plan_tests.md : TU-16 (tri invalide -> erreur_parametres)
    resultat = runner.invoke(app, ["search", "dette", "--tri", "invalide"])
    assert resultat.exit_code == 2
    assert "invalide" in (resultat.output + str(resultat.stderr)).lower()


@patch("src.main.rechercher_jeux")
def test_search_echec_technique_code_sortie(mock_recherche):
    # Réf. tests/plan_tests.md : TU-17 (erreur HTTP 500 -> statut echec_technique, pas d'exception)
    mock_recherche.return_value = {
        "statut": "echec_technique",
        "message": "Échec de l'appel à l'API data.gouv.fr",
        "donnees": {"suggestion": "réessayer"},
    }
    resultat = runner.invoke(app, ["search", "dette"])
    assert resultat.exit_code == 1
    assert "echec_technique" in (resultat.output + str(resultat.stderr))


@patch("src.main.rechercher_jeux")
def test_search_erreur_parametres_code_sortie(mock_recherche):
    # Réf. tests/plan_tests.md : TU-12 (mots_cles vide -> erreur_parametres)
    mock_recherche.return_value = {
        "statut": "erreur_parametres",
        "message": "Le paramètre 'mots_cles' est obligatoire et ne peut être vide.",
        "donnees": {},
    }
    resultat = runner.invoke(app, ["search", "dette"])
    assert resultat.exit_code == 2
