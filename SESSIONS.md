# Journal des Séances (SESSIONS.md)

Ce fichier documente les **actions clés** et **décisions** prises lors des séances de travail sur le projet **openDataAgent**.
Il est mis à jour automatiquement à la fin de chaque session et relu au début de la suivante pour reprendre le contexte.

---

## **Séance du 14/10/2026 (soir) — appropriation du code par le concepteur (séance de questions/réponses)**

### **Contexte**
- **Objectif** : séance d'appropriation du code généré lors des séances précédentes, par séries de questions/réponses couvrant Python en général (imports absolus, `__init__.py`, callbacks), la bibliothèque Typer, les contrats, l'agent et la logique applicative. Aucune modification de code — les écarts détectés sont formalisés au kanban (nouvelle section 10).

### **Actions réalisées**
1. **Kanban** : création de la section 10 « Séance d'appropriation du 14/10/2026 (soir) » avec six chantiers (T10.1 à T10.6, voir ci-dessous). Aucune autre modification.

### **Décisions**
- **T10.2 (inventaire persistant)** : le concepteur conteste le choix du 14/10 (inventaire scopé au processus en mode manuel) — `--id-execution` n'y a qu'un rôle de trace, aucun chaînage manuel n'est possible. Design acté en séance : persistance côté CLI uniquement (`data/executions/<id>/inventaire.json`, sérialisation additive sur l'inventaire, chargement/sauvegarde dans le callback Typer, enrichissement cumulatif), cœur et mode agentique inchangés.
- **T10.1 (écart au schéma de conception)** : acté comme l'écart le plus structurel — la mise à disposition vers la partie 2 (B7 → P) n'est réalisée que par la voie 2 (téléchargement brut) ; la voie 1 (extraction tabulaire) ne persiste rien ; la normalisation B7 n'existe pas dans le code.

### **Écarts et chantiers identifiés (résumé de la séance)**
- **T10.1** — Maillon B7 → P du schéma de conception non réalisé (voie 1 sans persistance, pas de normalisation commune).
- **T10.2** — Inventaire persistant par `id_execution` : design complet acté (voir Décisions).
- **T10.3** — Bug `id_execution` dans `executer_outil` (`src/agent/outils.py`) : id de la boucle non injecté si l'agent ne le fournit pas ; conflit TypeError s'il le fournit. Correctif : `options.setdefault("id_execution", id_execution)` + retrait des `FILTRES_OPTIONS`.
- **T10.4** — Validation Pydantic des `tool_calls` déclarée (docstring de `validation_api.py`) mais non branchée au runtime : les modèles ne servent qu'aux tests de cohérence ; validation runtime = lambdas superficielles.
- **T10.5** — Vocabulaires fermés de `main.py` (`TRIS`, `OPERATEURS_FILTRE`, `ORDRES_TRI`, `FENETRES_MAJ`) à déplacer vers le cœur ; plafond d'aperçu (5 lignes) de `query` à constanter/optionner ; `help` de `--id-execution` dupliqué.
- **T10.6** — (optionnel) Points packaging/portage : paquet générique `src`, `pyproject.toml` manquant, chemins relatifs au CWD (`data/`, `conversations/`, registre), `libmagic` Windows, `.env` explicite.

### **Enseignements Python/typer consignés à l'oral** (pour mémoire)
- `python -m src.main` vs `py src\main.py` : mode module (racine dans sys.path) vs mode script (répertoire du script) — d'où le `ModuleNotFoundError` en mode script.
- Les imports « absolus » (`from src.core...`) sont des noms de modules, pas des chemins : compatibles avec pip/PyInstaller (analyse statique) ; le risque réel est le nom de paquet générique `src`.
- Typer : dérivation de l'interface depuis les annotations ; `@app.callback()` exécuté avant chaque commande (et requis pour forcer le mode multi-commandes) ; portage Streamlit ne coûterait que la couche présentation (`main.py`), le cœur étant agnostique.

### **Tests**
- Non concerné (aucune modification de code).

### **Blocages**
- Aucun.

---

## **Séance du 14/10/2026 — clôture des sections 1 à 7 + réorganisation**

