import sqlite3
from .config import WAREHOUSE_DB

def validate_data(source_sales):
    """
    Validate transformed source sales data against SQLite warehouse.

    Returns:
      dict with source_valid_rows, warehouse_rows, duplicate_order_ids,
      source_total_sales, warehouse_total_sales, status ("PASS" / "FAIL").
    """
    conn = sqlite3.connect(WAREHOUSE_DB)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM fact_sales;")
    warehouse_rows = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM fact_sales;")
    duplicate_order_ids = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(sales_amount) FROM fact_sales;")
    wh_sales_res = cursor.fetchone()[0]
    warehouse_total_sales = float(round(wh_sales_res or 0.0, 2))

    conn.close()

    source_valid_rows = int(len(source_sales))
    source_total_sales = float(round(source_sales["sales_amount"].sum(), 2))

    is_pass = (
        source_valid_rows == warehouse_rows
        and duplicate_order_ids == 0
        and abs(source_total_sales - warehouse_total_sales) < 1e-4
    )

    return {
        "source_valid_rows": source_valid_rows,
        "warehouse_rows": warehouse_rows,
        "duplicate_order_ids": duplicate_order_ids,
        "source_total_sales": source_total_sales,
        "warehouse_total_sales": warehouse_total_sales,
        "status": "PASS" if is_pass else "FAIL",
    }

