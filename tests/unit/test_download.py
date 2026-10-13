# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application  : openDataAgent
# Script       : test_download.py
# Version      : 1
# Date         : 13-10-2026
# Design       : TSC
# Build        : Mistral Vibe
# ---------------------------------------------------------------------
"""Tests unitaires du telechargement brut (src/core/download.py, T3.4.1).

Sans reseau (`responses`). L'inventaire requis par le contrat est
peuple via un appel simule a lister_ressources (chaine TI-05).
"""
import json
from pathlib import Path

import pytest
import responses

from src.core.download import telecharger_brut
from src.core.resources import lister_ressources
from src.utils.registry import RegistreSourcesInaccessibles
from src.utils.storage import chemin_destination, nettoyer_nom_fichier

URL_JEU = "https://www.data.gouv.fr/api/1/datasets/jeu-t/"
URL_FICHIER = "https://exemple.fr/donnees/budget-2024.csv"


@pytest.fixture
def registre(tmp_path) -> RegistreSourcesInaccessibles:
    return RegistreSourcesInaccessibles(chemin=tmp_path / "registry.json")


@pytest.fixture
def inventaire_peuple(registre, tmp_path):
    """Peuple l'inventaire via un appel simule a lister_ressources (chaine TI-05)."""
    reponse_api = {
        "id": "jeu-t",
        "title": "Jeu T",
        "license": "lov2",
        "resources": [
            {
                "id": "res-1",
                "title": "Budget 2024",
                "url": URL_FICHIER,
                "format": "csv",
                "mime": "text/csv",
                "filesize": 100,
            }
        ],
    }
    with responses.mock:
        responses.add(responses.GET, URL_JEU, json=reponse_api, status=200)
        lister_ressources("jeu-t", registre=registre)
    return reponse_api


def test_chaine_inventaire_telechargement(inventaire_peuple, registre, tmp_path, monkeypatch):
    # Réf. tests/plan_tests.md : TI-05 (chaîne inventaire → téléchargement → fichier écrit, statut succes, chemin et format exacts)
    monkeypatch.chdir(tmp_path)
    with responses.mock:
        responses.add(responses.GET, URL_FICHIER, body=b"col1,col2\na,b\n", status=200)
        reponse = telecharger_brut("res-1", id_execution="20261013_120000_abc123", registre=registre)

    assert reponse["statut"] == "succes"
    chemin = Path(reponse["donnees"]["chemin_local"])
    assert chemin.exists()
    assert chemin.read_bytes() == b"col1,col2\na,b\n"
    assert chemin.name == "res-1_budget-2024.csv"
    assert chemin.parent.name == "20261013_120000_abc123"
    assert chemin.parent.parent.name == "raw"
    assert reponse["donnees"]["format"] == "csv"
    assert reponse["donnees"]["licence"] == "lov2"


def test_sans_inventaire_prealable(registre, tmp_path, monkeypatch):
    # Réf. tests/plan_tests.md : TI-06 (sans inventaire préalable → ressource_introuvable, aucune écriture disque)
    monkeypatch.chdir(tmp_path)
    reponse = telecharger_brut("res-jamais-vue", registre=registre)

    assert reponse["statut"] == "ressource_introuvable"
    assert reponse["donnees"]["suggestion"] == "reprendre par l'inventaire"
    assert not (tmp_path / "data").exists()


def test_refus_serveur_registre_et_aucune_ecriture(inventaire_peuple, registre, tmp_path, monkeypatch):
    # Réf. tests/plan_tests.md : TI-07 (refus serveur → echec_technique, registre motif serveur_origine_bloque, aucune écriture partielle)
    monkeypatch.chdir(tmp_path)
    with responses.mock:
        responses.add(responses.GET, URL_FICHIER, body=b"acces refuse", status=403)
        reponse = telecharger_brut("res-1", id_execution="20261013_120000_def456", registre=registre)

    assert reponse["statut"] == "echec_technique"
    assert reponse["donnees"]["suggestion"] == "fichier_heberge_exterieurement"

    entrees = registre.rapport_pour_agent()["sources_inaccessibles"]
    assert len(entrees) == 1
    assert entrees[0]["motif"] == "serveur_origine_bloque"
    assert entrees[0]["url"] == URL_FICHIER
    assert entrees[0]["licence"] == "lov2"

    # Aucune ecriture partielle : ni fichier ni .part
    raw = tmp_path / "data" / "raw"
    assert not raw.exists() or not any(raw.rglob("*"))


def test_erreur_reseau_echec_propre(inventaire_peuple, registre, tmp_path, monkeypatch):
    # Réf. tests/plan_tests.md : TB-05 simulé (échec réseau → échec propre, registre alimenté, pas de crash)
    from requests.exceptions import ConnectionError as ErreurConnexion

    monkeypatch.chdir(tmp_path)
    with responses.mock:
        for _ in range(3):
            responses.add(responses.GET, URL_FICHIER, body=ErreurConnexion("injoignable"))
        reponse = telecharger_brut("res-1", id_execution="20261013_120000_ghi789", registre=registre)

    assert reponse["statut"] == "echec_technique"
    assert len(registre.rapport_pour_agent()["sources_inaccessibles"]) == 1


