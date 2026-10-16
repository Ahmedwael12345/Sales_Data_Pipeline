-- Sales fact table.
--
-- Grain: one row per order line (row_id). Not one row per order, and not one
-- row per order and product: 8 order/product pairs appear twice in the sample,
-- which is why row_id is the key the tests assert on.
--
-- days_to_ship is a documented derived metric:
--   * both dates present -> whole days between the order and the shipment
--   * either date missing -> NULL, never zero
-- In the sample data it ranges from 0 (shipped the same day) to 7.

SELECT
    row_id,
    order_id,
    customer_id,
    product_id,
    order_date,
    ship_date,
    ship_mode,
    sales,
    CASE
        WHEN order_date IS NULL OR ship_date IS NULL THEN NULL
        ELSE (ship_date - order_date)
    END AS days_to_ship
FROM {{ ref('stg_orders') }}
