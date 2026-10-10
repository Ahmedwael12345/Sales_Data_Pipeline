# Sales Data Pipeline — dbt and Airflow over PostgreSQL

[![CI](https://github.com/Ahmedwael12345/Sales_Data_Pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/Ahmedwael12345/Sales_Data_Pipeline/actions/workflows/ci.yml)

A batch pipeline that loads a raw order export into PostgreSQL, models it into a small star schema
with dbt, tests it, and orchestrates the run with Airflow. Everything runs locally with Docker
Compose or against a PostgreSQL instance you already have.

**What this is not:** it is not deployed anywhere, it has no users, and it processes a 9,800-row
sample export rather than a production feed. The value of the project is that it is small enough to
run and check end to end, which is why the tests below are real and their output is quoted.

## Verified status

Run on 10 October 2026 against PostgreSQL 16.15 with dbt 1.12.5, from a clean checkout:

| Step | Command | Result |
| --- | --- | --- |
| Load the raw table | `python loaddata.py` | 9,800 rows loaded in 0.6s |
| Load it a second time | `python loaddata.py` | still 9,800 rows — the load is idempotent |
| Build and test | `dbt build --project-dir my_dbt_project --profiles-dir profiles --exclude resource_type:seed` | `PASS=28 WARN=0 ERROR=0 SKIP=0 TOTAL=28` |
| Orchestrate | `airflow dags test dbt_pipeline 2025-08-18` | `dbt_run` success, `dbt_test` success, DAG run success — `PASS=24 WARN=0 ERROR=0` |
| Final models | `select count(*)` | `dim_customer` 793, `dim_product` 1,861, `fact_sales` 9,800 |

The Airflow DAG wraps the same `dbt run` and `dbt test` commands, and that run above is Airflow
executing them rather than dbt being called by hand. The DAG is normally started by Docker Compose;
see [Running it](#running-it).

## The problem

Order data arrives as a flat CSV export: one row per order line, with the customer, the product and
the shipping address repeated on every row, dates stored as text, and nothing separating the raw
file from the model analysts would query. Answering a question such as *which category earns the
most revenue* means either hand-written SQL over the flat file or a spreadsheet.

This pipeline keeps the raw file exactly as it arrived, then builds the tables that make those
questions a single join: a customer dimension, a product dimension and a sales fact table at the
grain of one order line.

## Data source

`my_dbt_project/seeds/train.csv` — a public Superstore order export, committed so the project runs
without downloading anything. What it actually contains, measured rather than assumed:

| Property | Measured value |
| --- | --- |
| Rows | 9,800 (18 columns) |
| Orders | 4,922 |
| Customers | 793 |
| Products | 1,861 |
| Order dates | 2015-01-03 to 2018-12-30 |
| Grain | one row per line item; `Row ID` is unique, `(Order ID, Product ID)` is not (8 repeats) |
| Date format | `DD/MM/YYYY` |
| Nulls | only `Postal Code`, 11 rows |

The date format was verified instead of guessed. Parsing the column as `DD/MM/YYYY` yields a 0–7 day
gap between order and ship date (median 4 days); parsing it as `MM/DD/YYYY` leaves 5,841 of the
9,800 rows unparseable and implies a median gap of 122 days. A test now guards that assumption — see
`assert_ship_date_not_before_order_date`.

## Architecture

```
my_dbt_project/seeds/train.csv
        |
        |  loaddata.py        reads the CSV, parses dates explicitly, fails on anything
        |                     unexpected, truncates and bulk-loads
        v
pipeline.orders               raw table, exactly what the source said, plus _loaded_at
        |
        |  dbt staging        stg_orders: typed, trimmed, one row per order line
        v
pipeline_staging.stg_orders
        |
        |  dbt marts
        +--> pipeline_analytics.dim_customer   one row per customer
        +--> pipeline_analytics.dim_product    one row per product
        +--> pipeline_analytics.fact_sales     one row per order line
                     ^
                     |  Airflow DAG dbt_pipeline: dbt run, then dbt test
                     |  GitHub Actions CI: the same thing on every push
```

## Data model

| Model | Grain | Key | Rows |
| --- | --- | --- | --- |
| `stg_orders` | one order line | `row_id` | 9,800 |
| `dim_customer` | one customer | `customer_id` | 793 |
| `dim_product` | one product | `product_id` | 1,861 |
| `fact_sales` | one order line | `row_id` | 9,800 |

Two modelling decisions worth stating, because both were forced by the data rather than chosen
freely:

**Shipping geography is not a customer attribute.** City, state and region vary between the orders
of the same customer — 765 of the 793 customers shipped to more than one region. Putting `region` in
`dim_customer` would either duplicate the customer key or silently pick one destination as if it
were the only one. Those columns stay in `stg_orders` for order-level questions.

**32 products have conflicting names in the source.** For example `FUR-BO-10002213` appears as both
"DMI Eclipse Executive Suite Bookcases" and "Sauder Forest Hills Library, Woodland Oak Finish". There
is no way to tell which is correct, so the rule is explicit and deterministic — keep the name that
appears on the most lines, breaking ties alphabetically — and the number of competing names is
exposed as `name_variant_count` so the conflict can be queried instead of being buried.

## Tests

24 data tests run as part of `dbt build`: uniqueness and non-nullness on every key, relationship
tests from the fact table to both dimensions, and two singular tests for rules that a generic test
cannot express (sales must be positive; an order cannot ship before it was placed).

```bash
dbt test --project-dir my_dbt_project --profiles-dir profiles
```

The tests are not decoration. Fixing the four that were previously pointing at non-existent model
names immediately failed on `dim_customer`, because the dimension selected its columns without
deduplicating — the table had many rows per customer and was not a dimension at all. That is what the
repair fixed.

## Running it

### With Docker Compose

```bash
docker compose up -d                 # PostgreSQL, Airflow init, webserver, scheduler
open http://localhost:8080           # Airflow UI, login airflow / airflow
python loaddata.py                   # load the raw table from the host
```

The dbt profile reads its connection details from environment variables, so the same file works on
the host (where PostgreSQL is on `localhost`) and inside the container (where it is the service
`postgres`). Airflow keeps its metadata in a separate database from the pipeline data, so rebuilding
the pipeline cannot damage Airflow state.

### Without Docker

```bash
pip install -r requirements.txt
createdb mydatabase                     # or use an existing database

python loaddata.py                      # load the raw table
dbt build --project-dir my_dbt_project --profiles-dir profiles --exclude resource_type:seed
```

The seed is excluded from the build because `loaddata.py` already loads that CSV into the raw
schema; the seed exists only as a convenient copy of the sample data.

Configuration is read from `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD` and `SALES_CSV`,
each with a working default. Nothing needs to be edited to run the project on another machine, and no
credential is stored in a file.

## Example queries

```sql
-- Revenue by category
select p.category, round(sum(f.sales)::numeric, 2) as revenue, count(*) as order_lines
from pipeline_analytics.fact_sales f
join pipeline_analytics.dim_product p on f.product_id = p.product_id
group by p.category
order by revenue desc;
```

```
    category     |  revenue  | order_lines
-----------------+-----------+-------------
 Technology      | 827455.87 |        1813
 Furniture       | 728658.58 |        2078
 Office Supplies | 705422.33 |        5909
```

```sql
-- Products whose source names disagree, and how many names each has
select product_id, product_name, name_variant_count
from pipeline_analytics.dim_product
where name_variant_count > 1
order by name_variant_count desc, product_id;
```

## Known data-quality issues

| Issue | Count | How it is handled |
| --- | --- | --- |
| Products with conflicting names in the source | 32 of 1,861 | Deterministic rule, conflict exposed in `name_variant_count` |
| Customers shipping to more than one region | 765 of 793 | Geography excluded from `dim_customer`, documented above |
| Missing postal codes | 11 rows | Kept as NULL, not replaced with a placeholder |
| `(Order ID, Product ID)` repeats | 8 rows | Fact grain set to `row_id`, which is unique |

## Limitations

The pipeline has never run on a schedule against live data. Airflow is configured but has only been
run on demand: `airflow dags test` executed both tasks successfully, but no scheduler has been left
running against a timetable. The Docker Compose stack itself was not executed when this README was
written, because Docker was unavailable in that environment, so treat the compose file as reviewed
rather than proven. Snowflake, Spark and Kafka are deliberately absent: this pipeline does not need
them, and adding them would hide the parts that matter.

There is no incremental loading. Every run truncates and reloads the raw table, which is correct at
9,800 rows and wrong at any real volume; the fix would be a `_loaded_at` watermark and a merge into
the fact table.

## Project structure

```
.
├── dags/dbt_dag.py              Airflow DAG: dbt run, then dbt test
├── docker/postgres-init.sql     creates the separate Airflow metadata database
├── docker-compose.yml           PostgreSQL + Airflow (init, webserver, scheduler)
├── Dockerfile                   Airflow image with dbt installed
├── loaddata.py                  ingestion: CSV -> pipeline.orders
├── profiles/profiles.yml        dbt profile, all values from environment variables
├── requirements.txt             loader and CI dependencies
├── my_dbt_project/
│   ├── dbt_project.yml
│   ├── models/source.yml        source definition and column documentation
│   ├── models/staging/          stg_orders
│   ├── models/marts/            dim_customer, dim_product, fact_sales
│   ├── seeds/train.csv          sample dataset
│   └── tests/                   schema tests plus two singular tests
└── .github/workflows/ci.yml     loads, rebuilds and tests on every push
```

## What changed in this repair

The repository previously contained the pieces of a pipeline that had never been run together. The
changes below are the difference between a project that looks finished and one that is.

| Change | Reason |
| --- | --- |
| Test model names corrected to `dim_customer` and `dim_product` | Four declared tests pointed at names that do not exist, so dbt skipped them with a warning and the run still looked green |
| `dim_customer` deduplicated and geography removed | With working tests, the missing uniqueness failed immediately: the model had many rows per customer |
| `dim_product` conflict rule added | 32 product ids carry several names; the rule is now explicit and measurable |
| Loader rewritten | The CSV path was hard-coded to one machine, the load inserted row by row, and reruns duplicated every row |
| dbt profile moved to environment variables | Credentials were in a committed file and the host was hard-coded to the container name |
| Airflow scheduler service and user creation added | The stack started a webserver with no scheduler, so the DAG was never actually scheduled |
| Dependency and log files removed from git | 12,559 tracked files were dependencies and logs, which buried the twenty files that matter |
| CI added | The README claimed a passing build while no CI existed |

## Next steps

The next useful change is incremental loading with a watermark and a merge, followed by a
`dbt-expectations` or singular-test check on `sales` against `quantity × unit price` once those
columns exist in the source. After that, the same structure moves to the financial data platform
where the source is a public statement page rather than a CSV.
