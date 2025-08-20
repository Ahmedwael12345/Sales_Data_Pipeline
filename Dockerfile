FROM apache/airflow:2.9.3-python3.9
RUN pip install --no-cache-dir dbt-core dbt-postgres
