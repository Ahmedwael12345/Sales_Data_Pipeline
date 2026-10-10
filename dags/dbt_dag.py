"""Airflow DAG that builds and then tests the dbt models.

The DAG only orchestrates; all logic lives in dbt. Running the tests as a
separate task means a data-quality failure is visible in the Airflow UI as a
failed task rather than a line in a log nobody reads.

The dbt project directory is read from ``DBT_PROJECT_DIR`` so the same DAG works
inside the Airflow container (the default path) and in a local test run.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

DBT_PROJECT_DIR = os.environ.get("DBT_PROJECT_DIR", "/opt/airflow/dbt")
DBT = f"cd {DBT_PROJECT_DIR} && dbt"

default_args = {
    "owner": "ahmedwael",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="dbt_pipeline",
    description="Build and test the sales marts with dbt over the raw orders table.",
    default_args=default_args,
    start_date=datetime(2025, 8, 1),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    tags=["dbt", "postgres", "sales"],
) as dag:
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"{DBT} run",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"{DBT} test",
    )

    dbt_run >> dbt_test
