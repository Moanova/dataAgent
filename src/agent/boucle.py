# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application  : openDataAgent
# Script       : boucle.py
# Version      : 1
# Date         : 14-10-2026
# Design       : Mistral Vibe
# Build        : Mistral Vibe
# ---------------------------------------------------------------------
"""Boucle de conversation agentique (T5.3.2).

Envoi du message utilisateur à l'agent Mistral, réception des
tool_calls, exécution par le code (jamais par l'API), renvoi des
résultats normalisés, itération jusqu'à la réponse finale.
Plafond d'invocations d'outils (defaut 10, CA-11) : au delà, arrêt
propre avec synthèse partielle.

Journalisation sans blocage (TA-02) : chaque invocation est
journalisée avec son tour et ses arguments ; le rejeu des journaux
verifie la proprieté d'ordre, la boucle ne bloque rien."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from src.agent.journal import JournalConversation
from src.agent.outils import _decoder_arguments, executer_outil
from src.utils.logging import bind_context, get_logger, log_to_file

PLAFOND_DEFAUT = 10

logger = get_logger("openDataAgent.agent.boucle")


def boucle_conversation(
    agent: Any,
    message_utilisateur: str,
    plafond: Optional[int] = None,
    id_execution: Optional[str] = None,
    journal: Optional[JournalConversation] = None,
) -> Dict[str, Any]:
    """Exécute une conversation complète avec l'agent Mistral.

    Args:
        agent : objet Agent retourné par creer_agent.
        message_utilisateur : demande initiale de l'utilisateur.
        plafond : nombre maximum d'invocations d'outils (defaut 10 ou
                  PLAFOND_INVOCATIONS dans l'environnement).
        id_execution : identifiant d'exécution pour les traces.

    Returns:
        Reponse normalisee {statut, message, donnees} ; donnees
        contient reponse_agent (texte final ou synthèse partielle),
        nb_invocations et plafond.
    """
    plafond = plafond or int(os.environ.get("PLAFOND_INVOCATIONS", PLAFOND_DEFAUT))
    identifiant = id_execution or getattr(agent, "agent_id", "sans_id")
    if id_execution:
        bind_context(id_execution=identifiant)
    if journal is None:
        journal = JournalConversation(
            identifiant,
            modele=getattr(agent, "modele", ""),
            prompt="",
            plafond=plafond,
        )
    messages: List[Dict[str, Any]] = [{"role": "user", "content": message_utilisateur}]
    invocations = 0
    journal.enregistrer("message_utilisateur", contenu=message_utilisateur)
    log_to_file("boucle_debut", plafond=plafond, id_execution=identifiant)
    while True:
        try:
            reponse = agent.client.agents.complete(
                agent_id=agent.agent_id,
                messages=messages,
            )
        except Exception as erreur:
            journal.enregistrer("erreur_api", detail=str(erreur), nb_invocations=invocations)
            journal.fermer("echec_technique", nb_invocations=invocations, plafond=plafond)
            log_to_file(
                "boucle_erreur_api",
                detail=str(erreur),
                nb_invocations=invocations,
                id_execution=identifiant,
            )
            return {
                "statut": "echec_technique",
                "message": f"Échec de l'appel à l'API Mistral : {erreur}",
                "donnees": {"nb_invocations": invocations, "plafond": plafond},
            }
        tool_calls = _extraire_tool_calls(reponse)
        if not tool_calls:
            reponse_agent = _extraire_contenu(reponse)
            journal.enregistrer("reponse_finale", contenu=reponse_agent, nb_invocations=invocations)
            journal.fermer("succes", nb_invocations=invocations, plafond=plafond)
            log_to_file(
                "boucle_reponse_finale",
                nb_invocations=invocations,
                id_execution=identifiant,
            )
            return {
                "statut": "succes",
                "message": "",
                "donnees": {
                    "reponse_agent": reponse_agent,
                    "nb_invocations": invocations,
                    "plafond": plafond,
                },
            }
        contenu_tour = _extraire_contenu(reponse)
        if contenu_tour:
            journal.enregistrer("raisonnement_agent", tour=invocations + 1, contenu=contenu_tour)
        messages.append(_message_assistant(reponse))
        for tool_call in tool_calls:
            if invocations >= plafond:
                journal.enregistrer("plafond_atteint", nb_invocations=invocations, plafond=plafond)
                journal.fermer("succes_plafond", nb_invocations=invocations, plafond=plafond)
                log_to_file(
                    "boucle_plafond_atteint",
                    nb_invocations=invocations,
                    plafond=plafond,
                    id_execution=identifiant,
                )
                return {
                    "statut": "succes",
                    "message": "Plafond d'invocations atteint : synthèse partielle retournée.",
                    "donnees": {
                        "reponse_agent": (
                            f"Arret au plafond de {plafond} invocations d'outils. "
                            "Les acquisitions déjà effectuées sont valides ; "
                            "relancer le flux pour continuer l'exploration."
                        ),
                        "nb_invocations": invocations,
                        "plafond": plafond,
                    },
                }
            nom, arguments, id_appel = _decoder_tool_call(tool_call)
            invocations += 1
            journal.enregistrer(
                "outil_invoque",
                outil=nom,
                arguments=_decoder_arguments(arguments) or arguments,
                tour=invocations,
            )
            log_to_file(
                "boucle_outil_invoque",
                outil=nom,
                arguments=arguments,
                tour=invocations,
                plafond=plafond,
                id_execution=identifiant,
            )
            resultat = executer_outil(nom, arguments, identifiant)
            journal.enregistrer(
                "outil_resultat",
                outil=nom,
                statut=resultat["statut"],
                tour=invocations,
                message=resultat.get("message", ""),
            )
            log_to_file(
                "boucle_outil_resultat",
                outil=nom,
                statut=resultat["statut"],
                tour=invocations,
                id_execution=identifiant,
            )
            messages.append({
                "role": "tool",
                "content": json.dumps(resultat, ensure_ascii=False),
                "tool_call_id": id_appel,
                "name": nom,
            })


def _extraire_tool_calls(reponse: Any) -> List[Any]:
    """Extrait les tool_calls d'une réponse du SDK, formats objet ou dict."""
    try:
        choix = reponse.choices[0]
        message = getattr(choix, "message", None)
        if message is not None:
            appels = getattr(message, "tool_calls", None)
            if appels:
                return list(appels)
        if isinstance(reponse, dict):
            return list(reponse.get("choices", [{}])[0].get("message", {}).get("tool_calls") or [])
    except (AttributeError, IndexError, KeyError, TypeError):
        return []
    return []


def _decoder_tool_call(tool_call: Any) -> Any:
    """Décode un tool_call en (nom, arguments, id_appel)."""
    if isinstance(tool_call, dict):
        fonction = tool_call.get("function", {})
        return fonction.get("name", ""), fonction.get("arguments", {}), tool_call.get("id", "")
    fonction = getattr(tool_call, "function", None)
    nom = getattr(fonction, "name", "") if fonction is not None else ""
    arguments = getattr(fonction, "arguments", {}) if fonction is not None else {}
    return nom, arguments, getattr(tool_call, "id", "")


def _extraire_contenu(reponse: Any) -> str:
    """Extrait le texte final de la réponse de l'agent."""
    try:
        message = getattr(reponse.choices[0], "message", None)
        contenu = getattr(message, "content", None)
        if contenu:
            return contenu
    except (AttributeError, IndexError, TypeError):
        pass
    if isinstance(reponse, dict):
        try:
            return reponse.get("choices", [{}])[0].get("message", {}).get("content", "") or ""
        except (IndexError, AttributeError):
            return ""
    return ""


def _message_assistant(reponse: Any) -> Dict[str, Any]:
    """Construit le message assistant à renvoyer dans la conversation."""
    if isinstance(reponse, dict):
        return reponse.get("choices", [{}])[0].get("message", {"role": "assistant"})
    message = getattr(reponse.choices[0], "message", None)
    if message is None:
        return {"role": "assistant", "content": ""}
    try:
        return message.model_dump(exclude_none=True)
    except AttributeError:
        contenu = getattr(message, "content", "") or ""
        appels = getattr(message, "tool_calls", None) or []
        retour = {"role": "assistant", "content": contenu}
        if appels:
            retour["tool_calls"] = appels
        return retour
