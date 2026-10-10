-- Customer dimension.
--
-- Grain: one row per customer_id. Verified unique, so it is safe to join the
-- fact table on it.
--
-- Why the shipping geography is not here: city, state and region vary between
-- the orders of the same customer - 765 of the 793 customers in the sample
-- shipped to more than one region. A shipping destination describes an order,
-- not a customer, so putting it in this dimension would either duplicate the
-- customer key or silently pick one destination as if it were the only one.
-- Those columns stay available in stg_orders for order-level questions.

SELECT
    customer_id,
    customer_name,
    segment,
    country
FROM {{ ref('stg_orders') }}
GROUP BY customer_id, customer_name, segment, country
