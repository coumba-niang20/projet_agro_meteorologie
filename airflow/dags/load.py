"""
load.py — Étape LOAD du pipeline agro-météorologique

Charge les DataFrames nettoyés dans des tables PostgreSQL.
Utilise SQLAlchemy, qui gère la création de la table si elle n'existe pas.
"""

import os
import pandas as pd
from sqlalchemy import create_engine

# --- Configuration de connexion -----------------------------------------
# Deux modes disponibles :
#   - USE_SQLITE = True  : pas de serveur, pas de mot de passe, un simple
#                           fichier local agro_meteo.db (pratique pour
#                           avancer rapidement / tester)
#   - USE_SQLITE = False : PostgreSQL, à utiliser une fois la connexion
#                           réglée (identifiants via variables d'env)

USE_SQLITE = True

DB_USER = os.getenv("PG_USER", "postgres")
DB_PASSWORD = os.getenv("PG_PASSWORD", "postgres")
DB_HOST = os.getenv("PG_HOST", "localhost")
DB_PORT = os.getenv("PG_PORT", "5432")
DB_NAME = os.getenv("PG_DATABASE", "agro_meteo")


def get_engine():
    """Crée la connexion SQLAlchemy (SQLite ou PostgreSQL selon USE_SQLITE)."""
    if USE_SQLITE:
        # Crée (ou ouvre) un fichier agro_meteo.db dans le dossier courant
        return create_engine("sqlite:///agro_meteo.db")
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)


def load_to_postgres(df: pd.DataFrame, table_name: str, if_exists: str = "replace") -> None:
    """
    Écrit un DataFrame dans une table PostgreSQL.

    if_exists :
      - "replace" : écrase la table à chaque exécution (pratique en dev/test)
      - "append"  : ajoute les lignes sans supprimer l'existant (pour la prod)
    """
    engine = get_engine()
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
    print("Les deux tables sont chargées. Base : agro_meteo.db (ou PostgreSQL "
          "selon USE_SQLITE dans ce fichier).")