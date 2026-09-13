"""
extract.py — Étape EXTRACT du pipeline agro-météorologique

Contient deux fonctions d'extraction indépendantes :
  - extract_meteo()      : récupère les données météo via l'API Open-Meteo
  - extract_agricole()   : lit et filtre le fichier CSV de production agricole

Chacune renvoie un DataFrame pandas, prêt à être passé à transform.py
"""

import requests  # bibliothèque pour envoyer des requêtes HTTP et interroger l'API météo Open-Meteo
import pandas as pd   # bibliothèque de manipulation de données tabulaires : construit les DataFrames à partir des données météo et agricoles
import time # module natif de gestion du temps, utilisé ici pour temporiser les appels API (éviter de dépasser les limites de fréquence de l'API)

# --- Configuration -----------------------------------------------------

VILLES = [
    {"nom": "Thiès",          "pays": "Senegal",      "lat": 14.79, "lon": -16.93},
    {"nom": "Kaolack",        "pays": "Senegal",      "lat": 14.15, "lon": -16.07},
    {"nom": "Tambacounda",    "pays": "Senegal",      "lat": 13.77, "lon": -13.67},
    {"nom": "Ziguinchor",     "pays": "Senegal",      "lat": 12.57, "lon": -16.27},
    {"nom": "Sikasso",        "pays": "Mali",         "lat": 11.32, "lon": -5.67},
    {"nom": "Bobo-Dioulasso", "pays": "Burkina Faso", "lat": 11.18, "lon": -4.30},
]

PAYS_CIBLES = ["Senegal", "Mali", "Burkina Faso"]


# --- Extraction météo ----------------------------------------------------

def extract_meteo(start_date="2010-01-01", end_date="2022-12-31") -> pd.DataFrame:
    """
    Appelle l'API Open-Meteo (archive historique, gratuite, sans clé)
    pour chaque ville définie dans VILLES, et renvoie un DataFrame unique.
    """
    tous_les_df = []

    for ville in VILLES:
        print(f"[extract_meteo] Téléchargement : {ville['nom']} ({ville['pays']})...")
        url = (
            "https://archive-api.open-meteo.com/v1/archive"
            f"?latitude={ville['lat']}&longitude={ville['lon']}"
            f"&start_date={start_date}&end_date={end_date}"
            "&daily=precipitation_sum,temperature_2m_max,temperature_2m_min,"
            "relative_humidity_2m_max,relative_humidity_2m_min,wind_speed_10m_max"
            "&timezone=Africa%2FAbidjan"
        )
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            daily = r.json().get("daily", {})
            df = pd.DataFrame(daily)
            df.rename(columns={"time": "date"}, inplace=True)
            df.insert(0, "ville", ville["nom"])
            df.insert(1, "pays", ville["pays"])
            df.insert(2, "latitude", ville["lat"])
            df.insert(3, "longitude", ville["lon"])
            tous_les_df.append(df)
            print(f"  -> {len(df)} lignes récupérées")
        except Exception as e:
            print(f"  -> ERREUR pour {ville['nom']} : {e}")
        time.sleep(1)  # on évite de spammer l'API

    if not tous_les_df:
        raise RuntimeError("Aucune donnée météo récupérée.")

    df_final = pd.concat(tous_les_df, ignore_index=True)
    df_final.columns = [
        "ville", "pays", "latitude", "longitude", "date",
        "precipitation_mm", "temp_max_c", "temp_min_c",
        "humidite_max_pct", "humidite_min_pct", "vent_max_kmh",
    ]
    return df_final


def extract_meteo_from_csv(csv_path: str) -> pd.DataFrame:
    """
    Lit un fichier météo déjà généré par download_meteo_data.py (ou par
    extract_meteo() sauvegardé au préalable), plutôt que de rappeler l'API
    à chaque exécution. C'est l'approche recommandée une fois que vous avez
    déjà généré le fichier une première fois : plus rapide, et ça évite les
    erreurs 429/400 liées à l'API à chaque test.
    """
    print(f"[extract_meteo_from_csv] Lecture de {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"  -> {len(df)} lignes lues")
    return df


# --- Extraction agricole ---------------------------------------------------

def extract_agricole(csv_path: str, pays_cibles=None) -> pd.DataFrame:
    """
    Lit le fichier hvstat_africa_data_v1.0.csv et filtre sur les pays
    ciblés par le projet (Senegal, Mali, Burkina Faso par défaut).
    """
    pays_cibles = pays_cibles or PAYS_CIBLES
    print(f"[extract_agricole] Lecture de {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"  -> {len(df)} lignes au total dans le fichier brut")

    df_filtre = df[df["country"].isin(pays_cibles)].copy()
    print(f"  -> {len(df_filtre)} lignes après filtre sur {pays_cibles}")
    return df_filtre


if __name__ == "__main__":
    # Petit test manuel : extraction agricole uniquement (pas besoin d'internet)
    df_agri = extract_agricole("hvstat_africa_data_v1.0.csv")
    print(df_agri.head())