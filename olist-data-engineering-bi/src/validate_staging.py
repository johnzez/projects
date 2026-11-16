
from pathlib import Path
import duckdb

PROJECT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_DIR / "data" / "processed" / "olist_warehouse.duckdb"

con = duckdb.connect(str(DB_PATH))

print("=" * 70)
print("STAGING DATA QUALITY VALIDATION")
print("=" * 70)


# --------------------------------------------------
# 1. ROW COUNT VALIDATION
# --------------------------------------------------

print("\n1. ROW COUNT VALIDATION")
print("-" * 70)

table_pairs = {
    "customers": ("raw_customers", "stg_customers"),
    "orders": ("raw_orders", "stg_orders"),
    "order_items": ("raw_order_items", "stg_order_items"),
    "payments": ("raw_order_payments", "stg_order_payments"),
    "reviews": ("raw_order_reviews", "stg_order_reviews"),
    "products": ("raw_products", "stg_products"),
    "sellers": ("raw_sellers", "stg_sellers"),
    "geolocation": ("raw_geolocation", "stg_geolocation"),
    "category_translation": (
        "raw_category_translation",
        "stg_category_translation"
    )
}

for name, (raw_table, stg_table) in table_pairs.items():

    raw_count = con.execute(
        f"SELECT COUNT(*) FROM {raw_table}"
    ).fetchone()[0]

    stg_count = con.execute(
        f"SELECT COUNT(*) FROM {stg_table}"
    ).fetchone()[0]

    status = "PASS" if raw_count == stg_count else "FAIL"

    print(
        f"{name}: RAW={raw_count:,} | "
        f"STAGING={stg_count:,} | {status}"
    )


# --------------------------------------------------
# 2. DATA TYPE CONVERSION VALIDATION
# --------------------------------------------------

print("\n2. DATA TYPE CONVERSION VALIDATION")
print("-" * 70)

conversion_checks = [
    ("orders", "raw_orders", "order_approved_at",
     "stg_orders", "order_approved_at"),

    ("orders", "raw_orders", "order_purchase_timestamp",
     "stg_orders", "order_purchase_timestamp"),

    ("orders", "raw_orders", "order_delivered_customer_date",
     "stg_orders", "order_delivered_customer_date"),

    ("order_items", "raw_order_items", "price",
     "stg_order_items", "price"),

    ("order_items", "raw_order_items", "freight_value",
     "stg_order_items", "freight_value"),

    ("order_items", "raw_order_items", "shipping_limit_date",
     "stg_order_items", "shipping_limit_date"),

    ("payments", "raw_order_payments", "payment_value",
     "stg_order_payments", "payment_value"),

    ("reviews", "raw_order_reviews", "review_score",
     "stg_order_reviews", "review_score"),

    ("products", "raw_products", "product_weight_g",
     "stg_products", "product_weight_g"),

    ("geolocation", "raw_geolocation", "geolocation_lat",
     "stg_geolocation", "geolocation_lat"),

    ("geolocation", "raw_geolocation", "geolocation_lng",
     "stg_geolocation", "geolocation_lng")
]

for name, raw_table, raw_col, stg_table, stg_col in conversion_checks:

    failed = con.execute(f"""
        SELECT COUNT(*)
        FROM {raw_table} r
        JOIN {stg_table} s
          ON r.rowid = s.rowid
        WHERE r.{raw_col} IS NOT NULL
          AND s.{stg_col} IS NULL
    """).fetchone()[0]

    status = "PASS" if failed == 0 else "CHECK"

    print(f"{name} - {raw_col}: {failed} conversion failures [{status}]")


# --------------------------------------------------
# 3. PRIMARY KEY VALIDATION
# --------------------------------------------------

print("\n3. PRIMARY KEY VALIDATION")
print("-" * 70)