def test_429_puis_succes(inventaire_peuple, registre, tmp_path, monkeypatch):
    # Réf. tests/plan_tests.md : TU-20 transposé au téléchargement (429 → reprise puis succès)
    monkeypatch.chdir(tmp_path)
    with responses.mock:
        responses.add(responses.GET, URL_FICHIER, body=b"", status=429)
        responses.add(responses.GET, URL_FICHIER, body=b"donnees completes", status=200)
        reponse = telecharger_brut("res-1", id_execution="20261013_120000_jkl012", registre=registre)

    assert reponse["statut"] == "succes"
    assert Path(reponse["donnees"]["chemin_local"]).read_bytes() == b"donnees completes"


def test_nom_fichier_nettoye():
    # Test annexe : URL avec caractères spéciaux → nom de fichier valide
    chemin = chemin_destination("exec-1", "res-x", "https://exemple.fr/données/budget 2024!.csv")
    assert chemin.name == "res-x_budget-2024.csv"


def test_url_sans_nom_exploitable():
    # Test annexe : URL sans segment final exploitable → nom retombé sur l'id
    chemin = chemin_destination("exec-1", "res-y", "https://api.exemple.fr/v1/data/DD_CNA_APU_CSV_FR")
    assert chemin.name == "res-y_DD_CNA_APU_CSV_FR"


def test_id_execution_distincts(inventaire_peuple, registre, tmp_path, monkeypatch):
    # Test annexe : deux exécutions → deux arborescences, aucun écrasement
    monkeypatch.chdir(tmp_path)
    with responses.mock:
        responses.add(responses.GET, URL_FICHIER, body=b"premiere", status=200)
        premiere = telecharger_brut("res-1", id_execution="20261013_120000_aaa111", registre=registre)
        responses.add(responses.GET, URL_FICHIER, body=b"seconde", status=200)
        seconde = telecharger_brut("res-1", id_execution="20261013_130000_bbb222", registre=registre)

    assert premiere["donnees"]["chemin_local"] != seconde["donnees"]["chemin_local"]
    assert Path(premiere["donnees"]["chemin_local"]).read_bytes() == b"premiere"
    assert Path(seconde["donnees"]["chemin_local"]).read_bytes() == b"seconde"


def test_collision_meme_execution_suffixe_numerique(inventaire_peuple, registre, tmp_path, monkeypatch):
    # Réf. docs/specs/stockage.md §4 (même nom dans une même exécution → suffixe numérique, jamais d'écrasement)
    monkeypatch.chdir(tmp_path)
    with responses.mock:
        responses.add(responses.GET, URL_FICHIER, body=b"copie-1", status=200)
        premiere = telecharger_brut("res-1", id_execution="20261013_140000_ccc333", registre=registre)
        responses.add(responses.GET, URL_FICHIER, body=b"copie-2", status=200)
        seconde = telecharger_brut("res-1", id_execution="20261013_140000_ccc333", registre=registre)
        responses.add(responses.GET, URL_FICHIER, body=b"copie-3", status=200)
        troisieme = telecharger_brut("res-1", id_execution="20261013_140000_ccc333", registre=registre)

    assert premiere["donnees"]["chemin_local"].endswith("res-1_budget-2024.csv")
    assert seconde["donnees"]["chemin_local"].endswith("res-1_budget-2024_1.csv")
    assert troisieme["donnees"]["chemin_local"].endswith("res-1_budget-2024_2.csv")

    # Aucune perte : les trois copies coexistent avec leur contenu
    assert Path(premiere["donnees"]["chemin_local"]).read_bytes() == b"copie-1"
    assert Path(seconde["donnees"]["chemin_local"]).read_bytes() == b"copie-2"
    assert Path(troisieme["donnees"]["chemin_local"]).read_bytes() == b"copie-3"


def test_lister_fichiers_execution(inventaire_peuple, registre, tmp_path, monkeypatch):
    # Réf. docs/specs/stockage.md §3.1 (retrouver tous les fichiers d'une session)
    from src.utils.storage import lister_fichiers

    monkeypatch.chdir(tmp_path)
    with responses.mock:
        responses.add(responses.GET, URL_FICHIER, body=b"a", status=200)
        telecharger_brut("res-1", id_execution="20261013_150000_ddd444", registre=registre)

    fichiers = lister_fichiers("20261013_150000_ddd444")
    assert len(fichiers) == 1
    assert fichiers[0].name == "res-1_budget-2024.csv"

    assert lister_fichiers("execution_inexistante") == []
