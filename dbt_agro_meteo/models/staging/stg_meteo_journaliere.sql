-- Modèle de staging : nettoyage léger de la table brute meteo_journaliere

select
    ville,
    pays,
    date,
    annee,
    mois,
    precipitation_mm,
    temp_max_c,
    temp_min_c,
    humidite_max_pct,
    humidite_min_pct,
    vent_max_kmh
from {{ source('agro_meteo_src', 'meteo_journaliere') }}
