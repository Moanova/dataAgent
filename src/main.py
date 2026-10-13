# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application  : openDataAgent
# Script       : main.py
# Version      : 1
# Date         : 13-10-2026
# Design       : TSC
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
from src.utils.logging import configure_logging

app = typer.Typer(help="CLI openDataAgent : acquisition de donnees data.gouv.fr.")

TRIS = ["pertinence", "recent", "vues", "reutilisations"]
FENETRES_MAJ = ["toutes", "30_jours", "12_mois", "3_ans"]


def _id_execution_auto() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _afficher_recherche(reponse: dict) -> None:
    if reponse["statut"] != "succes":
        typer.secho(f"[{reponse['statut']}] {reponse['message']}", fg=typer.colors.RED, err=True)
        return
    donnees = reponse["donnees"]
    typer.echo(f"statut : {reponse['statut']}")
    typer.echo(f"{donnees['total_trouves']} jeu(x) correspondant(s), "
               f"{len(donnees['jeux'])} retourne(s), {donnees['exclus_licence']} exclu(s) licence")
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


if __name__ == "__main__":
    app()
