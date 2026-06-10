from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

default_args = {
    "owner": "DustiniaDelixia",
    "start_date": datetime(2024, 1, 1),
}

with DAG(
    "groceria_etl_pipeline",
    default_args=default_args,
    schedule_interval="@daily",
    catchup=False,
    max_active_runs=1,
    description="Groceria CSV → Pandas Transform → ClickHouse",
) as dag:

    extract = BashOperator(
        task_id="extract",
        bash_command="python /opt/airflow/dags/extract_data.py",
    )

    transform = BashOperator(
        task_id="transform",
        bash_command="python /opt/airflow/dags/transform_data.py",
    )

    load = BashOperator(
        task_id="load",
        bash_command="python /opt/airflow/dags/load_data.py",
    )

    extract >> transform >> load
