import psycopg2
import pandas as pd
from datetime import datetime
conn=psycopg2.connect(
    host="localhost",
    port="5432",
    database="mydatabase",
    user="myuser",
    password="mypassword",
)
cursor=conn.cursor()
csv_file="/Users/ahmedwael/Downloads/train.csv"
df=pd.read_csv(csv_file)
#print(df.head())  # Display the first few rows of the DataFrame
cursor.execute(
"""
create table if not exists pipline.train(
    Row_ID int
    ,Order_ID varchar
    ,Order_Date date
    ,Ship_Date date
    ,Ship_Mode varchar
    ,Customer_ID varchar
    ,Customer_Name varchar
    ,Segment varchar
    ,Country varchar
    ,City varchar
    ,State varchar
    ,Postal_Code varchar
    ,Region varchar
    ,Product_ID varchar
    ,Category varchar
    ,Sub_Category varchar
    ,Product_Name varchar
    ,Sales numeric(10,5)
   )

"""
)
conn.commit()
print("Table created successfully") 
for _, row in df.iterrows():
    order_date = datetime.strptime(row['Order Date'], "%d/%m/%Y").date()
    ship_date = datetime.strptime(row['Ship Date'], "%d/%m/%Y").date()
    cursor.execute(
        """
        INSERT INTO pipline.train(
            Row_ID, Order_ID, Order_Date, Ship_Date, Ship_Mode,
            Customer_ID, Customer_Name, Segment, Country, City, State,
            Postal_Code, Region, Product_ID, Category, Sub_Category,
            Product_Name, Sales
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            row['Row ID'],
            row['Order ID'],
            order_date,
            ship_date,
            row['Ship Mode'],
            row['Customer ID'],
            row['Customer Name'],
            row['Segment'],
            row['Country'],
            row['City'],
            row['State'],
            row['Postal Code'],
            row['Region'],
            row['Product ID'],
            row['Category'],
            row['Sub-Category'],
            row['Product Name'],
            row['Sales']
        )
    )

conn.commit()
print("Data inserted successfully")
cursor.close()
conn.close()
