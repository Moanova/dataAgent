# Critères d'acceptabilité — Partie 1 du flux : acquisition data.gouv.fr

## 1. Objet et méthode

Ce document définit les critères d'acceptabilité de la partie 1 du flux d'acquisition de données data.gouv.fr. Chaque critère est mesurable, associé à un seuil, à une méthode de vérification et à un niveau de blocage :

- Bloquant : le critère doit être satisfait pour qu'une itération soit considérée comme terminée ; toute non-conformité est un défaut à corriger avant validation.
- Avertissement : le critère est mesuré et consigné ; la non-conformité ne bloque pas la validation mais déclenche une action d'amélioration.

Les critères fonctionnels dérivent directement de la documentation des contrats (`docs/`) et des invariants qui y sont déclarés. Les tests du plan de tests référencent chaque critère par son identifiant (CA-x).

## 2. Critères fonctionnels

### CA-1 — Exhaustivité du filtre de licence

- Définition : tout jeu de données dont la licence n'apparaît pas dans la politique de licences acceptées (etalab-2.0, odc-odbl, cc-by, cc-by-sa, other-open) est exclu des résultats et consigné au registre avec le motif licence_incompatible.
- Seuil : 100 % des jeux incompatibles exclus ; zéro jeu incompatible retourné.
- Vérification : TU-01 à TU-04, TI-08.
- Blocage : bloquant.

### CA-2 — Exhaustivité du registre des sources inaccessibles

- Définition : toute exclusion juridique et tout échec technique produit une entrée complète au registre (horodatage, motif, identifiant, organisation, licence, URL, détail) ; aucune défaillance n'est perdue.
- Seuil : 100 % des exclusions et échecs tracés ; zéro échec non consigné.
- Vérification : TU-21 à TU-24, TI-07, TI-08, TA-03.
- Blocage : bloquant.

### CA-3 — Intégrité de la chaîne des identifiants

- Définition : tout identifiant de jeu utilisé provient de rechercher_jeux ; tout identifiant de ressource utilisé provient de lister_ressources ; aucun identifiant inventé ou transmis d'une autre source n'est accepté ; l'ordre d'appel des outils est respecté (aucun téléchargement sans inventaire préalable).
- Seuil : zéro identifiant hors chaîne ; zéro violation d'ordre.
- Vérification : TI-01, TI-02, TI-06, TA-01, TA-02.
- Blocage : bloquant.

### CA-4 — Exactitude des données acquises

- Définition : les données extraites par l'API tabulaire ou téléchargées correspondent à la ressource source : nombre de lignes exact, colonnes conformes, fichier local bit à bit complet (taille et empreinte).
- Seuil : conformité totale sur les ressources de référence.
- Vérification : TI-03, TI-05, TB-02.
- Blocage : bloquant.

### CA-5 — Complétude de la normalisation des réponses

- Définition : toute invocation d'outil retourne un objet statut / message / donnees valide avec un code de statut parmi les sept définis ; aucune exception ne remonte vers l'agent ; les défaillances simulées produisent le code prévu.
- Seuil : 100 % des invocations conformes, y compris en conditions dégradées.
- Vérification : TU-12, TU-17 à TU-20, TI-04.
- Blocage : bloquant.

### CA-6 — Exactitude de la classification des ressources

- Définition : chaque ressource est classée dans la bonne classe (fichier_tabulaire, fichier_autre_format, page_web, api_distante) ou marquée indetermine ; aucune classification erronée silencieuse.
- Seuil : 100 % des cas de référence classés correctement ; toute ambiguïté marquée, jamais devinée.
- Vérification : TU-05 à TU-11.
- Blocage : bloquant.

### CA-7 — Robustesse aux défaillances externes

- Définition : le flux supporte l'indisponibilité temporaire du catalogue (tentatives configurées, temporisation), le refus des serveurs d'origine, et les statuts d'erreur HTTP, sans perte des acquisitions déjà réalisées ni écriture partielle de fichier.
- Seuil : zéro perte de données acquises ; zéro fichier partiellement écrit ; échec propre avec motif discriminé.
- Vérification : TU-19, TU-20, TI-07, TB-05.
- Blocage : bloquant.

### CA-8 — Cohérence des contrats

- Définition : manifeste, noms de fichiers, function.name, signatures Python et documentation concordent ; le module refuse de démarrer en cas de divergence ; chaque code de statut documenté existe dans le code et réciproquement.
- Seuil : zéro divergence au démarrage et au balayage de la documentation.
- Vérification : TU-25 à TU-28, TC-01 à TC-05.
- Blocage : bloquant.

### CA-9 — Fonctionnement réel de la chaîne

