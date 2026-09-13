# Pipeline agro-météorologique — Afrique de l'Ouest

Projet 3 — Certificat Data Engineering

Pipeline ETL qui collecte, nettoie et analyse des données météo (API Open-Meteo)
et de production agricole (HarvestStat Africa) pour le Sénégal, le Mali et le
Burkina Faso, orchestré avec Apache Airflow et testé avec dbt.

## Structure du projet

```
.
├── data/
│   ├── hvstat_africa_data_v1.0.csv         # données agricoles (à télécharger sur Dryad)
│   └── meteo_afrique_ouest_2010_2022.csv   # données météo (générées par download_meteo_data.py)
├── download_meteo_data.py    # script d'appel à l'API Open-Meteo
├── extract.py                # fonctions d'extraction (météo + agricole)
├── transform.py               # fonctions de nettoyage
├── load.py                    # fonction de chargement en base (SQLite/PostgreSQL)
├── demo.py                    # script de démonstration : interroge la base
├── dbt_agro_meteo/            # projet dbt (modèles + tests de qualité)
├── airflow/                   # environnement Airflow (Docker)
├── requirements.txt
└── README.md
```

## Installation

### 1. Créer et activer l'environnement virtuel

```bash
python3 -m venv venv
source venv/bin/activate      # Linux/macOS
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Placer les données sources

- Téléchargez `hvstat_africa_data_v1.0.csv` sur Dryad et placez-le dans `data/`
- Générez le fichier météo :
```bash
python3 download_meteo_data.py
```
(nécessite un accès internet ; peut prendre 1-2 minutes)

## Lancer le pipeline manuellement

```bash
# 1. Charger les données en base (extract + transform + load)
python3 load.py

# 2. Exécuter les transformations dbt
cd dbt_agro_meteo
dbt run
dbt test
cd ..

# 3. Voir un résumé des données disponibles
python3 demo.py
```

## Lancer le pipeline via Airflow

```bash
cd airflow
docker compose up airflow-init
docker compose up -d
```

Interface web : http://localhost:8080 (identifiants : `airflow` / `airflow`)

Déclenchez manuellement le DAG `pipeline_agro_meteo` depuis l'interface.

## Base de données

Par défaut, le pipeline utilise **SQLite** (`agro_meteo.db`, créé automatiquement).
Pour utiliser PostgreSQL, modifiez `USE_SQLITE = False` dans `load.py` et configurez
les variables d'environnement `PG_USER`, `PG_PASSWORD`, `PG_HOST`, `PG_PORT`, `PG_DATABASE`.

## Tables et modèles produits

| Table / Modèle | Contenu |
|---|---|
| `production_agricole` | Données agricoles brutes nettoyées (27 472 lignes) |
| `meteo_journaliere` | Données météo brutes nettoyées (23 740 lignes) |
| `stg_production_agricole` | Modèle dbt staging agricole |
| `stg_meteo_journaliere` | Modèle dbt staging météo |
| `mart_rendement_par_region` | Rendement moyen par pays/région/culture/année |
| `mart_pluviometrie_mensuelle` | Pluviométrie et températures moyennes par ville/mois |

## Sources de données

| Source | Licence |
|---|---|
| Open-Meteo Historical Weather API | CC BY 4.0 |
| HarvestStat Africa | CC BY 4.0 |

## Limites connues

- Les stations météo sous-jacentes à l'API Open-Meteo sont sous-représentées dans les zones rurales isolées ; les valeurs pour ces zones sont des estimations interpolées.
- HarvestStat Africa présente également des zones rurales sous-représentées, avec une couverture inégale selon les années et les régions.
- Les résultats produits sont destinés à l'aide à la décision et à l'analyse exploratoire, pas à des prévisions météorologiques ou agricoles définitives.

## Auteur

Projet réalisé dans le cadre du certificat Data Engineering — Projet 3.