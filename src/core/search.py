# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application  : openDataAgent
# Script       : search.py
# Version      : 1
# Date         : 12-10-2026
# Design       : TSC
# Build        : Mistral Vibe
# ---------------------------------------------------------------------
"""
Module pour la recherche de jeux de données sur data.gouv.fr.
"""

from typing import List, Dict, Any, Optional
from src.utils.logging import get_logger, bind_context, log_to_file
from src.utils.http import rechercher_jeux_api
from src.core.licence import licence_est_acceptable
from src.utils.registry import RegistreSourcesInaccessibles

# Initialiser le logger pour ce module
logger = get_logger("openDataAgent.core.search")

_registre_par_defaut = RegistreSourcesInaccessibles()


def rechercher_jeux(
    mots_cles: List[str],
    tri: str = "pertinence",
    fenetre_maj: str = "toutes",
    limite: int = 10,
    page: int = 1,
    id_execution: Optional[str] = None,
    registre: Optional[RegistreSourcesInaccessibles] = None,
) -> Dict[str, Any]:
    """
    Recherche des jeux de données sur data.gouv.fr à partir de mots-clés.
    
    Args:
        mots_cles (List[str]): Liste de mots-clés pour la recherche.
        tri (str): Critère de tri (pertinence, recent, vues, reutilisations).
        fenetre_maj (str): Fenêtre de mise à jour (toutes, 30_jours, 12_mois, 3_ans).
        limite (int): Nombre maximum de jeux à retourner (défaut: 10, max: 20).
        page (int): Numéro de la page de résultats demandée (défaut : 1).
        id_execution (Optional[str]): Identifiant unique pour tracer l'exécution.
        registre (Optional[RegistreSourcesInaccessibles]): Registre des sources
            inaccessibles ; par défaut, l'instance globale sur data/registry.json.
    
    Returns:
        Dict[str, Any]: Résultat de la recherche au format normalisé.
    """
    if registre is None:
        registre = _registre_par_defaut
    # Mettre à jour le contexte de logging avec l'id_execution
    if id_execution:
        bind_context(id_execution=id_execution)
    
    # Log de l'appel de la fonction (console + fichier)
    logger.info(
        "Appel de rechercher_jeux",
        mots_cles=mots_cles,
        tri=tri,
        fenetre_maj=fenetre_maj,
        limite=limite,
    )
    log_to_file(
        "Appel de rechercher_jeux",
        mots_cles=mots_cles,
        tri=tri,
        fenetre_maj=fenetre_maj,
        limite=limite,
    )
    
    # Validation des arguments
    if not mots_cles:
        logger.error("Erreur de paramètres : mots_cles est vide")
        return {
            "statut": "erreur_parametres",
            "message": "Le paramètre 'mots_cles' est obligatoire et ne peut être vide.",
            "donnees": {},
        }
    
    if limite < 1 or limite > 20:
        limite = 10
        logger.warning(
            "Limite ajustée à la valeur par défaut (10)",
            limite_demandee=limite,
        )
    
    # Appel reel a l'API data.gouv.fr via la couche HTTP (T3.1.1)
    try:
        # Log de début de l'appel HTTP (console + fichier)
        logger.debug("Appel HTTP à l'API data.gouv.fr")
        log_to_file("Appel HTTP à l'API data.gouv.fr")

        resultat = rechercher_jeux_api(
            mots_cles=mots_cles,
            tri=tri,
            fenetre_maj=fenetre_maj,
            limite=limite,
            page=page,
        )

        if not resultat.reussi:
            # Log de l'erreur (console + fichier)
            logger.error(
                "Échec de l'appel HTTP à data.gouv.fr",
                statut=resultat.statut,
                erreur=resultat.erreur,
                suggestion="Réessayer après 30 secondes",
            )
            log_to_file(
                "Échec de l'appel HTTP à data.gouv.fr",
                statut=resultat.statut,
                erreur=resultat.erreur,
                suggestion="Réessayer après 30 secondes",
            )
            return {
                "statut": resultat.statut,
                "message": f"Échec de l'appel à l'API data.gouv.fr : {resultat.erreur or resultat.statut}",
                "donnees": {
                    "suggestion": "réessayer",
                },
            }

        data = resultat.donnees

        # Filtre de licence avant tout retour (T3.1.2) et consignation
        # des exclusions au registre (T3.1.3)
        jeux_acceptes = []
        exclus_licence = 0
        for jeu in data["data"]:
            licence = jeu.get("license")
            if licence_est_acceptable(licence):
                jeux_acceptes.append(jeu)
            else:
                exclus_licence += 1
                registre.consigner_exclusion_juridique(
                    id_jeu=jeu["id"],
                    organisation=(jeu.get("organization") or {}).get("name", ""),
                    licence=licence or "notspecified",
                    url=jeu.get("page", ""),
                )
        if exclus_licence:
            registre.sauvegarder()

        # Log du succès (console + fichier)
        logger.info(
            "Recherche terminée",
            total_trouves=data["total"],
            jeux_retournes=len(jeux_acceptes),
            exclus_licence=exclus_licence,
        )
        log_to_file(
            "Recherche terminée",
            total_trouves=data["total"],
            jeux_retournes=len(jeux_acceptes),
            exclus_licence=exclus_licence,
        )
        
        # Retour normalisé
        return {
            "statut": "succes",
            "message": "",
            "donnees": {
                "total_trouves": data["total"],
                "jeux": [
                    {
                        "id": jeu["id"],
                        "titre": jeu["title"],
                        "organisation": (jeu.get("organization") or {}).get("name", ""),
                        "licence": jeu["license"],
                        "derniere_maj": jeu.get("last_modified"),
                        "nb_ressources": len(jeu["resources"]),
                        "url": jeu.get("page", ""),
                    }
                    for jeu in jeux_acceptes
                ],
                "exclus_licence": exclus_licence,
                "page_courante": page,
                "page_suivante": data.get("page_suivante"),
            },
        }
        
    except Exception as e:
        # Log d'une erreur inattendue (console + fichier)
        logger.error(
            "Erreur inattendue lors de la recherche",
            erreur=str(e),
        )
        log_to_file(
            "Erreur inattendue lors de la recherche",
            erreur=str(e),
        )
        return {
            "statut": "echec_technique",
            "message": f"Erreur inattendue : {str(e)}",
            "donnees": {},
        }