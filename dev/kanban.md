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
  - [ ] Commande `search` : Appelle `rechercher_jeux`.
  - [ ] Commande `list` : Appelle `lister_ressources`.
  - [ ] Commande `query` : Appelle `interroger_ressource`.
  - [ ] Commande `download` : Appelle `telecharger_brut`.

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

#### 5.3. Intégration agentique Mistral

- [ ] **T5.3.1** : Créer (et détruire) l'agent Mistral : prompt système, choix du modèle, définition des outils (`scripts/agent.py`).
- [ ] **T5.3.2** : Implémenter la boucle de conversation : envoi du message utilisateur, réception et exécution des `tool_calls` vers les fonctions du cœur, renvoi des résultats normalisés (`src/agent/boucle.py`).
- [ ] **T5.3.3** : Journaliser les conversations (arguments, résultats, raisonnements) pour les tests TA et l'audit.
- [ ] **T5.3.4** : Rédiger le prompt système : consignes de reformulation (A1), sélection (A2), tranchage des indéterminations (A3), synthèse du registre (A4), pagination et plafond d'invocations.

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

- [ ] **T4.1** : Créer la CLI avec Typer (`src/main.py`). *(En cours — commande `search` livrée et testée ; `list`, `query`, `download` à venir avec T3.2/T3.3/T3.4)*
- [ ] **T4.2** : Configurer les arguments et options pour chaque commande. *(En cours — périmètre `search` livré)*


- [ ] **T6.1** : Configurer `structlog` pour tracer les appels et les erreurs (intégration en cours).

---

## ✅ Terminé

- [X] **T3.2.3** : Identifier les ressources ambiguës (`indetermination`). *(Termine le 13/10/2026 - semantique actee : contradictoire tranche par priorite, inconnu seulement -> indetermine ; autoportance A3 verrouillee)*

- [X] **T3.2.2** : Classifier les ressources (tabulaire, autre format, etc.). *(Termine le 13/10/2026 - TU-05..11 passes, ordre HTML > API > tabulaire > autre, valide en reel depuis la sandbox)*

- [X] **T3.2.1** : Implémenter l'appel HTTP pour lister les ressources d'un jeu (`src/core/resources.py`). *(Termine le 13/10/2026 - inventaire valide en reel depuis la sandbox, classification T3.2.2 restant a livrer)*

- [X] **T3.1.5** : Ajouter la pagination a `rechercher_jeux` (argument `page`, exposer `page_suivante`/`page_courante` dans la reponse) pour permettre a l'agent d'evaluer tous les jeux trouves. *(Termine le 13/10/2026 - contrat v1.1.0, valide en reel depuis la sandbox)*

- [X] **T3.1.1** : Implémenter l'appel HTTP à l'API data.gouv.fr (`src/utils/http.py`). *(Terminé le 13/10/2026 — API v1, TB-01/TB-03 non passés dans la sandbox, à exécuter en local)*
- [X] **T3.1.2** : Appliquer le filtre de licence (`src/core/search.py`). *(Terminé le 13/10/2026 — politique v1 : lov2, fr-lo, odc-odbl, cc-by, cc-by-sa, cc-zero, other-open)*
- [X] **T3.1.3** : Consigner les exclusions de licence dans le registre (`src/utils/registry.py`). *(Terminé le 13/10/2026)*
- [X] **T3.1.4** : Retourner les résultats au format normalisé (statut/message/données). *(Terminé le 13/10/2026)*
- [X] **T1.1** : Créer la structure des dossiers (`src/`, `tests/`, `src/contracts/`, `src/core/`, `src/utils/`). *(Terminé le 10/10/2026)*
- [X] **T1.2** : Configurer le fichier `.env` avec les variables d'environnement (ex : `DATA_GOUV_API_URL`). *(Terminé le 10/10/2026)*
- [X] **T1.3** : Initialiser le logging avec `structlog` (`src/utils/logging.py`). *(Terminé le 10/10/2026)*
- [X] **T2.1** : Créer les schémas Pydantic pour les contrats (`src/contracts/`). *(Terminé le 12/10/2026)*
- [X] **T2.2** : Valider les schémas avec `jsonschema` pour les réponses de l'API data.gouv.fr. *(Terminé le 12/10/2026 — tests TB/TA non passés dans la sandbox, à exécuter en local)*