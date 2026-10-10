# Guide pour les Agents (AGENTS.md)

Ce fichier décrit la **méthode de travail** à suivre pour contribuer au projet **dataAgent**.
Il est automatiquement chargé à chaque séance, mais **aucune action structurante n'est déclenchée sans demande explicite** de l'utilisateur.

---

## **1. Reprise de contexte à chaque séance**
### **Étapes automatiques (sans demande utilisateur)**
À chaque début de séance, l'agent **recharge automatiquement** les fichiers clés suivants pour reprendre le contexte :
1. **`SESSIONS.md`** : Pour prendre connaissance des **actions, décisions et blocages** des séances précédentes.
2. **`dev/kanban.md`** : Pour prendre connaissance du tableau des tâches.
3. **`plan_tests.md`** : Pour prendre connaissance des tests associés aux tâches.
4. **`ARCHITECTURE.md` et `DECISIONS_CONCEPTION.md`** : Pour prendre connaissance du contexte technique du projet.
5. **`docs/architecture/*.md`** : Pour prendre connaissance des contrats et des invariants.

### **Étapes à suivre (sur demande uniquement)**
1. **Vérifier les derniers commits** (si modifications hors session).
   - Exemple de demande :
     ```markdown
     Peux-tu lister les 5 derniers commits pour voir les changements récents ?
     ```
2. **Demander un résumé du contexte** :
   - Exemple de demande :
     ```markdown
     Peux-tu me faire un résumé des tâches en cours et des décisions de conception clés ?
     ```

---

## **2. Workflow par tâche**
### **Étape 1 : Choix de la tâche (Kanban)**
- **Action** : Identifier **uniquement la tâche explicitement demandée par l'utilisateur** dans `kanban.md` et la déplacer dans le bon paragraphe ("À faire", "En cours", "Terminé").
  - *L'agent ne choisit **jamais** automatiquement une tâche prioritaire, mais peut proposer une évaluation des priorités si l'utilisateur le demande.*
- **Vérification** : S'assurer que ses dépendances sont terminées (ex : T1.3 avant T2.1) et vérifier s'il y a des dépendances éventuelles avec d'autres tâches.
- **Exemple de demande** :
  ```markdown
  Peux-tu préparer le travail sur la tâche T2.1 du kanban ?
  ```
- **Exemple de proposition de priorisation (sur demande)** :
  ```markdown
  Quelles tâches me recommandes-tu de prioriser dans le kanban ?
  ```

---

### **Étape 2 : Planification (sur demande)**
- **Actions** :
  1. Lire les spécifications associées à la tâche dans les sources suivantes :
     - `docs/architecture/<nom_contrat>.md` (ex : `rechercher_jeux.md`).
     - `DECISIONS_CONCEPTION.md` (pour les choix techniques).
     - `plan_tests.md` (pour les tests associés).
     - `SESSIONS.md` (pour les décisions passées).
  2. Établir un **plan détaillé** avec :
     - Sous-tâches (ex : "Créer le schéma Pydantic pour `mots_cles`").
     - Fichiers à modifier (ex : `src/contracts/rechercher_jeux.py`).
     - Tests associés (ex : TU-12 à TU-16 dans `plan_tests.md`).
- **Exemple de demande** :
  ```markdown
  Peux-tu établir un plan détaillé pour la tâche T2.1 ?
  ```

---

