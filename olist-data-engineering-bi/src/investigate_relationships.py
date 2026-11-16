
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_DIR / "data" / "raw"

def load_dataset(filename):
    return pd.read_csv(RAW_DIR / filename, low_memory=False)


# Load datasets
customers = load_dataset("olist_customers_dataset.csv")
orders = load_dataset("olist_orders_dataset.csv")
products = load_dataset("olist_products_dataset.csv")
sellers = load_dataset("olist_sellers_dataset.csv")
items = load_dataset("olist_order_items_dataset.csv")
payments = load_dataset("olist_order_payments_dataset.csv")
reviews = load_dataset("olist_order_reviews_dataset.csv")


print("=" * 65)
print("PRIMARY KEY VALIDATION")
print("=" * 65)

primary_keys = {
    "customers": (customers, ["customer_id"]),
    "orders": (orders, ["order_id"]),
    "products": (products, ["product_id"]),
    "sellers": (sellers, ["seller_id"]),
    "order_items": (items, ["order_id", "order_item_id"]),
    "payments": (payments, ["order_id", "payment_sequential"]),
    "reviews": (reviews, ["review_id"])
}

for name, (df, keys) in primary_keys.items():

    duplicate_count = int(df.duplicated(subset=keys).sum())

    print(
        f"{name}: {duplicate_count} duplicate primary keys"
    )


print("\n" + "=" * 65)
print("FOREIGN KEY VALIDATION")
print("=" * 65)


def check_foreign_key(child, child_column, parent, parent_column, name):

    unmatched = ~child[child_column].isin(parent[parent_column])

    count = int(unmatched.sum())

    print(f"{name}: {count} unmatched records")


check_foreign_key(
    orders, "customer_id",
    customers, "customer_id",
    "Orders -> Customers"
)

check_foreign_key(
    items, "order_id",
    orders, "order_id",
    "Order Items -> Orders"
)

check_foreign_key(
    items, "product_id",
    products, "product_id",
    "Order Items -> Products"
)

check_foreign_key(
    items, "seller_id",
    sellers, "seller_id",
    "Order Items -> Sellers"
)

check_foreign_key(
    payments, "order_id",
    orders, "order_id",
    "Payments -> Orders"
)

check_foreign_key(
    reviews, "order_id",
    orders, "order_id",
    "Reviews -> Orders"
)


print("\n" + "=" * 65)
print("ORDER STATUS ANALYSIS")
print("=" * 65)

print("\nOrder status distribution:")
print(orders["order_status"].value_counts(dropna=False).to_string())

date_columns = [
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date"
]

print("\nMissing dates grouped by order status:")

print(
    orders.groupby("order_status")[date_columns]
    .apply(lambda group: group.isna().sum())
    .to_string()
)

print("\nRelationship investigation completed.")
