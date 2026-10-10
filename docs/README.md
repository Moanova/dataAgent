# dataAgent

**dataAgent** est un projet d'acquisition de données depuis [data.gouv.fr](https://www.data.gouv.fr/) via des agents Mistral. Il permet de :
- Rechercher des jeux de données par mots-clés.
- Lister les ressources (fichiers) associées à un jeu.
- Interroger les ressources indexées par l'API tabulaire.
- Télécharger les fichiers bruts pour les ressources non indexées.
- Consigner les sources inaccessibles dans un registre.

---

## 📁 Structure du projet
```
dataAgent/
├── .env                   # Variables d'environnement
├── requirements.txt       # Dépendances Python
├── venv/                  # Environnement virtuel (ignoré par Git)
│
├── docs/                  # Documentation globale
│   ├── README.md           # Présentation du projet (ce fichier)
│
├── specs/                 # Spécifications techniques
│   ├── contracts/          # Contrats JSON des outils
│   │   ├── rechercher_jeux.json
│   │   ├── lister_ressources.json
│   │   ├── interroger_ressource.json
│   │   ├── telecharger_brut.json
│   │   └── manifeste.json
│   │
│   ├── ARCHITECTURE.md    # Architecture technique
│   ├── REGISTRE.md        # Spécifications du registre
│   └── STOCKAGE.md        # Spécifications du stockage
│
├── design/                # Conception et décisions
│   ├── conception.mmd     # Diagramme des flux
│   └── DECISIONS_CONCEPTION.md  # Journal des décisions
│
├── dev/                   # Suivi du développement
│   └── kanban.md          # Kanban des tâches
│
├── src/                   # Code source
│   ├── __init__.py
│   ├── main.py            # CLI (Typer)
│   ├── contracts/         # Schémas Pydantic
│   ├── core/              # Logique métier
│   └── utils/             # Fonctions utilitaires
│
├── tests/                 # Tests
│   ├── unit/              # Tests unitaires
│   ├── integration/       # Tests d'intégration
│   └── plan_tests.md      # Plan de tests
│
└── data/                  # Stockage des fichiers téléchargés
    ├── raw/               # Fichiers bruts
    ├── processed/         # Fichiers normalisés
    └── registry.json      # Registre des sources inaccessibles
```

---

## 🚀 Installation
### Prérequis
- Python 3.9+
- Un compte Mistral (pour les agents)

### Étapes
1. **Cloner le projet** :
   ```bash
   git clone <url_du_projet>
   cd dataAgent
   ```

2. **Créer et activer un environnement virtuel** :
   - **Windows** :
     ```bash
     python -m venv venv
     .\venv\Scripts\activate
     ```
   - **macOS/Linux** :
     ```bash
     python -m venv venv
     source venv/bin/activate
     ```

3. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurer les variables d'environnement** :
   - Copier `.env.example` en `.env` et remplir les valeurs nécessaires.
     ```ini
     DATA_GOUV_API_URL=https://www.data.gouv.fr/api/1
     LOG_LEVEL=INFO
     ```

---

## ▶️ Utilisation
Le projet s'utilise via une **CLI** (Command Line Interface) avec Typer. Voici les commandes disponibles :

| Commande | Description | Exemple |
|----------|-------------|---------|
| `search` | Recherche des jeux de données par mots-clés. | `python src/main.py search "dette publique"` |
| `list`   | Liste les ressources d'un jeu. | `python src/main.py list <id_jeu>` |
| `query`  | Interroge une ressource indexée par l'API tabulaire. | `python src/main.py query <id_ressource>` |
| `download` | Télécharge une ressource non indexée. | `python src/main.py download <id_ressource>` |

---

## 📋 Suivi des tâches
Le suivi des tâches est disponible dans [`dev/kanban.md`](dev/kanban.md).

---

## 📄 Licence
Ce projet est sous licence **MIT**.