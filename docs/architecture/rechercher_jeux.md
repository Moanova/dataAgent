## Fichier : rechercher_jeux.md

# Outil rechercher_jeux

## Intention

Exécuter une recherche sur le catalogue data.gouv.fr à partir de mots-clés produits par l'étape de reformulation du thème (A1). C'est l'unique point d'entrée du flux : aucun autre outil ne doit être appelé sans un identifiant issu de cette fonction.

## Sémantique des arguments

- `mots_cles` (obligatoire) : la recherche applique une logique ET sur l'ensemble des termes. Des termes génériques (« données », « fichier ») produisent peu ou pas de résultats. L'agent doit produire des termes courts et spécifiques, et peut lancer plusieurs recherches complémentaires pour couvrir un thème.
- `tri` : `pertinence` (défaut), `recent` (mise à jour décroissante), `vues` (audience décroissante), `reutilisations`.
- `fenetre_maj` : restriction sur la date de dernière mise à jour : `toutes` (défaut), `30_jours`, `12_mois`, `3_ans`.
- `limite` : nombre maximum de jeux retournés, défaut 10, maximum 20. Au-delà, paginer.

## Retour en succès

`donnees.total_trouves` : nombre total de jeux correspondant à la requête, indépendant de `limite`. `donnees.jeux` : liste résumée (identifiant, titre, organisation, licence, date de dernière mise à jour, nombre de ressources, URL de la fiche). `donnees.exclus_licence` : nombre de jeux écartés par le filtre de licence et consignés au registre.

## Comportements d'échec

- `echec_technique` : le catalogue est injoignable après les tentatives configurées. Une seule relance est pertinente, puis abandon.
- `erreur_parametres` : `mots_cles` absent ou vide.

## Exemple de flux

Appel : `{"mots_cles": ["dette", "publique"], "tri": "vues", "limite": 10}`

Réponse (succès) : `{"statut": "succes", "donnees": {"total_trouves": 39, "jeux": [{"id": "67660551c8588734a16a6a60", "titre": "Comptes des administrations publiques", "organisation": "Insee", "licence": "etalab-2.0", "derniere_maj": "2026-01-15", "nb_ressources": 2, "url": "..."}], "exclus_licence": 3}}`

## Invariants

- Aucun jeu de licence incompatible n'apparaît dans `jeux`.
- Un jeu exclu n'est jamais retourné par une pagination ultérieure de la même requête.
