# Architecture du projet openDataAgent

## 1. Objet
Ce document décrit l'architecture technique du projet **openDataAgent**, conçu pour l'acquisition de données depuis **data.gouv.fr** via des agents Mistral.

## 2. Diagramme des flux
Le diagramme des flux est disponible dans [`docs/conception.mmd`](docs/conception.mmd).
Il couvre :
- Les étapes **agentiques** (reformulation, sélection, classification, synthèse).
- Les étapes **algorithmiques** (recherche, filtre de licence, inventaire, téléchargement).
- Les interactions entre l'agent et le code.

## 3. Composants principaux
| Composant | Rôle | Emplacement |
|-----------|------|-------------|
| **Agent Mistral** | Reformulation, sélection, classification, synthèse. | Intégré via les outils exposés (`rechercher_jeux`, `lister_ressources`, etc.). |
| **Code Python** | Exécution des appels HTTP, filtre de licence, normalisation, persistance. | Répertoire racine du projet. |
| **Contrats** | Schémas JSON des fonctions exposées aux agents. | `contrats/` |
| **Documentation** | Description sémantique des contrats et critères d'acceptabilité. | `docs/` |
| **Stockage** | Fichiers téléchargés et registre des sources inaccessibles. | `data/` (voir [`stockage.md`](stockage.md)). |

## 4. Dépendances
Les dépendances seront définies lors de la première itération d'implémentation.
Exemples attendus :
- `requests` pour les appels HTTP.
- `pydantic` pour la validation des schémas.
- `pytest` pour les tests.

## 5. Déploiement
Le projet s'exécute :
- **En local** : Sur le poste de travail de l'utilisateur.
- **En ligne** : Sur un compte Mistral (intégration directe via les outils exposés).

## 6. Sécurité
Les données de **data.gouv.fr** étant publiques, aucune mesure de sécurité spécifique n'est requise pour le chiffrement ou les listes blanches.
Voir [`registre.md`](registre.md) pour la gestion des sources inaccessibles.

## 7. Améliorations futures
- Ajout d'un mécanisme de **réessai intelligent** pour les échecs techniques.
- Support pour d'autres **sources de données** (ex : Eurostat, INSEE).
- Automatisation des **tests agentiques**.
