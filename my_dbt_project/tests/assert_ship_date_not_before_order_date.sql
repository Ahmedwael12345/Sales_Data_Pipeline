-- Singular test: an order cannot ship before it was placed.
--
-- This is the kind of rule that catches date-format mistakes. If the loader
-- ever parsed the source as MM/DD/YYYY instead of DD/MM/YYYY, this test would
-- return rows and fail the build.

SELECT
    row_id,
    order_id,
    order_date,
    ship_date
FROM {{ ref('fact_sales') }}
WHERE ship_date IS NOT NULL
  AND order_date IS NOT NULL
  AND ship_date < order_date
