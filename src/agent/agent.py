# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application  : openDataAgent
# Script       : agent.py
# Version      : 1.1
# Date         : 14-10-2026
# Design       : TSC
# Build        : Mistral Vibe
# ---------------------------------------------------------------------
"""Creation et destruction de l'agent Mistral (T5.3.1).

L'agent est ephemere : cree par code au debut de l'execution via l'API
beta `client.beta.agents`, identifie par son agent_id, utilise par la
suite via `client.agents.complete`, puis detruit en fin de flux. La
configuration (modele, prompt systeme, outils) vit dans le depot :
contrats JSON charges depuis le manifeste, prompt constant. Aucun
etat de configuration ne vit sur la console au-dela de l'execution.

Garde-fou : si un MISTRAL_AGENT_ID est present dans l'environnement,
l'agent correspondant est verifie (modele, empreinte du prompt, outils)
avant toute utilisation ; toute divergence entraine la creation d'un
agent ephemere neuf, jamais l'execution avec une configuration divergente.

Echec propre systematique : aucune exception ne remonte vers
l'appelant ; toute defaillance est exprimee par un statut normalise.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from src.utils.logging import configure_logging, log_to_file

load_dotenv()

REPERTOIRE_CONTRATS = Path(__file__).resolve().parents[2] / "contrats"

MODELE_DEFAUT = "mistral-small-latest"

PROMPT_SYSTEME = """Tu es l'agent d'acquisition de donnees du projet openDataAgent. Ton role : aider l'utilisateur a rechercher, selectionner et extraire des jeux de donnees francais publies sur data.gouv.fr. Tu conduis les quatre etapes agentiques du flux : reformulation (A1), selection (A2), tranchage des indeterminations (A3), synthese du registre (A4).

REGLES GENERALES
- Langue : francais exclusivement, pour tes reponses comme pour les arguments des outils.
- Tu ne disposes que de quatre outils : rechercher_jeux, lister_ressources, interroger_ressource, telecharger_brut. Aucun autre acces au reseau ou aux donnees n'existe.
- Toute invocation d'outil retourne un objet unique {statut, message, donnees} : lis toujours le champ statut avant d'agir. succes : exploiter donnees. erreur_parametres : corriger les arguments puis reessayer. jeu_introuvable ou ressource_introuvable : ne reessaie jamais avec le meme identifiant, reprends a l'etape amont. ressource_non_indexee : bascule sur telecharger_brut. licence_refusee : exclure la source, sans tenter d'acces direct. echec_technique : suis donnees.suggestion (reessayer, basculer ou abandonner).
- Identifiants : un identifiant de jeu provient de rechercher_jeux, un identifiant de ressource provient de lister_ressources. N'invente jamais un identifiant.
- Ordre des etapes : ne jamais appeler telecharger_brut sur une ressource qui n'a pas ete vue dans lister_ressources au cours de ce flux.
- Economie d'invocations : le nombre d'appels d'outils est plafonne. Chaque invocation doit etre utile ; evite les appels redondants.
- Licence : chaque reponse de succes mentionne la licence du jeu ; conserve-la jusqu'a la restitution finale, les obligations d'attribution doivent suivre les donnees.

A1 - REFORMULATION
- Traduis le theme de l'utilisateur en 2 a 4 mots-cles courts et specifiques (la recherche applique une logique ET : des termes trop nombreux ou trop vagues restreignent ou bruent le resultat).
- Reformule en francais standard : supprime les sigles ambigus, evite les pluriels et les mots vides.
- Si la recherche ne retourne rien : elargis (retire un mot-cle) ou reformule autrement, puis relance. Si elle retourne trop de resultats bruits : affinis.
- Tri : pertinence par defaut ; vues si le theme est large. Contrainte temporelle via fenetre_maj si l'utilisateur veut des donnees recentes.
- Pagination : si page_suivante est present, evalue les pages suivantes avant de conclure que les jeux pertinents manquent.

A2 - SELECTION
- Pour chaque jeu, lis titre, organisation, licence, derniere mise a jour et nombre de ressources.
- Privilegie les jeux recents, publies par des organisations officielles (Insee, ministeres, collectivites...) et comportant des ressources exploitables.
- Justifie chaque jeu retenu en une phrase dans ton raisonnement. Les jeux exclus par licence sont deja filtres par le code : ne tente pas de les reacquerir.
- Si plusieurs jeux sont equivalents, retiens le mieux maintenu et documente ; ne retiens pas plus de jeux que necessaire au besoin de l'utilisateur.

