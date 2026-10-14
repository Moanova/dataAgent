# Kanban du projet openDataAgent

Ce document suit l'avancement des tâches pour l'implémentation du projet **openDataAgent**. Il est organisé en **4 colonnes** :
- **📌 À faire** : Tâches non commencées.
- **🚧 En cours** : Tâches en cours d'implémentation.
- **🔍 En revue** : Tâches prêtes pour une revue ou des tests.
- **✅ Terminé** : Tâches validées.

---

## 📌 À faire

> Nota : la partie agentique Mistral est une section d'implémentation à part entière (section 5), pas une sous-section de tests ; les identifiants de tâches (T5.3.x, T5.1.x, T5.2.x) sont conservés inchangés pour la traçabilité avec `tests/plan_tests.md`, `docs/tasks/` et `SESSIONS.md`.

### 1. Initialisation du projet

---

### 2. Implémentation des contrats

---

### 3. Implémentation des fonctions de base

#### 3.1. Recherche de jeux (`rechercher_jeux`)


#### 3.2. Inventaire des ressources (`lister_ressources`)

#### 3.3. Interrogation des ressources (`interroger_ressource`)

#### 3.4. Téléchargement brut (`telecharger_brut`)

---

### 4. Intégration et CLI
  - [X] Commande `search` : Appelle `rechercher_jeux`. *(Livrée le 13/10/2026 — T4.1/T4.2)*
  - [X] Commande `list` : Appelle `lister_ressources`. *(Livrée le 13/10/2026 — avec T3.2.1)*
  - [X] Commande `query` : Appelle `interroger_ressource`. *(Livrée le 14/10/2026 — avec T4.1/T4.2, gardes CLI filtre/tri)*
  - [X] Commande `download` : Appelle `telecharger_brut`. *(Livrée le 14/10/2026 — avec T4.1/T4.2)*
  - [ ] **T4.3** : Commande `chat` : point d'entrée agentique grand public — un prompt libre en argument ; crée l'agent (T5.3.1), conduit la conversation (T5.3.2), journalise (T5.3.3), détruit l'agent, affiche la synthèse finale et le chemin du journal. Options : `--plafond`, `--id-execution`, `--json`. Remplace le lanceur de test jetable.

---

### 5. Intégration agentique Mistral

C'est la raison d'être du projet : l'agent Mistral porte les étapes A1 à A4 du flux (reformulation, sélection, tranchage des indéterminations, synthèse du registre) en s'appuyant sur les fonctions du cœur. Les identifiants T5.3.x sont conservés pour la traçabilité avec le plan de tests et les fichiers de suivi.

- [X] **T5.3.1** : Créer (et détruire) l'agent Mistral : prompt système (minimal, enrichi en T5.3.4), choix du modèle, définition des outils (`src/agent/agent.py`). *(Terminé le 14/10/2026 — agent éphémère via client.beta.agents, garde-fou MISTRAL_AGENT_ID, 18 TU ; test réel validé en local par le concepteur)*
- [X] **T5.3.2** : Implémenter la boucle de conversation : envoi du message utilisateur, réception et exécution des `tool_calls` vers les fonctions du cœur, renvoi des résultats normalisés (`src/agent/boucle.py`). *(Terminé le 14/10/2026 — dispatch src/agent/outils.py, plafond 10 configurable, journalisation sans blocage TA-02, 12 TU ; test réel validé en local par le concepteur)*
- [X] **T5.3.3** : Journaliser les conversations (arguments, résultats, raisonnements) pour les tests TA et l'audit. *(Terminé le 14/10/2026 — src/agent/journal.py, JSONL journaux/<id>/conversation.jsonl, rejeu extraire_invocations, 8 TU)*
- [X] **T5.3.4** : Rédiger le prompt système : consignes de reformulation (A1), sélection (A2), tranchage des indéterminations (A3), synthèse du registre (A4), pagination et plafond d'invocations. *(Terminé le 14/10/2026 — prompt structuré s1–s8 (~750 mots) dans src/agent/agent.py, 4 tests de contenu TU-D1..D4 ; évaluation des propriétés TA sur journaux réels à venir en local)*

---

### 6. Tests

