SELECT
  Row_ID 
    ,Order_ID 
    ,CAST(Order_Date AS DATE) AS Order_Date
    ,CAST(Ship_Date AS DATE) AS Ship_Date  
    ,Ship_Mode 
    ,Customer_ID 
    ,Customer_Name 
    ,Segment 
    ,Country 
    ,City 
    ,State 
    ,Postal_Code 
    ,Region 
    ,Product_ID 
    ,Category 
    ,Sub_Category 
    ,Product_Name 
    ,Sales 
   
FROM {{ source('pipline', 'train') }}