primary_keys = {
    "stg_customers": ["customer_id"],
    "stg_orders": ["order_id"],
    "stg_products": ["product_id"],
    "stg_sellers": ["seller_id"],
    "stg_order_items": ["order_id", "order_item_id"],
    "stg_order_payments": ["order_id", "payment_sequential"],
    "stg_order_reviews": ["review_id", "order_id"]
}

for table, keys in primary_keys.items():

    key_expression = ", ".join(keys)

    duplicates = con.execute(f"""
        SELECT COUNT(*)
        FROM (
            SELECT {key_expression}
            FROM {table}
            GROUP BY {key_expression}
            HAVING COUNT(*) > 1
        ) d
    """).fetchone()[0]

    null_condition = " OR ".join(
        f"{key} IS NULL" for key in keys
    )

    null_keys = con.execute(f"""
        SELECT COUNT(*)
        FROM {table}
        WHERE {null_condition}
    """).fetchone()[0]

    print(
        f"{table}: duplicate keys={duplicates}, "
        f"NULL keys={null_keys}"
    )


# --------------------------------------------------
# 4. FOREIGN KEY VALIDATION
# --------------------------------------------------

print("\n4. FOREIGN KEY VALIDATION")
print("-" * 70)

foreign_key_checks = [
    (
        "Orders -> Customers",
        "stg_orders", "customer_id",
        "stg_customers", "customer_id"
    ),
    (
        "Items -> Orders",
        "stg_order_items", "order_id",
        "stg_orders", "order_id"
    ),
    (
        "Items -> Products",
        "stg_order_items", "product_id",
        "stg_products", "product_id"
    ),
    (
        "Items -> Sellers",
        "stg_order_items", "seller_id",
        "stg_sellers", "seller_id"
    ),
    (
        "Payments -> Orders",
        "stg_order_payments", "order_id",
        "stg_orders", "order_id"
    ),
    (
        "Reviews -> Orders",
        "stg_order_reviews", "order_id",
        "stg_orders", "order_id"
    )
]

for name, child, child_col, parent, parent_col in foreign_key_checks:

    unmatched = con.execute(f"""
        SELECT COUNT(*)
        FROM {child} c
        WHERE NOT EXISTS (
            SELECT 1
            FROM {parent} p
            WHERE p.{parent_col} = c.{child_col}
        )
    """).fetchone()[0]

    status = "PASS" if unmatched == 0 else "FAIL"

    print(f"{name}: {unmatched} unmatched [{status}]")


# --------------------------------------------------
# 5. BUSINESS RULE VALIDATION
# --------------------------------------------------

print("\n5. BUSINESS RULE VALIDATION")
print("-" * 70)

business_checks = {
    "Invalid review scores": """
        SELECT COUNT(*)
        FROM stg_order_reviews
        WHERE review_score IS NOT NULL
          AND (review_score < 1 OR review_score > 5)
    """,

    "Negative product prices": """
        SELECT COUNT(*)
        FROM stg_order_items
        WHERE price < 0
    """,

    "Negative freight values": """
        SELECT COUNT(*)
        FROM stg_order_items
        WHERE freight_value < 0
    """,

    "Negative payment values": """
        SELECT COUNT(*)
        FROM stg_order_payments
        WHERE payment_value < 0
    """,

    "Invalid latitude": """
        SELECT COUNT(*)
        FROM stg_geolocation
        WHERE geolocation_lat IS NOT NULL
          AND (geolocation_lat < -90 OR geolocation_lat > 90)
    """,

    "Invalid longitude": """
        SELECT COUNT(*)
        FROM stg_geolocation
        WHERE geolocation_lng IS NOT NULL
          AND (geolocation_lng < -180 OR geolocation_lng > 180)
    """
}

for check_name, query in business_checks.items():

    violations = con.execute(query).fetchone()[0]

    status = "PASS" if violations == 0 else "CHECK"

    print(f"{check_name}: {violations} [{status}]")


# --------------------------------------------------
# 6. FINISH
# --------------------------------------------------

con.close()

print("\n" + "=" * 70)
print("STAGING VALIDATION COMPLETED")
print("=" * 70)
