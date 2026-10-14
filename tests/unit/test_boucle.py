# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application  : openDataAgent
# Script       : test_boucle.py
# Version      : 1
# Date         : 14-10-2026
# Design       : TSC
# Build        : Mistral Vibe
# ---------------------------------------------------------------------
"""Tests unitaires de la boucle de conversation (T5.3.2).

Refs tests/plan_tests.md : Annexes T5.3 (TU-B1..TU-B10). L'API Mistral
et les fonctions coeur sont simulees : aucun reseau."""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import src.agent.outils as module_outils
from src.agent.agent import Agent
from src.agent.boucle import PLAFOND_DEFAUT, boucle_conversation
from src.agent.outils import executer_outil


# ---------------------------------------------------------------------
# Helpers : reponses SDK simulees
# ---------------------------------------------------------------------

def _reponse_sdk(tool_calls=None, contenu=""):
    message = SimpleNamespace(content=contenu, tool_calls=tool_calls or None)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def _tool_call_sdk(nom, arguments, id_appel="appel-1"):
    fonction = SimpleNamespace(name=nom, arguments=json.dumps(arguments))
    return SimpleNamespace(id=id_appel, function=fonction)


def _agent(complete_side_effects=None):
    client = MagicMock()
    if complete_side_effects is not None:
        client.agents.complete.side_effect = complete_side_effects
    return Agent(client=client, agent_id="ag-test", modele="m", outils=[], ephemere=True)


# ---------------------------------------------------------------------
# executer_outil (TU-B1, TU-B2, TU-B3)
# ---------------------------------------------------------------------

def test_executer_outil_route_chaque_outil(monkeypatch):
    # Réf. tests/plan_tests.md : TU-B1 — dispatch vers les 4 fonctions cœur
    outils = {}
    for nom in ("rechercher_jeux", "lister_ressources", "interroger_ressource", "telecharger_brut"):
        faux = MagicMock(return_value={"statut": "succes", "message": "", "donnees": {}})
        monkeypatch.setitem(module_outils.TABLE_OUTILS, nom, faux)
        outils[nom] = faux

    executer_outil("rechercher_jeux", {"mots_cles": ["dette"]}, "id")
    outils["rechercher_jeux"].assert_called_once_with(mots_cles=["dette"])

    executer_outil("lister_ressources", {"id_jeu": "abc"}, "id")
    outils["lister_ressources"].assert_called_once_with(id_jeu="abc")

    executer_outil("interroger_ressource", {"id_ressource": "r1", "page": 2, "tri": {"colonne": "v", "ordre": "croissant"}}, "id")
    outils["interroger_ressource"].assert_called_once_with(id_ressource="r1", page=2, tri={"colonne": "v", "ordre": "croissant"})

    executer_outil("telecharger_brut", {"id_ressource": "r1"}, "id")
    outils["telecharger_brut"].assert_called_once_with(id_ressource="r1")


def test_executer_outil_inconnu():
    # Réf. tests/plan_tests.md : TU-B2 — outil hors table → erreur_parametres
    reponse = executer_outil("outil_invente", {}, "id")
    assert reponse["statut"] == "erreur_parametres"
    assert "outil_invente" in reponse["message"]


def test_executer_outil_arguments_invalides(monkeypatch):
    # Réf. tests/plan_tests.md : TU-B2 — arguments invalides → erreur_parametres
    assert executer_outil("rechercher_jeux", {"mots_cles": []}, "id")["statut"] == "erreur_parametres"
    assert executer_outil("telecharger_brut", {}, "id")["statut"] == "erreur_parametres"
    assert executer_outil("lister_ressources", "pas un json{", "id")["statut"] == "erreur_parametres"
    faux = MagicMock(return_value={"statut": "succes", "message": "", "donnees": {}})
    monkeypatch.setitem(module_outils.TABLE_OUTILS, "interroger_ressource", faux)
    assert executer_outil("interroger_ressource", json.dumps({"id_ressource": "r1"}), "id")["statut"] == "succes"


def test_executer_outil_arguments_json(monkeypatch):
    # Réf. tests/plan_tests.md : TU-B3 — arguments en chaîne JSON acceptés
    faux = MagicMock(return_value={"statut": "succes", "message": "", "donnees": {}})
    monkeypatch.setitem(module_outils.TABLE_OUTILS, "rechercher_jeux", faux)
    reponse = executer_outil("rechercher_jeux", json.dumps({"mots_cles": ["insee"]}), "id")
    assert reponse["statut"] == "succes"
    faux.assert_called_once_with(mots_cles=["insee"])


# ---------------------------------------------------------------------
# boucle_conversation (TU-B4..TU-B10)
# ---------------------------------------------------------------------

def test_boucle_conversation_simple(monkeypatch):
    # Réf. tests/plan_tests.md : TU-B4 — 1 tool_call puis réponse finale
    mock_search = MagicMock(return_value={"statut": "succes", "message": "", "donnees": {"jeux": []}})
    monkeypatch.setitem(module_outils.TABLE_OUTILS, "rechercher_jeux", mock_search)
    appel_outil = _reponse_sdk(tool_calls=[_tool_call_sdk("rechercher_jeux", {"mots_cles": ["dette"]})])
    final = _reponse_sdk(contenu="Voici les jeux trouves.")
    agent = _agent([appel_outil, final])
    reponse = boucle_conversation(agent, "cherche la dette publique", id_execution="id")
    assert reponse["statut"] == "succes"
    assert reponse["donnees"]["reponse_agent"] == "Voici les jeux trouves."
    assert reponse["donnees"]["nb_invocations"] == 1
    assert reponse["donnees"]["plafond"] == PLAFOND_DEFAUT
    assert agent.client.agents.complete.call_count == 2
    mock_search.assert_called_once()


