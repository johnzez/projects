import duckdb
import pandas as pd

con = duckdb.connect("data/processed/olist_warehouse.duckdb", read_only=True)

print("Γραμμές στα CSV:")
for f in ["02_category_performance", "03_seller_performance"]:
    print(f, len(pd.read_csv(f"output/{f}.csv")))

print("\nΣτο warehouse:")
print(con.execute("""
    SELECT
        COUNT(DISTINCT seller_id) AS sellers_with_sales,
        COUNT(DISTINCT product_id) AS products_sold
    FROM fact_order_items
""").df())
print(con.execute("SELECT COUNT(*) AS sellers FROM dim_sellers").df())
print(con.execute("SELECT COUNT(DISTINCT product_category) AS categories FROM dim_products").df())

con.close()