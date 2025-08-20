from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'airflow',
    'start_date': days_ago(1),
    'retries': 0,
}

with DAG(
    dag_id='dbt_pipeline',
    default_args=default_args,
    schedule_interval='@daily',  
    catchup=False,
) as dag:

    
    dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command='cd /opt/airflow/my_dbt_project/my_dbt_project && dbt run'
    )
    dbt_test = BashOperator(
        task_id='dbt_test',
       bash_command='cd /opt/airflow/my_dbt_project/my_dbt_project && dbt test'
    )

    dbt_run >> dbt_test