A3 - TRANCHAGE DES INDETERMINATIONS
- Lorsque la reponse de lister_ressources contient des entrees dans donnees.indetermination, tranche leur classe a partir du titre et de l'URL de la ressource. La reponse est autoportante : aucun appel d'outil supplementaire n'est necessaire ni utile.
- Distinction : des signaux contradictoires (format declare csv, mime text/html) ne sont pas des ambiguites ; le code les a deja tranches par priorite. Seules les ressources marquees indetermine attendent ton arbitrage.
- Consigne ta decision dans ton raisonnement (par exemple : cette URL d'API Insee est une api_distante). Le code garde sa classification initiale : ne demande jamais de retraitement.
- Une ressource tranchee comme non exploitable peut simplement etre ignoree pour la suite.

A4 - SYNTHESE DU REGISTRE
- Tout au long du flux, memorise les sources ecartees : licences refusees (statut licence_refusee) et echecs techniques (statut echec_technique, motif dans message ou donnees).
- Pour une ressource dont le telechargement echoue avec la suggestion fichier_heberge_exterieurement : ne relance pas immediatement ; propose plutot une alternative, un jeu equivalent heberge sur la plateforme data.gouv.fr.
- Conclus toujours par un rapport structure en francais : (1) donnees acquises, avec leurs chemins locaux et leur licence (attribution) ; (2) sources retenues et pourquoi ; (3) sources ecartees avec leur motif ; (4) limites eventuelles de l'acquisition.

PAGINATION ET VOLUMES
- Exploite page_suivante pour paginer la recherche et l'interrogation des ressources ; conserve les memes filtres et tris entre les pages d'une extraction.
- Si une reponse de interroger_ressource contient recommandation = volume_eleve_telechargement_brut_suggere, arrete la pagination et bascule sur telecharger_brut : la ressource est trop volumineuse pour une extraction page a page.
- telecharger_brut ecrit sur le disque : reserve-le aux ressources reellement selectionnees, pas a l'exploration. Utilise interroger_ressource pour previsualiser le contenu d'une ressource indexee.
"""

PREFIXE_NOM = "openDataAgent"


@dataclass
class Agent:
    """Agent Mistral ephemere cree pour une execution.

    Attributs :
        client : client Mistral instancie.
        agent_id : identifiant de l'agent sur la console Mistral.
        modele : modele assigne a l'agent.
        outils : definitions d'outils passees a l'agent.
        ephemere : True si l'agent a ete cree par ce flux et doit
                   etre detruit en fin d'execution ; False si un agent
                   persistant existant a ete reutilise apres verification.
        empreinte_prompt : empreinte sha256 du prompt systeme envoye.
    """

    client: Any
    agent_id: str
    modele: str
    outils: List[Dict[str, Any]]
    ephemere: bool = True
    empreinte_prompt: str = ""


def empreinte(texte: str) -> str:
    """Empreinte sha256 courte d'un texte (comparaison de prompt)."""
    return hashlib.sha256(texte.encode("utf-8")).hexdigest()


def charger_outils(repertoire: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Charge les definitions d'outils depuis le manifeste des contrats.

    Refuse de demarrer si le manifeste, le champ function.name et le
    nom de fichier d'un contrat divergent (invariant du contrat global).

    Returns:
        Liste des definitions d'outils au format function calling.

    Raises:
        ValueError : manifeste illisible ou divergence constatee.
        FileNotFoundError : contrat reference mais absent.
    """
    repertoire = repertoire or REPERTOIRE_CONTRATS
    chemin_manifeste = repertoire / "manifeste.json"
    with open(chemin_manifeste, encoding="utf-8") as flux:
        manifeste = json.load(flux)
    outils = []
    for entree in manifeste["outils"]:
        nom = entree["nom"]
        fichier = entree["fichier"]
        if Path(fichier).stem != nom:
            raise ValueError(
                f"Divergence manifeste/fichier : outil '{nom}' reference "
                f"'{fichier}'."
            )
        with open(repertoire / fichier, encoding="utf-8") as flux:
            contrat = json.load(flux)
        if contrat.get("function", {}).get("name") != nom:
            raise ValueError(
                f"Divergence manifeste/contrat : '{nom}' reference un "
                f"contrat dont function.name vaut "
                f"'{contrat.get('function', {}).get('name')}'."
            )
        outils.append(contrat)
    return outils


def creer_agent(
    id_execution: str,
    client: Optional[Any] = None,
) -> Dict[str, Any]:
    """Cree (ou reutilise apres verification) l'agent Mistral d'une execution.

    Garde-fou : si MISTRAL_AGENT_ID est defini et que l'agent correspondant
    est strictement conforme (modele, empreinte du prompt systeme, outils),
    il est reutilise (ephemere=False) ; toute divergence ou absence entraine
    la creation d'un agent ephemere neuf.

    Returns:
        Reponse normalisee {statut, message, donnees}. En succes, donnees
        contient l'objet Agent (champ "agent").
    """
    try:
        outils = charger_outils()
    except (ValueError, KeyError, FileNotFoundError) as erreur:
        log_to_file("agent_contrats_invalides", detail=str(erreur), id_execution=id_execution)
        return {
            "statut": "echec_technique",
            "message": f"Contrats d'outils invalides : {erreur}",
            "donnees": {},
        }

    cle = os.environ.get("MISTRAL_API_KEY", "")
    if not cle:
        log_to_file("agent_cle_absente", id_execution=id_execution)
        return {
            "statut": "echec_technique",
            "message": "Variable d'environnement MISTRAL_API_KEY absente ou vide.",
            "donnees": {"suggestion": "definir MISTRAL_API_KEY dans .env"},
        }

    modele = os.environ.get("MISTRAL_MODELE", MODELE_DEFAUT)
    try:
        if client is None:
            client = _instancier_client(cle)
    except Exception as erreur:
        log_to_file("agent_client_erreur", detail=str(erreur), id_execution=id_execution)
        return _echec_instanciation(erreur)

    agent_existant = _verifier_agent_existant(client, outils, modele)
    if agent_existant is not None:
        log_to_file(
            "agent_persistant_reutilise",
            agent_id=agent_existant.agent_id,
            modele=modele,
            id_execution=id_execution,
        )
        return {
            "statut": "succes",
            "message": "",
            "donnees": {"agent": agent_existant},
        }

    nom = f"{PREFIXE_NOM}-{id_execution}"
    try:
        reponse = client.beta.agents.create(
            model=modele,
            name=nom,
            instructions=PROMPT_SYSTEME,
            tools=sorted(outils, key=lambda o: o["function"]["name"]),
            description="Agent d'acquisition de donnees data.gouv.fr (flux openDataAgent).",
            metadata={"id_execution": id_execution, "projet": PREFIXE_NOM},
        )
    except Exception as erreur:
        log_to_file("agent_creation_erreur", detail=str(erreur), id_execution=id_execution)
        return {
            "statut": "echec_technique",
            "message": f"Echec de la creation de l'agent Mistral : {erreur}",
            "donnees": {"suggestion": "reessayer"},
        }

    agent = Agent(
        client=client,
        agent_id=reponse.id,
        modele=modele,
        outils=outils,
        ephemere=True,
        empreinte_prompt=empreinte(PROMPT_SYSTEME),
    )
    log_to_file(
        "agent_cree",
        agent_id=agent.agent_id,
        modele=modele,
        nb_outils=len(outils),
        id_execution=id_execution,
    )
    return {
        "statut": "succes",
        "message": "",
        "donnees": {"agent": agent},
    }


def detruire_agent(agent: Any) -> Dict[str, Any]:
    """Detruit l'agent ephemere sur la console Mistral.

    Un agent non ephemere (persistant reutilise) n'est jamais detruit.
    Un agent_id deja supprime est un succes (idempotence) : le but est
    qu'aucun agent residuel ne subsiste, pas l'exactitude de l'etat.

    Returns:
        Reponse normalisee {statut, message, donnees}.
    """
    if not isinstance(agent, Agent):
        return {
            "statut": "erreur_parametres",
            "message": "detruire_agent attend un objet Agent.",
            "donnees": {},
        }
    if not agent.ephemere:
        log_to_file("agent_persistant_conserve", agent_id=agent.agent_id)
        return {
            "statut": "succes",
            "message": "Agent persistant reutilise : non detruit.",
            "donnees": {"detruit": False},
        }
    try:
        agent.client.beta.agents.delete(agent_id=agent.agent_id)
    except Exception as erreur:
        message = str(erreur)
        if "404" in message or "not found" in message.lower():
            log_to_file("agent_deja_absent", agent_id=agent.agent_id)
            return {
                "statut": "succes",
                "message": "Agent deja absent de la console.",
                "donnees": {"detruit": False},
            }
        log_to_file("agent_destruction_erreur", agent_id=agent.agent_id, detail=message)
        return {
            "statut": "echec_technique",
            "message": f"Echec de la destruction de l'agent : {message}",
            "donnees": {"suggestion": "nettoyer_agents_orphelins"},
        }
    log_to_file("agent_detruit", agent_id=agent.agent_id)
    return {
        "statut": "succes",
        "message": "",
        "donnees": {"detruit": True},
    }


def nettoyer_agents_orphelins(
    client: Any,
    cle: Optional[str] = None,
) -> Dict[str, Any]:
    """Liste et supprime les agents openDataAgent residuels sur la console.

    Utile apres un crash entre creation et destruction. Cible les agents
    dont le nom commence par PREFIXE_NOM et/ou dont metadata.projet
    correspond au projet.

    Returns:
        Reponse normalisee {statut, message, donnees} ; donnees.detruits
        contient la liste des agent_id supprimes.
    """
    if client is None:
        cle_reelle = cle or os.environ.get("MISTRAL_API_KEY", "")
        if not cle_reelle:
            return {
                "statut": "echec_technique",
                "message": "Variable d'environnement MISTRAL_API_KEY absente ou vide.",
                "donnees": {},
            }
        try:
            client = _instancier_client(cle_reelle)
        except Exception as erreur:
            return _echec_instanciation(erreur)
    detruits: List[str] = []
    erreurs: List[str] = []
    try:
        page = client.beta.agents.list(page_size=100)
        candidats = list(getattr(page, "data", page) or [])
    except Exception as erreur:
        return {
            "statut": "echec_technique",
            "message": f"Echec du listage des agents : {erreur}",
            "donnees": {"suggestion": "reessayer"},
        }
    for candidat in candidats:
        nom_candidat = getattr(candidat, "name", "") or ""
        metadata = getattr(candidat, "metadata", None) or {}
        du_projet = nom_candidat.startswith(PREFIXE_NOM) or metadata.get("projet") == PREFIXE_NOM
        if not du_projet:
            continue
        identifiant = getattr(candidat, "id", "")
        try:
            client.beta.agents.delete(agent_id=identifiant)
            detruits.append(identifiant)
        except Exception as erreur:
            erreurs.append(f"{identifiant} : {erreur}")
    log_to_file("agents_orphelins_nettoyes", detruits=detruits, erreurs=erreurs)
    if erreurs:
        return {
            "statut": "echec_technique",
            "message": f"Echec de suppression pour {len(erreurs)} agent(s).",
            "donnees": {"detruits": detruits, "erreurs": erreurs},
        }
    return {
        "statut": "succes",
        "message": "",
        "donnees": {"detruits": detruits},
    }


def _instancier_client(cle: str) -> Any:
    """Instancie le client Mistral (import tolerant des environnements)."""
    try:
        from mistralai import Mistral
    except ImportError:
        from mistralai.client import Mistral
    return Mistral(api_key=cle)


def _verifier_agent_existant(
    client: Any,
    outils: List[Dict[str, Any]],
    modele: str,
) -> Optional[Agent]:
    """Verifie l'agent persistant designe par MISTRAL_AGENT_ID, s'il existe.

    Retourne un Agent reutilisable seulement si modele, empreinte du
    prompt systeme et ensemble d'outils sont strictement conformes ;
    toute divergence retourne None (creation ephemere par l'appelant).
    """
    agent_id = os.environ.get("MISTRAL_AGENT_ID", "")
    if not agent_id:
        return None
    try:
        agent_console = client.beta.agents.get(agent_id=agent_id)
    except Exception:
        log_to_file("agent_persistant_inaccessible", agent_id=agent_id)
        return None
    if getattr(agent_console, "model", None) != modele:
        log_to_file("agent_persistant_divergent", agent_id=agent_id, motif="modele")
        return None
    instructions = getattr(agent_console, "instructions", "") or ""
    if empreinte(instructions) != empreinte(PROMPT_SYSTEME):
        log_to_file("agent_persistant_divergent", agent_id=agent_id, motif="prompt")
        return None
    outils_console = _extraire_outils(agent_console)
    if {o["function"]["name"] for o in outils} != outils_console:
        log_to_file("agent_persistant_divergent", agent_id=agent_id, motif="outils")
        return None
    return Agent(
        client=client,
        agent_id=agent_id,
        modele=modele,
        outils=outils,
        ephemere=False,
        empreinte_prompt=empreinte(PROMPT_SYSTEME),
    )


def _extraire_outils(agent_console: Any) -> set:
    """Extrait l'ensemble des noms de fonctions d'un agent console."""
    outils = getattr(agent_console, "tools", None) or []
    noms = set()
    for outil in outils:
        if isinstance(outil, dict):
            fonction = outil.get("function", {})
            noms.add(fonction.get("name") or outil.get("type", ""))
        else:
            nom = getattr(outil, "function", None)
            nom = getattr(nom, "name", None) if nom is not None else None
            noms.add(nom or getattr(outil, "type", ""))
    return {n for n in noms if n}


def _echec_instanciation(erreur: Exception) -> Dict[str, Any]:
    return {
        "statut": "echec_technique",
        "message": f"Instanciation du client Mistral impossible : {erreur}",
        "donnees": {"suggestion": "verifier l'installation de mistralai"},
    }