### **Contexte**
- **Objectif** : clôturer T4.1/T4.2 (CLI query/download), livrer toute la partie agentique (T5.3.1..T5.3.4), la commande `chat` (T4.3), les tests d'intégration restants (T5.1.5, T5.2.1, T5.2.2), corriger le logging, documenter la politique de licence et réorganiser l'arborescence.
- **Validations réelles du concepteur en local** : création/destruction d'agent (T5.3.1), boucle de conversation (T5.3.2), téléchargement ZIP réel (TI-11 partiel : GeoJSON TI-12 restant).

### **Actions réalisées**
1. **T4.1/T4.2 clôturés** (commits 70bb045) : commandes query/download déjà implémentées, gardes CLI filtre/tri ajoutées, 11 tests CLI, kanban synchronisé.
2. **T5.3.1 agent éphémère** (f5ee456, refactor ef7b4a2) : `client.beta.agents` (mistralai>=3.2.0), choix concepteur après comparatif éphémère/persistant + garde-fou MISTRAL_AGENT_ID (vérification stricte modèle/prompt/outils, sinon recréation), `nettoyer_agents_orphelins`. Refactor `scripts/agent.py` → `src/agent/agent.py` (décision concepteur : toute la logique agentique dans src/agent/).
3. **T5.3.2 boucle** (ef7b4a2) : `src/agent/outils.py` (dispatch tool_calls vers le cœur, validation arguments), `src/agent/boucle.py` (itération tool_calls → exécution → renvoi normalisé, plafond 10 configurable, journalisation **sans blocage** TA-02 — décision concepteur : tracer, le cœur refusant déjà les ids hors chaîne).
4. **T5.3.3 journal** (3d1d090, b3642b5) : `src/agent/journal.py`, JSONL `conversations/<id>/conversation.jsonl` (initialement journaux/, renommé en fin de séance), rejeu `extraire_invocations` (base TA-01/TA-02), raisonnements capturés.
5. **T5.3.4 prompt système** (ef45a3f) : ~750 mots, sections A1-A4 + règles générales (7 statuts, identifiants, ordre, plafond, licence), pagination/volumes. Distinction clarifiée avec le concepteur : T5.3.1 = prompt minimal (mécanisme), T5.3.4 = prompt final (expertise).
6. **T4.3 commande chat** (688aea2) : point d'entrée agentique (prompt libre, try/finally destruction garantie, --plafond/--id-execution/--json), 7 tests, documentation d'utilisation complète dans docs/README.md.
7. **T5.1.5** (3525583) : formats non tabulaires ZIP/GeoJSON/JSON/SHP/PDF (TU-40..46, renumérotation section 3.9 du plan — doublons TU-30..33 corrigés), 9 tests.
8. **Logging corrigé** (9fee7f8) : bug réel découvert via le test du concepteur (id_execution=None) — get_logger capturait le contexte en snapshot à l'import ; correction par processor structlog injectant le contexte à chaque événement.
9. **T5.2.1/T5.2.2** (019abb7, 346c129) : flux complet avec exclusion licence (TI-14) + ressource hors chaîne refusée (TI-14b, illustration du piège list→download identifié par le concepteur) ; persistance du registre validée (TI-15/15b/15c) : rechargement entre instances, enrichissement cumulatif, re-test non bloquant.
10. **Politique de licence documentée** : section README (7 licences + obligations + implications partie 2) ; tâche T7.5 créée puis section 9 dédiée (30a30e1) : registre descriptif + mention d'attribution.
11. **Réorganisation arborescence** (f6eb48a, 0563c44) : kanban → docs/projet/kanban.md (redirection conservée en dev/), journaux/ → conversations/ (distinction logs techniques vs dialogues agentiques), .gitignore dédoublonné, AGENTS.md et références mis à jour. Skills mis à jour par le concepteur.

### **Décisions**
- **Agent éphémère** plutôt que persistant : la configuration vit dans le dépôt (invariant contrat_global) ; garde-fou pour réutiliser un agent console strictement conforme.
- **Journalisation TA-02 sans blocage** : le cœur refuse déjà les identifiants hors chaîne ; la boucle observe pour le rejeu.
- **Mode manuel multi-commandes** : chaque commande = un processus = un flux isolé (inventaire en mémoire) — documenté comme limite connue dans le README ; évolution « inventaire persistant par id d'exécution » évoquée, non créée.
- **T7.5 en section 9** : préparation de la partie 2 (registre descriptif licences + attribution), distinct des améliorations optionnelles.
- **Kanban restructuré** : la partie agentique est une section d'implémentation à part entière (section 5), pas une sous-section de tests ; identifiants de tâches inchangés pour la traçabilité.

