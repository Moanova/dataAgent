# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application  : openDataAgent
# Script       : test_licence.py
# Version      : 1
# Date         : 12-10-2026
# Design       : TSC
# Build        : Mistral Vibe
# ---------------------------------------------------------------------
"""Tests unitaires du filtre de licence (src/core/licence.py, T3.1.2).

Couvre TU-01 a TU-04 du plan de tests.
"""
import pytest

from src.core.licence import licence_est_acceptable


@pytest.mark.parametrize("licence", [
    "lov2",
    "fr-lo",
    "odc-odbl",
    "cc-by",
    "cc-by-sa",
    "cc-zero",
    "other-open",
])
def test_licences_acceptees(licence):
    # Réf. tests/plan_tests.md : TU-01 (licences acceptées -> Vrai pour chacune)
    assert licence_est_acceptable(licence) is True


@pytest.mark.parametrize("licence", [
    "notspecified",
    "other-closed",
    "odc-by",      # licence a attribution, hors politique du projet
    "commercial",  # valeur commerciale
])
def test_licences_exclues(licence):
    # Réf. tests/plan_tests.md : TU-02 (licences exclues -> Faux pour chacune)
    assert licence_est_acceptable(licence) is False


def test_licence_absente_nulle_vide():
    # Réf. tests/plan_tests.md : TU-03 (licence absente, nulle, chaîne vide -> Faux)
    assert licence_est_acceptable(None) is False
    assert licence_est_acceptable("") is False


@pytest.mark.parametrize("licence,attendu", [
    ("LOV2", True),
    ("  FR-LO  ", True),
    (" CC-ZERO ", True),
    ("  CC-BY  ", True),
    (" Other-Open ", True),
    ("  NotSpecified  ", False),
    ("OTHER-CLOSED", False),
])
def test_casse_et_espaces_parasites(licence, attendu):
    # Réf. tests/plan_tests.md : TU-04 (casse et espaces parasites -> évaluation insensible)
    assert licence_est_acceptable(licence) is attendu
