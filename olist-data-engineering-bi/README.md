# Olist E-Commerce: Data Engineering & Business Intelligence Project

An end-to-end analytics project built on the public [Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). Raw CSV files are ingested into an embedded DuckDB database, cleaned and typed in a staging layer, modeled as a star-schema data warehouse, validated with automated checks, analyzed with SQL, exported to CSV with Python, and presented in a 3-page Power BI report.

## Project Highlights

- **1,650,922** raw rows across 9 CSV files ingested and processed
- 3-layer pipeline: **RAW → STAGING → WAREHOUSE**
- Dimensional model with **4 dimension tables** and **4 fact tables**
- **31/31** warehouse validation checks passed
- **5** SQL analytical queries, automated through a Python runner
- **3-page** Power BI report with figures reconciled against the SQL outputs

## Tech Stack

| Area | Tool |
|---|---|
| Language | Python |
| Database | DuckDB (embedded, file-based) |
| Query language | SQL |
| Visualization | Power BI |
| Editor | Visual Studio Code |
| Data format | CSV |

**Not used in this project:** PostgreSQL, Apache Airflow, Docker, cloud infrastructure, or production orchestration. PostgreSQL was initially considered, but installation problems led to the decision to use DuckDB through Python instead.

## Pipeline Architecture

```text
data/raw/*.csv
      │  src/load_raw_data.py
      ▼
RAW layer        raw_* tables, every column kept as VARCHAR
      │  src/build_staging.py   (+ src/validate_staging.py)
      ▼
STAGING layer    stg_* tables, proper data types (TRY_CAST)
      │  src/build_warehouse.py (+ src/validate_warehouse.py)
      ▼
WAREHOUSE        dim_* and fact_* tables
      │  src/run_analytics.py   (sql/*.sql)
      ▼
output/*.csv  ──►  Power BI report
```

Database file: `data/processed/olist_warehouse.duckdb`

### 1. RAW layer
`src/load_raw_data.py` loads all 9 CSV files into `raw_*` tables. All fields are stored as `VARCHAR` on purpose, so the original representation is preserved and type conversion happens in a separate, controlled step. The script uses `CREATE OR REPLACE TABLE`, so it can be re-run safely.

### 2. STAGING layer
`src/build_staging.py` converts the raw fields into proper types using `TRY_CAST`:

- IDs stay `VARCHAR`
- ZIP code prefixes stay `VARCHAR` to preserve leading zeros
- Monetary values become `DECIMAL(12,2)`
- Dates and times become `TIMESTAMP`
- Coordinates become `DOUBLE`

`src/validate_staging.py` checks raw vs. staging row counts, type conversion failures (11 conversions checked, 0 failures), primary key uniqueness, NULL keys, foreign key integrity (0 unmatched records), and invalid business values (review scores, negative amounts, invalid coordinates). All checks passed.

### 3. WAREHOUSE layer
`src/build_warehouse.py` builds the dimensional model.

| Table | Type | Rows | Grain |
|---|---|---:|---|
| `dim_customers` | Dimension | 99,441 | One row per customer |
| `dim_products` | Dimension | 32,951 | One row per product (includes English category names) |
| `dim_sellers` | Dimension | 3,095 | One row per seller |
| `dim_date` | Dimension | 774 | One row per day |
| `fact_order_items` | Fact | 112,650 | One row per order item |
| `fact_orders` | Fact | 99,441 | One row per order |
| `fact_payments` | Fact | 103,886 | One row per payment sequence |
| `fact_reviews` | Fact | 99,224 | One row per `(review_id, order_id)` |

`src/validate_warehouse.py` runs **31 checks** (row counts, primary and composite keys, foreign keys, NULL keys, business rules, fact table grain, and product translation join multiplication). Result: **31 passed, 0 failed**.

## Key Design Decisions

- **Separate fact tables to avoid join fanout.** One order can have many items and many payment records. Joining them directly would multiply rows and inflate monetary totals, so each fact table keeps its own grain.
- **Composite key for reviews.** The same `review_id` can appear with different `order_id` values (789 duplicated review IDs, 1,603 rows involved), so reviews are keyed on `(review_id, order_id)`.
- **No blind deduplication of geolocation.** The geolocation file has 261,831 exact duplicate rows out of 1,000,163. It was not deduplicated blindly and is **not yet integrated** into the warehouse.
- **NULLs are not deleted automatically.** Missing timestamps were examined per order status to see whether they are expected from the business process (for example, undelivered orders have no delivery date).
- **Unknown category fallback.** Products with no English translation, or no category, are labeled `Unknown`.
- **`price`, `freight_value` and `item_total_amount` are kept distinct.** `price` is product value, `freight_value` is shipping cost, and `item_total_amount` combines both. `item_total_amount` is not treated as pure product revenue.

## SQL Analytics

| File | Purpose |
|---|---|
| `sql/01_monthly_sales.sql` | Monthly orders, items and product sales (delivered orders) |
| `sql/02_category_performance.sql` | Sales and average price by product category |
| `sql/03_seller_performance.sql` | Orders, items, sales and freight by seller |
| `sql/04_delivery_performance.sql` | Delivery time and late delivery statistics |
| `sql/05_payment_analysis.sql` | Payment methods, values and installments |

