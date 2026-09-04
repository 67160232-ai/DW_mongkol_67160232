import sqlite3
from .config import WAREHOUSE_DB

def load_data(customers, products, sales):
    """
    Create/load SQLite tables:
      - dim_customer
      - dim_product
      - fact_sales

    Ensures idempotency using PRIMARY KEY constraints and INSERT OR REPLACE logic.
    """
    WAREHOUSE_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(WAREHOUSE_DB)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_customer (
        customer_id TEXT PRIMARY KEY,
        name TEXT,
        province TEXT,
        email TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_product (
        product_id TEXT PRIMARY KEY,
        product_name TEXT,
        category TEXT,
        price REAL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fact_sales (
        order_id TEXT PRIMARY KEY,
        customer_id TEXT,
        product_id TEXT,
        order_date TEXT,
        qty INTEGER,
        unit_price REAL,
        discount_pct REAL,
        sales_amount REAL
    );
    """)

    # Insert / Upsert dim_customer
    cust_records = customers[["customer_id", "name", "province", "email"]].to_dict(orient="records")
    cursor.executemany("""
    INSERT OR REPLACE INTO dim_customer (customer_id, name, province, email)
    VALUES (:customer_id, :name, :province, :email);
    """, cust_records)

    # Insert / Upsert dim_product
    prod_records = products[["product_id", "product_name", "category", "price"]].to_dict(orient="records")
    cursor.executemany("""
    INSERT OR REPLACE INTO dim_product (product_id, product_name, category, price)
    VALUES (:product_id, :product_name, :category, :price);
    """, prod_records)

    # Insert / Upsert fact_sales
    sales_records = sales[[
        "order_id", "customer_id", "product_id", "order_date",
        "qty", "unit_price", "discount_pct", "sales_amount"
    ]].to_dict(orient="records")
    cursor.executemany("""
    INSERT OR REPLACE INTO fact_sales (order_id, customer_id, product_id, order_date, qty, unit_price, discount_pct, sales_amount)
    VALUES (:order_id, :customer_id, :product_id, :order_date, :qty, :unit_price, :discount_pct, :sales_amount);
    """, sales_records)

    conn.commit()
    conn.close()

