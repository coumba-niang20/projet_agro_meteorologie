"""
pipeline_agro_meteo.py — DAG Airflow du pipeline agro-météorologique

Orchestre deux branches indépendantes en parallèle :
  - Branche météo    : extract_meteo    -> transform_meteo    -> load_meteo
  - Branche agricole  : extract_agricole -> transform_agricole -> load_agricole
"""

from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from extract import extract_agricole, extract_meteo_from_csv
from transform import transform_agricole, transform_meteo
from load import load_to_postgres
import os

# Ces variables surchargent les valeurs par défaut de load.py, spécifiquement
# pour l'exécution à l'intérieur des conteneurs Airflow (réseau Docker interne)
os.environ.setdefault("PG_HOST", "postgres-agro-meteo")
os.environ.setdefault("PG_PORT", "5432")
os.environ.setdefault("PG_USER", "agro")
os.environ.setdefault("PG_PASSWORD", "agro_pwd")
os.environ.setdefault("PG_DATABASE", "agro_meteo")

CSV_AGRICOLE = "/opt/airflow/dags/data/hvstat_africa_data_v1.0.csv"
CSV_METEO = "/opt/airflow/dags/data/meteo_afrique_ouest_2010_2022.csv"

DBT_PROJECT_DIR = "/opt/airflow/dags/dbt_agro_meteo"
DBT_PROFILES_DIR = "/opt/airflow/dags/dbt_agro_meteo"


def pipeline_agricole():
    df = extract_agricole(CSV_AGRICOLE)
    df_clean = transform_agricole(df)
    load_to_postgres(df_clean, "production_agricole")


def pipeline_meteo():
    df = extract_meteo_from_csv(CSV_METEO)
    df_clean = transform_meteo(df)
    load_to_postgres(df_clean, "meteo_journaliere")


with DAG(
    dag_id="pipeline_agro_meteo",
    description="Pipeline ETL agro-météorologique (météo + agricole, Afrique de l'Ouest)",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["projet3", "agro-meteo"],
) as dag:

    extract_meteo_task = PythonOperator(
        task_id="extract_meteo",
        python_callable=extract_meteo_from_csv,
        op_kwargs={"csv_path": CSV_METEO},
    )
    transform_meteo_task = PythonOperator(
        task_id="transform_meteo_and_load",
        python_callable=pipeline_meteo,
    )

    extract_agricole_task = PythonOperator(
        task_id="extract_agricole",
        python_callable=extract_agricole,
        op_kwargs={"csv_path": CSV_AGRICOLE},
    )
    transform_agricole_task = PythonOperator(
        task_id="transform_agricole_and_load",
        python_callable=pipeline_agricole,
    )

    dbt_run_task = BashOperator(
        task_id="dbt_run",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && "
            f"dbt run --profiles-dir {DBT_PROFILES_DIR}"
        ),
    )

    dbt_test_task = BashOperator(
        task_id="dbt_test",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && "
            f"dbt test --profiles-dir {DBT_PROFILES_DIR}"
        ),
    )

    extract_meteo_task >> transform_meteo_task
    extract_agricole_task >> transform_agricole_task

    [transform_meteo_task, transform_agricole_task] >> dbt_run_task >> dbt_test_task
