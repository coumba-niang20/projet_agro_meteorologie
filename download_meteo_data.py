import requests
import pandas as pd
import time
import os

# Villes agricoles d'Afrique de l'Ouest du projet
villes = [
    {"nom": "Thiès",           "pays": "Sénégal",      "lat": 14.79, "lon": -16.93},
    {"nom": "Kaolack",         "pays": "Sénégal",      "lat": 14.15, "lon": -16.07},
    {"nom": "Tambacounda",     "pays": "Sénégal",      "lat": 13.77, "lon": -13.67},
    {"nom": "Ziguinchor",      "pays": "Sénégal",      "lat": 12.57, "lon": -16.27},
    {"nom": "Sikasso",         "pays": "Mali",         "lat": 11.32, "lon": -5.67},
    {"nom": "Bobo-Dioulasso",  "pays": "Burkina Faso", "lat": 11.18, "lon": -4.30},
]

tous_les_df = []

for ville in villes:
    print(f"Téléchargement : {ville['nom']} ({ville['pays']})...")
    url = (
        f"https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={ville['lat']}&longitude={ville['lon']}"
        f"&start_date=2010-01-01&end_date=2022-12-31"
        f"&daily=precipitation_sum,temperature_2m_max,temperature_2m_min,"
        f"relative_humidity_2m_max,relative_humidity_2m_min,wind_speed_10m_max"
        f"&timezone=Africa%2FAbidjan"
    )
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        daily = data.get("daily", {})
        df = pd.DataFrame(daily)
        df.rename(columns={"time": "date"}, inplace=True)
        df.insert(0, "ville", ville["nom"])
        df.insert(1, "pays", ville["pays"])
        df.insert(2, "latitude", ville["lat"])
        df.insert(3, "longitude", ville["lon"])
        tous_les_df.append(df)
        print(f"  ✓ {len(df)} lignes récupérées")
    except Exception as e:
        print(f"  ✗ Erreur pour {ville['nom']} : {e}")
    time.sleep(6)

if tous_les_df:
    final_df = pd.concat(tous_les_df, ignore_index=True)
    final_df.columns = [
        "ville", "pays", "latitude", "longitude", "date",
        "precipitation_mm", "temp_max_c", "temp_min_c",
        "humidite_max_pct", "humidite_min_pct", "vent_max_kmh"
    ]
    os.makedirs("data", exist_ok=True)
    output_path = "data/meteo_afrique_ouest_2010_2022.csv"
    final_df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"\n✅ Fichier sauvegardé : {output_path}")
    print(f"   {len(final_df)} lignes | {final_df['ville'].nunique()} villes | colonnes : {list(final_df.columns)}")
    print(f"\nAperçu :")
    print(final_df.head(10).to_string())
else:
    print("Aucune donnée récupérée.")
