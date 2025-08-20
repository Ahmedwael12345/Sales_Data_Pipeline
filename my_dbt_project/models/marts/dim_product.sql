SELECT DISTINCT
  Product_ID,
  Product_Name,
  Category,
  Sub_Category
FROM {{ ref('stg_orders') }}
