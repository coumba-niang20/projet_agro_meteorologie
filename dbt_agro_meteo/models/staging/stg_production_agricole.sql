-- Modèle de staging : nettoyage léger de la table brute production_agricole

select
    pays,
    region,
    sous_region,
    culture,
    season_name,
    planting_year,
    annee_recolte,
    surface_ha,
    production_tonnes,
    rendement
from {{ source('agro_meteo_src', 'production_agricole') }}
where surface_ha > 0
