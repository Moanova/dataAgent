# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application  : openDataAgent
# Script       : base.py
# Version      : 1
# Date         : 12-10-2026
# Design       : Mistral Vibe
# Build        : Mistral Vibe
# ---------------------------------------------------------------------
"""Modeles Pydantic communs aux contrats des outils exposes aux agents.

Ce module definit les types fondamentaux partagees par tous les contrats :
- `StatutEnum` : les sept codes de statut normalises.
- `ReponseBase` : enveloppe standardisee (statut / message / donnees).
- `JeuResume` : resume d'un jeu de donnees retourne par `rechercher_jeux`.
- `RessourceResume` : resume d'une ressource retourne par `lister_ressources`.
- `ClasseRessource` : classification d'une ressource.

Il fournit egalement `valider_coherence_contrat()` qui verifie la concordance
entre un contrat JSON (source de verite pour le function calling) et le
modele Pydantic correspondant.
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any, Type

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Codes de statut normalises (contrat_global.md)
# ---------------------------------------------------------------------------

class StatutEnum(str, Enum):
    """Codes de statut retournes par tout outil, sans exception."""

    SUCCES = "succes"
    JEU_INTROUVABLE = "jeu_introuvable"
    RESSOURCE_INTROUVABLE = "ressource_introuvable"
    RESSOURCE_NON_INDEXEE = "ressource_non_indexee"
    LICENCE_REFUSEE = "licence_refusee"
    ECHEC_TECHNIQUE = "echec_technique"
    ERREUR_PARAMETRES = "erreur_parametres"


# ---------------------------------------------------------------------------
# Classification des ressources (lister_ressources.md)
# ---------------------------------------------------------------------------

class ClasseRessource(str, Enum):
    """Classes de ressources determinees par le classificateur (B3)."""

    FICHIER_TABULAIRE = "fichier_tabulaire"
    FICHIER_AUTRE_FORMAT = "fichier_autre_format"
    PAGE_WEB = "page_web"
    API_DISTANTE = "api_distante"
    INDETERMINE = "indetermine"


# ---------------------------------------------------------------------------
# Enveloppe de reponse standardisee
# ---------------------------------------------------------------------------

class ReponseBase(BaseModel):
    """Tout retour d'outil est un objet de ce type, serialisable en JSON.

    Aucune fonction exposee ne leve d'exception vers l'agent.
    """

    statut: StatutEnum
    message: str = ""
    donnees: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Resumes partages
# ---------------------------------------------------------------------------

class JeuResume(BaseModel):
    """Resume d'un jeu de donnees, retourne dans `donnees.jeux`."""

    id: str
    titre: str
    organisation: str
    licence: str
    derniere_maj: str
    nb_ressources: int
    url: str


class RessourceResume(BaseModel):
    """Resume d'une ressource, retourne dans `donnees.ressources`."""

    id: str
    titre: str
    format: str
    taille_octets: int | None = None
    classe: ClasseRessource
    api_tabulaire: bool
    heberge_sur_plateforme: bool
    url: str


# ---------------------------------------------------------------------------
# Validation de coherence JSON <-> Pydantic
# ---------------------------------------------------------------------------

# Correspondance nom d'outil -> (module, classe Input, classe Output)
_REGISTRE_MODELES: dict[str, tuple[str, str, str]] = {
    "rechercher_jeux": ("rechercher_jeux", "RechercherJeuxInput", "RechercherJeuxOutput"),
    "lister_ressources": ("lister_ressources", "ListerRessourcesInput", "ListerRessourcesOutput"),
    "interroger_ressource": ("interroger_ressource", "InterrogerRessourceInput", "InterrogerRessourceOutput"),
    "telecharger_brut": ("telecharger_brut", "TelechargerBrutInput", "TelechargerBrutOutput"),
}


