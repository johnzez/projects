
from pathlib import Path
import duckdb

PROJECT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_DIR / "data" / "processed" / "olist_warehouse.duckdb"

con = duckdb.connect(str(DB_PATH))

passed = 0
failed = 0


def check(name, condition, details=""):
    global passed, failed

    if condition:
        passed += 1
        status = "PASS"
    else:
        failed += 1
        status = "FAIL"

    print(f"[{status}] {name}")

    if details:
        print(f"       {details}")


def get_value(query):
    return con.execute(query).fetchone()[0]


print("=" * 70)
print("OLIST DATA WAREHOUSE VALIDATION")
print("=" * 70)


# ============================================================
# 1. ROW COUNT VALIDATION
# ============================================================

print("\n1. ROW COUNT VALIDATION")
print("-" * 70)

row_count_checks = {
    "dim_customers": ("stg_customers",),
    "dim_products": ("stg_products",),
    "dim_sellers": ("stg_sellers",),
    "fact_order_items": ("stg_order_items",),
    "fact_orders": ("stg_orders",),
    "fact_payments": ("stg_order_payments",),
    "fact_reviews": ("stg_order_reviews",),
}

for warehouse_table, (staging_table,) in row_count_checks.items():
    warehouse_count = get_value(
        f"SELECT COUNT(*) FROM {warehouse_table}"
    )

    staging_count = get_value(
        f"SELECT COUNT(*) FROM {staging_table}"
    )

    check(
        f"{warehouse_table} row count",
        warehouse_count == staging_count,
        f"Warehouse: {warehouse_count:,} | Staging: {staging_count:,}"
    )


# ============================================================
# 2. PRIMARY KEY VALIDATION
# ============================================================

print("\n2. PRIMARY KEY VALIDATION")
print("-" * 70)


def check_primary_key(table, columns):
    column_list = ", ".join(columns)

    null_conditions = " OR ".join(
        f"{column} IS NULL" for column in columns
    )

    null_count = get_value(f"""
        SELECT COUNT(*)
        FROM {table}
        WHERE {null_conditions}
    """)

    duplicate_count = get_value(f"""
        SELECT COUNT(*)
        FROM (
            SELECT {column_list}
            FROM {table}
            GROUP BY {column_list}
            HAVING COUNT(*) > 1
        ) duplicates
    """)

    check(
        f"{table} primary key",
        null_count == 0 and duplicate_count == 0,
        f"Null keys: {null_count:,} | Duplicate key groups: {duplicate_count:,}"
    )


check_primary_key("dim_customers", ["customer_id"])
check_primary_key("dim_products", ["product_id"])
check_primary_key("dim_sellers", ["seller_id"])
check_primary_key("dim_date", ["date_key"])

check_primary_key(
    "fact_order_items",
    ["order_id", "order_item_id"]
)

check_primary_key(
    "fact_orders",
    ["order_id"]
)

check_primary_key(
    "fact_payments",
    ["order_id", "payment_sequential"]
)

check_primary_key(
    "fact_reviews",
    ["review_id", "order_id"]
)


# ============================================================
# 3. FOREIGN KEY VALIDATION
# ============================================================

print("\n3. FOREIGN KEY VALIDATION")
print("-" * 70)


def check_foreign_key(name, query):
    unmatched = get_value(query)

    check(
        name,
        unmatched == 0,
        f"Unmatched records: {unmatched:,}"
    )


# fact_order_items -> dimensions

check_foreign_key(
    "fact_order_items -> dim_customers",
    """
    SELECT COUNT(*)
    FROM fact_order_items f
    LEFT JOIN dim_customers d
        ON f.customer_id = d.customer_id
    WHERE d.customer_id IS NULL
    """
)

check_foreign_key(
    "fact_order_items -> dim_products",
    """
    SELECT COUNT(*)
    FROM fact_order_items f
    LEFT JOIN dim_products d
        ON f.product_id = d.product_id
    WHERE d.product_id IS NULL
    """
)

check_foreign_key(
    "fact_order_items -> dim_sellers",
    """
    SELECT COUNT(*)
    FROM fact_order_items f
    LEFT JOIN dim_sellers d
        ON f.seller_id = d.seller_id
    WHERE d.seller_id IS NULL
    """
)

check_foreign_key(
    "fact_order_items -> dim_date",
    """
    SELECT COUNT(*)
    FROM fact_order_items f
    LEFT JOIN dim_date d
        ON f.purchase_date_key = d.date_key
    WHERE d.date_key IS NULL
    """
)


