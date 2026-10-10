# Journal des décisions de conception

Ce document recense les décisions prises lors de la conception du projet **dataAgent**, ainsi que leur justification, leur date de prise de décision et leur impact sur les artefacts du projet.

---

## Décisions prises le **10 octobre 2026**

---

### 1. Diagramme des flux

#### Décision
Utiliser le fichier [`docs/conception.mmd`](conception.mmd) pour représenter le diagramme des flux du projet.

### Justification
- Le fichier `conception.mmd` couvre déjà l'ensemble des **étapes agentiques** (A1 à A4) et **algorithmiques** (B1 à B8).
- Il décrit également les **interactions** entre l'agent et le code, ainsi que les **points de décision** (ex : filtre de licence, classification des ressources).

### Impact
- Référencé dans [`ARCHITECTURE.md`](ARCHITECTURE.md).
- Aucun ajout ou modification nécessaire.

---

### 2. Arborescence pour le stockage des fichiers téléchargés

#### Décision
Adopter l'arborescence suivante pour le stockage des fichiers téléchargés :
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

### Détails
- **`<id_execution>`** : Identifiant unique pour chaque exécution, au format `<date>_<heure>_<hash_court>` (ex : `20261010_143022_a1b2c3`).
- **`<id_ressource>`** : Identifiant de la ressource (ex : `71ff1335`).
- **`<nom_fichier_original>`** : Nom du fichier d'origine (nettoyé pour éviter les caractères spéciaux).
- **`<extension>`** : Extension du fichier (ex : `csv`, `zip`, `geojson`).

### Justification
- **Évite les conflits de noms** : Chaque exécution est isolée dans un dossier dédié.
- **Traçabilité** : L'`id_execution` permet de retrouver tous les fichiers d'une session.
- **Persistance** : Le registre (`registry.json`) est stocké dans `data/` pour être conservé entre les exécutions.

### Impact
- Documenté dans [`STOCKAGE.md`](STOCKAGE.md).

---

### 3. Réalignement des contrats JSON

#### Décision
Mettre à jour les fichiers JSON des contrats pour les aligner sur leur documentation (`*.md`). Les modifications apportées sont les suivantes :

| Fichier JSON | Champ ajouté/modifié | Description |
|--------------|-----------------------|-------------|
| `rechercher_jeux.json` | `donnees.exclus_licence` | Nombre de jeux écartés par le filtre de licence. |
| `lister_ressources.json` | `donnees.indetermination` | Identifiants des ressources non classées automatiquement. |
| `interroger_ressource.json` | `donnees.recommandation` | Recommandation pour les volumes élevés (ex : `volume_eleve_telechargement_brut_suggere`). |
| `telecharger_brut.json` | `donnees.chemin_local`, `donnees.licence`, `donnees.suggestion` | Métadonnées du fichier téléchargé et suggestion en cas d'échec. |

### Justification
- **Cohérence** : Aligner les schémas JSON sur la documentation pour éviter les divergences.
- **Exhaustivité** : Tous les champs mentionnés dans la documentation sont désormais définis dans les contrats.

### Impact
- Fichiers JSON mis à jour dans `contrats/`.

---

### 4. Gestion des conflits de noms de fichiers

#### Décision
Utiliser l'`id_execution` et l'`id_ressource` pour éviter les conflits de noms de fichiers téléchargés.

### Détails
- **Conflits entre exécutions** : Résolus par l'`id_execution` (ex : `20261010_143022_a1b2c3`).
- **Conflits dans une même exécution** : Si deux fichiers ont le même `<nom_fichier_original>.<extension>`, un suffixe numérique est ajouté (ex : `71ff1335_budget-fr-indicateurs_1.csv`).

### Justification
- **Robustesse** : Évite les écrasements accidentels.
- **Traçabilité** : Permet de retrouver l'origine d'un fichier.

### Impact
- Documenté dans [`STOCKAGE.md`](STOCKAGE.md).

---

### 5. Tests des formats non tabulaires

#### Décision
Ajouter des tests pour valider le traitement des formats non tabulaires (ZIP, GeoJSON, JSON, SHP, PDF).

### Détails
- **Tests unitaires (TU-29 à TU-33)** : Validation de la classification et de la persistance.
- **Tests d'intégration (TI-11 et TI-12)** : Téléchargement et vérification des fichiers ZIP et GeoJSON.

### Justification
- **Exhaustivité** : Couvrir tous les formats mentionnés dans la documentation.
- **Robustesse** : Valider le traitement des formats complexes.

### Impact
- Ajout des tests dans [`planTest.md`](planTest.md).

---

### 6. Sécurité

#### Décision
Ne pas implémenter de **listes blanches** ni de **chiffrement** pour ce projet.

### Justification
- **Listes blanches** : Les données de **data.gouv.fr** sont publiques et ne présentent pas de risque de phishing ou de liens malveillants.
- **Chiffrement** : Aucune donnée sensible n'est manipulée (pas de mots de passe, pas de tokens, pas de données personnelles).

### Impact
- Aucun impact sur les artefacts du projet.

---

### 7. Déploiement

#### Décision
Le projet s'exécute :
- **En local** : Sur le poste de travail de l'utilisateur.
- **En ligne** : Sur un compte Mistral (intégration directe via les outils exposés).

### Justification
- **Simplicité** : Pas besoin de configuration complexe ou d'infrastructure dédiée.
- **Flexibilité** : Adapté à un usage personnel ou en ligne.

### Impact
- Documenté dans [`ARCHITECTURE.md`](ARCHITECTURE.md).

---

### 8. Journalisation des décisions

#### Décision
Créer ce fichier (`DECISIONS_CONCEPTION.md`) pour journaliser les décisions de conception.

### Justification
- **Traçabilité** : Conserver une trace des choix de conception et de leur justification.
- **Maintenabilité** : Faciliter l'onboarding et les évolutions futures.

### Impact
- Fichier créé dans `docs/`.

---

### 9. Prochaines étapes

Les décisions suivantes sont reportées à des itérations ultérieures :
- **Réessai intelligent** : Mécanisme de réessai avec délai exponentiel pour les échecs techniques.
- **Support pour d'autres sources de données** : Intégration de plateformes comme Eurostat ou INSEE.
- **Nettoyage automatique** : Suppression des anciennes exécutions (ex : dossiers vieux de plus de 30 jours).
- **Automatisation des tests agentiques** : Automatisation des tests TA avec des scénarios prédéfinis.