SELECT
  Order_ID,
  Customer_ID,
  Product_ID,
  Row_ID,
  CAST(Order_Date AS DATE) AS Order_Date,
  CAST(Ship_Date AS DATE) AS Ship_Date , 
  Ship_Mode,
  CAST(Sales AS Numeric) AS Sales
FROM {{ ref('stg_orders') }}
