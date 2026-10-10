-- Staging layer: a stable, typed interface over the raw table.
--
-- Grain: one row per row_id (one order line).
-- This layer does not aggregate or join. It trims text fields so that
-- whitespace cannot create phantom duplicates downstream, and it exposes a
-- fixed set of column names so the marts do not depend on the raw schema.

SELECT
    row_id,
    order_id,
    order_date,
    ship_date,
    TRIM(ship_mode)      AS ship_mode,
    TRIM(customer_id)    AS customer_id,
    TRIM(customer_name)  AS customer_name,
    TRIM(segment)        AS segment,
    TRIM(country)        AS country,
    TRIM(city)           AS city,
    TRIM(state)          AS state,
    NULLIF(TRIM(postal_code), '') AS postal_code,
    TRIM(region)         AS region,
    TRIM(product_id)     AS product_id,
    TRIM(category)       AS category,
    TRIM(sub_category)   AS sub_category,
    TRIM(product_name)   AS product_name,
    sales
FROM {{ source('sales', 'orders') }}
