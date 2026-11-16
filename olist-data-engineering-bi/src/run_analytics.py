
from pathlib import Path
import duckdb

# ============================================================
# PROJECT CONFIGURATION
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parents[1]

DB_PATH = PROJECT_DIR / "data" / "processed" / "olist_warehouse.duckdb"
SQL_DIR = PROJECT_DIR / "sql"
OUTPUT_DIR = PROJECT_DIR / "output"

# Create output directory if it does not exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# DATABASE CONNECTION
# ============================================================

con = duckdb.connect(str(DB_PATH), read_only=True)

print("=" * 80)
print("OLIST BUSINESS ANALYTICS")
print("=" * 80)

sql_files = sorted(SQL_DIR.glob("*.sql"))

successful = 0
failed = 0

print(f"\nFound {len(sql_files)} SQL files.")

try:

    for sql_file in sql_files:

        print("\n" + "=" * 80)
        print(f"ANALYSIS: {sql_file.stem.upper()}")
        print("=" * 80)

        try:

            # Read SQL query
            query = sql_file.read_text(encoding="utf-8")

            # Execute query
            result = con.execute(query).df()

            # Display results
            print(result.to_string(index=False))
            print(f"\nRows returned: {len(result):,}")

            # Export results to CSV
            output_file = OUTPUT_DIR / f"{sql_file.stem}.csv"

            result.to_csv(
                output_file,
                index=False,
                encoding="utf-8-sig"
            )

            print(f"Exported to: {output_file}")

            successful += 1

        except Exception as error:

            print(f"\nERROR: {error}")
            failed += 1

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print("\n" + "=" * 80)
    print("ANALYTICS EXECUTION SUMMARY")
    print("=" * 80)

    print(f"Total SQL files: {len(sql_files)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\nALL ANALYTICS QUERIES COMPLETED SUCCESSFULLY!")
    else:
        print("\nSOME ANALYTICS QUERIES FAILED.")

    print(f"\nCSV files saved in: {OUTPUT_DIR}")

finally:
    con.close()