def test_boucle_multi_tours(monkeypatch):
    # Réf. tests/plan_tests.md : TU-B5 — plusieurs tool_calls successifs
    mock_search = MagicMock(return_value={"statut": "succes", "message": "", "donnees": {"jeux": [{"id": "abc"}]}})
    mock_list = MagicMock(return_value={"statut": "succes", "message": "", "donnees": {"ressources": []}})
    monkeypatch.setitem(module_outils.TABLE_OUTILS, "rechercher_jeux", mock_search)
    monkeypatch.setitem(module_outils.TABLE_OUTILS, "lister_ressources", mock_list)
    tour1 = _reponse_sdk(tool_calls=[_tool_call_sdk("rechercher_jeux", {"mots_cles": ["dette"]}, "a1")])
    tour2 = _reponse_sdk(tool_calls=[_tool_call_sdk("lister_ressources", {"id_jeu": "abc"}, "a2")])
    final = _reponse_sdk(contenu="Analyse complete.")
    agent = _agent([tour1, tour2, final])
    reponse = boucle_conversation(agent, "dette", id_execution="id")
    assert reponse["statut"] == "succes"
    assert reponse["donnees"]["nb_invocations"] == 2
    messages_envoyes = agent.client.agents.complete.call_args_list[-1].kwargs["messages"]
    roles = [m["role"] for m in messages_envoyes]
    assert roles == ["user", "assistant", "tool", "assistant", "tool"]
    resultats_outils = [m for m in messages_envoyes if m["role"] == "tool"]
    assert all(json.loads(m["content"])["statut"] == "succes" for m in resultats_outils)


def test_boucle_reponse_directe_sans_outil():
    # Réf. tests/plan_tests.md : TU-B4 — réponse immédiate sans outil
    agent = _agent([_reponse_sdk(contenu="Bonjour.")])
    reponse = boucle_conversation(agent, "bonjour", id_execution="id")
    assert reponse["statut"] == "succes"
    assert reponse["donnees"]["nb_invocations"] == 0


def test_boucle_plafond_atteint():
    # Réf. tests/plan_tests.md : TU-B6 — plafond → arrêt propre, synthèse partielle
    appel = _reponse_sdk(tool_calls=[_tool_call_sdk("rechercher_jeux", {"mots_cles": ["x"]})])
    agent = _agent([appel] * 20)
    reponse = boucle_conversation(agent, "x", plafond=3, id_execution="id")
    assert reponse["statut"] == "succes"
    assert reponse["donnees"]["nb_invocations"] == 3
    assert reponse["donnees"]["plafond"] == 3
    assert "plafond" in reponse["message"].lower()


def test_boucle_erreur_outil_renvoyee_agent(monkeypatch):
    # Réf. tests/plan_tests.md : TU-B7 — statut d'erreur du cœur renvoyé tel quel
    mock_dl = MagicMock(return_value={"statut": "ressource_introuvable", "message": "inconnu", "donnees": {}})
    monkeypatch.setitem(module_outils.TABLE_OUTILS, "telecharger_brut", mock_dl)
    appel = _reponse_sdk(tool_calls=[_tool_call_sdk("telecharger_brut", {"id_ressource": "r1"})])
    final = _reponse_sdk(contenu="Je n'ai pas trouve la ressource.")
    agent = _agent([appel, final])
    reponse = boucle_conversation(agent, "telecharge", id_execution="id")
    assert reponse["statut"] == "succes"
    contenu_outil = json.loads(agent.client.agents.complete.call_args_list[-1].kwargs["messages"][2]["content"])
    assert contenu_outil["statut"] == "ressource_introuvable"


def test_boucle_arguments_non_json():
    # Réf. tests/plan_tests.md : TU-B8 — tool_call illisible → erreur_parametres à l'agent
    appel = _tool_call_sdk("rechercher_jeux", None)
    appel.function.arguments = "{pas du json"
    tour = _reponse_sdk(tool_calls=[appel])
    final = _reponse_sdk(contenu="Arguments corriges.")
    agent = _agent([tour, final])
    reponse = boucle_conversation(agent, "x", id_execution="id")
    assert reponse["statut"] == "succes"
    assert reponse["donnees"]["nb_invocations"] == 1
    contenu_outil = json.loads(agent.client.agents.complete.call_args_list[-1].kwargs["messages"][2]["content"])
    assert contenu_outil["statut"] == "erreur_parametres"


def test_boucle_erreur_api():
    # Réf. tests/plan_tests.md : TU-B9 — erreur API → echec_technique propre
    agent = MagicMock()
    agent.agent_id = "ag-test"
    agent.client.agents.complete.side_effect = RuntimeError("429 rate limit")
    reponse = boucle_conversation(agent, "x", id_execution="id")
    assert reponse["statut"] == "echec_technique"
    assert "429" in reponse["message"]
    assert reponse["donnees"]["nb_invocations"] == 0


def test_boucle_plafond_configure_par_env(monkeypatch):
    # Réf. tests/plan_tests.md : TU-B10 — PLAFOND_INVOCATIONS respecté
    monkeypatch.setenv("PLAFOND_INVOCATIONS", "2")
    agent = _agent([])
    reponse = boucle_conversation(agent, "bonjour", id_execution="id")
    assert reponse["donnees"]["plafond"] == 2
