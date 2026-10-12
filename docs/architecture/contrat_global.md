# Documentation des contrats — Répertoire docs/

Ce document contient le contenu des cinq fichiers de documentation à copier dans le répertoire `docs/` de l'arborescence applicative. Chaque section correspond à un fichier distinct.

---

## Fichier : contrat_global.md

# Contrat global des outils exposés aux agents

## Objet

Ce document spécifie les conventions transversales applicables à l'ensemble des outils exposés aux agents Mistral dans la partie 1 du flux d'acquisition de données data.gouv.fr (recherche thématique, sélection, extraction). Les contrats individuels (`rechercher_jeux.md`, `lister_ressources.md`, `interroger_ressource.md`, `telecharger_brut.md`) décrivent chacun une fonction ; le présent document décrit ce qu'ils partagent.

## Sources de vérité

- Structurelle : les fichiers JSON du répertoire `contrats/`, référencés par `contrats/manifeste.json`. Le code charge les schémas depuis ces fichiers.
- Sémantique : le présent répertoire `docs/`.
- Garantie de cohérence : le code refuse de démarrer si le manifeste, le champ `function.name` et le nom de fichier d'un contrat divergent. Tout changement de schémas doit être répercuté dans les deux sources et incrémenté dans le manifeste.

## Rôles et frontières

- L'agent décide : reformulation du thème, sélection des jeux, classification des ressources ambiguës, synthèse du registre.
- Le code exécute : tous les appels HTTP, le filtre de licence, la normalisation, la persistance. L'agent n'accède jamais directement au réseau ; il ne dispose que des quatre outils décrits dans ce répertoire.
- Le registre des sources inaccessibles est en écriture interne uniquement : aucune fonction exposée ne permet de le modifier ou de le vider. L'agent n'y accède qu'en lecture, en fin de flux, pour l'étape de synthèse.

## Format de réponse normalisé

Toute invocation d'outil, sans exception, retourne un objet unique sérialisé en JSON :

```json
{
  "statut": "<code>",
  "message": "<texte court, vide si succès>",
  "donnees": { }
}
```

- `statut` : code normalisé, voir la section suivante.
- `message` : explication brève en cas d'échec ; chaîne vide en cas de succès.
- `donnees` : charge utile spécifique à la fonction, décrite dans son contrat individuel.

Aucune fonction ne lève d'exception vers l'agent. Toute défaillance est exprimée par un code de statut.

## Codes de statut

| Code                    | Signification                                               | Action attendue de l'agent                                                 |
|-------------------------|-------------------------------------------------------------|----------------------------------------------------------------------------|
| `succes`                | Opération réussie.                                          | Exploiter `donnees`.                                                       |
| `erreur_parametres`     | Arguments invalides ou manquants.                           | Corriger les arguments et réessayer.                                       |
| `jeu_introuvable`       | Identifiant de jeu inconnu ou inaccessible.                 | Ne pas réessayer avec le même identifiant ; reprendre à `rechercher_jeux`. |
| `ressource_introuvable` | Identifiant de ressource jamais vu par `lister_ressources`. | Appeler `lister_ressources` sur le jeu concerné.                           |
| `ressource_non_indexee` | Ressource absente de l'API tabulaire.                       | Basculer sur `telecharger_brut`.                                           |
| `licence_refusee`       | Licence du jeu incompatible avec la politique.              | Exclure la source ; ne pas tenter d'accès direct.                          |
| `echec_technique`       | Échec réseau, blocage serveur, expiration.                  | Selon le champ `donnees.suggestion` : réessayer, basculer, ou abandonner.  |

## Conventions transversales

1. Identifiants. Les fonctions s'échangent des identifiants, jamais des contenus bruts. Un identifiant de jeu provient de `rechercher_jeux` ; un identifiant de ressource provient de `lister_ressources`. Un identifiant jamais délivré par la chaîne est refusé.
2. Bornes. Toute fonction limitant le nombre d'éléments retournés applique un défaut (10) et un maximum (20). Il incombe à l'agent de paginer, pas au code d'étendre les bornes.
3. Licence et attribution. Tout retour de succès inclut la licence du jeu. Les obligations associées (mention de la source pour CC-BY, partage à l'identique pour ODbL) doivent être conservées jusqu'à la partie visualisation.
4. Journalisation. Les appels réels transitent par le code et sont journalisés localement avec leurs arguments et résultats. Le rejeu d'un flux algorithmique est déterministe ; les étapes agentiques sont journalisées séparément.
5. Langue. Les descriptions exposées à l'agent, les messages d'erreur et la documentation sont en français. Les codes de statut sont en minuscules sans accent.

## Politique de licence

Licences acceptées : `etalab-2.0`, `odc-odbl`, `cc-by`, `cc-by-sa`, `other-open`. Licences exclues : toute licence fermée, non spécifiée (`notspecified`) ou commerciale. Le filtre s'applique avant tout retour de résultats : un jeu exclu n'est jamais retourné par `rechercher_jeux`, mais il est consigné au registre avec le motif `licence_incompatible`. Cette règle est déterministe et ne fait pas l'objet d'une décision agentique.

## Registre des sources inaccessibles

Deux familles d'entrées :

- Exclusions juridiques (motif `licence_incompatible`), écrites par `rechercher_jeux`.
- Échecs techniques (motifs `serveur_origine_bloque`, `statut_http_*`), écrits par `telecharger_brut`.

Chaque entrée comporte : horodatage, motif, identifiant et organisation du jeu, licence, URL, détail. Le registre est persistant entre les exécutions. Une entrée technique peut être re-testée lors d'une exécution ultérieure ; une entrée juridique est définitive tant que la licence du jeu ne change pas.