# fact_orders -> dimensions

check_foreign_key(
    "fact_orders -> dim_customers",
    """
    SELECT COUNT(*)
    FROM fact_orders f
    LEFT JOIN dim_customers d
        ON f.customer_id = d.customer_id
    WHERE d.customer_id IS NULL
    """
)

check_foreign_key(
    "fact_orders -> dim_date",
    """
    SELECT COUNT(*)
    FROM fact_orders f
    LEFT JOIN dim_date d
        ON f.purchase_date_key = d.date_key
    WHERE d.date_key IS NULL
    """
)


# Other fact tables -> fact_orders

check_foreign_key(
    "fact_payments -> fact_orders",
    """
    SELECT COUNT(*)
    FROM fact_payments f
    LEFT JOIN fact_orders o
        ON f.order_id = o.order_id
    WHERE o.order_id IS NULL
    """
)

check_foreign_key(
    "fact_reviews -> fact_orders",
    """
    SELECT COUNT(*)
    FROM fact_reviews f
    LEFT JOIN fact_orders o
        ON f.order_id = o.order_id
    WHERE o.order_id IS NULL
    """
)


# ============================================================
# 4. BUSINESS RULE VALIDATION
# ============================================================

print("\n4. BUSINESS RULE VALIDATION")
print("-" * 70)


negative_prices = get_value("""
    SELECT COUNT(*)
    FROM fact_order_items
    WHERE price < 0
""")

check(
    "No negative item prices",
    negative_prices == 0,
    f"Invalid records: {negative_prices:,}"
)


negative_freight = get_value("""
    SELECT COUNT(*)
    FROM fact_order_items
    WHERE freight_value < 0
""")

check(
    "No negative freight values",
    negative_freight == 0,
    f"Invalid records: {negative_freight:,}"
)


negative_payments = get_value("""
    SELECT COUNT(*)
    FROM fact_payments
    WHERE payment_value < 0
""")

check(
    "No negative payment values",
    negative_payments == 0,
    f"Invalid records: {negative_payments:,}"
)


invalid_delivery_days = get_value("""
    SELECT COUNT(*)
    FROM fact_orders
    WHERE delivery_days < 0
""")

check(
    "No negative delivery durations",
    invalid_delivery_days == 0,
    f"Invalid records: {invalid_delivery_days:,}"
)


invalid_review_scores = get_value("""
    SELECT COUNT(*)
    FROM fact_reviews
    WHERE review_score NOT BETWEEN 1 AND 5
       OR review_score IS NULL
""")

check(
    "Review scores between 1 and 5",
    invalid_review_scores == 0,
    f"Invalid records: {invalid_review_scores:,}"
)


# ============================================================
# 5. WAREHOUSE RELATIONSHIP / GRAIN CHECKS
# ============================================================

print("\n5. WAREHOUSE GRAIN VALIDATION")
print("-" * 70)

# Each order must have exactly one record in fact_orders.

orders_with_multiple_records = get_value("""
    SELECT COUNT(*)
    FROM (
        SELECT order_id
        FROM fact_orders
        GROUP BY order_id
        HAVING COUNT(*) > 1
    ) duplicates
""")

check(
    "One fact_orders record per order",
    orders_with_multiple_records == 0,
    f"Orders with multiple records: {orders_with_multiple_records:,}"
)


# Fact order items must preserve the original order item grain.

source_items = get_value("""
    SELECT COUNT(*)
    FROM stg_order_items
""")

warehouse_items = get_value("""
    SELECT COUNT(*)
    FROM fact_order_items
""")

check(
    "Order item grain preserved",
    source_items == warehouse_items,
    f"Source: {source_items:,} | Warehouse: {warehouse_items:,}"
)


# Check whether the product translation join created extra rows.

source_products = get_value("""
    SELECT COUNT(*)
    FROM stg_products
""")

warehouse_products = get_value("""
    SELECT COUNT(*)
    FROM dim_products
""")

check(
    "Product translation did not multiply rows",
    source_products == warehouse_products,
    f"Source: {source_products:,} | Warehouse: {warehouse_products:,}"
)


# ============================================================
# 6. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("VALIDATION SUMMARY")
print("=" * 70)

print(f"Passed checks: {passed}")
print(f"Failed checks: {failed}")
print(f"Total checks:  {passed + failed}")

if failed == 0:
    print("\nALL WAREHOUSE VALIDATIONS PASSED!")
else:
    print("\nSOME VALIDATIONS FAILED. REVIEW THE RESULTS ABOVE.")

print("=" * 70)

con.close()