def valider_coherence_contrat(
    nom_outil: str,
    repertoire_contrats: Path = Path("contrats"),
) -> list[str]:
    """Verifie la coherence entre le contrat JSON et les modeles Pydantic.

    Retourne une liste de divergences (vide si tout est conforme).
    Leve `ValueError` si l'outil est inconnu ou le JSON est absent.
    """
    if nom_outil not in _REGISTRE_MODELES:
        raise ValueError(f"Outil inconnu : '{nom_outil}'.")

    chemin_json = repertoire_contrats / f"{nom_outil}.json"
    if not chemin_json.exists():
        raise ValueError(f"Contrat JSON absent : {chemin_json}")

    contrat = json.loads(chemin_json.read_text(encoding="utf-8"))
    params_json = contrat["function"]["parameters"]
    returns_json = contrat["function"]["returns"]

    divergences: list[str] = []

    # --- Verifier les champs d'entree ---
    module_nom, input_nom, _ = _REGISTRE_MODELES[nom_outil]
    module = __import__(f"src.contracts.{module_nom}", fromlist=[input_nom])
    modele_input: Type[BaseModel] = getattr(module, input_nom)

    champs_json = set(params_json.get("properties", {}).keys())
    champs_pydantic = set(modele_input.model_fields.keys())
    required_json = set(params_json.get("required", []))

    for champ in champs_json - champs_pydantic:
        divergences.append(f"Champ '{champ}' present dans le JSON mais absent du modele Pydantic.")
    for champ in champs_pydantic - champs_json:
        divergences.append(f"Champ '{champ}' present dans le modele Pydantic mais absent du JSON.")
    for champ in required_json:
        field_info = modele_input.model_fields.get(champ)
        if field_info is not None and field_info.is_required() is False:
            divergences.append(f"Champ '{champ}' obligatoire dans le JSON mais optionnel dans Pydantic.")

    # --- Verifier les enums ---
    for champ, spec in params_json.get("properties", {}).items():
        if "enum" in spec and champ in champs_pydantic:
            field_info = modele_input.model_fields[champ]
            annotation = field_info.annotation
            # Resoudre Optional[Enum] -> Enum
            enum_cls = None
            if hasattr(annotation, "__args__"):
                for arg in annotation.__args__:
                    if isinstance(arg, type) and issubclass(arg, Enum):
                        enum_cls = arg
                        break
            elif isinstance(annotation, type) and issubclass(annotation, Enum):
                enum_cls = annotation
            if enum_cls is not None:
                valeurs_json = set(spec["enum"])
                valeurs_pydantic = {e.value for e in enum_cls}
                if valeurs_json != valeurs_pydantic:
                    divergences.append(
                        f"Enum '{champ}' : JSON={sorted(valeurs_json)} "
                        f"Pydantic={sorted(valeurs_pydantic)}"
                    )

    # --- Verifier les champs de sortie ---
    _, _, output_nom = _REGISTRE_MODELES[nom_outil]
    modele_output: Type[BaseModel] = getattr(module, output_nom)

    donnees_json = returns_json.get("properties", {}).get("donnees", {})
    champs_donnees_json = set(donnees_json.get("properties", {}).keys())
    champs_donnees_pydantic = set(modele_output.model_fields.keys())

    for champ in champs_donnees_json - champs_donnees_pydantic:
        divergences.append(f"Champ de sortie '{champ}' present dans le JSON mais absent du modele Pydantic.")
    for champ in champs_donnees_pydantic - champs_donnees_json:
        divergences.append(f"Champ de sortie '{champ}' present dans le modele Pydantic mais absent du JSON.")

    # Verifier le statut enum dans le retour
    statut_json = returns_json.get("properties", {}).get("statut", {})
    if "enum" in statut_json:
        valeurs_json = set(statut_json["enum"])
        # Le statut dans ReponseBase est StatutEnum, mais chaque contrat peut restreindre
        # On verifie que les valeurs du JSON sont un sous-ensemble de StatutEnum
        valeurs_statut = {e.value for e in StatutEnum}
        if not valeurs_json.issubset(valeurs_statut):
            divergences.append(
                f"Statut : valeurs JSON {sorted(valeurs_json)} non incluses dans StatutEnum."
            )

    return divergences
