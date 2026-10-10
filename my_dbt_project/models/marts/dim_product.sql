-- Product dimension.
--
-- Grain: one row per product_id. Category and sub-category are constant per
-- product in the sample data, so grouping by all three keeps the key unique.
--
-- Known source defect: 32 of the 1,861 product ids carry more than one product
-- name in the export (for example FUR-BO-10002213 appears as both
-- "DMI Eclipse Executive Suite Bookcases" and "Sauder Forest Hills Library,
-- Woodland Oak Finish"). There is no way to tell which name is correct, so the
-- rule is explicit and deterministic: keep the name that appears on the most
-- lines, breaking ties alphabetically. The conflict is not hidden - the number
-- of competing names is exposed as name_variant_count so it can be queried and
-- reported.

WITH product_attributes AS (
    SELECT
        product_id,
        category,
        sub_category,
        COUNT(DISTINCT product_name) AS name_variant_count
    FROM {{ ref('stg_orders') }}
    GROUP BY product_id, category, sub_category
),

name_variants AS (
    SELECT
        product_id,
        product_name,
        ROW_NUMBER() OVER (
            PARTITION BY product_id
            ORDER BY COUNT(*) DESC, product_name
        ) AS name_rank
    FROM {{ ref('stg_orders') }}
    GROUP BY product_id, product_name
)

SELECT
    attributes.product_id,
    variants.product_name,
    attributes.category,
    attributes.sub_category,
    attributes.name_variant_count
FROM product_attributes AS attributes
INNER JOIN name_variants AS variants
    ON attributes.product_id = variants.product_id
    AND variants.name_rank = 1
