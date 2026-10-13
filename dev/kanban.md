# Kanban du projet openDataAgent

Ce document suit l'avancement des tâches pour l'implémentation du projet **openDataAgent**. Il est organisé en **4 colonnes** :
- **📌 À faire** : Tâches non commencées.
- **🚧 En cours** : Tâches en cours d'implémentation.
- **🔍 En revue** : Tâches prêtes pour une revue ou des tests.
- **✅ Terminé** : Tâches validées.

---

## 📌 À faire

### 1. Initialisation du projet

---

### 2. Implémentation des contrats

---

### 3. Implémentation des fonctions de base

#### 3.1. Recherche de jeux (`rechercher_jeux`)

#### 3.2. Inventaire des ressources (`lister_ressources`)
- [ ] **T3.2.1** : Implémenter l'appel HTTP pour lister les ressources d'un jeu (`src/core/resources.py`).
- [ ] **T3.2.2** : Classifier les ressources (tabulaire, autre format, etc.).
- [ ] **T3.2.3** : Identifier les ressources ambiguës (`indetermination`).

#### 3.3. Interrogation des ressources (`interroger_ressource`)
- [ ] **T3.3.1** : Implémenter l'appel à l'API tabulaire (`src/core/query.py`).
- [ ] **T3.3.2** : Gérer la pagination, le filtrage et le tri.
- [ ] **T3.3.3** : Retourner une recommandation pour les volumes élevés.

#### 3.4. Téléchargement brut (`telecharger_brut`)
- [ ] **T3.4.1** : Implémenter le téléchargement des fichiers (`src/core/download.py`).
- [ ] **T3.4.2** : Stocker les fichiers dans `data/raw/<id_execution>/` (`src/utils/storage.py`).
- [ ] **T3.4.3** : Gérer les échecs techniques et consigner dans le registre.

---

### 4. Intégration et CLI
- [ ] **T4.1** : Créer la CLI avec Typer (`src/main.py`).
  - [ ] Commande `search` : Appelle `rechercher_jeux`.
  - [ ] Commande `list` : Appelle `lister_ressources`.
  - [ ] Commande `query` : Appelle `interroger_ressource`.
  - [ ] Commande `download` : Appelle `telecharger_brut`.
- [ ] **T4.2** : Configurer les arguments et options pour chaque commande.

---

### 5. Tests

#### 5.1. Tests unitaires
- [ ] **T5.1.1** : Écrire les tests pour `rechercher_jeux` (`tests/test_search.py`).
- [ ] **T5.1.2** : Écrire les tests pour `lister_ressources` (`tests/test_resources.py`).
- [ ] **T5.1.3** : Écrire les tests pour `interroger_ressource` (`tests/test_query.py`).
- [ ] **T5.1.4** : Écrire les tests pour `telecharger_brut` (`tests/test_download.py`).
- [ ] **T5.1.5** : Tester les formats non tabulaires (ZIP, GeoJSON, etc.).

#### 5.2. Tests d'intégration
- [ ] **T5.2.1** : Tester le flux complet (recherche → inventaire → téléchargement).
- [ ] **T5.2.2** : Valider la persistance du registre des sources inaccessibles.

---

### 6. Logging et journalisation
- [ ] **T6.1** : Configurer `structlog` pour tracer les appels et les erreurs.
- [ ] **T6.2** : Ajouter des logs pour chaque étape du flux.

---

### 7. Améliorations futures (optionnel)
- [ ] **T7.1** : Ajouter un mécanisme de réessai intelligent pour les échecs techniques.
- [ ] **T7.2** : Implémenter un nettoyage automatique des anciennes exécutions.
- [ ] **T7.3** : Automatiser les tests agentiques.
- [ ] **T7.4** : Supporter d'autres sources de données (ex : Eurostat, INSEE).

---

## 🚧 En cours

- [ ] **T3.1.2** : Appliquer le filtre de licence (`src/core/search.py`). *(Implémentation et tests unitaires terminés, en attente de validation)*
- [ ] **T3.1.3** : Consigner les exclusions de licence dans le registre (`src/utils/registry.py`). *(Implémentation et tests unitaires terminés, en attente de validation)*
- [ ] **T3.1.4** : Retourner les résultats au format normalisé (statut/message/données). *(Implémentation et tests unitaires terminés, en attente de validation)*

- [ ] **T3.1.1** : Implémenter l'appel HTTP à l'API data.gouv.fr (`src/utils/http.py`). *(Implémentation et tests unitaires terminés, en attente de validation)*
- [ ] **T6.1** : Configurer `structlog` pour tracer les appels et les erreurs (intégration en cours).

---

## ✅ Terminé
- [X] **T1.1** : Créer la structure des dossiers (`src/`, `tests/`, `src/contracts/`, `src/core/`, `src/utils/`). *(Terminé le 10/10/2026)*
- [X] **T1.2** : Configurer le fichier `.env` avec les variables d'environnement (ex : `DATA_GOUV_API_URL`). *(Terminé le 10/10/2026)*
- [X] **T1.3** : Initialiser le logging avec `structlog` (`src/utils/logging.py`). *(Terminé le 10/10/2026)*
- [X] **T2.1** : Créer les schémas Pydantic pour les contrats (`src/contracts/`). *(Terminé le 12/10/2026)*
- [X] **T2.2** : Valider les schémas avec `jsonschema` pour les réponses de l'API data.gouv.fr. *(Terminé le 12/10/2026 — tests TB/TA non passés dans la sandbox, à exécuter en local)*