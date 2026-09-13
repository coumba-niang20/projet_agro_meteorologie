"""
transform.py — Étape TRANSFORM du pipeline agro-météorologique

Nettoie et prépare les deux DataFrames issus de extract.py, avant chargement
en base PostgreSQL.
"""

import pandas as pd


def transform_meteo(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoyage des données météo journalières."""
    df = df.copy()

    # 1. Typage correct de la date
    df["date"] = pd.to_datetime(df["date"])

    # 2. Suppression des doublons exacts (ville + date)
    avant = len(df)
    df = df.drop_duplicates(subset=["ville", "date"])
    print(f"[transform_meteo] {avant - len(df)} doublons supprimés")

    # 3. Suppression des lignes sans aucune mesure exploitable
    colonnes_mesures = [
        "precipitation_mm", "temp_max_c", "temp_min_c",
        "humidite_max_pct", "humidite_min_pct", "vent_max_kmh",
    ]
    df = df.dropna(subset=colonnes_mesures, how="all")

    # 4. Garde-fous : on retire les valeurs physiquement impossibles
    df = df[(df["temp_max_c"].between(-10, 55)) | df["temp_max_c"].isna()]
    df = df[(df["precipitation_mm"] >= 0) | df["precipitation_mm"].isna()]

    # 5. Colonne dérivée utile pour l'analyse : année et mois
    df["annee"] = df["date"].dt.year
    df["mois"] = df["date"].dt.month

    print(f"[transform_meteo] {len(df)} lignes après nettoyage")
    return df


def transform_agricole(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoyage des données de production agricole."""
    df = df.copy()

    # 1. Colonnes utiles uniquement (on garde le nécessaire pour l'analyse)
    colonnes_utiles = [
        "country", "admin_1", "admin_2", "product", "season_name",
        "planting_year", "harvest_year", "area", "production", "yield",
    ]
    df = df[colonnes_utiles]

    # 2. Suppression des lignes sans surface ou production (pas exploitables)
    avant = len(df)
    df = df.dropna(subset=["area", "production"])
    print(f"[transform_agricole] {avant - len(df)} lignes sans area/production supprimées")

    # 3. Suppression des valeurs négatives ou nulles incohérentes
    df = df[(df["area"] > 0) & (df["production"] >= 0)]

    # 4. Suppression des doublons
    df = df.drop_duplicates()

    # 5. Renommage en français pour cohérence avec la table météo
    df = df.rename(columns={
        "country": "pays",
        "admin_1": "region",
        "admin_2": "sous_region",
        "product": "culture",
        "harvest_year": "annee_recolte",
        "area": "surface_ha",
        "production": "production_tonnes",
        "yield": "rendement",
    })

    print(f"[transform_agricole] {len(df)} lignes après nettoyage")
    return df


if __name__ == "__main__":
    from extract import extract_agricole, extract_meteo_from_csv

    print("=" * 60)
    print("TEST 1 : transform_agricole")
    print("=" * 60)
    df_agri = extract_agricole("hvstat_africa_data_v1.0.csv")
    df_agri_clean = transform_agricole(df_agri)
    print(df_agri_clean.head())
    print(df_agri_clean.dtypes)

    print()
    print("=" * 60)
    print("TEST 2 : transform_meteo")
    print("=" * 60)
    # Adaptez le chemin si votre fichier météo est ailleurs
    df_meteo = extract_meteo_from_csv("data/meteo_afrique_ouest_2010_2022.csv")
    df_meteo_clean = transform_meteo(df_meteo)
    print(df_meteo_clean.head())
    print(df_meteo_clean.dtypes)