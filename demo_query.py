"""
demo.py — Script de démonstration du pipeline agro-météorologique

Interroge la base de données (agro_meteo.db) et affiche un résumé
des données disponibles : volumes, périodes couvertes, aperçus.

Usage :
    python3 demo.py
"""

from sqlalchemy import create_engine, text

DB_PATH = "agro_meteo.db"


def afficher_separateur(titre: str) -> None:
    print("\n" + "=" * 60)
    print(titre)
    print("=" * 60)


def resume_meteo(conn) -> None:
    afficher_separateur("DONNÉES MÉTÉO — meteo_journaliere")

    total = conn.execute(text("SELECT COUNT(*) FROM meteo_journaliere")).scalar()
    print(f"Nombre total de lignes : {total}")

    villes = conn.execute(
        text("SELECT DISTINCT ville, pays FROM meteo_journaliere ORDER BY pays, ville")
    ).fetchall()
    print(f"\nVilles couvertes ({len(villes)}) :")
    for ville, pays in villes:
        print(f"  - {ville} ({pays})")

    periode = conn.execute(
        text("SELECT MIN(date), MAX(date) FROM meteo_journaliere")
    ).fetchone()
    print(f"\nPériode couverte : {periode[0]} → {periode[1]}")

    print("\nMoyennes climatiques globales :")
    moyennes = conn.execute(
        text(
            """
            SELECT
                ROUND(AVG(precipitation_mm), 2) AS pluie_moy,
                ROUND(AVG(temp_max_c), 2) AS temp_max_moy,
                ROUND(AVG(temp_min_c), 2) AS temp_min_moy
            FROM meteo_journaliere
            """
        )
    ).fetchone()
    print(f"  - Précipitations moyennes/jour : {moyennes[0]} mm")
    print(f"  - Température max moyenne      : {moyennes[1]} °C")
    print(f"  - Température min moyenne      : {moyennes[2]} °C")

    print("\nAperçu (5 dernières lignes) :")
    apercu = conn.execute(
        text("SELECT ville, date, precipitation_mm, temp_max_c, temp_min_c "
             "FROM meteo_journaliere ORDER BY date DESC LIMIT 5")
    ).fetchall()
    for row in apercu:
        print(f"  {row}")


def resume_agricole(conn) -> None:
    afficher_separateur("DONNÉES AGRICOLES — production_agricole")

    total = conn.execute(text("SELECT COUNT(*) FROM production_agricole")).scalar()
    print(f"Nombre total de lignes : {total}")

    pays = conn.execute(
        text("SELECT DISTINCT pays FROM production_agricole ORDER BY pays")
    ).fetchall()
    print(f"\nPays couverts ({len(pays)}) : {', '.join(p[0] for p in pays)}")

    cultures = conn.execute(
        text("SELECT DISTINCT culture FROM production_agricole ORDER BY culture LIMIT 10")
    ).fetchall()
    print(f"\nCultures présentes (aperçu, 10 premières) :")
    for c in cultures:
        print(f"  - {c[0]}")

    print("\nRendement moyen par pays :")
    rendements = conn.execute(
        text(
            """
            SELECT pays, ROUND(AVG(rendement), 3) AS rendement_moyen
            FROM production_agricole
            GROUP BY pays
            ORDER BY pays
            """
        )
    ).fetchall()
    for pays_nom, rdt in rendements:
        print(f"  - {pays_nom} : {rdt}")


def resume_dbt_marts(conn) -> None:
    afficher_separateur("MODÈLES DBT — aperçu des agrégations")

    try:
        n = conn.execute(text("SELECT COUNT(*) FROM mart_rendement_par_region")).scalar()
        print(f"mart_rendement_par_region : {n} lignes")
    except Exception:
        print("mart_rendement_par_region : non trouvé (lancez 'dbt run' d'abord)")

    try:
        n = conn.execute(text("SELECT COUNT(*) FROM mart_pluviometrie_mensuelle")).scalar()
        print(f"mart_pluviometrie_mensuelle : {n} lignes")
    except Exception:
        print("mart_pluviometrie_mensuelle : non trouvé (lancez 'dbt run' d'abord)")


def main() -> None:
    print("Pipeline agro-météorologique — Script de démonstration")
    print(f"Base interrogée : {DB_PATH}")

    engine = create_engine(f"sqlite:///{DB_PATH}")
    with engine.connect() as conn:
        resume_meteo(conn)
        resume_agricole(conn)
        resume_dbt_marts(conn)

    print("\n" + "=" * 60)
    print("Fin de la démonstration.")
    print("=" * 60)


if __name__ == "__main__":
    main()