# Stockage des fichiers téléchargés

## 1. Objet
Ce document décrit l'organisation du **stockage des fichiers téléchargés** depuis **data.gouv.fr**, ainsi que la gestion des conflits de noms.

## 2. Arborescence
Les fichiers sont stockés dans le répertoire `data/` avec la structure suivante :
```
dataAgent/
├── data/
│   ├── raw/                  # Fichiers bruts téléchargés
│   │   ├── <id_execution>/   # Identifiant unique par exécution (ex : 20261010_143022_a1b2c3)
│   │   │   ├── <id_ressource>_<nom_fichier_original>.<extension>
│   │   │   └── ...
│   │   └── ...
│   ├── processed/            # Fichiers normalisés (si applicable)
│   └── registry.json         # Registre des sources inaccessibles
```

## 3. Détails
### 3.1. Identifiant d'exécution (`<id_execution>`)
- **Format** : `<date>_<heure>_<hash_court>`.
  - Exemple : `20261010_143022_a1b2c3`.
- **Génération** :
  - Date et heure au format `YYYYMMDD_HHMMSS`.
  - Hash court (6 caractères) basé sur un timestamp ou un UUID.
- **Utilité** :
  - Évite les conflits entre exécutions.
  - Permet de retrouver tous les fichiers d'une session.

### 3.2. Nom des fichiers téléchargés
- **Format** : `<id_ressource>_<nom_fichier_original>.<extension>`.
  - Exemple : `71ff1335_budget-fr-indicateurs.csv`.
- **Règles** :
  - `<id_ressource>` : Identifiant de la ressource (ex : `71ff1335`).
  - `<nom_fichier_original>` : Nom du fichier d'origine (nettoyé pour éviter les caractères spéciaux).
  - `<extension>` : Extension du fichier (ex : `csv`, `zip`, `geojson`).

### 3.3. Exemple concret
```
dataAgent/
├── data/
│   ├── raw/
│   │   ├── 20261010_143022_a1b2c3/
│   │   │   ├── 71ff1335_budget-fr-indicateurs.csv
│   │   │   ├── 8a2b4c6d_donnees-geographiques.geojson
│   │   │   └── 9e8f7g2h_archive.zip
│   │   └── 20261010_154530_b4c5d6/
│   │       └── 3d4e5f6a_donnees-climatiques.csv
│   └── registry.json
```

## 4. Gestion des conflits
- **Conflits entre exécutions** : Résolus par l'`id_execution`.
- **Conflits dans une même exécution** :
  - Si deux fichiers ont le même `<nom_fichier_original>.<extension>`, un suffixe numérique est ajouté.
  - Exemple : `71ff1335_budget-fr-indicateurs_1.csv`, `71ff1335_budget-fr-indicateurs_2.csv`.

## 5. Persistance
- **Registre** : `data/registry.json` est persistant entre les exécutions.
- **Fichiers téléchargés** : Conservés jusqu'à suppression manuelle ou automatisée (ex : nettoyage des anciennes exécutions).

## 6. Améliorations futures
- Ajout d'un **mécanisme de nettoyage automatique** pour les anciennes exécutions.
- Support pour le **stockage distant** (ex : S3, Google Drive).