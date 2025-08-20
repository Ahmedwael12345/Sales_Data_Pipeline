SELECT
Customer_ID,
Customer_Name,
Segment,
Country,
Region
FROM {{ ref('stg_orders') }}