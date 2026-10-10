# Plan de tests — Partie 1 du flux : acquisition data.gouv.fr

## 1. Objet et périmètre

Ce plan décrit la stratégie de vérification de la partie 1 du flux (recherche, sélection, acquisition, registre), couvrant les composants algorithmiques, les contrats de function calling et les étapes agentiques. Il s'appuie sur la pyramide de tests : base large de tests unitaires sans réseau, couche d'intégration entre composants internes, sommet restreint de tests de bout en bout, plus une couche transversale de tests de contrat.

Chaque test est identifié (TU, TI, TB, TC, TA), rattaché au critère d'acceptabilité qu'il vérifie (CA-x, voir le document Critères d'acceptabilité), et associé à un niveau de blocage : bloquant ou avertissement.

## 2. Outillage et conventions

- Cadriciel : pytest, avec fixtures pour les composants partagés (client simulé, registre temporaire).
- Simulation HTTP : responses ou requests-mock pour les tests sans réseau ; enregistrements de réponses réelles comme fixtures (cassette).
- Marqueur réseau : `@pytest.mark.reseau` pour tous les tests nécessitant un accès extérieur ; ces tests sont exclus de l'exécution par défaut et exécutés lors des validations complètes.
- Journaux : toute conversation agentique est journalisée (arguments, résultats) dans un répertoire de traces ; ces journaux servent aux tests de propriétés (TA).
- Exigences : chaque invariant déclaré dans la documentation des contrats (`docs/*.md`) doit être couvert par au moins un test de ce plan.

## 3. Niveau 1 — Tests unitaires (TU)

Tests isolés, sans réseau. La couche HTTP est simulée.

### 3.1 Filtre de licence

| Id | Cas de test | Résultat attendu | Blocage |
|---|---|---|---|
| TU-01 | licence_est_acceptable pour chaque licence acceptée (etalab-2.0, odc-odbl, cc-by, cc-by-sa, other-open) | Vrai pour chacune | Bloquant (CA-1) |
| TU-02 | licences exclues : notspecified, other-closed, valeur commerciale | Faux pour chacune | Bloquant (CA-1) |
| TU-03 | licence absente, nulle, chaîne vide | Faux (comportement sûr par défaut) | Bloquant (CA-1) |
| TU-04 | casse et espaces parasites dans le code de licence | Évaluation insensible à la casse | Bloquant (CA-1) |

### 3.2 Classificateur de ressources

| Id | Cas de test | Résultat attendu | Blocage |
|---|---|---|---|
| TU-05 | CSV (format csv, mime text/csv) | fichier_tabulaire, non indéterminé | Bloquant (CA-6) |
| TU-06 | XLSX, XLS, TSV | fichier_tabulaire | Bloquant (CA-6) |
| TU-07 | ZIP, GeoJSON, JSON, SHP, PDF, Parquet | fichier_autre_format | Bloquant (CA-6) |
| TU-08 | HTML (format ou mime text/html) | page_web | Bloquant (CA-6) |
| TU-09 | URL contenant /api, format api | api_distante | Bloquant (CA-6) |
| TU-10 | Format inconnu, mime absent, URL neutre | indetermine, indéterminé vrai | Bloquant (CA-6) |
| TU-11 | Absence totale de métadonnées | indetermine, jamais une classification erronée silencieuse | Bloquant (CA-6) |

### 3.3 Normalisation des arguments

| Id | Cas de test | Résultat attendu | Blocage |
|---|---|---|---|
| TU-12 | rechercher_jeux avec mots_cles vide | erreur_parametres, jamais d'appel HTTP | Bloquant (CA-5) |
| TU-13 | limite omise | valeur par défaut 10 appliquée | Bloquant |
| TU-14 | limite au-delà du maximum | corrigée au maximum, pas d'exception | Bloquant (CA-5) |
| TU-15 | tri et fenetre_maj valides | traduction correcte vers les paramètres API (sort, last_update_range) | Bloquant |
| TU-16 | tri invalide | repli sur pertinence ou erreur_parametres, selon spécification | Avertissement |

### 3.4 Réponses normalisées

| Id | Cas de test | Résultat attendu | Blocage |
|---|---|---|---|
| TU-17 | Simuler une erreur HTTP 500 sur la recherche | statut echec_technique, pas d'exception | Bloquant (CA-2, CA-5) |
| TU-18 | Simuler un jeu inexistant (404) | statut jeu_introuvable | Bloquant (CA-5) |
| TU-19 | Simuler l'expiration du délai | statut echec_technique après les tentatives configurées | Bloquant (CA-7) |
| TU-20 | Simuler les statuts 429, 502, 503 | nouvelle tentative puis succès si récupération | Bloquant (CA-7) |

### 3.5 Registre des sources inaccessibles

| Id | Cas de test | Résultat attendu | Blocage |
|---|---|---|---|
| TU-21 | Consignation d'une exclusion juridique | entrée complète : horodatage, motif, id_jeu, organisation, licence, url, detail | Bloquant (CA-2) |
| TU-22 | Sauvegarde puis rechargement | contenu préservé, format JSON valide | Bloquant (CA-2) |
| TU-23 | rapport_pour_agent() | retourne une copie ; la modification de la copie n'altère pas le registre | Bloquant (CA-2) |
| TU-24 | Registre préexistant au démarrage | entrées antérieures chargées et non écrasées | Bloquant (CA-2) |

### 3.6 Chargement des contrats

| Id | Cas de test | Résultat attendu | Blocage |
|---|---|---|---|
| TU-25 | Chargement du manifeste réel | les quatre outils présents, déclarations conformes | Bloquant (CA-8) |
| TU-26 | Manifeste avec nom divergent du function.name | échec au démarrage avec message explicite | Bloquant (CA-8) |
| TU-27 | Nom de fichier divergent du nom déclaré | échec au démarrage | Bloquant (CA-8) |
| TU-28 | Contrat JSON absent du chemin déclaré | échec au démarrage, aucun outil partiellement chargé | Bloquant (CA-8) |

| TU-29 | Fichier ZIP (format zip, mime application/zip) | fichier_autre_format, persistance locale, chemin valide | Bloquant (CA-13) |
| TU-30 | Fichier GeoJSON (format geojson, mime application/geo+json) | fichier_autre_format, persistance locale, chemin valide | Bloquant (CA-13) |
| TU-31 | Fichier JSON (format json, mime application/json) | fichier_autre_format, persistance locale, chemin valide | Bloquant (CA-13) |
| TU-32 | Fichier SHP (format shp, mime application/octet-stream) | fichier_autre_format, persistance locale, chemin valide | Bloquant (CA-13) |
| TU-33 | Fichier PDF (format pdf, mime application/pdf) | fichier_autre_format, persistance locale, chemin valide | Bloquant (CA-13) |
## 4. Niveau 2 — Tests d'intégration (TI)

Composants assemblés, réseau simulé, sans agent.

| Id | Cas de test | Résultat attendu | Blocage |
|---|---|---|---|
| TI-01 | Chaîne recherche → inventaire : identifiant de jeu valide issu d'une recherche simulée, puis lister_ressources | inventaire complet, métadonnées enregistrées | Bloquant (CA-3) |
| TI-02 | lister_ressources avec identifiant jamais délivré | jeu_introuvable, aucune écriture au registre | Bloquant (CA-3) |
| TI-03 | Chaîne inventaire → interrogation : ressource api_tabulaire vrai | extraction paginée conforme, colonnes détectées | Bloquant (CA-4) |
| TI-04 | interroger_ressource sur ressource non indexée | ressource_non_indexee, suggestion de bascule vers telecharger_brut | Bloquant (CA-5) |
| TI-05 | Chaîne inventaire → téléchargement : ressource non indexée, URL accessible (simulée) | fichier écrit localement, statut succes, chemin et format exacts | Bloquant (CA-4) |
| TI-06 | telecharger_brut sans inventaire préalable | ressource_introuvable, aucune écriture disque | Bloquant (CA-3) |
| TI-07 | telecharger_brut avec refus serveur simulé | echec_technique, entrée au registre avec motif serveur_origine_bloque, aucune écriture partielle sur disque | Bloquant (CA-2, CA-7) |
| TI-08 | Flux simulé complet avec une exclusion de licence et un échec de téléchargement | registre final : deux entrées, motifs exacts, ordre chronologique | Bloquant (CA-2) |
| TI-09 | Volume tabulaire au-delà du seuil | présence du champ recommandation volume_eleve_telechargement_brut_suggere | Avertissement |
| TI-10 | Vérification systématique des invariants de la documentation : chaque invariant des fichiers docs/*.md couvert par une assertion | tous les invariants vérifiés | Bloquant |
| TI-11 | Téléchargement d'un fichier ZIP | Fichier téléchargé, chemin valide, statut succes | Bloquant (CA-13) |
| TI-12 | Téléchargement d'un fichier GeoJSON | Fichier téléchargé, chemin valide, statut succes | Bloquant (CA-13) |

## 5. Niveau 3 — Tests de bout en bout (TB)

Marqueur reseau. Exécutés à la demande ou périodiquement, pas à chaque modification.

| Id | Cas de test | Résultat attendu | Blocage |
|---|---|---|---|
| TB-01 | Recherche réelle dette publique, tri vues | le jeu Comptes des administrations publiques figure dans les résultats | Bloquant (CA-9) |
| TB-02 | Interrogation réelle de la ressource budget-fr-indicateurs.csv | 74 lignes, colonnes attendues (theme, indicateur, annee_horizon, valeur, unite, statut, source) | Bloquant (CA-9) |
| TB-03 | Parcours de fumée : flux algorithmique complet sans agent, identifiants figés | données acquises, registre cohérent, aucune exception | Bloquant (CA-9) |
| TB-04 | Flux complet avec agent Mistral, thème simple | conversation terminée sans erreur, données acquises, registre concordant | Avertissement (CA-10) |
| TB-05 | Confrontation réelle au serveur Insee (fichier non indexé) | échec propre : statut echec_technique, entrée au registre, pas de crash | Bloquant (CA-7) |

## 6. Niveau transversal — Tests de contrat (TC)

Vérifient la cohérence entre les trois sources : code, contrats JSON, documentation.

| Id | Cas de test | Résultat attendu | Blocage |
|---|---|---|---|
| TC-01 | Cohérence triple manifeste / nom de fichier / function.name pour chaque outil | concordance exacte | Bloquant (CA-8) |
| TC-02 | Introspection : chaque argument du schéma JSON existe dans la signature Python, type compatible | aucune divergence | Bloquant (CA-8) |
| TC-03 | Chaque argument obligatoire du schéma est déclaré required | conformité totale | Bloquant (CA-8) |
| TC-04 | Chaque description (fonction et argument) est non vide ; chaque enum déclaré est non vide | conformité totale | Bloquant (CA-8) |
| TC-05 | Balayage des fichiers docs/*.md : chaque code de statut mentionné existe dans CODES_STATUT, et réciproquement | aucune divergence | Bloquant (CA-8) |
| TC-06 | Invariants mentionnés dans la documentation au moins une fois testés dans le plan | couverture complète | Avertissement |

## 7. Tests de la partie agentique (TA)

Non déterministes : vérification par propriétés observables et grille d'évaluation, sur journaux de conversations réels. Coûteux en tokens : exécutés à chaque évolution du prompt ou du modèle.

| Id | Cas de test | Résultat attendu | Blocage |
|---|---|---|---|
| TA-01 | Propriété d'intégrité des identifiants : rejeu des journaux, vérification que tout identifiant utilisé par l'agent figure dans les sorties des outils précédents | zéro identifiant hors chaîne | Bloquant (CA-3) |
| TA-02 | Propriété d'ordre : aucun appel telecharger_brut sans lister_ressources préalable sur la même ressource | zéro violation | Bloquant (CA-3) |
| TA-03 | Propriété de registre : entrées du registre concordent avec les échecs réellement retournés par les outils | concordance totale | Bloquant (CA-2) |
| TA-04 | Grille d'évaluation de la sélection : corpus de listes prédéfinies ; conformité des jeux retenus (présents dans la liste, licences correctes, exclusions justifiées) | taux de conformité supérieur au seuil défini | Avertissement (CA-10) |
| TA-05 | Propriété de terminaison : la conversation agentique se termine en un nombre d'invocations sous le plafond | nombre d'invocations inférieur au plafond | Avertissement (CA-11) |

## 8. Ordre d'exécution et définition de fini

1. À chaque modification de code : TU et TI (sans réseau), TC. Exécution en quelques secondes.
2. À chaque validation d'itération : ajout de TB-01 à TB-03, TB-05.
3. À chaque évolution de la boucle agentique ou du prompt : TB-04 et l'ensemble TA, avec conservation des journaux.
4. Définition de fini d'une itération : tous les tests bloquants passent ; les critères d'avertissement sont mesurés et consignés même s'ils ne bloquent pas.

## 9. Traces et conservation

- Fixtures de réponses réelles : enregistrées une fois par version majeure des API, stockées dans le dépôt.
- Journaux de conversations agentiques : conservés avec le contexte d'exécution (modèle, prompt, date), servant aux tests TA et à l'audit.
- Résultats des exécutions de validation : consignés avec la version du code et les seuils mesurés (tokens, invocations, durées), pour le suivi des critères non fonctionnels.