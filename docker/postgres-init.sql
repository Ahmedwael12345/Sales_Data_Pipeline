-- Runs once, on the first start of the PostgreSQL container.
--
-- POSTGRES_DB already creates the pipeline database (mydatabase). This adds a
-- separate database for Airflow's own metadata so that rebuilding the pipeline
-- cannot damage Airflow state.

CREATE DATABASE airflow;