### **Tests**
- **Résultat final : 253/253 PASSED** en ~23 s (208 en début de séance → 253).
- Validations réelles du concepteur : agent (création/conversation/destruction), téléchargement ZIP.
- Restants en local : TI-12 (GeoJSON réel), validation chat de T5.2.1 (recoupe TB-04), campagne TA sur journaux réels.

### **Blocages**
- Aucun. Nota : piège list→download en mode manuel identifié et documenté (pas un bug : l'inventaire est scopé au processus, conforme au contrat).

### **État en fin de séance**
- **Kanban : sections 1 à 7 entièrement terminées** (39 tâches ✅). Restent : T7.1..T7.4 (optionnelles) et T7.5 (section 9, partie 2).
- Sandbox : environnement fonctionnel (mistralai 3.2.0 installable, pytest/responses/typer).

---

## **Séance du 13/10/2026 — parties 1 à 4 (T3.1.x à T3.3.x, T4.1/T4.2, T6.1)**

### **Contexte**
- **Objectif initial** : référencer les tests du plan dans `tests/unit/`, puis implémenter les fonctions de base (sections 3.1 à 3.4), la CLI (T4.1/T4.2 périmètre search) et clore la section 3.3 (objectif de fin de séance : atteint).
- **Contrainte levée** : contrairement aux séances précédentes, la sandbox a pu joindre data.gouv.fr en réel — TB-01 validé depuis la sandbox, fixtures réelles capturées, API tabulaire sondée avant implémentation.

### **Actions réalisées**
1. **Référencement des tests** (68 → commit `00cc036`) : chaque test de `tests/unit/` porte en commentaire sa référence `tests/plan_tests.md` (TU-xx/TC-xx) ou la mention « Test annexe ».
2. **T3.1.1 à T3.1.4** (commit `e4f1227`) : client HTTP (`src/utils/http.py`, reprises 429/502/503, 404→`jeu_introuvable`, zéro exception), filtre de licence (`src/core/licence.py`), registre persistant (`src/utils/registry.py`), flux complet `rechercher_jeux`.
3. **Réalignement API v1** (même commit) : le projet était incohérent (docs v1, code v2). Choix du concepteur : rester en v1. Vérifié en réel (`license` chaîne, `lov2`, `sort=-views`, `page`) ; schémas jsonschema, fixtures, docs et politique de licence alignés (acceptées : lov2, fr-lo, odc-odbl, cc-by, cc-by-sa, cc-zero, other-open).
4. **T4.1/T4.2 périmètre search** (commit `5e05d31`) : CLI Typer (`src/main.py`), commande `search` ; bug Typer mode commande unique corrigé par `@app.callback()`. TB-01 validé en réel.
5. **T3.1.5 pagination** (commit `512b893`) : écart de conception détecté (l'agent ne pouvait pas paginer) — contrat v1.1.0 (`page`, `page_courante`, `page_suivante`).
6. **T3.2.1 à T3.2.3** (commit `2eb2811`) : inventaire (`src/core/resources.py`, inventaire en mémoire = invariant « métadonnées enregistrées »), classificateur (`src/core/classification.py`, listes fermées, ordre HTML > api_distante > tabulaire > autre > indetermine), indéterminations (sémantique actée : contradictoire tranché par priorité, inconnu seul → indetermine ; autoportance A3). Ajout section 5.3 (T5.3.1..4 intégration agentique) au kanban.
7. **T3.4.1 à T3.4.3** (commit `0cfa8d6`) : téléchargement en flux avec écriture atomique (TI-07), stockage conforme `stockage.md` (collisions par suffixe numérique), échecs→registre (`serveur_origine_bloque`), inventaire enrichi (id_jeu, organisation, licence). TI-08 : premier test de chaîne complète. Validé en réel : CSV 4,3 Mo via API Insee.
8. **T3.3.1 à T3.3.3** (commit de fin de séance) : API tabulaire **sondée en réel avant implémentation** (tabular-api.data.gouv.fr, opérateurs, tri, pagination max 50 — le contrat disait 100, corrigé). Deux URLs de base (catalogue + tabulaire). Détection `api_tabulaire` par ping (fin de l'état transitoire). Colonnes par première ligne, repli `profile/`. Recommandation volume (T3.3.3, seuil 5000 configurable). T3.3.2 : `page_suivante` (contrat v1.1.0), erreur actionnable colonne inexistante (l'API répond 500 « Database error », message propagé). Validé en réel : films CNC avec filtre + tri.
9. **Kanban fiabilisé** : correctifs sections 4 (commandes search/list cochées), 5.1 (T5.1.1/T5.1.2 terminées avec les T3.x, chemins unit/), 6 (T6.1 terminée, T6.2 partielle).

### **Décisions**
- **API v1** retenue ; le coût observé était celui de réparer la divergence docs/code, pas celui de la v1. Préparation d'une éventuelle bascule v2 : extraire un adaptateur (plan esquissé, non retenu pour l'instant — le projet pourrait prendre d'autres directions, ex. nouvelles sources).
- **Ordre de priorité du classificateur** (validé avec le concepteur) : HTML > api_distante > fichier_tabulaire > fichier_autre_format > indetermine ; liste fermée des formats ; licence absente/inconnue → refusée.
- **Recherche par format** : l'API v1 le permet (vérifié : q=test 134, format=csv 30, format=geojson 1) — piste d'évolution annotée pour A1, ne remplace pas la classification (format déclaré non fiable).
- **Architecture agentique clarifiée** : les étapes A1-A4 ne sont pas du code appelé depuis `main` ; l'humain via CLI joue A1/A2 en mode manuel, l'agent Mistral (créé par code : prompt système, modèle, destruction — T5.3.1..4) les tiendra dans la boucle de conversation ; l'exécution des `tool_calls` reste dans le code Python (l'API Mistral n'exécute jamais les fonctions).
- **`api_tabulaire`** : fait vérifiable par HTTP (ping 200/404) → responsabilité du code ; l'agent lit le champ (confirmé par `contrat_global` : « le code exécute : tous les appels HTTP »).
- **Motif registre pour échec technique** : `serveur_origine_bloque` statu quo, statut HTTP dans `detail`.

### **Tests**
- **Résultat final : 179/179 PASSED** en 22 s (`tests/unit/`).
- **Validés en réel depuis la sandbox** : TB-01 (recherche « dette publique », tri vues, jeu Insee présent, licence lov2, exclusion consignée) ; inventaire réel jeu Insee ; téléchargement réel CSV 4,3 Mo API Insee ; interrogation réelle API tabulaire (films CNC, filtre + tri).
- **TB-05 partiellement contourné** : l'API Insee a répondu 200 (pas de refus) — le cas refus reste couvert par TI-07 en simulation ; à re-tester en local.

### **Blocages**
- Aucun. Nota : la détection `api_tabulaire` a initialement ralenti la suite de tests (pings réseau réels non mockés, 64 s) — corrigé par mocks systématiques (22 s).

### **Environnement sandbox**
- Accès réseau sortant **fonctionnel** vers data.gouv.fr et tabular-api.data.gouv.fr (lever du blocage des séances précédentes) ; `responses`, `typer` installés.

---

## **Séance du 12/10/2026 — partie 2 (T2.2)**

### **Contexte**
- **Objectif** : Implémentation de la tâche T2.2 (validation des réponses de l'API data.gouv.fr avec `jsonschema`).
- **Contrainte** : pas de commit ni push à la demande du concepteur ; tests réseau (TB) et agentiques (TA) non exécutables dans la sandbox (réseau sortant bloqué) — non passés et documentés comme tels.

### **Actions réalisées**
1. **Plan T2.2** validé par le concepteur (schémas de réponses API + module de validation + tests TU-34..38 + documentation).
2. **Schémas de réponses API** (`contrats/schemas_api/`) :
   - `rechercher_jeux.reponse.json` (recherche `/api/2/datasets/search/`), `lister_ressources.reponse.json` (détail `/api/2/datasets/{id}/`).
   - Draft 2020-12, `additionalProperties: true`, champs optionnels typés null.
3. **Module de validation** (`src/contracts/validation_api.py`) :
   - `valider_reponse_api()`, `valider_json_brut()`, `charger_schema()`, `ResultatValidation` (valide/erreurs/statut) ; échec propre systématique (jamais d'exception), erreurs avec chemin JSON pointer.
   - Exports ajoutés à `src/contracts/__init__.py`.
4. **Fixtures et tests** :
   - Fixtures dans `tests/fixtures/api/` (réponses simulées conformes à l'API v2).
   - `tests/unit/test_validation_api.py` : TU-34..TU-38 + 2 tests annexes = 10 tests.
   - Section 3.8 ajoutée à `tests/plan_tests.md`.
5. **Documentation** : `docs/tasks/T2.2_validation_jsonschema.md` (statut des tests TB/TA explicitement non passés), kanban T2.2 → Terminé.

### **Décisions**
- Séparation stricte des schémas de réponses API (`contrats/schemas_api/`) et des contrats d'outils (source de vérité Mistral).
- Échec propre systématique : tout écart (données non conformes, outil inconnu, schéma illisible) → `echec_technique` sans exception.
- `mistralai` 3.1.0 est disponible dans la sandbox mais les appels réels à l'API restent bloqués (réseau) — TB-04 et TA restent à passer en local.

### **Tests**
- **Résultat : 68/68 PASSED** (`tests/unit/` = 58 existants + 10 nouveaux T2.2).
- **Non passés (documentés)** : TB-01..05 (marqueur réseau) et TA-01..05 (agentiques) — non exécutables dans la sandbox, à passer côté poste local lors de la validation d'itération.

### **Blocages**
- Aucun. Nota : 1 itération de test nécessaire (assertion TU-35 corrigée : chemin JSON de la racine = `/` et non `/total`).

### **Environnement sandbox**
- `jsonschema` 4.26.0, `pydantic` 2.13.5, `pytest` 9.1.1, `mistralai` 3.1.0 installés ; réseau sortant bloqué.

---

## **Séance du 12/10/2026**

### **Contexte**
- **Objectif** : Renommage du projet (dataAgent → openDataAgent), ajout des en-têtes standard, puis implémentation de la tâche T2.1 (schémas Pydantic pour les contrats).
- **Tâches réalisées** : T2.1 (schémas Pydantic).

### **Actions réalisées**

1. **Renommage et en-têtes** :
   - Vérification qu'aucune référence à `dataAgent` ne persiste dans le code.
   - Ajout de l'en-tête standard (Application / Script / Version / Date / Design / Build) à `src/core/search.py` et `src/utils/logging.py`.

2. **Implémentation de T2.1 — Schémas Pydantic** :
   - Création de `src/contracts/base.py` : `StatutEnum` (7 codes), `ClasseRessource` (5 valeurs), `ReponseBase`, `JeuResume`, `RessourceResume`, et `valider_coherence_contrat()`.
   - Création de `src/contracts/rechercher_jeux.py` : `TriRecherche`, `FenetreMaj`, `RechercherJeuxInput` (mots_cles, tri, fenetre_maj, limite 1-20), `RechercherJeuxOutput`.
   - Création de `src/contracts/lister_ressources.py` : `ListerRessourcesInput` (id_jeu), `ListerRessourcesOutput` (ressources, indetermination).
   - Création de `src/contracts/interroger_ressource.py` : `OperateurFiltre`, `OrdreTri`, `FiltreColonne`, `TriColonne`, `InterrogerRessourceInput` (pagination 1-100, filtre, tri), `InterrogerRessourceOutput`.
   - Création de `src/contracts/telecharger_brut.py` : `TelechargerBrutInput` (id_ressource), `TelechargerBrutOutput` (chemin_local, format, licence, suggestion).
   - Création de `src/contracts/__init__.py` : exports publics de tous les modèles.

3. **Tests** :
   - Création de `tests/unit/test_contracts.py` avec 53 tests couvrant TU-25 à TU-28, TC-01 à TC-05, et la validation des modèles Pydantic (bornes, défauts, champs obligatoires).
   - **Résultat : 53/53 tests PASSED** + 5 tests existants toujours PASSED = **58/58 au total**.

4. **Corrections des contrats JSON** (détectées par TC-04) :
   - Ajout des descriptions manquantes dans `contrats/lister_ressources.json` (`id_jeu`, `donnees.ressources`).
   - Ajout des descriptions manquantes dans `contrats/interroger_ressource.json` (`id_ressource`, `filtre` + sous-propriétés, `tri` + sous-propriétés).
   - Ajout des descriptions manquantes dans `contrats/telecharger_brut.json` (`id_ressource`).
   - Ajout des descriptions manquantes dans `contrats/rechercher_jeux.json` (`donnees.jeux`).

5. **Documentation** :
   - Création de `docs/tasks/T2.1_schemas_pydantic.md` (suivi de tâche, nom sans caractères spéciaux).
   - Mise à jour de `dev/kanban.md` : T2.1 déplacée en **✅ Terminé**.

### **Décisions**
- **Pydantic v2** : Utilisation de l'API Pydantic 2.14.1 (`model_fields`, `Field`, `BaseModel`).
- **Enums `str, Enum`** : Héritage mixte pour compatibilité JSON (sérialisation en string).
- **Miroir fidèle JSON ↔ Pydantic** : Les modèles Pydantic reflètent exactement les contrats JSON (champs, types, enums, bornes, obligatoires).
- **Validation de cohérence** : Fonction `valider_coherence_contrat()` dans `base.py` pour détecter toute divergence JSON ↔ Pydantic.
- **Nommage sans caractères spéciaux** : Fichier de suivi `T2.1_schemas_pydantic.md` (sans accent) pour éviter les problèmes de versionnement/récupération.

### **Blocages**
- Aucun.

---

## **Séance du 10/10/2026**
### **Contexte**
- **Objectif** : Finaliser la tâche T1.3 (logging avec `structlog`) et préparer l'intégration du logging dans les autres modules.
- **Tâches en cours** : T6.1 (intégration du logging).

### **Actions réalisées**
1. **Implémentation de T1.3** :
   - Création de `src/utils/logging.py` avec :
     - Configuration de `structlog` pour produire des logs **au format JSON**.
     - Ajout des champs obligatoires : `timestamp`, `event`, `id_execution`, `logger`.
     - Gestion des métadonnées dynamiques via `bind_context()`.
     - Écriture des logs dans `logs/openDataAgent_<id_execution>.log`.
   - Intégration dans `src/core/search.py` pour logger les appels, succès et erreurs.

2. **Tests unitaires** :
   - Création de `tests/unit/test_logging.py` avec les tests suivants :
     - TU-29 : Format JSON des logs.
     - TU-30 : Métadonnées dynamiques (`bind_context`).
     - TU-31 : Écriture dans le fichier de logs.
     - TU-32 : Niveaux de log (simulés).
     - Bonus : Gestion des erreurs d'écriture.
   - Correction des erreurs (gestion des fichiers ouverts, mocks).

3. **Mise à jour des fichiers** :
   - `dev/kanban.md` :
     - T1.3 déplacée en **✅ Terminé**.
     - T6.1 déplacée en **🚧 En cours**.
   - `plan_tests.md` : Ajout des tests TU-29 à TU-32 (journalisation) et TI-13 à TI-15 (intégration).

4. **Création de `AGENTS.md`** :
   - Définition du **workflow standard** pour les agents (reprise de contexte, planification, implémentation, tests).
   - Automatisation du rechargement des fichiers clés (`kanban.md`, `plan_tests.md`, etc.).

### **Décisions**
- **Format des logs** : JSON pour les fichiers (`logs/openDataAgent_<id_execution>.log`), clé-valeur pour la console.
- **Champs obligatoires** : `timestamp`, `event`, `id_execution`, `logger`.
- **Métadonnées dynamiques** : Utilisation de `bind_context()` pour ajouter des champs comme `id_jeu` ou `id_ressource`.
- **Gestion des erreurs** : Les erreurs d'écriture dans les fichiers de logs sont gérées silencieusement.

### **Blocages**
- Aucun blocage majeur.
  - Problème mineur : Fichiers de logs verrouillés sous Windows (résolu en fermant explicitement les fichiers après écriture).

---

## **Séance du 09/10/2026** *(exemple rétroactif)*
### **Contexte**
- **Objectif** : Initialisation du projet, création de la structure de base et traitement des tâches T1.1. et T1.2.

### **Actions réalisées**
1. **Création de la structure des dossiers** :
   - `src/`, `tests/`, `src/contracts/`, `src/core/`, `src/utils/`.
   - `dev/kanban.md` pour le suivi des tâches.

2. **Configuration du fichier `.env`** :
   - Ajout de `DATA_GOUV_API_URL` et autres variables d'environnement.

3. **Initialisation du repository Git** :
   - Création des branches `main` et `dev`.
   - Association avec le repository distant sur GitHub.

### **Décisions**
- **Arborescence** : Inspirée des bonnes pratiques Python (src/, tests/).
- **Gestion des tâches** : Utilisation de `kanban.md` pour suivre l'avancement.
- **Variables d'environnement** : Centralisées dans `.env` (ignoré par Git).

### **Blocages**
- Problème d'environnement non identifié (résolu hors séance).