# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application  : openDataAgent
# Script       : test_classification.py
# Version      : 1
# Date         : 13-10-2026
# Design       : TSC
# Build        : Mistral Vibe
# ---------------------------------------------------------------------
"""Tests unitaires du classificateur de ressources (src/core/classification.py, T3.2.2).

Couvre TU-05 a TU-11 du plan de tests, plus l'ordre de priorite des
signaux en cas de conflit : HTML > api_distante > tabulaire > autre.
"""
import pytest

from src.core.classification import classer_ressource


@pytest.mark.parametrize("format_,mime", [
    ("csv", "text/csv"),
    (None, "text/csv"),
    ("csv", None),
])
def test_tu05_csv_tabulaire(format_, mime):
    # Réf. tests/plan_tests.md : TU-05 (CSV format/csv + mime text/csv -> fichier_tabulaire, non indéterminé)
    classe, indetermine = classer_ressource(format_, mime, "https://exemple.fr/donnees.csv")
    assert classe == "fichier_tabulaire"
    assert indetermine is False


@pytest.mark.parametrize("format_", ["xlsx", "xls", "tsv"])
def test_tu06_tableurs(format_):
    # Réf. tests/plan_tests.md : TU-06 (XLSX, XLS, TSV -> fichier_tabulaire)
    classe, indetermine = classer_ressource(format_, None, "https://exemple.fr/donnees")
    assert classe == "fichier_tabulaire"
    assert indetermine is False


@pytest.mark.parametrize("format_", ["zip", "geojson", "json", "shp", "pdf", "parquet"])
def test_tu07_autres_formats(format_):
    # Réf. tests/plan_tests.md : TU-07 (ZIP, GeoJSON, JSON, SHP, PDF, Parquet -> fichier_autre_format)
    classe, indetermine = classer_ressource(format_, None, "https://exemple.fr/donnees")
    assert classe == "fichier_autre_format"
    assert indetermine is False


def test_tu08_html_format():
    # Réf. tests/plan_tests.md : TU-08 (HTML par format -> page_web)
    classe, indetermine = classer_ressource("html", None, "https://exemple.fr/page")
    assert classe == "page_web"
    assert indetermine is False


def test_tu08_html_mime():
    # Réf. tests/plan_tests.md : TU-08 (HTML par mime text/html -> page_web)
    classe, indetermine = classer_ressource(None, "text/html", "https://exemple.fr/page")
    assert classe == "page_web"
    assert indetermine is False


def test_tu09_api_url():
    # Réf. tests/plan_tests.md : TU-09 (URL contenant /api -> api_distante)
    classe, indetermine = classer_ressource(None, None, "https://exemple.fr/api/v1/data")
    assert classe == "api_distante"
    assert indetermine is False


def test_tu09_api_format():
    # Réf. tests/plan_tests.md : TU-09 (format api -> api_distante)
    classe, indetermine = classer_ressource("api", None, "https://exemple.fr/endpoint")
    assert classe == "api_distante"
    assert indetermine is False


def test_tu10_format_inconnu_mime_absent_url_neutre():
    # Réf. tests/plan_tests.md : TU-10 (format inconnu, mime absent, URL neutre -> indetermine, indéterminé vrai)
    classe, indetermine = classer_ressource("docx", None, "https://exemple.fr/donnees")
    assert classe == "indetermine"
    assert indetermine is True


def test_tu11_absence_totale_de_metadonnees():
    # Réf. tests/plan_tests.md : TU-11 (absence totale de métadonnées -> indetermine, jamais une classification erronée silencieuse)
    for format_, mime, url in [(None, None, None), ("", "", ""), (None, None, "")]:
        classe, indetermine = classer_ressource(format_, mime, url)
        assert classe == "indetermine"
        assert indetermine is True


@pytest.mark.parametrize("format_,mime,attendu", [
    ("CSV", "TEXT/CSV", "fichier_tabulaire"),
    ("  XLSX  ", None, "fichier_tabulaire"),
    ("PDF", None, "fichier_autre_format"),
    ("API", None, "api_distante"),
    ("HTML", None, "page_web"),
])
def test_casse_et_espaces(format_, mime, attendu):
    # Test annexe : insensibilité casse/espaces (cohérent avec licence_est_acceptable)
    classe, _ = classer_ressource(format_, mime, "https://exemple.fr/d")
    assert classe == attendu


def test_conflit_html_prioritaire():
    # Test annexe : conflit format csv / mime text/html -> HTML prioritaire
    classe, _ = classer_ressource("csv", "text/html", "https://exemple.fr/export")
    assert classe == "page_web"


def test_conflit_api_prioritaire_sur_tabulaire():
    # Test annexe : conflit format csv / URL /api -> api_distante
    classe, _ = classer_ressource("csv", None, "https://exemple.fr/api/export?format=csv")
    assert classe == "api_distante"


def test_conflit_html_sur_url_api():
    # Test annexe : conflit mime text/html / URL /api -> HTML prioritaire (ordre validé HTML > API)
    classe, _ = classer_ressource(None, "text/html", "https://api.exemple.fr/v1/data")
    assert classe == "page_web"


def test_conflit_html_prioritaire_sur_api():
    # Test annexe : conflit format api / mime text/html -> HTML prioritaire
    classe, _ = classer_ressource("api", "text/html", "https://exemple.fr/endpoint")
    assert classe == "page_web"


def test_mime_autre_format():
    # Test annexe : mimes des autres formats (zip, geo+json, json, pdf)
    for mime in ["application/zip", "application/geo+json", "application/json", "application/pdf"]:
        classe, indetermine = classer_ressource(None, mime, "https://exemple.fr/fichier")
        assert classe == "fichier_autre_format"
        assert indetermine is False
