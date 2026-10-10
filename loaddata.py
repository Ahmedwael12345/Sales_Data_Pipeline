#!/usr/bin/env python3
"""Load the raw Superstore order export into PostgreSQL.

The loader is the ingestion step of the pipeline. It writes one raw table and
nothing else; every transformation happens in dbt.

Design decisions
----------------
* **Portable input path.** The CSV location comes from ``SALES_CSV`` and falls
  back to the sample dataset committed in this repository, so the script runs
  from a clean checkout on any machine.
* **Idempotent.** The raw table is truncated before each load, so running the
  pipeline twice produces the same rows rather than duplicates.
* **Dates are parsed explicitly.** The source stores dates as ``DD/MM/YYYY``.
  That was verified rather than assumed: parsing as ``DD/MM/YYYY`` gives a
  0-7 day gap between order and ship date (median 4 days), while ``MM/DD/YYYY``
  leaves 5,841 of the 9,800 rows unparseable.
* **No silent coercion.** A row that cannot be parsed fails the load instead of
  being written as NULL.
* **Audit column.** Every raw row records when it was loaded, so a cleaned value
  can be traced back to a load.

Configuration (environment variables, defaults match docker-compose.yml):

===============  ==================================  ===================
Variable         Default                             Meaning
===============  ==================================  ===================
``PGHOST``       ``localhost``                       Database host
``PGPORT``       ``5432``                            Database port
``PGDATABASE``   ``mydatabase``                      Database name
``PGUSER``       ``myuser``                          Database user
``PGPASSWORD``   ``mypassword``                      Database password
``SALES_CSV``    ``my_dbt_project/seeds/train.csv``  Source CSV path
===============  ==================================  ===================

Usage::

    python loaddata.py
"""

from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2 import OperationalError, extras, sql

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("loaddata")

REPO_ROOT = Path(__file__).resolve().parent
RAW_SCHEMA = "pipeline"
RAW_TABLE = "orders"

# Column name -> PostgreSQL type. The raw table keeps the source columns in
# snake_case and applies only the types needed to store them.
COLUMNS = {
    "row_id": "integer",
    "order_id": "text",
    "order_date": "date",
    "ship_date": "date",
    "ship_mode": "text",
    "customer_id": "text",
    "customer_name": "text",
    "segment": "text",
    "country": "text",
    "city": "text",
    "state": "text",
    "postal_code": "text",
    "region": "text",
    "product_id": "text",
    "category": "text",
    "sub_category": "text",
    "product_name": "text",
    "sales": "numeric(12,4)",
}

CSV_TO_COLUMN = {
    "Row ID": "row_id",
    "Order ID": "order_id",
    "Order Date": "order_date",
    "Ship Date": "ship_date",
    "Ship Mode": "ship_mode",
    "Customer ID": "customer_id",
    "Customer Name": "customer_name",
    "Segment": "segment",
    "Country": "country",
    "City": "city",
    "State": "state",
    "Postal Code": "postal_code",
    "Region": "region",
    "Product ID": "product_id",
    "Category": "category",
    "Sub-Category": "sub_category",
    "Product Name": "product_name",
    "Sales": "sales",
}

DATE_FORMAT = "%d/%m/%Y"
CONNECT_ATTEMPTS = 5
CONNECT_DELAY_SECONDS = 2


def source_path() -> Path:
    """Resolve the CSV path from the environment, defaulting to the sample data."""
    configured = os.environ.get("SALES_CSV")
    if configured:
        return Path(configured).expanduser().resolve()
    return REPO_ROOT / "my_dbt_project" / "seeds" / "train.csv"


