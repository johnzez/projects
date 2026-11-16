
from pathlib import Path
import duckdb

# --------------------------------------------------
# 1. PROJECT CONFIGURATION
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parents[1]

DB_PATH = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "olist_warehouse.duckdb"
)

con = duckdb.connect(str(DB_PATH))

print("=" * 70)
print("OLIST STAGING LAYER")
print("=" * 70)


# --------------------------------------------------
# 2. CREATE STAGING TABLES
# --------------------------------------------------

staging_queries = {

    "stg_customers": """
        SELECT
            customer_id,
            customer_unique_id,
            TRY_CAST(customer_zip_code_prefix AS VARCHAR)
                AS customer_zip_code_prefix,
            customer_city,
            customer_state
        FROM raw_customers
    """,

    "stg_orders": """
        SELECT
            order_id,
            customer_id,
            order_status,
            TRY_CAST(order_purchase_timestamp AS TIMESTAMP)
                AS order_purchase_timestamp,
            TRY_CAST(order_approved_at AS TIMESTAMP)
                AS order_approved_at,
            TRY_CAST(order_delivered_carrier_date AS TIMESTAMP)
                AS order_delivered_carrier_date,
            TRY_CAST(order_delivered_customer_date AS TIMESTAMP)
                AS order_delivered_customer_date,
            TRY_CAST(order_estimated_delivery_date AS TIMESTAMP)
                AS order_estimated_delivery_date
        FROM raw_orders
    """,

    "stg_order_items": """
        SELECT
            order_id,
            TRY_CAST(order_item_id AS INTEGER) AS order_item_id,
            product_id,
            seller_id,
            TRY_CAST(shipping_limit_date AS TIMESTAMP)
                AS shipping_limit_date,
            TRY_CAST(price AS DECIMAL(12,2)) AS price,
            TRY_CAST(freight_value AS DECIMAL(12,2))
                AS freight_value
        FROM raw_order_items
    """,

    "stg_order_payments": """
        SELECT
            order_id,
            TRY_CAST(payment_sequential AS INTEGER)
                AS payment_sequential,
            payment_type,
            TRY_CAST(payment_installments AS INTEGER)
                AS payment_installments,
            TRY_CAST(payment_value AS DECIMAL(12,2))
                AS payment_value
        FROM raw_order_payments
    """,

    "stg_order_reviews": """
        SELECT
            review_id,
            order_id,
            TRY_CAST(review_score AS INTEGER) AS review_score,
            review_comment_title,
            review_comment_message,
            TRY_CAST(review_creation_date AS TIMESTAMP)
                AS review_creation_date,
            TRY_CAST(review_answer_timestamp AS TIMESTAMP)
                AS review_answer_timestamp
        FROM raw_order_reviews
    """,

    "stg_products": """
        SELECT
            product_id,
            product_category_name,
            TRY_CAST(product_name_lenght AS INTEGER)
                AS product_name_length,
            TRY_CAST(product_description_lenght AS INTEGER)
                AS product_description_length,
            TRY_CAST(product_photos_qty AS INTEGER)
                AS product_photos_qty,
            TRY_CAST(product_weight_g AS INTEGER)
                AS product_weight_g,
            TRY_CAST(product_length_cm AS INTEGER)
                AS product_length_cm,
            TRY_CAST(product_height_cm AS INTEGER)
                AS product_height_cm,
            TRY_CAST(product_width_cm AS INTEGER)
                AS product_width_cm
        FROM raw_products
    """,

    "stg_sellers": """
        SELECT
            seller_id,
            TRY_CAST(seller_zip_code_prefix AS VARCHAR)
                AS seller_zip_code_prefix,
            seller_city,
            seller_state
        FROM raw_sellers
    """,

    "stg_geolocation": """
        SELECT
            TRY_CAST(geolocation_zip_code_prefix AS VARCHAR)
                AS geolocation_zip_code_prefix,
            TRY_CAST(geolocation_lat AS DOUBLE)
                AS geolocation_lat,
            TRY_CAST(geolocation_lng AS DOUBLE)
                AS geolocation_lng,
            geolocation_city,
            geolocation_state
        FROM raw_geolocation
    """,

    "stg_category_translation": """
        SELECT
            product_category_name,
            product_category_name_english
        FROM raw_category_translation
    """
}


# --------------------------------------------------
# 3. EXECUTE STAGING TRANSFORMATIONS
# --------------------------------------------------

for table_name, query in staging_queries.items():

    print(f"\nBuilding: {table_name}")

    con.execute(f"""
        CREATE OR REPLACE TABLE {table_name} AS
        {query}
    """)

    row_count = con.execute(
        f"SELECT COUNT(*) FROM {table_name}"
    ).fetchone()[0]

    column_count = len(
        con.execute(f"DESCRIBE {table_name}").fetchall()
    )

    print(f"Created: {table_name}")
    print(f"Rows: {row_count:,}")
    print(f"Columns: {column_count}")


# --------------------------------------------------
# 4. VALIDATE STAGING TABLES
# --------------------------------------------------

print("\n" + "=" * 70)
print("STAGING LAYER VALIDATION")
print("=" * 70)

staging_tables = con.execute("""
    SHOW TABLES
""").fetchall()

staging_tables = [
    row[0]
    for row in staging_tables
    if row[0].startswith("stg_")
]

print("Staging tables found:", len(staging_tables))

for table_name in sorted(staging_tables):

    count = con.execute(
        f"SELECT COUNT(*) FROM {table_name}"
    ).fetchone()[0]

    print(f"{table_name}: {count:,} rows")


# --------------------------------------------------
# 5. CLOSE CONNECTION
# --------------------------------------------------

con.close()

print("\n" + "=" * 70)
print("STAGING LAYER COMPLETED")
print("=" * 70)
