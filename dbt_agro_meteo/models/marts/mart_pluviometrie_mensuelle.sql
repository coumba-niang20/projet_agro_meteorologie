-- Modèle d'agrégation : pluviométrie moyenne par ville et par mois/année

select
    ville,
    pays,
    annee,
    mois,
    round(sum(precipitation_mm), 1) as precipitation_totale_mm,
    round(avg(temp_max_c), 1) as temp_max_moyenne_c,
    round(avg(temp_min_c), 1) as temp_min_moyenne_c
from {{ ref('stg_meteo_journaliere') }}
group by ville, pays, annee, mois
