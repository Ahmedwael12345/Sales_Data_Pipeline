-- Singular test: the fact table must not contain a zero or negative sale.
--
-- A dbt singular test fails when the query returns rows, so this returns the
-- offending lines. The sample data has none, which is exactly why the check is
-- worth keeping: it is cheap, and it will fail loudly if the source changes.

SELECT
    row_id,
    order_id,
    sales
FROM {{ ref('fact_sales') }}
WHERE sales IS NULL
   OR sales <= 0
