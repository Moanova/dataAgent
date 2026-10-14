# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application  : openDataAgent
# Script       : main.py
# Version      : 1
# Date         : 13-10-2026
# Design       : Mistral Vibe
# Build        : Mistral Vibe
# ---------------------------------------------------------------------
"""CLI openDataAgent (Typer).

Couche mince de presentation : traduit une ligne de commande en appel
de la fonction coeur correspondante et affiche la reponse normalisee
{statut, message, donnees}. Aucune logique metier ici.
"""
from datetime import datetime
from typing import List, Optional

import typer

from src.core.search import rechercher_jeux
from src.core.resources import lister_ressources
from src.core.download import telecharger_brut
from src.core.query import interroger_ressource
from src.utils.logging import configure_logging
from src.agent.agent import creer_agent, detruire_agent
from src.agent.boucle import PLAFOND_DEFAUT, boucle_conversation
from src.agent.journal import REPERTOIRE_JOURNAUX

app = typer.Typer(help="CLI openDataAgent : acquisition de donnees data.gouv.fr.")

TRIS = ["pertinence", "recent", "vues", "reutilisations"]
OPERATEURS_FILTRE = ["exact", "contient", "inferieur", "superieur", "strictement_inferieur", "strictement_superieur"]
ORDRES_TRI = ["croissant", "decroissant"]
FENETRES_MAJ = ["toutes", "30_jours", "12_mois", "3_ans"]


def _id_execution_auto() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _afficher_recherche(reponse: dict) -> None:
    if reponse["statut"] != "succes":
        typer.secho(f"[{reponse['statut']}] {reponse['message']}", fg=typer.colors.RED, err=True)
        return
    donnees = reponse["donnees"]
    typer.echo(f"statut : {reponse['statut']}")
    suite = f", page suivante : {donnees['page_suivante']}" if donnees.get("page_suivante") else ""
    typer.echo(f"{donnees['total_trouves']} jeu(x) correspondant(s), "
               f"{len(donnees['jeux'])} retourne(s) (page {donnees['page_courante']}), "
               f"{donnees['exclus_licence']} exclu(s) licence{suite}")
    for jeu in donnees["jeux"]:
        typer.echo(f"- {jeu['titre']}  [{jeu['licence']}]  {jeu['organisation']}")
        typer.echo(f"  id={jeu['id']}  maj={jeu['derniere_maj']}  {jeu['url']}")


@app.callback()
def racine() -> None:
    """CLI openDataAgent : acquisition de donnees data.gouv.fr."""


