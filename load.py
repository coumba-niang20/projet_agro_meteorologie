"""
load.py — Étape LOAD du pipeline agro-météorologique

Charge les DataFrames nettoyés dans des tables PostgreSQL.
Utilise SQLAlchemy, qui gère la création de la table si elle n'existe pas.
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text

# --- Configuration de connexion -----------------------------------------
# Deux modes disponibles :
#   - USE_SQLITE = True  : pas de serveur, pas de mot de passe, un simple
#                           fichier local agro_meteo.db (pratique pour
#                           avancer rapidement / tester)
#   - USE_SQLITE = False : PostgreSQL, à utiliser une fois la connexion
#                           réglée (identifiants via variables d'env)

USE_SQLITE = False

DB_USER = os.getenv("PG_USER", "agro")
DB_PASSWORD = os.getenv("PG_PASSWORD", "agro_pwd")
DB_HOST = os.getenv("PG_HOST", "localhost")
DB_PORT = os.getenv("PG_PORT", "5434")
DB_DATABASE = os.getenv("PG_DATABASE", "agro_meteo")

# Vues dbt connues qui dépendent directement d'une table source. Si l'une
# de ces tables doit être rechargée (if_exists="replace"), la vue
# correspondante est supprimée d'abord (CASCADE) puis recréée par le
# prochain `dbt run` — sans ça, PostgreSQL refuse le DROP TABLE tant que
# la vue existe (erreur DependentObjectsStillExist).
DEPENDENT_VIEWS = {
    "production_agricole": ["stg_production_agricole"],
    "meteo_journaliere": ["stg_meteo_journaliere"],
}


def get_engine():
    """Crée la connexion SQLAlchemy (SQLite ou PostgreSQL selon USE_SQLITE)."""
    if USE_SQLITE:
        # Crée (ou ouvre) un fichier agro_meteo.db dans le dossier courant
        return create_engine("sqlite:///agro_meteo.db")
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"
    return create_engine(url)


def drop_dependent_views(engine, table_name: str) -> None:
    """
    Supprime (CASCADE) les vues dbt connues qui dépendent de `table_name`,
    pour permettre à pandas de faire un DROP TABLE / CREATE TABLE propre
    avec if_exists="replace". N'a aucun effet en SQLite (pas de vues dbt
    matérialisées de la même façon, et le problème ne s'y pose pas).
    Sans effet non plus si aucune vue de ce nom n'existe encore.
    """
    if USE_SQLITE:
        return
    views = DEPENDENT_VIEWS.get(table_name, [])
    if not views:
        return
    with engine.begin() as conn:
        for view_name in views:
            conn.execute(text(f'DROP VIEW IF EXISTS "{view_name}" CASCADE'))
            print(f"[load] Vue dépendante supprimée avant rechargement : {view_name}")


def load_to_postgres(df: pd.DataFrame, table_name: str, if_exists: str = "replace") -> None:
    """
    Écrit un DataFrame dans une table PostgreSQL.

    if_exists :
      - "replace" : écrase la table à chaque exécution (pratique en dev/test)
      - "append"  : ajoute les lignes sans supprimer l'existant (pour la prod)
    """
    engine = get_engine()
    if if_exists == "replace":
        drop_dependent_views(engine, table_name)
    print(f"[load] Écriture de {len(df)} lignes dans la table '{table_name}' "
          f"(mode={if_exists})...")
    df.to_sql(table_name, engine, if_exists=if_exists, index=False, chunksize=5000)
    print(f"[load] Terminé : table '{table_name}' mise à jour.")


if __name__ == "__main__":
    from extract import extract_agricole, extract_meteo_from_csv
    from transform import transform_agricole, transform_meteo

    print("=" * 60)
    print("Chargement 1/2 : production_agricole")
    print("=" * 60)
    df_agri = extract_agricole("hvstat_africa_data_v1.0.csv")
    df_agri_clean = transform_agricole(df_agri)
    load_to_postgres(df_agri_clean, "production_agricole")

    print()
    print("=" * 60)
    print("Chargement 2/2 : meteo_journaliere")
    print("=" * 60)
    # Adaptez le chemin si votre fichier météo est ailleurs
    df_meteo = extract_meteo_from_csv("data/meteo_afrique_ouest_2010_2022.csv")
    df_meteo_clean = transform_meteo(df_meteo)
    load_to_postgres(df_meteo_clean, "meteo_journaliere")

    print()
    print(f"Les deux tables sont chargées dans PostgreSQL ({DB_HOST}:{DB_PORT}/{DB_DATABASE}).")
    print("Pensez à relancer 'dbt run' pour reconstruire les vues/tables dbt supprimées.")