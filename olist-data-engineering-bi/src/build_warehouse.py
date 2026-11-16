
from pathlib import Path
import duckdb

# --------------------------------------------------
# 1. CONFIGURATION
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_DIR / "data" / "processed" / "olist_warehouse.duckdb"

con = duckdb.connect(str(DB_PATH))

print("=" * 70)
print("OLIST ANALYTICS DATA WAREHOUSE")
print("=" * 70)


# --------------------------------------------------
# 2. DIMENSION: CUSTOMERS
# --------------------------------------------------

print("\nBuilding dim_customers...")

con.execute("""
    CREATE OR REPLACE TABLE dim_customers AS
    SELECT
        customer_id,
        customer_unique_id,
        customer_zip_code_prefix,
        customer_city,
        customer_state
    FROM stg_customers
""")


# --------------------------------------------------
# 3. DIMENSION: PRODUCTS
# --------------------------------------------------

print("Building dim_products...")

con.execute("""
    CREATE OR REPLACE TABLE dim_products AS
    SELECT
        p.product_id,
        p.product_category_name,
        COALESCE(
            t.product_category_name_english,
            p.product_category_name,
            'Unknown'
        ) AS product_category_english,
        p.product_name_length,
        p.product_description_length,
        p.product_photos_qty,
        p.product_weight_g,
        p.product_length_cm,
        p.product_height_cm,
        p.product_width_cm
    FROM stg_products p
    LEFT JOIN stg_category_translation t
        ON p.product_category_name = t.product_category_name
""")


# --------------------------------------------------
# 4. DIMENSION: SELLERS
# --------------------------------------------------

print("Building dim_sellers...")

con.execute("""
    CREATE OR REPLACE TABLE dim_sellers AS
    SELECT
        seller_id,
        seller_zip_code_prefix,
        seller_city,
        seller_state
    FROM stg_sellers
""")


# --------------------------------------------------
# 5. DIMENSION: DATE
# --------------------------------------------------

print("Building dim_date...")

con.execute("""
    CREATE OR REPLACE TABLE dim_date AS

    WITH date_limits AS (
        SELECT
            CAST(MIN(order_purchase_timestamp) AS DATE) AS min_date,
            CAST(MAX(order_purchase_timestamp) AS DATE) AS max_date
        FROM stg_orders
    ),

    calendar AS (
        SELECT
            CAST(date_value AS DATE) AS full_date
        FROM date_limits,
        generate_series(
            min_date,
            max_date,
            INTERVAL 1 DAY
        ) AS dates(date_value)
    )

    SELECT
        CAST(strftime(full_date, '%Y%m%d') AS INTEGER)
            AS date_key,
        full_date,
        EXTRACT(YEAR FROM full_date) AS year,
        EXTRACT(QUARTER FROM full_date) AS quarter,
        EXTRACT(MONTH FROM full_date) AS month,
        strftime(full_date, '%B') AS month_name,
        EXTRACT(DAY FROM full_date) AS day,
        strftime(full_date, '%A') AS day_name,
        EXTRACT(ISODOW FROM full_date) AS day_of_week,
        CASE
            WHEN EXTRACT(ISODOW FROM full_date) IN (6, 7)
            THEN TRUE
            ELSE FALSE
        END AS is_weekend
    FROM calendar
""")


# --------------------------------------------------
# 6. FACT: ORDER ITEMS
# Grain: one row per order item
# --------------------------------------------------

print("Building fact_order_items...")

con.execute("""
    CREATE OR REPLACE TABLE fact_order_items AS
    SELECT
        oi.order_id,
        oi.order_item_id,
        o.customer_id,
        oi.product_id,
        oi.seller_id,

        CAST(
            strftime(
                CAST(o.order_purchase_timestamp AS DATE),
                '%Y%m%d'
            ) AS INTEGER
        ) AS purchase_date_key,

        o.order_status,

        oi.price,
        oi.freight_value,

        oi.price + oi.freight_value AS item_total_amount

    FROM stg_order_items oi

    INNER JOIN stg_orders o
        ON oi.order_id = o.order_id
""")


# --------------------------------------------------
# 7. FACT: ORDERS
# Grain: one row per order
# --------------------------------------------------

print("Building fact_orders...")

con.execute("""
    CREATE OR REPLACE TABLE fact_orders AS
    SELECT
        order_id,
        customer_id,

        CAST(
            strftime(
                CAST(order_purchase_timestamp AS DATE),
                '%Y%m%d'
            ) AS INTEGER
        ) AS purchase_date_key,

        order_status,
        order_purchase_timestamp,
        order_approved_at,
        order_delivered_carrier_date,
        order_delivered_customer_date,
        order_estimated_delivery_date,

        DATE_DIFF(
            'day',
            CAST(order_purchase_timestamp AS DATE),
            CAST(order_delivered_customer_date AS DATE)
        ) AS delivery_days,

        CASE
            WHEN order_delivered_customer_date IS NOT NULL
             AND order_estimated_delivery_date IS NOT NULL
            THEN CAST(order_delivered_customer_date AS DATE)
                 > CAST(order_estimated_delivery_date AS DATE)
            ELSE NULL
        END AS delivered_late

    FROM stg_orders
""")


# --------------------------------------------------
# 8. FACT: PAYMENTS
# Grain: one row per order payment record
# --------------------------------------------------

print("Building fact_payments...")

con.execute("""
    CREATE OR REPLACE TABLE fact_payments AS
    SELECT
        order_id,
        payment_sequential,
        payment_type,
        payment_installments,
        payment_value
    FROM stg_order_payments
""")


# --------------------------------------------------
# 9. FACT: REVIEWS
# Grain: one row per review-order pair
# --------------------------------------------------

print("Building fact_reviews...")

con.execute("""
    CREATE OR REPLACE TABLE fact_reviews AS
    SELECT
        review_id,
        order_id,
        review_score,
        review_comment_title,
        review_comment_message,
        review_creation_date,
        review_answer_timestamp
    FROM stg_order_reviews
""")


# --------------------------------------------------
# 10. WAREHOUSE VALIDATION
# --------------------------------------------------

print("\n" + "=" * 70)
print("WAREHOUSE TABLE VALIDATION")
print("=" * 70)

warehouse_tables = [
    "dim_customers",
    "dim_products",
    "dim_sellers",
    "dim_date",
    "fact_order_items",
    "fact_orders",
    "fact_payments",
    "fact_reviews"
]

for table_name in warehouse_tables:

    row_count = con.execute(
        f"SELECT COUNT(*) FROM {table_name}"
    ).fetchone()[0]

    print(f"{table_name}: {row_count:,} rows")


print("\nTotal warehouse tables:", len(warehouse_tables))

con.close()

print("\n" + "=" * 70)
print("DATA WAREHOUSE BUILD COMPLETED")
print("=" * 70)