@app.command()
def search(
    mots_cles: List[str] = typer.Argument(..., help="Mots-cles de la recherche (logique ET)."),
    tri: str = typer.Option("pertinence", "--tri", help="Ordre de tri des resultats."),
    fenetre_maj: str = typer.Option("toutes", "--fenetre-maj", help="Restriction sur la derniere mise a jour."),
    limite: int = typer.Option(10, "--limite", min=1, max=20, help="Nombre maximum de jeux retournes."),
    page: int = typer.Option(1, "--page", min=1, help="Numero de la page de resultats demandee."),
    id_execution: Optional[str] = typer.Option(None, "--id-execution", help="Identifiant d'execution pour les traces."),
    sortie_json: bool = typer.Option(False, "--json", help="Sortie JSON brute de la reponse normalisee."),
) -> None:
    """Recherche des jeux de donnees sur data.gouv.fr par mots-cles."""
    if tri not in TRIS:
        typer.secho(f"Valeur --tri invalide : {tri}. Valeurs acceptees : {', '.join(TRIS)}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)
    if fenetre_maj not in FENETRES_MAJ:
        typer.secho(f"Valeur --fenetre-maj invalide : {fenetre_maj}. Valeurs acceptees : {', '.join(FENETRES_MAJ)}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)

    identifiant = id_execution or _id_execution_auto()
    configure_logging(id_execution=identifiant)

    reponse = rechercher_jeux(
        mots_cles=mots_cles,
        tri=tri,
        fenetre_maj=fenetre_maj,
        limite=limite,
        page=page,
        id_execution=identifiant,
    )

    if sortie_json:
        import json
        typer.echo(json.dumps(reponse, ensure_ascii=False, indent=2))
    else:
        _afficher_recherche(reponse)

    if reponse["statut"] == "erreur_parametres":
        raise typer.Exit(code=2)
    if reponse["statut"] != "succes":
        raise typer.Exit(code=1)


@app.command()
def list(
    id_jeu: str = typer.Argument(..., help="Identifiant du jeu, issu de la recherche."),
    id_execution: Optional[str] = typer.Option(None, "--id-execution", help="Identifiant d'execution pour les traces."),
    sortie_json: bool = typer.Option(False, "--json", help="Sortie JSON brute de la reponse normalisee."),
) -> None:
    """Liste les ressources d'un jeu de donnees avec leurs metadonnees."""
    identifiant = id_execution or _id_execution_auto()
    configure_logging(id_execution=identifiant)

    reponse = lister_ressources(id_jeu=id_jeu, id_execution=identifiant)

    if sortie_json:
        import json
        typer.echo(json.dumps(reponse, ensure_ascii=False, indent=2))
    elif reponse["statut"] == "succes":
        donnees = reponse["donnees"]
        typer.echo(f"statut : {reponse['statut']}")
        typer.echo(f"{len(donnees['ressources'])} ressource(s), "
                   f"{len(donnees['indetermination'])} indeterminee(s)")
        for res in donnees["ressources"]:
            typer.echo(f"- [{res['classe']}] {res['titre']}  ({res['format'] or 'format inconnu'})")
            typer.echo(f"  id={res['id']}  taille={res['taille_octets']}  {res['url']}")
    else:
        typer.secho(f"[{reponse['statut']}] {reponse['message']}", fg=typer.colors.RED, err=True)

    if reponse["statut"] == "erreur_parametres":
        raise typer.Exit(code=2)
    if reponse["statut"] != "succes":
        raise typer.Exit(code=1)


@app.command()
def download(
    id_ressource: str = typer.Argument(..., help="Identifiant de la ressource, issu de l'inventaire."),
    id_execution: Optional[str] = typer.Option(None, "--id-execution", help="Identifiant d'execution pour les traces."),
    sortie_json: bool = typer.Option(False, "--json", help="Sortie JSON brute de la reponse normalisee."),
) -> None:
    """Telecharge une ressource non indexee dans son etat brut."""
    identifiant = id_execution or _id_execution_auto()
    configure_logging(id_execution=identifiant)

    reponse = telecharger_brut(id_ressource=id_ressource, id_execution=identifiant)

    if sortie_json:
        import json
        typer.echo(json.dumps(reponse, ensure_ascii=False, indent=2))
    elif reponse["statut"] == "succes":
        donnees = reponse["donnees"]
        typer.echo(f"statut : {reponse['statut']}")
        typer.echo(f"fichier : {donnees['chemin_local']}")
        typer.echo(f"format : {donnees['format'] or 'inconnu'}  licence : {donnees['licence'] or 'inconnue'}")
    else:
        typer.secho(f"[{reponse['statut']}] {reponse['message']}", fg=typer.colors.RED, err=True)
        if reponse["donnees"].get("suggestion"):
            typer.secho(f"suggestion : {reponse['donnees']['suggestion']}", fg=typer.colors.YELLOW, err=True)

    if reponse["statut"] in ("erreur_parametres", "ressource_introuvable"):
        raise typer.Exit(code=2)
    if reponse["statut"] != "succes":
        raise typer.Exit(code=1)


@app.command()
def query(
    id_ressource: str = typer.Argument(..., help="Identifiant de la ressource, issu de l'inventaire."),
    page: int = typer.Option(1, "--page", min=1, help="Page demandee."),
    taille_page: int = typer.Option(20, "--taille-page", min=1, max=50, help="Lignes par page (max 50)."),
    colonne: Optional[str] = typer.Option(None, "--filtre-colonne", help="Colonne du filtre."),
    valeur: Optional[str] = typer.Option(None, "--filtre-valeur", help="Valeur du filtre."),
    operateur: Optional[str] = typer.Option("exact", "--filtre-operateur", help="Operateur : exact, contient, inferieur, superieur, strictement_inferieur, strictement_superieur."),
    tri_colonne: Optional[str] = typer.Option(None, "--tri-colonne", help="Colonne du tri."),
    tri_ordre: Optional[str] = typer.Option("croissant", "--tri-ordre", help="Ordre : croissant ou decroissant."),
    id_execution: Optional[str] = typer.Option(None, "--id-execution", help="Identifiant d'execution pour les traces."),
    sortie_json: bool = typer.Option(False, "--json", help="Sortie JSON brute de la reponse normalisee."),
) -> None:
    """Interroge une ressource indexee par l'API tabulaire."""
    if operateur not in OPERATEURS_FILTRE:
        typer.secho(f"Valeur --filtre-operateur invalide : {operateur}. Valeurs acceptees : {', '.join(OPERATEURS_FILTRE)}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)
    if tri_ordre not in ORDRES_TRI:
        typer.secho(f"Valeur --tri-ordre invalide : {tri_ordre}. Valeurs acceptees : {', '.join(ORDRES_TRI)}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)
    identifiant = id_execution or _id_execution_auto()
    configure_logging(id_execution=identifiant)

    filtre = {"colonne": colonne, "valeur": valeur, "operateur": operateur} if colonne and valeur is not None else None
    tri = {"colonne": tri_colonne, "ordre": tri_ordre} if tri_colonne else None

    reponse = interroger_ressource(
        id_ressource=id_ressource,
        page=page,
        taille_page=taille_page,
        filtre=filtre,
        tri=tri,
        id_execution=identifiant,
    )

    if sortie_json:
        import json
        typer.echo(json.dumps(reponse, ensure_ascii=False, indent=2))
    elif reponse["statut"] == "succes":
        donnees = reponse["donnees"]
        typer.echo(f"statut : {reponse['statut']}")
        typer.echo(f"{donnees['total_lignes']} ligne(s), colonnes : {', '.join(donnees['colonnes']) or '(aucune)'}")
        if donnees.get("recommandation"):
            typer.secho(f"recommandation : {donnees['recommandation']}", fg=typer.colors.YELLOW)
        for ligne in donnees["lignes"][:5]:
            typer.echo(f"- {ligne}")
        if len(donnees["lignes"]) > 5:
            typer.echo(f"  ... ({len(donnees['lignes']) - 5} ligne(s) supplementaires)")
    else:
        typer.secho(f"[{reponse['statut']}] {reponse['message']}", fg=typer.colors.RED, err=True)
        if reponse["donnees"].get("suggestion"):
            typer.secho(f"suggestion : {reponse['donnees']['suggestion']}", fg=typer.colors.YELLOW, err=True)

    if reponse["statut"] in ("erreur_parametres", "ressource_introuvable"):
        raise typer.Exit(code=2)
    if reponse["statut"] != "succes":
        raise typer.Exit(code=1)


@app.command()
def chat(
    prompt: List[str] = typer.Argument(..., help="Demande en francais : l'agent conduit recherche, selection et acquisition."),
    plafond: int = typer.Option(10, "--plafond", min=1, help="Nombre maximum d'invocations d'outils."),
    id_execution: Optional[str] = typer.Option(None, "--id-execution", help="Identifiant d'execution pour les traces et le journal."),
    sortie_json: bool = typer.Option(False, "--json", help="Sortie JSON brute de la reponse normalisee."),
) -> None:
    """Conversation agentique : cree l'agent, conduit le flux, journalise, detruit l'agent."""
    texte = " ".join(prompt).strip()
    if not texte:
        typer.secho("Le prompt ne peut pas etre vide.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)
    identifiant = id_execution or _id_execution_auto()
    configure_logging(id_execution=identifiant)

    creation = creer_agent(identifiant)
    if creation["statut"] != "succes":
        typer.secho(f"[{creation['statut']}] {creation['message']}", fg=typer.colors.RED, err=True)
        suggestion = creation.get("donnees", {}).get("suggestion")
        if suggestion:
            typer.secho(f"suggestion : {suggestion}", fg=typer.colors.YELLOW, err=True)
        raise typer.Exit(code=1)
    agent = creation["donnees"]["agent"]

    try:
        reponse = boucle_conversation(agent, texte, plafond=plafond, id_execution=identifiant)
    finally:
        destruction = detruire_agent(agent)

    chemin_journal = REPERTOIRE_JOURNAUX / identifiant / "conversation.jsonl"
    if sortie_json:
        import json
        charge = dict(reponse)
        charge["donnees"] = dict(reponse.get("donnees", {}), journal=str(chemin_journal))
        if destruction["statut"] == "succes":
            charge["donnees"]["agent_detruit"] = destruction["donnees"].get("detruit", False)
        typer.echo(json.dumps(charge, ensure_ascii=False, indent=2))
    elif reponse["statut"] == "succes":
        donnees = reponse["donnees"]
        typer.echo(f"statut : {reponse['statut']}")
        if reponse["message"]:
            typer.echo(reponse["message"])
        typer.echo(f"invocations d'outils : {donnees['nb_invocations']}/{donnees['plafond']}")
        if destruction["statut"] != "succes" or not destruction["donnees"].get("detruit", True):
            typer.secho(f"destruction de l'agent : {destruction['statut']} {destruction['message']}", fg=typer.colors.YELLOW, err=True)
        typer.echo("")
        typer.echo(donnees["reponse_agent"])
        typer.echo("")
        typer.secho(f"journal de conversation : {chemin_journal}", fg=typer.colors.BLUE)
    else:
        typer.secho(f"[{reponse['statut']}] {reponse['message']}", fg=typer.colors.RED, err=True)
        typer.secho(f"journal de conversation : {chemin_journal}", fg=typer.colors.BLUE, err=True)

    if reponse["statut"] != "succes":
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
