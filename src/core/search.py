# -*- coding: utf-8 -*-
"""
Module pour la recherche de jeux de données sur data.gouv.fr.
"""

from typing import List, Dict, Any, Optional
import requests
from src.utils.logging import get_logger, bind_context, log_to_file

# Initialiser le logger pour ce module
logger = get_logger("dataAgent.core.search")


def rechercher_jeux(
    mots_cles: List[str],
    tri: str = "pertinence",
    fenetre_maj: str = "toutes",
    limite: int = 10,
    id_execution: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Recherche des jeux de données sur data.gouv.fr à partir de mots-clés.
    
    Args:
        mots_cles (List[str]): Liste de mots-clés pour la recherche.
        tri (str): Critère de tri (pertinence, recent, vues, reutilisations).
        fenetre_maj (str): Fenêtre de mise à jour (toutes, 30_jours, 12_mois, 3_ans).
        limite (int): Nombre maximum de jeux à retourner (défaut: 10, max: 20).
        id_execution (Optional[str]): Identifiant unique pour tracer l'exécution.
    
    Returns:
        Dict[str, Any]: Résultat de la recherche au format normalisé.
    """
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
    
    # Simulation d'un appel à l'API data.gouv.fr
    try:
        # Log de début de l'appel HTTP (console + fichier)
        logger.debug("Appel HTTP à l'API data.gouv.fr")
        log_to_file("Appel HTTP à l'API data.gouv.fr")
        
        # Remplace cette partie par un vrai appel à l'API data.gouv.fr
        # Exemple :
        # response = requests.get(
        #     "https://www.data.gouv.fr/api/1/datasets/",
        #     params={
        #         "q": " ".join(mots_cles),
        #         "sort": tri,
        #         "refine.created": fenetre_maj,
        #         "page_size": limite,
        #     },
        # )
        # response.raise_for_status()
        # data = response.json()
        
        # Simulation de données pour le test
        data = {
            "total_count": 39,
            "data": [
                {
                    "id": "67660551c8588734a16a6a60",
                    "title": "Comptes des administrations publiques",
                    "organization": {"name": "Insee"},
                    "license": "etalab-2.0",
                    "last_update": "2026-01-15",
                    "resources": [{"id": "71ff1335"}],
                    "page": "https://www.data.gouv.fr/fr/datasets/67660551c8588734a16a6a60/",
                }
            ],
        }
        
        # Log du succès (console + fichier)
        logger.info(
            "Recherche terminée",
            total_trouves=data["total_count"],
            jeux_retournes=len(data["data"]),
            exclus_licence=3,  # Simulé
        )
        log_to_file(
            "Recherche terminée",
            total_trouves=data["total_count"],
            jeux_retournes=len(data["data"]),
            exclus_licence=3,  # Simulé
        )
        
        # Retour normalisé
        return {
            "statut": "succes",
            "message": "",
            "donnees": {
                "total_trouves": data["total_count"],
                "jeux": [
                    {
                        "id": jeu["id"],
                        "titre": jeu["title"],
                        "organisation": jeu["organization"]["name"],
                        "licence": jeu["license"],
                        "derniere_maj": jeu["last_update"],
                        "nb_ressources": len(jeu["resources"]),
                        "url": jeu["page"],
                    }
                    for jeu in data["data"]
                ],
                "exclus_licence": 3,  # Simulé
            },
        }
        
    except requests.exceptions.RequestException as e:
        # Log de l'erreur HTTP (console + fichier)
        logger.error(
            "Échec de l'appel HTTP à data.gouv.fr",
            url="https://www.data.gouv.fr/api/1/datasets/",
            erreur=str(e),
            suggestion="Réessayer après 30 secondes",
        )
        log_to_file(
            "Échec de l'appel HTTP à data.gouv.fr",
            url="https://www.data.gouv.fr/api/1/datasets/",
            erreur=str(e),
            suggestion="Réessayer après 30 secondes",
        )
        return {
            "statut": "echec_technique",
            "message": f"Échec de l'appel à l'API data.gouv.fr : {str(e)}",
            "donnees": {
                "suggestion": "réessayer",
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