#### 6.1. Tests unitaires
- [X] **T5.1.3** : Écrire les tests pour `interroger_ressource` (`tests/unit/test_query.py`). *(Terminé le 13/10/2026 — livrés avec T3.3.x, kanban non tenu à jour)*
- [X] **T5.1.4** : Écrire les tests pour `telecharger_brut` (`tests/unit/test_download.py`). *(Terminé le 13/10/2026 — livrés avec T3.4.x, kanban non tenu à jour)*
- [ ] **T5.1.5** : Tester les formats non tabulaires (ZIP, GeoJSON, etc.).

#### 6.2. Tests d'intégration
- [ ] **T5.2.1** : Tester le flux complet (recherche → inventaire → téléchargement).
- [ ] **T5.2.2** : Valider la persistance du registre des sources inaccessibles.

---

### 7. Logging et journalisation
- [X] **T6.2** : Ajouter des logs pour chaque étape du flux. *(Terminé le 14/10/2026 — recherche, inventaire, interroger, télécharger, HTTP, registre couverts (src/core/*.py, src/utils/*.py), plus les événements agentiques de src/agent/ ; kanban non tenu à jour lors de T3.3/T3.4)*

---

### 8. Améliorations futures (optionnel)
- [ ] **T7.1** : Ajouter un mécanisme de réessai intelligent pour les échecs techniques.
- [ ] **T7.2** : Implémenter un nettoyage automatique des anciennes exécutions.
- [ ] **T7.3** : Automatiser les tests agentiques.
- [ ] **T7.4** : Supporter d'autres sources de données (ex : Eurostat, INSEE).

---

## 🚧 En cours

- [X] **T4.1** : Créer la CLI avec Typer (`src/main.py`). *(Terminé le 14/10/2026 — commandes search, list, query, download livrées et testées)*
- [X] **T4.2** : Configurer les arguments et options pour chaque commande. *(Terminé le 14/10/2026 — gardes CLI filtre/tri ajoutées sur query, codes de sortie 0/1/2)*



---

## ✅ Terminé

- [X] **T3.3.2** : Gérer la pagination, le filtrage et le tri. *(Termine le 13/10/2026 - traductions livrees avec T3.3.1 ; consolide : page_suivante (contrat v1.1.0), erreur actionnable colonne inexistante)*
- [X] **T3.3.3** : Retourner une recommandation pour les volumes élevés. *(Termine le 13/10/2026 - livree avec T3.3.1, revue formelle conclurante : seuil 5000 configurable, TI-09 en trois volets)*

- [X] **T3.3.1** : Implémenter l'appel à l'API tabulaire (`src/core/query.py`). *(Termine le 13/10/2026 - API sondée en réel au préalable, détection api_tabulaire incluse, max taille_page 50, validé en réel : films CNC avec filtre et tri)*

- [X] **T3.4.3** : Gérer les échecs techniques et consigner dans le registre. *(Termine le 13/10/2026 - TI-08 passe, motif serveur_origine_bloque statu quo, organisation reportee)*

- [X] **T3.4.2** : Stocker les fichiers dans `data/raw/<id_execution>/` (`src/utils/storage.py`). *(Termine le 13/10/2026 - nommage et arborescence livres avec T3.4.1, collisions par suffixe numerique ajoutees)*

- [X] **T3.4.1** : Implémenter le téléchargement des fichiers (`src/core/download.py`). *(Termine le 13/10/2026 - TI-05..07 passes, ecriture atomique, valide en reel depuis la sandbox : CSV 4,3 Mo via API Insee)*

- [X] **T6.1** : Configurer `structlog` pour tracer les appels et les erreurs. *(Terminé le 13/10/2026 — configure_logging/log_to_file/bind_context, TU-29 à TU-32, utilisé par tous les modules)*
- [X] **T5.1.1** : Écrire les tests pour `rechercher_jeux` (`tests/unit/test_search.py`). *(Terminé le 13/10/2026 — TU-12, TU-14, TU-17, invariants licence/registre, pagination)*
- [X] **T5.1.2** : Écrire les tests pour `lister_ressources` (`tests/unit/test_resources.py`). *(Terminé le 13/10/2026 — TI-01, TI-02, TU-37, cohérence indétermination)*

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