- Définition : sur les services réels, la recherche retrouve les jeux de référence, l'interrogation retourne les données attendues, et le parcours de fumée complet aboutit sans exception.
- Seuil : TB-01 à TB-03 et TB-05 tous conformes lors de la validation.
- Vérification : TB-01 à TB-03, TB-05.
- Blocage : bloquant (pour la validation d'itération ; ces tests ne s'exécutent pas à chaque modification).

## 3. Critères non fonctionnels

### CA-10 — Qualité des étapes agentiques

- Définition : la sélection opérée par l'agent est conforme (jeux présents dans la liste, licences correctement rapportées, exclusions justifiées) et le flux complet avec agent se termine sans erreur.
- Seuil : taux de conformité de la grille d'évaluation supérieur à un seuil fixé lors de la première campagne (proposition initiale : 90 %) ; TB-04 aboutit.
- Vérification : TA-04, TB-04.
- Blocage : avertissement. Une non-conformité répétée sur deux campagnes successives devient bloquante.

### CA-11 — Coût par flux

- Définition : nombre d'invocations d'outils et de tokens consommés par exécution du flux complet avec agent.
- Seuil : nombre d'invocations d'agent sous le plafond fixé (proposition initiale : 10) ; tokens suivis sans plafond dur.
- Vérification : TA-05, suivi des journaux de validation.
- Blocage : avertissement. Indicateur d'optimisation, pas de conformité.

### CA-12 — Temps de réponse

- Définition : durée d'une recherche et d'un inventaire hors téléchargement.
- Seuil : sous le plafond fixé (proposition initiale : 10 secondes chacun).
- Vérification : mesure lors des exécutions de validation (TB-01 à TB-03).
- Blocage : avertissement.

### CA-13 — Robustesse aux formats non tabulaires

- Définition : les fichiers ZIP, GeoJSON, JSON et autres formats non tabulaires sont acceptés, persistés et classés correctement, même en l'absence de pipeline de transformation.
- Seuil : 100 % des formats de référence du classificateur traités sans erreur.
- Vérification : TU-07, TI-05 (variante format non tabulaire).
- Blocage : bloquant pour la classification et la persistance ; avertissement pour l'exploitation (partie 2 du flux).

### CA-14 — Maintenabilité des contrats

- Définition : toute modification de schéma de contrat s'accompagne d'une incrément de version au manifeste et de la mise à jour concordante de la documentation.
- Seuil : zéro écart constaté en revue entre schéma, manifeste et documentation.
- Vérification : revue de code systématique ; TC-05 en exécution.
- Blocage : procédural (revue), adossé à CA-8 pour la part automatisable.

## 4. Synthèse

| Critère | Nature          | Blocage       | Tests                              |
|---------|-----------------|---------------|------------------------------------|
| CA-1    | Fonctionnel     | Bloquant      | TU-01 à TU-04, TI-08               |
| CA-2    | Fonctionnel     | Bloquant      | TU-21 à TU-24, TI-07, TI-08, TA-03 |
| CA-3    | Fonctionnel     | Bloquant      | TI-01, TI-02, TI-06, TA-01, TA-02  |
| CA-4    | Fonctionnel     | Bloquant      | TI-03, TI-05, TB-02                |
| CA-5    | Fonctionnel     | Bloquant      | TU-12, TU-17 à TU-20, TI-04        |
| CA-6    | Fonctionnel     | Bloquant      | TU-05 à TU-11                      |
| CA-7    | Fonctionnel     | Bloquant      | TU-19, TU-20, TI-07, TB-05         |
| CA-8    | Fonctionnel     | Bloquant      | TU-25 à TU-28, TC-01 à TC-05       |
| CA-9    | Fonctionnel     | Bloquant      | TB-01 à TB-03, TB-05               |
| CA-10   | Non fonctionnel | Avertissement | TA-04, TB-04                       |
| CA-11   | Non fonctionnel | Avertissement | TA-05                              |
| CA-12   | Non fonctionnel | Avertissement | TB-01 à TB-03                      |
| CA-13   | Non fonctionnel | Mixte         | TU-07, TI-05                       |
| CA-14   | Procédural      | Revue         | TC-05                              |

## 5. Règles d'application

1. Une itération est terminée lorsque tous les critères bloquants sont satisfaits aux tests correspondants.
2. Les critères d'avertissement sont mesurés à chaque validation et consignés ; leur évolution est suivie d'une itération à l'autre.
3. Tout changement affectant un critère (nouvelle licence, nouveau format, évolution du prompt agentique) entraîne la révision du critère concerné et de ses tests.
4. Les seuils proposés (90 % de conformité, 10 invocations, 10 secondes) sont des valeurs initiales à ajuster après la première campagne de mesure.
