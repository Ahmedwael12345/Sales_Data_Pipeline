# Sales_Data_Pipeline

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![Airflow](https://img.shields.io/badge/orchestrator-Airflow-orange)
![dbt](https://img.shields.io/badge/transform-dbt-red)

## 📌 Project Overview
This project implements an **end-to-end data pipeline** for sales analytics using **PostgreSQL, dbt, and Apache Airflow**.  
It ingests sales data from CSV files into PostgreSQL, transforms it with dbt into **staging, dimension, and fact tables**, and orchestrates the workflow using Airflow.  

The result is a structured analytics-ready dataset (customers, products, sales) that can be used for reporting and BI dashboards.  

---

## 🏗️ Architecture
![Architecture Diagram]  
*(Placeholder — add your diagram here)*  

**Workflow**:
1. Load raw CSV → PostgreSQL (`loaddata.py`).
2. Airflow DAG (`dbt_dag`) triggers dbt.
3. dbt creates staging, dimension, and fact models.
4. Data becomes analytics-ready in PostgreSQL schema.

---

## ⚙️ Tech Stack
- **PostgreSQL** → Database for raw + transformed data  
- **dbt (Data Build Tool)** → SQL-based transformations and testing  
- **Apache Airflow** → Orchestration and scheduling (DAGs)  
- **Docker & Docker Compose** → Containerized environment  
- **Python (psycopg2, pandas)** → Load CSV into Postgres  

---

## 📂 Data Sources
- **Batch CSV**: `train.csv` (Sales data with orders, customers, products).  
  > Dataset: [Superstore Sales dataset](https://www.kaggle.com/datasets/vivek468/superstore-dataset-final) *(replace if different)*  

Columns include:  
`Row ID, Order ID, Order Date, Ship Date, Ship Mode, Customer ID, Customer Name, Segment, Country, City, State, Postal Code, Region, Product ID, Category, Sub-Category, Product Name, Sales`

---

## 🚀 Project Features
- ✅ Ingest CSV sales data into PostgreSQL  
- ✅ Staging, dimension, and fact models with dbt  
- ✅ Data quality tests (not null, unique, relationships)  
- ✅ Airflow DAG (`dbt_dag`) orchestrates dbt runs + tests  
- ✅ Dockerized setup for easy deployment  

---

## 🗂️ dbt Models
- **Staging**: `stg_orders`  
- **Dimensions**: `dim_customers`, `dim_products`  
- **Fact**: `fact_sales`  

---

## 🛠️ Setup Instructions

### 1. Clone the Repo
```bash
git clone https://github.com/yourusername/Sales_Data_Pipeline.git
cd Sales_Data_Pipeline
```
Start Docker

```bash
docker-compose up -d
```
Load CSV into PostgreSQL
```bash
python loaddata.py
```
Run dbt inside Airflow container

```bash
docker exec -it airflow_container bash
cd /opt/airflow/my_dbt_project/my_dbt_project
dbt run
dbt test
```
Open Airflow UI

URL: http://localhost:8080


Folder Structure
```bash
Sales_Data_Pipeline/
│── dags/                 # Airflow DAGs
│   └── dbt_dag.py
│── my_dbt_project/       # dbt models + tests
│── profiles/             # dbt profiles.yml
│── dbt/                  # extra dbt configs if any
│── logs/                 # Airflow logs
│── plugins/              # Airflow plugins
│── loaddata.py           # CSV ingestion script
│── docker-compose.yml    # Docker services
│── Dockerfile            # Airflow custom image
│── venv/                 # local virtual environment
│── README.md             # project documentation

```