`src/run_analytics.py` discovers every `.sql` file in `sql/`, runs each one against DuckDB in read-only mode, handles errors per query, and exports each result to `output/` as a UTF-8 CSV with BOM (`utf-8-sig`).

## Power BI Report

The report is built from the five CSV exports in `output/`.

**Page 1: Sales Overview**
KPI cards (product sales, delivered orders, items sold, average delivery time), Monthly Product Sales (line), Monthly Orders (column).

**Page 2: Product & Seller Performance**
KPI cards (categories, sellers, items sold, average item price), Top 5 Product Categories, Top 5 Sellers by Sales, Average Item Price for the top 10 categories by sales.

**Page 3: Delivery & Payments**
KPI cards (delivered orders, average delivery days, late deliveries, late delivery rate), On-time vs Late Deliveries, Payment Methods Distribution, Average Installments by Payment Method.

<!-- Add screenshots to a /screenshots folder and uncomment:
![Sales Overview](screenshots/01_sales_overview.png)
![Product & Seller Performance](screenshots/02_product_seller.png)
![Delivery & Payments](screenshots/03_delivery_payments.png)
-->

## Key Results

All figures below are for **delivered orders** only, unless stated otherwise.

| Metric | Value |
|---|---:|
| Product sales (excluding freight) | ~13.22M BRL |
| Delivered orders | 96,478 |
| Items sold | ~110.2K |
| Average item price | ~119.98 BRL |
| Average delivery time | 12.5 days |
| Late deliveries | 6,534 (6.77%) |
| Product categories | 73 (plus `Unknown`) |
| Sellers with delivered sales | ~2,970 of 3,095 |

- **Peak month:** November 2017, with 987,765.37 BRL in product sales, 7,289 delivered orders and 8,475 items sold.
- **Top categories by sales:** `health_beauty` (1,233,131.72 BRL), `watches_gifts` (1,166,176.98 BRL), `bed_bath_table` (1,023,434.76 BRL).
- **Highest average item price:** `watches_gifts` (~199 BRL).
- **Payments:** credit card dominates, with about 78% of total payment value (12.54M BRL across 76,795 records), followed by boleto (2.87M BRL). Credit card payments average 3.51 installments.

## Assumptions and Limitations

- **Delivered orders only.** Sales, orders and items KPIs exclude other statuses (shipped, canceled, unavailable, and so on). The dataset has 99,441 orders in total; 96,478 are delivered.
- **Product sales exclude freight.** Only `price` is summed.
- **Partial months.** September 2016 and December 2016 are partial periods, and November 2016 has no data. The monthly series covers 23 months, from September 2016 to August 2018.
- **Late delivery rate denominator.** The 6.77% is computed over the 96,470 delivered orders that have a non-NULL `delivered_late` value, not all 96,478.
- **Payment records are not orders.** An order can have several payment records, so record counts and distinct order counts differ (for example, vouchers: 5,775 records across 3,866 orders).
- **Average installments are per payment record,** not per order.
- **`not_defined` payment type** has only 3 records with a value of 0 and is not meaningful for the installments chart.
- **`Unknown` category** accounts for 1,537 items and about 170.7K BRL (roughly 1.3% of product sales). It is kept in totals so they reconcile across pages, but it is not counted as a real category in the Total Categories KPI.
- **Currency** is Brazilian Real (BRL).
- **Geolocation** is not part of the warehouse yet.
- **Power BI decimals:** when importing the CSVs into a Greek-locale Power BI, decimal columns must be converted with *Transform → Data Type → Using Locale* (Decimal Number, English (United States)). Otherwise `987765.37` is read as `98776537`.

## How to Run

1. Download the dataset from Kaggle and place the 9 CSV files in `data/raw/`.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the pipeline in order:
   ```bash
   python src/load_raw_data.py
   python src/build_staging.py
   python src/validate_staging.py
   python src/build_warehouse.py
   python src/validate_warehouse.py
   python src/run_analytics.py
   ```
4. Open the Power BI report and refresh the data (point the sources to your local `output/` folder if needed).

## Project Structure

```text
Sales-Data-Engineering/
├── data/
│   ├── raw/                  # 9 source CSV files (not included, see Kaggle link)
│   └── processed/
│       └── olist_warehouse.duckdb
├── src/
│   ├── load_raw_data.py
│   ├── build_staging.py
│   ├── validate_staging.py
│   ├── build_warehouse.py
│   ├── validate_warehouse.py
│   └── run_analytics.py
├── sql/                      # 5 analytical queries
├── output/                   # CSV exports used by Power BI
├── README.md
└── requirements.txt
```

## Possible Next Steps

- Integrate geolocation into the warehouse with a reviewed deduplication strategy
- Add review score analysis using `fact_reviews`
- Add customer-level analysis (repeat purchases, regional sales)
- Connect Power BI directly to the warehouse instead of CSV exports

## Author

Ioannis Zezas
