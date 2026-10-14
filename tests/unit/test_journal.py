# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application  : openDataAgent
# Script       : test_journal.py
# Version      : 1
# Date         : 14-10-2026
# Design       : TSC
# Build        : Mistral Vibe
# ---------------------------------------------------------------------
"""Tests unitaires du journal de conversation (T5.3.3).

Refs tests/plan_tests.md : Annexes T5.3.3 (TU-C1..TU-C8). Aucun
reseau : le journal ecrit dans des repertoires temporaires."""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from src.agent.agent import Agent
from src.agent.boucle import boucle_conversation
from src.agent.journal import (
    JournalConversation,
    extraire_invocations,
    lire_journal,
)


def _reponse_sdk(tool_calls=None, contenu=""):
    message = SimpleNamespace(content=contenu, tool_calls=tool_calls or None)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def _tool_call_sdk(nom, arguments, id_appel="appel-1"):
    fonction = SimpleNamespace(name=nom, arguments=json.dumps(arguments))
    return SimpleNamespace(id=id_appel, function=fonction)


def _agent(effets):
    client = MagicMock()
    client.agents.complete.side_effect = effets
    return Agent(client=client, agent_id="ag-test", modele="mistral-small-latest", outils=[], ephemere=True)


# ---------------------------------------------------------------------
# JournalConversation (TU-C1..TU-C4)
# ---------------------------------------------------------------------

def test_entete_contexte(tmp_path):
    # Réf. tests/plan_tests.md : TU-C1 — en-tête contexte (modèle, prompt, plafond, date)
    journal = JournalConversation("id_test", modele="mistral-small-latest", prompt="prompt X", plafond=10, repertoire=tmp_path)
    journal.fermer("succes")
    enregistrements = lire_journal(journal.chemin)
    assert enregistrements[0]["event"] == "contexte"
    assert enregistrements[0]["modele"] == "mistral-small-latest"
    assert enregistrements[0]["prompt"] == "prompt X"
    assert enregistrements[0]["plafond"] == 10
    assert enregistrements[0]["date"]
    assert enregistrements[-1]["event"] == "fin"
    assert enregistrements[-1]["statut"] == "succes"


def test_enregistrements_horotes(tmp_path):
    # Réf. tests/plan_tests.md : TU-C2 — un enregistrement JSONL par événement, horodaté
    journal = JournalConversation("id_test", repertoire=tmp_path)
    journal.enregistrer("message_utilisateur", contenu="bonjour")
    journal.enregistrer("outil_invoque", outil="rechercher_jeux", arguments={"mots_cles": ["dette"]}, tour=1)
    journal.fermer("succes")
    lignes = journal.chemin.read_text(encoding="utf-8").strip().splitlines()
    assert len(lignes) == 4
    for ligne in lignes:
        enregistrement = json.loads(ligne)
        assert enregistrement["timestamp"]
        assert enregistrement["id_execution"] == "id_test"
    evenements = [json.loads(l)["event"] for l in lignes]
    assert evenements == ["contexte", "message_utilisateur", "outil_invoque", "fin"]


def test_evenement_inconnu_devient_fin(tmp_path):
    # Réf. tests/plan_tests.md : Test annexe — event hors liste bornée
    journal = JournalConversation("id_test", repertoire=tmp_path)
    journal.enregistrer("evenement_bizarre", x=1)
    journal.fermer("succes")
    evenements = [e["event"] for e in lire_journal(journal.chemin)]
    assert "evenement_bizarre" not in evenements


def test_erreur_ecriture_silencieuse(tmp_path, monkeypatch):
    # Réf. tests/plan_tests.md : TU-C3 — échec d'écriture jamais remonté
    journal = JournalConversation("id_test", repertoire=tmp_path)
    monkeypatch.setattr(journal, "_flux", None)
    journal.enregistrer("message_utilisateur", contenu="x")
    journal.fermer("succes")


# ---------------------------------------------------------------------
# Intégration boucle -> journal (TU-C5, TU-C6)
# ---------------------------------------------------------------------

