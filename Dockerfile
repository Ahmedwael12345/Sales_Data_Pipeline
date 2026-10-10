FROM apache/airflow:2.9.3-python3.11

# Pinned to the same range as requirements.txt so the image and CI agree.
RUN pip install --no-cache-dir "dbt-core>=1.10,<2.0" "dbt-postgres>=1.10,<2.0"