### **Étape 3 : Implémentation (sur demande)**
- **Actions** :
  1. Coder la fonctionnalité en respectant les **invariants** du projet.
  2. Coder les **tests associés** (unitaires et/ou d'intégration).
- **Exemple de demande** :
  ```markdown
  Peux-tu implémenter la tâche T2.1 en suivant le plan établi ?
  ```

---

### **Étape 4 : Tests et itérations (sur demande)**
- **Actions** :
  1. Lancer les tests avec `pytest`.
     - Exemple de commande :
       ```bash
       python -m pytest tests/unit/test_rechercher_jeux.py -v
       ```
  2. **Itérer en cas d’échec** :
     - **1ère tentative** : Corriger directement.
     - **2ème tentative** : Relire le fichier et vérifier les hypothèses.
     - **3ème tentative** : **Arrêter** et documenter le blocage.
- **Règle d'arrêt** : Si un test échoue **3 fois**, créer une entrée dans [`BLOCKERS.md`](BLOCKERS.md) et passer à une autre tâche.
- **Exemple de demande** :
  ```markdown
  Peux-tu lancer les tests pour la tâche T2.1 et corriger les erreurs si nécessaire ?
  ```

---

### **Étape 5 : Validation (sur demande)**
- **Actions** :
  1. Valider que tous les tests passent.
  2. Mettre à jour `kanban.md` (déplacer la tâche en **✅ Terminé**).
  3. Commiter les changements avec un message explicite.
- **Exemple de demande** :
  ```markdown
  Peux-tu valider la tâche T2.1 et la déplacer en ✅ Terminé dans le kanban ?
  ```

---

## **3. Règles supplémentaires**
### **A. Documentation systématique (sur demande)**
- Pour chaque tâche, créer un **fichier de suivi** dans `docs/tasks/` (ex : `T2.1_schémas_pydantic.md`).
  ```markdown
  # Tâche T2.1 : Schémas Pydantic

  ## Statut
  - [X] Implémentation
  - [ ] Tests unitaires
  - [ ] Tests d'intégration

  ## Fichiers modifiés
  - `src/contracts/rechercher_jeux.py`

  ## Blocages
  - Aucun.
  ```
- **Exemple de demande** :
  ```markdown
  Peux-tu créer un fichier de suivi pour la tâche T2.1 dans `docs/tasks/` ?
  ```

---

### **B. Gestion des blocages (sur demande)**
- Si une tâche est bloquée :
  1. Créer une entrée dans [`BLOCKERS.md`](BLOCKERS.md) :
     ```markdown
     # Blocages

     ## T2.1 : Schémas Pydantic
     - **Problème** : Le test TU-14 échoue car le champ `limite` n'est pas validé.
     - **Tentatives** : 3/3.
     - **Proposition** : Vérifier la documentation de Pydantic pour les `conint`.
     ```
  2. Passer à une autre tâche.
- **Exemple de demande** :
  ```markdown
  Peux-tu documenter ce blocage dans `BLOCKERS.md` et passer à une autre tâche ?
  ```

---

## **4. Actions ponctuelles (hors workflow)**
Les actions suivantes peuvent être demandées en séance **sans être référencées dans ce fichier** :
- **Analyse/Revue** :
  ```markdown
  Peux-tu analyser la cohérence entre `src/core/search.py` et `docs/architecture/rechercher_jeux.md` ?
  ```
- **Corrections ponctuelles** :
  ```markdown
  Peux-tu corriger cette erreur de typage dans `src/contracts/rechercher_jeux.py` ?
  ```
- **Génération de documentation** :
  ```markdown
  Peux-tu générer un exemple de payload pour l'API `rechercher_jeux` ?
  ```
- **Autres demandes** :
  ```markdown
  Peux-tu me proposer une évaluation des priorités dans le kanban ?
  ```

---

## **5. Résumé des fichiers clés**
| Fichier                  | Rôle                                                                                     |
|--------------------------|------------------------------------------------------------------------------------------|
| `SESSIONS.md`             | Journal des **actions, décisions et blocages** par séance. Utilisé pour la reprise de contexte. |
| `dev/kanban.md`          | Suivi des tâches (À faire → En cours → Terminé).                                         |
| `plan_tests.md`          | Plan de tests (TU, TI, TB) et couverture des critères d'acceptabilité.                   |
| `docs/tasks/`            | Suivi détaillé par tâche (optionnel).                                                    |
| `BLOCKERS.md`            | Liste des **blocages non résolus** (documentés après 3 échecs de test).                  |