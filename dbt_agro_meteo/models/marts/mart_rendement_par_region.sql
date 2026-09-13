-- Modèle d'agrégation : rendement moyen par région, culture et année

select
    pays,
    region,
    culture,
    annee_recolte,
    round(avg(rendement), 3) as rendement_moyen,
    round(sum(surface_ha), 1) as surface_totale_ha,
    round(sum(production_tonnes), 1) as production_totale_tonnes
from {{ ref('stg_production_agricole') }}
group by pays, region, culture, annee_recolte
