# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application  : openDataAgent
# Script       : registry.py
# Version      : 1
# Date         : 12-10-2026
# Design       : Mistral Vibe
# Build        : Mistral Vibe
# ---------------------------------------------------------------------
"""Registre des sources inaccessibles (T3.1.3, cf. docs/specs/registre.md).

Persistant dans `data/registry.json`. Invariants :
- aucune entree n'est supprimee ou modifiee apres ecriture ;
- le registre persiste entre les executions ;
- ecriture interne uniquement : l'agent n'y accede qu'en lecture via
  `rapport_pour_agent()`, qui retourne une copie.
"""
import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.logging import get_logger, log_to_file

logger = get_logger("openDataAgent.utils.registry")

MOTIF_LICENCE = "licence_incompatible"
MOTIF_SERVEUR = "serveur_origine_bloque"


class RegistreSourcesInaccessibles:
    """Registre persistant des sources inaccessibles (JSON, data/registry.json)."""

    def __init__(self, chemin: Optional[Path] = None) -> None:
        self.chemin = Path(chemin) if chemin else Path("data/registry.json")
        self._entrees: List[Dict[str, Any]] = self._charger()

    def _charger(self) -> List[Dict[str, Any]]:
        """Charge le registre preexistant sans l'ecraser (TU-24).

        Un fichier absent ou invalide produit un registre vide, sans
        exception.
        """
        if not self.chemin.exists():
            return []
        try:
            contenu = json.loads(self.chemin.read_text(encoding="utf-8"))
            entrees = contenu.get("sources_inaccessibles", [])
            if isinstance(entrees, list):
                return entrees
            return []
        except (json.JSONDecodeError, OSError) as exc:
            log_to_file("Registre illisible, demarrage sur registre vide", chemin=str(self.chemin), erreur=str(exc))
            return []

    def _consigner(self, motif: str, id_jeu: str, organisation: str, licence: str, url: str, detail: str) -> Dict[str, Any]:
        entree = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "motif": motif,
            "id_jeu": id_jeu,
            "organisation": organisation,
            "licence": licence,
            "url": url,
            "detail": detail,
        }
        self._entrees.append(entree)
        log_to_file(
            "Source consignee au registre",
            motif=motif,
            id_jeu=id_jeu,
            organisation=organisation,
            licence=licence,
            url=url,
            detail=detail,
        )
        return entree

    def consigner_exclusion_juridique(
        self,
        id_jeu: str,
        organisation: str,
        licence: str,
        url: str,
        detail: str = "Licence non ouverte",
    ) -> Dict[str, Any]:
        """Consigne une exclusion de licence (ecrit par rechercher_jeux, TU-21)."""
        return self._consigner(MOTIF_LICENCE, id_jeu, organisation, licence, url, detail)

    def consigner_echec_technique(
        self,
        id_jeu: str,
        organisation: str,
        licence: str,
        url: str,
        detail: str,
        motif: str = MOTIF_SERVEUR,
    ) -> Dict[str, Any]:
        """Consigne un echec technique (ecrit par telecharger_brut, T3.4)."""
        return self._consigner(motif, id_jeu, organisation, licence, url, detail)

    def sauvegarder(self) -> None:
        """Ecrit le registre au format JSON valide (TU-22)."""
        self.chemin.parent.mkdir(parents=True, exist_ok=True)
        contenu = {"sources_inaccessibles": self._entrees}
        self.chemin.write_text(json.dumps(contenu, ensure_ascii=False, indent=2), encoding="utf-8")

    def rapport_pour_agent(self) -> Dict[str, Any]:
        """Retourne une copie pour la lecture agentique (TU-23)."""
        return copy.deepcopy({"sources_inaccessibles": self._entrees})