def test_conversation_complete_journalisee(tmp_path, monkeypatch):
    # Réf. tests/plan_tests.md : TU-C5 — conversation complète : séquence d'événements
    import src.agent.outils as module_outils
    monkeypatch.setitem(module_outils.TABLE_OUTILS, "rechercher_jeux",
                        MagicMock(return_value={"statut": "succes", "message": "", "donnees": {"jeux": []}}))
    appel = _reponse_sdk(tool_calls=[_tool_call_sdk("rechercher_jeux", {"mots_cles": ["dette"]})], contenu="Je lance la recherche.")
    final = _reponse_sdk(contenu="Voici les jeux.")
    agent = _agent([appel, final])
    journal = JournalConversation("id_flux", modele="mistral-small-latest", prompt="P", plafond=10, repertoire=tmp_path)
    reponse = boucle_conversation(agent, "cherche la dette", id_execution="id_flux", journal=journal)
    assert reponse["statut"] == "succes"
    evenements = [e["event"] for e in lire_journal(journal.chemin)]
    assert evenements == [
        "contexte",
        "message_utilisateur",
        "raisonnement_agent",
        "outil_invoque",
        "outil_resultat",
        "reponse_finale",
        "fin",
    ]
    raisonnement = lire_journal(journal.chemin)[2]
    assert raisonnement["contenu"] == "Je lance la recherche."
    assert raisonnement["tour"] == 1


def test_journal_plafond_et_erreur(tmp_path):
    # Réf. tests/plan_tests.md : TU-C6 — plafond et erreur API journalisés
    appel = _reponse_sdk(tool_calls=[_tool_call_sdk("rechercher_jeux", {"mots_cles": ["x"]})])
    agent = _agent([appel] * 30)
    journal = JournalConversation("id_p", repertoire=tmp_path)
    boucle_conversation(agent, "x", plafond=2, id_execution="id_p", journal=journal)
    evenements = [e["event"] for e in lire_journal(journal.chemin)]
    assert "plafond_atteint" in evenements
    assert lire_journal(journal.chemin)[-1]["statut"] == "succes_plafond"

    agent_ko = MagicMock()
    agent_ko.agent_id = "ag"
    agent_ko.client.agents.complete.side_effect = RuntimeError("429")
    journal_ko = JournalConversation("id_ko", repertoire=tmp_path)
    boucle_conversation(agent_ko, "x", id_execution="id_ko", journal=journal_ko)
    evenements_ko = [e["event"] for e in lire_journal(journal_ko.chemin)]
    assert "erreur_api" in evenements_ko
    assert lire_journal(journal_ko.chemin)[-1]["statut"] == "echec_technique"


# ---------------------------------------------------------------------
# Rejeu : lire_journal / extraire_invocations (TU-C7, TU-C8)
# ---------------------------------------------------------------------

def test_extraire_invocations_rejeu(tmp_path, monkeypatch):
    # Réf. tests/plan_tests.md : TU-C7 — extraction ordonnée (base TA-01/TA-02)
    import src.agent.outils as module_outils
    monkeypatch.setitem(module_outils.TABLE_OUTILS, "rechercher_jeux",
                        MagicMock(return_value={"statut": "succes", "message": "", "donnees": {"jeux": [{"id": "abc"}]}}))
    monkeypatch.setitem(module_outils.TABLE_OUTILS, "lister_ressources",
                        MagicMock(return_value={"statut": "succes", "message": "", "donnees": {"ressources": []}}))
    tour1 = _reponse_sdk(tool_calls=[_tool_call_sdk("rechercher_jeux", {"mots_cles": ["dette"]}, "a1")])
    tour2 = _reponse_sdk(tool_calls=[_tool_call_sdk("lister_ressources", {"id_jeu": "abc"}, "a2")])
    final = _reponse_sdk(contenu="Fini.")
    agent = _agent([tour1, tour2, final])
    journal = JournalConversation("id_r", repertoire=tmp_path)
    boucle_conversation(agent, "dette", id_execution="id_r", journal=journal)
    invocations = extraire_invocations(lire_journal(journal.chemin))
    assert len(invocations) == 2
    assert invocations[0]["outil"] == "rechercher_jeux"
    assert invocations[0]["arguments"] == {"mots_cles": ["dette"]}
    assert invocations[0]["statut"] == "succes"
    assert invocations[1]["outil"] == "lister_ressources"
    assert invocations[1]["arguments"]["id_jeu"] == "abc"
    assert [i["tour"] for i in invocations] == [1, 2]


def test_lire_journal_tolerant(tmp_path):
    # Réf. tests/plan_tests.md : TU-C8 — lignes corrompues/absentes ignorées
    chemin = tmp_path / "conversation.jsonl"
    chemin.write_text(
        json.dumps({"event": "contexte", "id_execution": "x"}) + "\n"
        + "{ligne corrompue\n"
        + "\n"
        + json.dumps({"event": "fin", "statut": "succes"}) + "\n",
        encoding="utf-8",
    )
    enregistrements = lire_journal(chemin)
    assert len(enregistrements) == 2
    assert lire_journal(tmp_path / "absent.jsonl") == []