def read_source(path: Path) -> pd.DataFrame:
    """Read and validate the CSV, failing loudly on anything unexpected."""
    if not path.is_file():
        sys.exit(f"Source CSV not found: {path}\nSet SALES_CSV to the correct path.")

    log.info("reading %s", path)
    frame = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])

    missing = [name for name in CSV_TO_COLUMN if name not in frame.columns]
    if missing:
        sys.exit(f"Source CSV is missing expected column(s): {', '.join(missing)}")

    frame = frame.rename(columns=CSV_TO_COLUMN)[list(COLUMNS)]

    for column in ("order_date", "ship_date"):
        parsed = pd.to_datetime(frame[column], format=DATE_FORMAT, errors="coerce")
        unparsed = int(parsed.isna().sum())
        if unparsed:
            sys.exit(
                f"{unparsed} row(s) in '{column}' do not match the expected "
                f"{DATE_FORMAT} format. Fix the source or the format before loading."
            )
        frame[column] = parsed.dt.date

    frame["row_id"] = pd.to_numeric(frame["row_id"], errors="coerce").astype("Int64")
    if frame["row_id"].isna().any():
        sys.exit("row_id contains non-numeric values.")

    frame["sales"] = pd.to_numeric(frame["sales"], errors="coerce")
    if frame["sales"].isna().any():
        sys.exit("sales contains non-numeric values.")

    frame = frame.astype(object).where(pd.notnull(frame), None)

    log.info("read %s rows and %s columns", f"{len(frame):,}", len(frame.columns))
    return frame


def connect():
    """Connect with a few retries, because a container may still be starting."""
    settings = {
        "host": os.environ.get("PGHOST", "localhost"),
        "port": os.environ.get("PGPORT", "5432"),
        "dbname": os.environ.get("PGDATABASE", "mydatabase"),
        "user": os.environ.get("PGUSER", "myuser"),
        "password": os.environ.get("PGPASSWORD", "mypassword"),
    }
    for attempt in range(1, CONNECT_ATTEMPTS + 1):
        try:
            connection = psycopg2.connect(**settings)
            connection.autocommit = False
            log.info("connected to %s:%s/%s", settings["host"], settings["port"], settings["dbname"])
            return connection
        except OperationalError as error:
            if attempt == CONNECT_ATTEMPTS:
                sys.exit(f"Could not connect after {CONNECT_ATTEMPTS} attempts: {error}")
            log.warning("connection attempt %s failed, retrying in %ss", attempt, CONNECT_DELAY_SECONDS)
            time.sleep(CONNECT_DELAY_SECONDS)


def create_raw_table(cursor) -> None:
    """Create the raw schema and table if they do not exist yet."""
    columns = ",\n    ".join(f"{name} {type_}" for name, type_ in COLUMNS.items())
    cursor.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(RAW_SCHEMA)))
    cursor.execute(
        sql.SQL(
            "CREATE TABLE IF NOT EXISTS {}.{} (\n    {},\n    _loaded_at timestamptz NOT NULL DEFAULT now()\n)"
        ).format(sql.Identifier(RAW_SCHEMA), sql.Identifier(RAW_TABLE), sql.SQL(columns))
    )


def load(frame: pd.DataFrame) -> None:
    """Replace the contents of the raw table with the given frame."""
    connection = connect()
    try:
        with connection.cursor() as cursor:
            create_raw_table(cursor)

            # Truncate first: a rerun must produce the same table, not double it.
            cursor.execute(
                sql.SQL("TRUNCATE TABLE {}.{}").format(
                    sql.Identifier(RAW_SCHEMA), sql.Identifier(RAW_TABLE)
                )
            )

            rows = list(frame.itertuples(index=False, name=None))
            extras.execute_values(
                cursor,
                sql.SQL("INSERT INTO {}.{} ({}) VALUES %s").format(
                    sql.Identifier(RAW_SCHEMA),
                    sql.Identifier(RAW_TABLE),
                    sql.SQL(", ").join(sql.Identifier(column) for column in COLUMNS),
                ).as_string(cursor),
                rows,
                page_size=1000,
            )
            connection.commit()

            cursor.execute(
                sql.SQL("SELECT count(*) FROM {}.{}").format(
                    sql.Identifier(RAW_SCHEMA), sql.Identifier(RAW_TABLE)
                )
            )
            loaded = cursor.fetchone()[0]
    finally:
        connection.close()

    log.info("loaded %s rows into %s.%s", f"{loaded:,}", RAW_SCHEMA, RAW_TABLE)


def main() -> None:
    started = time.time()
    frame = read_source(source_path())

    log.info(
        "source summary: %s rows, %s orders, %s customers, %s products, dates %s to %s",
        f"{len(frame):,}",
        f"{frame['order_id'].nunique():,}",
        f"{frame['customer_id'].nunique():,}",
        f"{frame['product_id'].nunique():,}",
        frame["order_date"].min().isoformat(),
        frame["order_date"].max().isoformat(),
    )

    load(frame)
    log.info("done in %.1fs", time.time() - started)


if __name__ == "__main__":
    main()
